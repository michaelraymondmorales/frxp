import io
import gzip
import redis
import numpy as np
from PIL import Image
from frxp.core import fractal_calcs
from frxp.core import normalize_map
from frxp.core import coord_converter
from frxp.core import coord_generator
from celery import Task
from celery_app import celery_app

# Initialize the Redis client. This client is used by the worker to store the cached data.
# The connection string should match the one used by Celery.
# We're using a specific port to match our docker-compose file
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Function dispatch dictionary
FRACTAL_RENDER_FUNCTIONS = {
'Julia': fractal_calcs.julia_numba,
'Multi-julia': fractal_calcs.julia_numba,
'Mandelbrot': fractal_calcs.mandelbrot_numba,
'Multi-mandelbrot': fractal_calcs.mandelbrot_numba}

@celery_app.task(bind=True)
def calculate_fractal(self, 
                      fractal_type: str, 
                      x_center: float, 
                      x_span: float, 
                      y_center: float, 
                      y_span: float, 
                      c_real: float, 
                      c_imag: float, 
                      power: float, 
                      resolution: int, 
                      iterations: int, 
                      bailout: float, 
                      fixed_iteration: int, 
                      trap_type: int, 
                      trap_x1: float, 
                      trap_y1: float, 
                      trap_x2: float, 
                      trap_y2: float, 
                      trap_x3: float, 
                      trap_y3: float,
                      main_cache_key: str):
    """
    Performs the fractal calculation as the first step of a Celery task chain.
    
    This task's sole purpose is to compute the raw NumPy arrays from the given
    fractal parameters and cache them. This design allows for subsequent tasks
    to consume the raw data for different purposes (e.g., rendering a PNG vs.
    returning a raw binary file).
    
    Args:
        self: The task instance itself, automatically bound by Celery.
        fractal_type (str): The type of fractal to render (e.g., 'Mandelbrot').
        x_center (float): The x-coordinate of the center of the viewport.
        x_span (float): The horizontal span of the viewport.
        y_center (float): The y-coordinate of the center of the viewport.
        y_span (float): The vertical span of the viewport.
        c_real (float): The real component of the Julia set constant.
        c_imag (float): The imaginary component of the Julia set constant.
        power (float): The power to raise Z to in the fractal formula.
        resolution (int): The resolution of the resulting map (width and height).
        iterations (int): The maximum number of iterations.
        bailout (float): The bailout radius.
        fixed_iteration (int): A fixed iteration value for specific map calculations.
        trap_type (int): The type of orbit trap to use.
        trap_x1 (float): x-coordinate of the first orbit trap point.
        trap_y1 (float): y-coordinate of the first orbit trap point.
        trap_x2 (float): x-coordinate of the second orbit trap point.
        trap_y2 (float): y-coordinate of the second orbit trap point.
        trap_x3 (float): x-coordinate of the third orbit trap point.
        trap_y3 (float): y-coordinate of the third orbit trap point.
        main_cache_key (str): Cache key created with hashed fractal parameters. 

    Returns:
        tuple: A tuple of 18 NumPy arrays, each representing a different map
               calculated by the fractal function.
    
    Raises:
        ValueError: If an invalid fractal type is provided.
        Exception: Catches and propagates any other exceptions that occur
                   during the calculation, updating the task state.
    """
    try:
        maps = [
            'iterations_map',
            'normalized_iterations_map',
            'magnitudes_map',
            'initial_angles_map',
            'final_angles_map',
            'distance_map',
            'final_derivative_magnitude_map',
            'min_distance_to_trap_map',
            'min_distance_iteration_map',
            'derivative_bailout_map',
            'final_Z_real_map',
            'final_Z_imag_map',
            'final_derivative_real_map',
            'final_derivative_imag_map',
            'bailout_location_real_map',
            'bailout_location_imag_map',
            'final_Z_real_at_fixed_iteration_map',
            'final_Z_imag_at_fixed_iteration_map']

        # Get the correct calculation function based on fractal type.
        fractal_function = FRACTAL_RENDER_FUNCTIONS.get(fractal_type)
        if not fractal_function:
            raise ValueError(f"Invalid fractal type: {fractal_type}")

        trap_params = (trap_type, trap_x1, trap_y1, trap_x2, trap_y2, trap_x3, trap_y3)

        x_min, x_max, y_min, y_max = coord_converter.convert_to_minmax(x_center,
                                                                       x_span,
                                                                       y_center,
                                                                       y_span)

        x_coords, y_coords = coord_generator.generate_coords(x_min,
                                                             x_max,
                                                             y_min,
                                                             y_max,
                                                             resolution)

        # Common arguments for all fractal types
        fractal_calc_args = {'x_coords': x_coords,
                             'y_coords': y_coords,
                             'power': power,
                             'iterations': iterations,
                             'bailout': bailout,
                             'fixed_iteration': fixed_iteration,
                             'trap_params': trap_params}

        if fractal_type in ['Julia', 'Multi-julia']:         
            # Sanity check for Julia fractals
            if c_real is None or c_imag is None:
                raise ValueError(f"Fractal type '{fractal_type}' requires 'c_real' and 'c_imag' to be non-None values.")       
            
            # Add Julia-specific arguments
            fractal_calc_args['c_real'] = c_real
            fractal_calc_args['c_imag'] = c_imag
            
            map_tuple = fractal_function(**fractal_calc_args)

        elif fractal_type in ['Mandelbrot', 'Multi-mandelbrot']:
            map_tuple = fractal_function(**fractal_calc_args)
            
        else:
            # This 'else' should not be reached if FRACTAL_RENDER_FUNCTIONS is comprehensive
            raise ValueError(f"Unhandled fractal type in renderer: {fractal_type}")
      
        # Loop through the tuple and save each raw map to Redis.
        for i, map_name in enumerate(maps):
            map_array = map_tuple[i]
            # Convert NumPy array to a compressed byte string.
            map_bytes = map_array.astype(np.float64).tobytes()
            compressed_data = gzip.compress(map_bytes)
            
            # Store the raw, compressed data in Redis with an expiration time (e.g., 24 hours).
            redis_client.set(f'{main_cache_key}_{map_name}_raw', compressed_data, ex=86400) 

        # Return a success message and the list of keys saved to the cache.
        return {"status": "success", "message": f"Successfully calculated and saved all raw maps with key: {main_cache_key}"}

    except Exception as e:
        # If an error occurs, the task will fail and the exception will be stored in the result backend.
        return {"status": "failure", "error": str(e)}

@celery_app.task(bind=True)
def process_and_save_png_map(self: Task, 
                             main_cache_key: str, 
                             map_name: str, 
                             resolution: int, 
                             iterations: int, 
                             fixed_iteration: int):
    """
    Celery task to generate a single PNG from a raw map and save it to Redis.

    This task is triggered on-demand by the main Flask API. It fetches the raw,
    compressed map data, decompresses it, normalizes it, and saves the resulting
    PNG to the Redis cache.
    """
    try:
        # Construct the key for the raw map
        raw_cache_key = f'{main_cache_key}_{map_name}_raw'
        
        # Get the raw, compressed data from Redis
        cached_raw_data = redis_client.get(raw_cache_key)
        if not cached_raw_data:
            raise ValueError("Raw map data not found in cache.")
        
        # Decompress and reshape the raw data
        decompressed_data = gzip.decompress(cached_raw_data)
        map_array = np.frombuffer(decompressed_data, dtype=np.float64)
        map_array = map_array.reshape(resolution, resolution)

        # Normalize the map to a [0, 1] range
        norm_map_array = normalize_map.normalize_map(map_array, map_name, iterations, fixed_iteration)
        norm_map_array = np.flipud(norm_map_array)
        # Convert the normalized array to an 8-bit image and save to buffer
        img = Image.fromarray((norm_map_array * 255).astype(np.uint8))
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        # Cache the newly generated PNG and set an expiration time
        png_cache_key = f'{main_cache_key}_{map_name}_png'
        redis_client.set(png_cache_key, img_io.getvalue(), ex=86400)
        
        return {"status": "success", "message": f"Successfully generated and saved PNG for map: {map_name}"}

    except Exception as e:
        return {"status": "failure", "error": str(e)}
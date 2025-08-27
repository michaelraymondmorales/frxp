import hashlib
import redis
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from flask_compress import Compress
from celery.result import AsyncResult
from celery_app import celery_app
from celery_worker import calculate_fractal, process_and_save_png_map

# Create the Flask application instance.
app = Flask(__name__)
CORS(app) # Enable CORS for all routes
Compress(app)

# Initialize the Redis client. This client is used by the main API server to check the cache.
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

@app.route('/status')
def status():
    """
    A simple status endpoint to check if the API is running.
    """
    return jsonify({"status": "healthy"})

@app.route('/calculate_map', methods=['GET'])
def calculate_map():
    """
    Handles GET requests to start a fractal map calculation.
    
    This endpoint does not return the map directly. Instead, it queues
    a Celery task and returns a task ID, which the client can use to
    check the status and retrieve the result.
    
    The request should include the following URL parameters:
    - fractal_type (str): The type of fractal to render.
    - params (JSON string): A JSON string of the fractal calculation parameters.
    """
    try:
        # Get parameters from the request
        fractal_type = str(request.args.get('fractal_type', 'Mandelbrot')).capitalize()
        x_center = float(request.args.get('x_center', -1.0))
        x_span = float(request.args.get('x_span', 1.0)) 
        y_center = float(request.args.get('y_center', 0.0))
        y_span = float(request.args.get('y_span', 1.0)) 
        c_real = float(request.args.get('c_real', 0.0))
        c_imag = float(request.args.get('c_imag', 0.0))
        power = float(request.args.get('power', 2.0)) 
        resolution = int(request.args.get('resolution', 512))
        iterations = int(request.args.get('iterations', 512)) 
        bailout = float(request.args.get('bailout', 4.0))
        fixed_iteration = int(request.args.get('fixed_iteration', 20))
        trap_type = int(request.args.get('trap_type', 0))
        trap_x1 = float(request.args.get('trap_x1', 0.0))
        trap_y1 = float(request.args.get('trap_y1', 0.0))
        trap_x2 = float(request.args.get('trap_x2', 0.0))
        trap_y2 = float(request.args.get('trap_y2', 0.0))
        trap_x3 = float(request.args.get('trap_x3', 0.0))
        trap_y3 = float(request.args.get('trap_y3', 0.0))

        # We'll use a single cache key to represent the entire fractal calculation
        cache_key_data = f'{fractal_type}_{x_center}_{x_span}_{y_center}_{y_span}_{c_real}_{c_imag}_{power}_{resolution}_{iterations}_{bailout}_{fixed_iteration}_{trap_type}_{trap_x1}_{trap_y1}_{trap_x2}_{trap_y2}_{trap_x3}_{trap_y3}'
        main_cache_key = hashlib.sha256(cache_key_data.encode('utf-8')).hexdigest()

        # Check if the result is already in the Redis cache. We'll check for one raw map.
        if redis_client.exists(f'{main_cache_key}_iterations_map_raw'):
            return jsonify({
                "status": "cached",
                "message": "The fractal maps for these parameters already exist in the cache."
            }), 200

        # Start the calculation task
        result = calculate_fractal.apply_async(
            args=(fractal_type, x_center, x_span, y_center, y_span, c_real, c_imag, power, 
                  resolution, iterations, bailout, fixed_iteration, trap_type, 
                  trap_x1, trap_y1, trap_x2, trap_y2, trap_x3, trap_y3, main_cache_key))

        # Return the task ID to the client
        return jsonify({
            "status": "calculating",
            "task_id": result.id,
            "message": "Calculation queued successfully."
        }), 202

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

@app.route('/get_map', methods=['GET'])
def get_map():
    """
    Handles GET requests to retrieve a single fractal map from the cache.
    
    The request should include the following URL parameters:
    - map_name (str): The name of the specific map to retrieve.
    - map_type (str): 'png' or 'raw', to specify the format.
    - fractal_type (str): The type of fractal to render.
    - params (JSON string): A JSON string of the fractal calculation parameters.
    """
    try:
        # Get parameters from the request
        map_name = str(request.args.get('map_name', 'distance_map'))
        map_type = str(request.args.get('map_type', 'raw'))
        fractal_type = str(request.args.get('fractal_type', 'Mandelbrot')).capitalize()
        x_center = float(request.args.get('x_center', -1.0))
        x_span = float(request.args.get('x_span', 1.0)) 
        y_center = float(request.args.get('y_center', 0.0))
        y_span = float(request.args.get('y_span', 1.0)) 
        c_real = float(request.args.get('c_real', 0.0))
        c_imag = float(request.args.get('c_imag', 0.0))
        power = float(request.args.get('power', 2.0)) 
        resolution = int(request.args.get('resolution', 512))
        iterations = int(request.args.get('iterations', 512)) 
        bailout = float(request.args.get('bailout', 4.0))
        fixed_iteration = int(request.args.get('fixed_iteration', 20))
        trap_type = int(request.args.get('trap_type', 0))
        trap_x1 = float(request.args.get('trap_x1', 0.0))
        trap_y1 = float(request.args.get('trap_y1', 0.0))
        trap_x2 = float(request.args.get('trap_x2', 0.0))
        trap_y2 = float(request.args.get('trap_y2', 0.0))
        trap_x3 = float(request.args.get('trap_x3', 0.0))
        trap_y3 = float(request.args.get('trap_y3', 0.0))

        # Generate the same main_cache_key as the calculate_map endpoint
        cache_key_data = f'{fractal_type}_{x_center}_{x_span}_{y_center}_{y_span}_{c_real}_{c_imag}_{power}_{resolution}_{iterations}_{bailout}_{fixed_iteration}_{trap_type}_{trap_x1}_{trap_y1}_{trap_x2}_{trap_y2}_{trap_x3}_{trap_y3}'
        main_cache_key = hashlib.sha256(cache_key_data.encode('utf-8')).hexdigest()

        # Handle the on-demand PNG generation
        if map_type == 'png':
            png_cache_key = f'{main_cache_key}_{map_name}_png'
            cached_png_data = redis_client.get(png_cache_key)
            
            # Check if the PNG is already cached
            if cached_png_data:
                return Response(cached_png_data, mimetype='image/png')
            
            # If PNG is not cached, check if the raw map exists
            raw_cache_key = f'{main_cache_key}_{map_name}_raw'
            if not redis_client.exists(raw_cache_key):
                return jsonify({"error": "Map not found in cache. It may still be calculating."}), 404
            
            # Asynchronously call the new Celery task to generate the PNG
            result = process_and_save_png_map.apply_async(
                args=(main_cache_key, map_name, resolution, iterations, fixed_iteration))
            
            # Return a pending status with the new task ID
            return jsonify({
                "status": "calculating_png",
                "task_id": result.id,
                "message": "PNG generation queued successfully. Poll this ID for status."
            }), 202

        # Handle requests for raw data
        elif map_type == 'raw':
            raw_cache_key = f'{main_cache_key}_{map_name}_raw'
            cached_raw_data = redis_client.get(raw_cache_key)
            if not cached_raw_data:
                return jsonify({"error": "Raw map not found in cache. It may still be calculating."}), 404
            
            return Response(cached_raw_data, mimetype='application/octet-stream', headers={'Content-Encoding': 'gzip'})

        else:
            return jsonify({"error": f"Invalid map_type provided: {map_type}"}), 400

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

@app.route('/task_status/<task_id>')
def task_status(task_id):
    """
    Endpoint to check the status of a Celery task.
    """
    task = AsyncResult(task_id, app=celery_app)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is pending...'
        }
    elif task.state == 'FAILURE':
        response = {
            'state': task.state,
            'status': str(task.info),
        }
    else:
        # The task has a result, either success or otherwise.
        response = {
            'state': task.state,
            'status': 'Task has completed.',
            'result': task.info
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
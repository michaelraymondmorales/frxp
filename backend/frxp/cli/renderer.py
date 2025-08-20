import os
import matplotlib.cm as cm
import matplotlib.pyplot as plt 
import matplotlib.colors as clr
from pathlib import Path
from cmap import Catalog, Colormap
from frxp.core import lch_color
from frxp.core import fractal_calcs
from frxp.core import normalize_maps
from frxp.core import coord_generator
from frxp.core import coord_converter

# Function dispatch dictionary
FRACTAL_RENDER_FUNCTIONS = {
    'Julia': fractal_calcs.julia_numba,
    'Multi-Julia': fractal_calcs.julia_numba, 
    'Mandelbrot': fractal_calcs.mandelbrot_numba,
    'Multi-Mandelbrot': fractal_calcs.mandelbrot_numba,
}

# Fix tuple second Colormap helper.
def _validate_color_map(colormap_name: str) -> tuple[bool, str | clr.Colormap]:
    """
    Validates if a given string corresponds to a valid color map.

    Checks for custom LCH maps, Matplotlib maps, and 'cmap' library maps.
    This function will return a tuple containing a boolean and either the string
    name for LCH or the actual Matplotlib Colormap object.

    Args:
        colormap_name (str): The name of the color map to validate.

    Returns:
        tuple[bool, str | cm.Colormap]:
            A tuple where the first element is True if the map is valid,
            and the second element is the map name for LCH or the
            colormap object for Matplotlib and 'cmap' libraries.

    Raises:
        ValueError: If the provided colormap_name is not valid in any of the
                    supported libraries.
    """
    VALID_LCH_MAPS = ['ima', 'iam', 'mia', 'mai', 'aim', 'ami']
    
    # Check 1: Custom LCH maps
    if colormap_name in VALID_LCH_MAPS:
        return True, colormap_name
    
    # Check 2: Matplotlib colormaps
    try:
        # cm.get_cmap will raise a ValueError if the name is invalid
        cmap_object = cm.get_cmap(colormap_name)
        return True, cmap_object
    except ValueError:
        # Matplotlib check failed. Now, try the next library.  
        # Check 3: cmap library colormaps
        try:
            cmap_cat = Catalog()
            all_cmap_names = set(cmap_cat.short_keys()) | set(cmap_cat.namespaced_keys())
            
            if colormap_name in all_cmap_names:
                return True, Colormap(colormap_name).to_mpl()
            else:
                # If the name isn't found in the cmap library, raise an error.
                raise ValueError(f"'{colormap_name}' not found in cmap library.")
        except (ValueError, KeyError) as e:
            # If all checks fail, raise a final, descriptive error.
            raise ValueError(f"'{colormap_name}' is not a valid LCH, Matplotlib, or cmap color map.") from e

def _apply_and_save_colormap(args: dict) -> Path:
    """
        Applies a colormap to a data map and saves the result as a PNG image.

    This function handles the image creation process, including setting up
    the plot figure, applying the specified colormap, and saving the final
    image without extra borders or padding.

    Args:
        args (dict): A dictionary containing all necessary arguments for rendering.
            It must contain the following keys:
            - 'seed_data' (dict): The seed data used to generate the fractal.
            - 'output_dir' (Path): The directory path to save the image.
            - 'resolution' (int): The square image resolution (e.g., 1024).
            - 'colormap_info' (tuple): A tuple from `_validate_color_map` containing
               the colormap validity boolean and the colormap object or name.
            - 'x_min', 'x_max', 'y_min', 'y_max' (float): The complex plane bounds.
            - 'r_type' (str): The rendering type ('iterations', 'magnitudes', 'angles', 'lch').
            - 'data_map' (np.ndarray): The 2D numpy array of data to be colored.

    Returns:
        Path: The file path to the newly saved PNG image.
    """
    # Create a figure with no frame and set DPI based on desired resolution
    fig = plt.figure(figsize=(args['resolution']/100, args['resolution']/100), dpi=100, frameon=False)
    
    # Create an Axes object that spans the entire figure (0 to 1 in figure coordinates)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    
    # Ensure equal aspect ratio and turn off all axis elements (ticks, labels, spines)
    ax.set_aspect('equal')
    ax.set_axis_off()
    
    # Add the custom axes to the figure
    fig.add_axes(ax)

    # Display the image using imshow
    # 'origin="lower"' is crucial for mathematical plots to match Cartesian coordinates
    # 'extent' sets the data limits for the axes, matching the fractal's complex plane bounds
    # Unpack for clarity
    data_map = args['data_map']
    colormap_info = args['colormap_info']
    x_min, x_max, y_min, y_max = args['x_min'], args['x_max'], args['y_min'], args['y_max']
    
    # Conditionally apply colormap based on type
    # For LCH maps, the data_map is already a 3D RGB array, so no 'cmap' is needed.
    if isinstance(colormap_info[1], str):
        ax.imshow(data_map, origin='lower', extent=[x_min, x_max, y_min, y_max])
        colormap_name_for_filename = colormap_info[1]
    else:
        ax.imshow(data_map, origin='lower', cmap=colormap_info[1], extent=[x_min, x_max, y_min, y_max])
        colormap_name_for_filename = colormap_info[1].name


    # Construct a filename for the output image, including the rendering_type and colormap
    seed_id_part = args['seed_data'].get('seed_id', 'N_A')
    filename = f"fractal_{args['seed_data']['type']}_{args['seed_data']['x_span']}_{seed_id_part}_{args['seed_data']['power']}_{args['resolution']}_{args['r_type']}_{colormap_name_for_filename}.png"
    output_filepath = args['output_dir'] / filename

    # Save the figure with no extra padding or bounding box adjustments
    # This ensures only the image content is saved.
    plt.savefig(output_filepath, dpi=100, bbox_inches=None, pad_inches=0)
    plt.clf()
    plt.close(fig)

    return output_filepath

def render_fractal_to_file(seed_data: dict, 
                          output_dir: Path, 
                          resolution: int = 1024,
                          colormap_names: list = ['twilight'], # Now accepts a list of colormap names
                          rendering_types: list = ['all'] # 'all', 'iterations', 'magnitudes', or 'angles'
                          ) -> list[dict]:
    """
    Renders one or more fractal images (iterations, magnitudes, or angles map) with multiple colormaps
    and saves them to the specified directory.
    The output images will be clean fractals, filling the entire frame, without axes, titles, or colorbars.

    Args:
        seed_data (dict): The seed parameters to render.
        output_dir (Path): The directory where the image(s) should be saved (e.g., staging).
        resolution (int): The resolution of the square image (e.g., 1024).
        colormap_names (list[str]): A list of colormap names to use (e.g., ['viridis', 'magma', 'twilight']).
        rendering_type (str): Specifies which map(s) to render: 'all', 'iterations', 'magnitudes', or 'angles'.

    Returns:
        list[dict]: A list of dictionaries, each containing:
                    - 'filepath': Path to the saved image file.
                    - 'rendering_type': The type of map rendered ('iterations', 'magnitudes', 'angles').
                    - 'colormap': The colormap used for this image.
    """
    fractal_function = FRACTAL_RENDER_FUNCTIONS.get(seed_data['type'])

    if fractal_function is None:
        raise ValueError(f"Unsupported fractal type: {seed_data['type']}")
    
    x_min, x_max, y_min, y_max = coord_converter.convert_to_minmax(seed_data['x_center'],
                                                                   seed_data['x_span'],
                                                                   seed_data['y_center'],
                                                                   seed_data['y_span'])

    x_coords, y_coords = coord_generator.generate_coords(x_min,
                                                         x_max,
                                                         y_min,
                                                         y_max,
                                                         resolution)
    
    # Common arguments for all fractal types
    fractal_calc_args = {'x_coords': x_coords,
                         'y_coords': y_coords,
                         'power': seed_data['power'],
                         'iterations': seed_data['iterations'],
                         'bailout': seed_data['bailout']}

    if seed_data['type'] in ['Julia', 'Multi-Julia']:
        c_real = seed_data.get('c_real')
        c_imag = seed_data.get('c_imag')
        
        # Sanity check for Julia fractals
        if c_real is None or c_imag is None:
            raise ValueError(f"Fractal type '{seed_data['type']}' requires 'c_real' and 'c_imag' to be non-None values.")
        
        # Add Julia-specific arguments
        fractal_calc_args['c_real'] = c_real
        fractal_calc_args['c_imag'] = c_imag
        
        map_tuple = fractal_function(**fractal_calc_args)

    elif seed_data['type'] in ['Mandelbrot', 'Multi-Mandelbrot']:
        map_tuple = fractal_function(**fractal_calc_args)
        
    else:
        # This 'else' should not be reached if FRACTAL_RENDER_FUNCTIONS is comprehensive
        raise ValueError(f"Unhandled fractal type in renderer: {seed_data['type']}")

    # Unpack the tuple and create a dictionary from the returned maps.
    maps = {
        'iterations_map': map_tuple[0],
        'normalized_iterations_map': map_tuple[1],
        'magnitudes_map': map_tuple[2],
        'initial_angles_map': map_tuple[3],
        'final_angles_map': map_tuple[4],
        'distance_map': map_tuple[5],
        'final_derivative_magnitude_map': map_tuple[6],
        'min_distance_to_trap_map': map_tuple[7],
        'min_distance_iteration_map': map_tuple[8],
        'derivative_bailout_map': map_tuple[9],
        'final_Z_real_map': map_tuple[10],
        'final_Z_imag_map': map_tuple[11],
        'final_derivative_real_map': map_tuple[12],
        'final_derivative_imag_map': map_tuple[13],
        'bailout_location_real_map': map_tuple[14],
        'bailout_location_imag_map': map_tuple[15],
        'final_Z_real_at_fixed_iteration_map': map_tuple[16],
        'final_Z_imag_at_fixed_iteration_map': map_tuple[17]}
    
    # Normalize the raw maps for rendering
    norm_iterations_map, norm_magnitudes_map, norm_angles_map = normalize_maps.normalize_maps(
                                                                maps['iterations_map'],
                                                                maps['magnitudes_map'],
                                                                maps['final_angles_map'],
                                                                seed_data['iterations'])

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # To store details of all generated images
    generated_image_details = []
    for name in colormap_names:
        try:
            colormap_info = _validate_color_map(name)
        except ValueError as e:
            print(f"Skipping invalid colormap '{name}': {e}")
            continue

        render_args = {'seed_data': seed_data, 
                       'output_dir': output_dir,
                       'resolution': resolution,
                       'colormap_info': colormap_info,
                       'x_min': x_min,
                       'x_max': x_max,
                       'y_min': y_min,
                       'y_max': y_max,}
        
        # Determine which rendering path to take
        if isinstance(colormap_info[1], str):  # This is a custom LCH map
            data_map = lch_color.generate_colors(norm_iterations_map,
                                                 norm_magnitudes_map,
                                                 norm_angles_map,
                                                 colormap_info[1])
            
            render_args['r_type'] = 'lch'
            render_args['data_map'] = data_map
            output_filepath = _apply_and_save_colormap(render_args)
            
            print(f"Fractal image (lch, colormap: {name}) rendered and saved to: {output_filepath}")
            generated_image_details.append({
                'filepath': output_filepath,
                'rendering_type': 'lch',
                'colormap': name
            })
        else:  # This is a standard Matplotlib or cmap colormap
            # Handle the 'all' case by iterating over all three maps
            maps_to_render = []
            if 'all' in rendering_types or 'iterations' in rendering_types:
                maps_to_render.append(('iterations', norm_iterations_map))
            if 'all' in rendering_types or 'magnitudes' in rendering_types:
                maps_to_render.append(('magnitudes', norm_magnitudes_map))
            if 'all' in rendering_types or 'angles' in rendering_types:
                maps_to_render.append(('angles', norm_angles_map))

            for r_type, data_map in maps_to_render:
                render_args['r_type'] = r_type
                render_args['data_map'] = data_map
                output_filepath = _apply_and_save_colormap(render_args)

                print(f"Fractal image ({r_type}, colormap: {name}) rendered and saved to: {output_filepath}")
                generated_image_details.append({
                    'filepath': output_filepath,
                    'rendering_type': r_type,
                    'colormap': name
                })
                
    return generated_image_details
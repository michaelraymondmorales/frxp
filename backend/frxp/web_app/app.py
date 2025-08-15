from flask import Flask, request, jsonify
from flask_cors import CORS
from frxp.core import fractal_calcs
from frxp.core import coord_generator
from frxp.core import coord_converter

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

@app.route('/generate_fractal', methods=['GET'])
def generate_fractal_endpoint():

    type = request.args.get('type', 'Julia') 
    x_center = float(request.args.get('x_center', 0.0))
    x_span = float(request.args.get('x_span', .225)) 
    y_center = float(request.args.get('y_center', 0.0))
    y_span = float(request.args.get('y_span', .225)) 
    c_real = float(request.args.get('c_real', -0.8))
    c_imag = float(request.args.get('c_imag', 0.156))
    power = float(request.args.get('power', 2.0)) 
    resolution = int(request.args.get('resolution', 1024))
    iterations = int(request.args.get('iterations', 256)) 
    bailout = float(request.args.get('bailout', 2.0))

    x_min, x_max, y_min, y_max = coord_converter.convert_to_minmax(x_center, 
                                                                   x_span,
                                                                   y_center, 
                                                                   y_span)
    
    x_coords, y_coords = coord_generator.generate_coords(x_min, 
                                                         x_max, 
                                                         y_min, 
                                                         y_max,
                                                         resolution)

    # Function dispatch dictionary
    FRACTAL_RENDER_FUNCTIONS = {
    'Julia': fractal_calcs.julia_numba,
    'Multi-Julia': fractal_calcs.julia_numba, 
    'Mandelbrot': fractal_calcs.mandelbrot_numba,
    'Multi-Mandelbrot': fractal_calcs.mandelbrot_numba,
    }

    fractal_function = FRACTAL_RENDER_FUNCTIONS.get(type)
    
    if type in ['Julia', 'Multi-Julia']:
        iterations_map, magnitudes_map, angle_map = fractal_function(x_coords, 
                                                                     y_coords, 
                                                                     c_real, 
                                                                     c_imag, 
                                                                     power, 
                                                                     iterations, 
                                                                     bailout)
    elif type in ['Mandelbrot', 'Multi-Mandelbrot']:
        iterations_map, magnitudes_map, angle_map = fractal_function(x_coords, 
                                                                     y_coords, 
                                                                     power, 
                                                                     iterations, 
                                                                     bailout)

    # Convert NumPy arrays to Python lists for JSON serialization
    # This is crucial as JSON doesn't directly support NumPy arrays.
    iterations_list = iterations_map.tolist()
    magnitudes_list = magnitudes_map.tolist()
    angles_list = angle_map.tolist()

    # Return the data as a JSON response
    return jsonify({'iterations': iterations_list,
                    'magnitudes': magnitudes_list,
                    'angles': angles_list
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000) # Run on port 5000
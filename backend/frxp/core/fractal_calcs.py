import numpy as np
from numba import njit, prange

@njit(parallel=True)
def julia_numba(
    x_coords, 
    y_coords, 
    c_real, 
    c_imag, 
    power, 
    iterations, 
    bailout):
    """
    Calculates iteration count and final magnitudes for Multi-Julia set.

    Args:
        x_coords (np.ndarray): 1D array of initial imaginary coordinates (from np.linspace).
                               Expected shape (width_pixels).
        y_coords (np.ndarray): 1D array of initial real coordinates (from np.linspace).
                               Expected shape (height_pixels).
        c_real (float): Real part of the complex constant 'c'.
        c_imag (float): Imaginary part of the complex constant 'c'.
        power (int): The power of Z (e.g., 2 for standard Julia).
        iterations (int): Maximum number of iterations.
        bailout (float): Bailout radius.

    Returns:
        tuple: (iterations_map, final_magnitudes_map, angle_map)
            iterations_map (np.ndarray): Array of iteration counts.
            magnitudes_map (np.ndarray): Array of final magnitudes before bailout.
            angle_map (np.ndarray): Array of angles (phase) of Z at the final state.
    """
    # Determine height and width from the shapes of the input coordinate arrays
    height = y_coords.shape[0]
    width = x_coords.shape[0]
    # Initialize iteration map: all points start as iterations aka interior.
    iterations_map = np.full((height, width), iterations, dtype = np.int32)
    # Initialize final magnitudes map: will store magnitude at escape.
    magnitudes_map = np.zeros((height, width), dtype = np.float64)
    # Mutable arrays for Z's real and imaginary numbers.
    Z_real = np.empty((height, width), dtype=np.float64)
    Z_imag = np.empty((height, width), dtype=np.float64)
    for row in range(height):
        for col in range(width):
            Z_real[row, col] = x_coords[col]
            Z_imag[row, col] = y_coords[row]
    # Perform bailout square outside of loop for optimization.
    bailout_sq = bailout * bailout
    # Create a boolean mask to track which points are still active.
    active_mask = np.ones((height, width), dtype = np.bool_)
    
    # Check if any points are active.
    for i in range(iterations):
        if not np.any(active_mask):
            break

    # Iterate over each pixel using Numba to optimize loop.
    # Parallel range for outer loop and range for inner loop.
        for row in prange(height):
            for col in range(width):
                if active_mask[row, col]:
                    zr = Z_real[row, col]
                    zi = Z_imag[row, col]
                    magnitude_sq = zr * zr + zi * zi

                    if magnitude_sq >= bailout_sq:
    # This point has escaped, log iteration and set mask to False.
                        iterations_map[row, col] = i + 1
                        magnitudes_map[row, col] = np.sqrt(magnitude_sq)
                        active_mask[row, col] = False
                    else:
    # Perform iteration: Z_new = Z^power + c using polar coordinates.
    # For detailed explanation please see docs/julia_set_math.md 
                        r_z = np.sqrt(magnitude_sq)
                        theta_z = np.arctan2(zi, zr)

                        new_r = r_z**power
                        new_theta = power * theta_z

                        next_zr = new_r * np.cos(new_theta) + c_real
                        next_zi = new_r * np.sin(new_theta) + c_imag
                            
                        Z_real[row, col] = next_zr
                        Z_imag[row, col] = next_zi        

    angle_map = np.arctan2(Z_imag, Z_real)
    return iterations_map, magnitudes_map, angle_map

@njit(parallel=True)
def mandelbrot_numba(
    x_coords, 
    y_coords, 
    power, 
    iterations, 
    bailout):
    """
    Calculates iteration count and final magnitudes for Multi-Mandelbrot set.

    Args:
        x_coords (np.ndarray): 1D array of real coordinates (which serve as 'c_real' for each pixel).
                               Expected shape (width_pixels).
        y_coords (np.ndarray): 1D array of imaginary coordinates (which serve as 'c_imag' for each pixel).
                               Expected shape (height_pixels).
        power (int): The power of Z (e.g., 2 for standard Mandelbrot).
        iterations (int): Maximum number of iterations.
        bailout (float): Bailout radius.

    Returns:
        tuple: (iterations_map, final_magnitudes_map, angle_map)
            iterations_map (np.ndarray): Array of iteration counts.
            magnitudes_map (np.ndarray): Array of final magnitudes before bailout.
            angle_map (np.ndarray): Array of angles (phase) of Z at the final state.
    """
    height = y_coords.shape[0]
    width = x_coords.shape[0]
    
    # Initialize iteration map: all points start as iterations (interior).
    iterations_map = np.full((height, width), iterations, dtype = np.int32)
    # Initialize final magnitudes map: will store magnitude at escape.
    magnitudes_map = np.zeros((height, width), dtype = np.float64)
    
    # For Mandelbrot, Z starts at 0 for each point.
    Z_real = np.zeros((height, width), dtype=np.float64)
    Z_imag = np.zeros((height, width), dtype=np.float64)
    
    # Pre-calculate bailout square for optimization.
    bailout_sq = bailout * bailout
    # Create a boolean mask to track which points are still active.
    active_mask = np.ones((height, width), dtype = np.bool_)
    
    # Iterate for a maximum number of times.
    for i in range(iterations):
        # If no points are active, we can stop early.
        if not np.any(active_mask):
            break

        # Iterate over each pixel using Numba's parallel capabilities.
        for row in prange(height):
            for col in range(width):
                if active_mask[row, col]:
                    zr = Z_real[row, col]
                    zi = Z_imag[row, col]
                    
                    # For Mandelbrot, the 'c' constant for this pixel is its initial coordinate.
                    c_real_pixel = x_coords[col]
                    c_imag_pixel = y_coords[row]

                    magnitude_sq = zr * zr + zi * zi

                    if magnitude_sq >= bailout_sq:
                        # This point has escaped, log iteration and set mask to False.
                        iterations_map[row, col] = i + 1
                        magnitudes_map[row, col] = np.sqrt(magnitude_sq)
                        active_mask[row, col] = False
                    else:
                        # Perform iteration: Z_new = Z^power + C_pixel using polar coordinates.
                        # For detailed explanation please see docs/julia_set_math.md 
                        r_z = np.sqrt(magnitude_sq)
                        theta_z = np.arctan2(zi, zr)

                        new_r = r_z**power
                        new_theta = power * theta_z

                        # Update Z using the pixel's 'c' constant.
                        next_zr = new_r * np.cos(new_theta) + c_real_pixel
                        next_zi = new_r * np.sin(new_theta) + c_imag_pixel
                            
                        Z_real[row, col] = next_zr
                        Z_imag[row, col] = next_zi        

    # Calculate the angle map from the final Z values.
    angle_map = np.arctan2(Z_imag, Z_real)
    return iterations_map, magnitudes_map, angle_map
import math
import numpy as np
from numba import njit, prange

# A helper function to compute the distance from a point (x,y) to a line segment.
# This function is used by the line trap logic and for the triangle trap.
@njit
def _distance_to_line_segment(x: float, 
                              y: float, 
                              x1: float, 
                              y1: float, 
                              x2: float, 
                              y2: float
                              ) -> float:
    """
    Calculates the minimum distance from a point (x,y) to a line segment defined by (x1,y1) and (x2,y2).

    This function is used to implement a 'trap' or 'distance estimator' for fractal
    algorithms. It determines how close a point in a complex plane orbit gets to
    a specific line segment.

    Args:
        x (float): The real part of the point.
        y (float): The imaginary part of the point.
        x1 (float): The real part of the first point of the line segment.
        y1 (float): The imaginary part of the first point of the line segment.
        x2 (float): The real part of the second point of the line segment.
        y2 (float): The imaginary part of the second point of the line segment.

    Returns:
        float: The minimum Euclidean distance from the point to the line segment.
    """
    dx = x2 - x1
    dy = y2 - y1
    seg_len_sq = dx*dx + dy*dy
    if seg_len_sq == 0.0:
        # The line segment is a point.
        return math.sqrt((x - x1)**2 + (y - y1)**2)

    # Project the point onto the line defined by the segment.
    t = ((x - x1) * dx + (y - y1) * dy) / seg_len_sq
    
    # Check if the projection falls on the line segment.
    if t < 0.0:
        closest_x = x1
        closest_y = y1
    elif t > 1.0:
        closest_x = x2
        closest_y = y2
    else:
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

    return math.sqrt((x - closest_x)**2 + (y - closest_y)**2)

@njit
def get_orbit_trail_numba(z0_real: float, 
                          z0_imag: float, 
                          c_real: float, 
                          c_imag: float, 
                          max_iterations: int, 
                          bailout_radius: float
                          ) -> tuple:
    """
    Calculates the orbit trail for a given complex number c with a given starting point z0.
    This function is suitable for both Mandelbrot and Julia sets.
    
    This function uses a 'try...except' block to handle potential overflows,
    preventing large values from becoming 'inf'. The orbit calculation stops
    if the magnitude of z exceeds the bailout radius or an overflow occurs.
    
    Args:
        z0_real (float): The real part of the initial complex number z0.
        z0_imag (float): The imaginary part of the initial complex number z0.
        c_real (float): The real part of the complex number c.
        c_imag (float): The imaginary part of the complex number c.
        max_iterations (int): The maximum number of iterations to perform.
        bailout_radius (float): The radius at which to stop iterating.

    Returns:
        tuple: A tuple containing two NumPy arrays:
               - The real components of the orbit trail.
               - The imaginary components of the orbit trail.
    """
    z_real = z0_real
    z_imag = z0_imag
    
    # Store the initial value z_0
    orbit_real = np.zeros(int(max_iterations) + 1, dtype=np.float64)
    orbit_imag = np.zeros(int(max_iterations) + 1, dtype=np.float64)

    orbit_real[0] = z_real
    orbit_imag[0] = z_imag

    for i in range(int(max_iterations)):
        # The Mandelbrot/Julia iteration: z = z*z + c
        try:
            z_real_squared = z_real * z_real
            z_imag_squared = z_imag * z_imag
            
            # Check for overflow before the next calculation
            if z_real_squared > 1e300 or z_imag_squared > 1e300:
                break
                
            new_z_real = z_real_squared - z_imag_squared + c_real
            new_z_imag = 2.0 * z_real * z_imag + c_imag
            
            z_real = new_z_real
            z_imag = new_z_imag
            
        except Exception:
            # If an overflow occurs, we've gone too far.
            # Stop the loop and return the data up to this point.
            break

        magnitude_squared = z_real * z_real + z_imag * z_imag
        
        # Check if the point has escaped the bailout radius
        if magnitude_squared >= bailout_radius * bailout_radius:
            # We don't want to include the point that escaped
            return orbit_real[:i+1], orbit_imag[:i+1]

        # Store the current iteration values
        orbit_real[i+1] = z_real
        orbit_imag[i+1] = z_imag

    # If the loop finishes without escaping, return the full arrays
    return orbit_real, orbit_imag

@njit(parallel=True)
def mandelbrot_numba(
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    power: float,
    iterations: int,
    bailout: float,
    fixed_iteration: int=20,
    trap_params: tuple=(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ) -> tuple:
    """
    Calculates iteration count, final magnitudes, and other maps for the Multi-Mandelbrot set.
    This version includes an optional orbit trap with advanced trap shapes.

    Args:
        x_coords (np.ndarray): 1D array of real coordinates.
        y_coords (np.ndarray): 1D array of imaginary coordinates.
        power (float): The power of Z (e.g., 2.0 for standard Mandelbrot).
        iterations (int): Maximum number of iterations.
        bailout (float): Bailout radius.
        fixed_iteration (int): The iteration at which to capture Z and derivative values.
        trap_params (tuple): A tuple for advanced trap parameters. The first element is an
            integer representing the trap type. The tuple should always have 7 elements.
            - (0, ...): No trap (default).
            - (1, x, y, 0.0, 0.0, 0.0, 0.0): Point trap at (x, y).
            - (2, x1, y1, x2, y2, 0.0, 0.0): Line trap from (x1, y1) to (x2, y2).
            - (3, x, y, radius, 0.0, 0.0, 0.0): Circle trap at (x, y) with a given radius.
            - (4, x, y, side, 0.0, 0.0, 0.0): Square trap at (x, y) with a given side length.
            - (5, x1, y1, x2, y2, x3, y3): Triangle trap with vertices (x1, y1), (x2, y2), and (x3, y3).

    Returns:
        tuple: A tuple of 2D numpy arrays representing different data maps.
               - iterations_map: Iteration count for each point to escape.
               - normalized_iterations_map: Normalized escape iteration count.
               - magnitudes_map: Magnitude of Z at escape.
               - initial_angles_map: Initial angle of C.
               - final_angles_map: Final angle of Z for non-escaped points.
               - distance_map: Distance to the origin at escape.
               - final_derivative_magnitude_map: Log magnitude of final derivative.
               - min_distance_to_trap_map: Minimum distance to the orbit trap.
               - min_distance_iteration_map: Iteration at which min distance to trap occurred.
               - derivative_bailout_map: Iteration at which derivative magnitude exceeded bailout.
               - bailout_location_real_map: Real part of Z at bailout.
               - bailout_location_imag_map: Imaginary part of Z at bailout.
               - final_Z_real_map: Final Z real for non-escaped points.
               - final_Z_imag_map: Final Z imag for non-escaped points.
               - final_derivative_real_map: Final derivative real for non-escaped points.
               - final_derivative_imag_map: Final derivative imag for non-escaped points.
               - final_Z_real_at_fixed_iteration_map: Real part of Z at a fixed iteration.
               - final_Z_imag_at_fixed_iteration_map: Imaginary part of Z at a fixed iteration.
    """
    width = x_coords.shape[0]
    height = y_coords.shape[0]
    bailout_sq = bailout * bailout

    # Initialize all data maps to be filled by the parallel loop.
    iterations_map = np.full((height, width), iterations, dtype=np.int32)
    normalized_iterations_map = np.zeros((height, width), dtype=np.float64)
    magnitudes_map = np.zeros((height, width), dtype=np.float64)
    initial_angles_map = np.zeros((height, width), dtype=np.float64)
    final_angles_map = np.zeros((height, width), dtype=np.float64)
    distance_map = np.zeros((height, width), dtype=np.float64)
    final_derivative_magnitude_map = np.zeros((height, width), dtype=np.float64)
    derivative_bailout_map = np.zeros((height, width), dtype=np.float64)
    final_Z_real_map = np.zeros((height, width), dtype=np.float64)
    final_Z_imag_map = np.zeros((height, width), dtype=np.float64)
    final_derivative_real_map = np.zeros((height, width), dtype=np.float64)
    final_derivative_imag_map = np.zeros((height, width), dtype=np.float64)
    bailout_location_real_map = np.zeros((height, width), dtype=np.float64)
    bailout_location_imag_map = np.zeros((height, width), dtype=np.float64)
    min_distance_to_trap_map = np.full((height, width), np.inf, dtype=np.float64)
    min_distance_iteration_map = np.zeros((height, width), dtype=np.int32)
    final_Z_real_at_fixed_iteration_map = np.zeros((height, width), dtype=np.float64)
    final_Z_imag_at_fixed_iteration_map = np.zeros((height, width), dtype=np.float64)

    # Store the trap type for cleaner access in the loop.
    trap_type = trap_params[0]

    # Use a flattened, parallelized loop.
    for pixel_index in prange(height * width):
        row = pixel_index // width
        col = pixel_index % width

        z_real = 0.0
        z_imag = 0.0
        
        dz_by_dc_real = 0.0
        dz_by_dc_imag = 0.0

        c_real_pixel = x_coords[col]
        c_imag_pixel = y_coords[row]
        initial_angles_map[row, col] = np.arctan2(c_imag_pixel, c_real_pixel)

        # Pre-calculate the initial distance to the trap if a trap is enabled
        if trap_type != 0:
             min_distance_to_trap_map[row, col] = np.inf

        is_integer_power = power == int(power)
        
        for i in range(iterations):
            if i == fixed_iteration:
                final_Z_real_at_fixed_iteration_map[row, col] = z_real
                final_Z_imag_at_fixed_iteration_map[row, col] = z_imag

            magnitude_sq = z_real * z_real + z_imag * z_imag
            sqrt_magnitude_sq = np.sqrt(magnitude_sq)

            if magnitude_sq >= bailout_sq:
                iterations_map[row, col] = i
                magnitudes_map[row, col] = sqrt_magnitude_sq
                normalized_iterations_map[row, col] = i + 1 - np.log(np.log(magnitudes_map[row, col])) / np.log(power)
                final_angles_map[row, col] = np.arctan2(z_imag, z_real)
                dz_by_dc_magnitude_sq = dz_by_dc_real**2 + dz_by_dc_imag**2
                if dz_by_dc_magnitude_sq > 0:
                    final_derivative_magnitude_map[row, col] = np.log(np.sqrt(dz_by_dc_magnitude_sq))
                    distance_map[row, col] = 2.0 * sqrt_magnitude_sq * np.log(sqrt_magnitude_sq) / np.sqrt(dz_by_dc_magnitude_sq)
                    derivative_bailout_map[row, col] = sqrt_magnitude_sq * np.log(sqrt_magnitude_sq) / np.sqrt(dz_by_dc_magnitude_sq)
                else:
                    final_derivative_magnitude_map[row, col] = 0.0
                    distance_map[row, col] = 0.0
                    derivative_bailout_map[row, col] = 0.0

                final_Z_real_map[row, col] = z_real
                final_Z_imag_map[row, col] = z_imag
                final_derivative_real_map[row, col] = dz_by_dc_real
                final_derivative_imag_map[row, col] = dz_by_dc_imag
                bailout_location_real_map[row, col] = z_real
                bailout_location_imag_map[row, col] = z_imag
                break

            # ORBIT TRAP LOGIC
            # Only compute if a trap is enabled and we are not on the first iteration
            if trap_type != 0 and i > 0:
                current_distance = 0.0

                if trap_type == 1: # Point Trap
                    trap_x = trap_params[1]
                    trap_y = trap_params[2]
                    current_distance = math.sqrt((z_real - trap_x)**2 + (z_imag - trap_y)**2)
                elif trap_type == 2: # Line Trap
                    current_distance = _distance_to_line_segment(z_real, z_imag, trap_params[1], trap_params[2], trap_params[3], trap_params[4])
                elif trap_type == 3: # Circle Trap
                    trap_x = trap_params[1]
                    trap_y = trap_params[2]
                    trap_radius = trap_params[3]
                    distance_from_center = math.sqrt((z_real - trap_x)**2 + (z_imag - trap_y)**2)
                    current_distance = abs(distance_from_center - trap_radius)
                elif trap_type == 4: # Square Trap
                    half_side = trap_params[3] / 2.0
                    x_dist = max(0.0, abs(z_real - trap_params[1]) - half_side)
                    y_dist = max(0.0, abs(z_imag - trap_params[2]) - half_side)
                    current_distance = math.sqrt(x_dist**2 + y_dist**2)
                elif trap_type == 5: # Triangle Trap
                    # Distance to each of the three line segments
                    dist1 = _distance_to_line_segment(z_real, z_imag, trap_params[1], trap_params[2], trap_params[3], trap_params[4])
                    dist2 = _distance_to_line_segment(z_real, z_imag, trap_params[3], trap_params[4], trap_params[5], trap_params[6])
                    dist3 = _distance_to_line_segment(z_real, z_imag, trap_params[5], trap_params[6], trap_params[1], trap_params[2])
                    current_distance = min(dist1, dist2, dist3)

                if current_distance < min_distance_to_trap_map[row, col]:
                    min_distance_to_trap_map[row, col] = current_distance
                    min_distance_iteration_map[row, col] = i
            
            # Hybrid Calculation for Derivative:
            if is_integer_power:
                if power == 2:
                    next_dz_by_dc_real = 2 * (z_real * dz_by_dc_real - z_imag * dz_by_dc_imag) + 1
                    next_dz_by_dc_imag = 2 * (z_real * dz_by_dc_imag + z_imag * dz_by_dc_real)
                else:
                    z_mag = np.sqrt(z_real*z_real + z_imag*z_imag)
                    z_angle = np.arctan2(z_imag, z_real)
                    z_power_minus_1_mag = z_mag**(power-1)
                    z_power_minus_1_angle = z_angle * (power-1)
                    z_power_minus_1_real = z_power_minus_1_mag * np.cos(z_power_minus_1_angle)
                    z_power_minus_1_imag = z_power_minus_1_mag * np.sin(z_power_minus_1_angle)
                    next_dz_by_dc_real = power * (z_power_minus_1_real * dz_by_dc_real - z_power_minus_1_imag * dz_by_dc_imag) + 1
                    next_dz_by_dc_imag = power * (z_power_minus_1_real * dz_by_dc_imag + z_power_minus_1_imag * dz_by_dc_real)
            else:
                z_mag = np.sqrt(z_real*z_real + z_imag*z_imag)
                z_angle = np.arctan2(z_imag, z_real)
                z_power_minus_1_mag = z_mag**(power-1)
                z_power_minus_1_angle = z_angle * (power-1)
                z_power_minus_1_real = z_power_minus_1_mag * np.cos(z_power_minus_1_angle)
                z_power_minus_1_imag = z_power_minus_1_mag * np.sin(z_power_minus_1_angle)
                next_dz_by_dc_real = power * (z_power_minus_1_real * dz_by_dc_real - z_power_minus_1_imag * dz_by_dc_imag) + 1
                next_dz_by_dc_imag = power * (z_power_minus_1_real * dz_by_dc_imag + z_power_minus_1_imag * dz_by_dc_real)

            dz_by_dc_real = next_dz_by_dc_real
            dz_by_dc_imag = next_dz_by_dc_imag
            
            # Hybrid Calculation for Z:
            if is_integer_power:
                if power == 2:
                    next_z_real = z_real * z_real - z_imag * z_imag + c_real_pixel
                    next_z_imag = 2 * z_real * z_imag + c_imag_pixel
                else:
                    if power == 0:
                        z_power_real = 1.0
                        z_power_imag = 0.0
                    else:
                        z_power_real = z_real
                        z_power_imag = z_imag
                        for _ in range(int(power)-1):
                            temp_real = z_power_real
                            z_power_real = z_power_real * z_real - z_power_imag * z_imag
                            z_power_imag = temp_real * z_imag + z_power_imag * z_real

                    next_z_real = z_power_real + c_real_pixel
                    next_z_imag = z_power_imag + c_imag_pixel
            else:
                r_z = sqrt_magnitude_sq
                theta_z = np.arctan2(z_imag, z_real)
                new_r = r_z**power
                new_theta = power * theta_z
                next_z_real = new_r * np.cos(new_theta) + c_real_pixel
                next_z_imag = new_r * np.sin(new_theta) + c_imag_pixel

            z_real = next_z_real
            z_imag = next_z_imag

        # Record final values for points that didn't escape.
        if iterations_map[row, col] == iterations:
            final_angles_map[row, col] = np.arctan2(z_imag, z_real)
            dz_by_dc_magnitude_sq = dz_by_dc_real**2 + dz_by_dc_imag**2
            if dz_by_dc_magnitude_sq > 0:
                 final_derivative_magnitude_map[row, col] = np.log(np.sqrt(dz_by_dc_magnitude_sq))
            else:
                 final_derivative_magnitude_map[row, col] = 0.0
            
            final_Z_real_map[row, col] = z_real
            final_Z_imag_map[row, col] = z_imag
            final_derivative_real_map[row, col] = dz_by_dc_real
            final_derivative_imag_map[row, col] = dz_by_dc_imag

    return (iterations_map,
            normalized_iterations_map,
            magnitudes_map,
            initial_angles_map,
            final_angles_map,
            distance_map,
            final_derivative_magnitude_map,
            min_distance_to_trap_map,
            min_distance_iteration_map,
            derivative_bailout_map,
            final_Z_real_map,
            final_Z_imag_map,
            final_derivative_real_map,
            final_derivative_imag_map,
            bailout_location_real_map,
            bailout_location_imag_map,
            final_Z_real_at_fixed_iteration_map,
            final_Z_imag_at_fixed_iteration_map)

@njit(parallel=True)
def julia_numba(
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    c_real: float,
    c_imag: float,
    power: float,
    iterations: int,
    bailout: float,
    fixed_iteration: int=20,
    trap_params: tuple=(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ) -> tuple:
    """
    Calculates iteration count, final magnitudes, and other maps for the Multi-Julia set.
    This version includes an optional orbit trap with advanced trap shapes.

    Args:
        x_coords (np.ndarray): 1D array of real coordinates.
        y_coords (np.ndarray): 1D array of imaginary coordinates.
        c_real (float): The fixed real part of the Julia constant.
        c_imag (float): The fixed imaginary part of the Julia constant.
        power (float): The power of Z (e.g., 2.0 for standard Julia).
        iterations (int): Maximum number of iterations.
        bailout (float): Bailout radius.
        fixed_iteration (int): The iteration at which to capture Z and derivative values.
        trap_params (tuple): A tuple for advanced trap parameters. The first element is an
            integer representing the trap type. The tuple should always have 7 elements.
            - (0, ...): No trap (default).
            - (1, x, y, 0.0, 0.0, 0.0, 0.0): Point trap at (x, y).
            - (2, x1, y1, x2, y2, 0.0, 0.0): Line trap from (x1, y1) to (x2, y2).
            - (3, x, y, radius, 0.0, 0.0, 0.0): Circle trap at (x, y) with a given radius.
            - (4, x, y, side, 0.0, 0.0, 0.0): Square trap at (x, y) with a given side length.
            - (5, x1, y1, x2, y2, x3, y3): Triangle trap with vertices (x1, y1), (x2, y2), and (x3, y3).

    Returns:
        tuple: A tuple of 2D numpy arrays representing different data maps.
               - iterations_map: Iteration count for each point to escape.
               - normalized_iterations_map: Normalized escape iteration count.
               - magnitudes_map: Magnitude of Z at escape.
               - initial_angles_map: Initial angle of C.
               - final_angles_map: Final angle of Z for non-escaped points.
               - distance_map: Distance to the origin at escape.
               - final_derivative_magnitude_map: Log magnitude of final derivative.
               - min_distance_to_trap_map: Minimum distance to the orbit trap.
               - min_distance_iteration_map: Iteration at which min distance to trap occurred.
               - derivative_bailout_map: Iteration at which derivative magnitude exceeded bailout.
               - bailout_location_real_map: Real part of Z at bailout.
               - bailout_location_imag_map: Imaginary part of Z at bailout.
               - final_Z_real_map: Final Z real for non-escaped points.
               - final_Z_imag_map: Final Z imag for non-escaped points.
               - final_derivative_real_map: Final derivative real for non-escaped points.
               - final_derivative_imag_map: Final derivative imag for non-escaped points.
               - final_Z_real_at_fixed_iteration_map: Real part of Z at a fixed iteration.
               - final_Z_imag_at_fixed_iteration_map: Imaginary part of Z at a fixed iteration.
    """
    width = x_coords.shape[0]
    height = y_coords.shape[0]
    bailout_sq = bailout * bailout

    # Initialize all data maps to be filled by the parallel loop.
    iterations_map = np.full((height, width), iterations, dtype=np.int32)
    normalized_iterations_map = np.zeros((height, width), dtype=np.float64)
    magnitudes_map = np.zeros((height, width), dtype=np.float64)
    initial_angles_map = np.zeros((height, width), dtype=np.float64)
    final_angles_map = np.zeros((height, width), dtype=np.float64)
    distance_map = np.zeros((height, width), dtype=np.float64)
    final_derivative_magnitude_map = np.zeros((height, width), dtype=np.float64)
    derivative_bailout_map = np.zeros((height, width), dtype=np.float64)
    final_Z_real_map = np.zeros((height, width), dtype=np.float64)
    final_Z_imag_map = np.zeros((height, width), dtype=np.float64)
    final_derivative_real_map = np.zeros((height, width), dtype=np.float64)
    final_derivative_imag_map = np.zeros((height, width), dtype=np.float64)
    bailout_location_real_map = np.zeros((height, width), dtype=np.float64)
    bailout_location_imag_map = np.zeros((height, width), dtype=np.float64)
    min_distance_to_trap_map = np.full((height, width), np.inf, dtype=np.float64)
    min_distance_iteration_map = np.zeros((height, width), dtype=np.int32)
    final_Z_real_at_fixed_iteration_map = np.zeros((height, width), dtype=np.float64)
    final_Z_imag_at_fixed_iteration_map = np.zeros((height, width), dtype=np.float64)

    # Store the trap type for cleaner access in the loop.
    trap_type = trap_params[0]

    # Use a flattened, parallelized loop.
    for pixel_index in prange(height * width):
        row = pixel_index // width
        col = pixel_index % width

        z_real = x_coords[col]
        z_imag = y_coords[row]
        
        # For Julia, the derivative is with respect to the starting point z_0,
        # so it starts at 1.0. For Mandelbrot, it starts at 0.0.
        dz_by_dz0_real = 1.0
        dz_by_dz0_imag = 0.0

        initial_angles_map[row, col] = np.arctan2(z_imag, z_real)

        # Pre-calculate the initial distance to the trap if a trap is enabled
        if trap_type != 0:
             min_distance_to_trap_map[row, col] = np.inf

        is_integer_power = power == int(power)
        
        for i in range(iterations):
            if i == fixed_iteration:
                final_Z_real_at_fixed_iteration_map[row, col] = z_real
                final_Z_imag_at_fixed_iteration_map[row, col] = z_imag

            magnitude_sq = z_real * z_real + z_imag * z_imag
            sqrt_magnitude_sq = np.sqrt(magnitude_sq)

            if magnitude_sq >= bailout_sq:
                iterations_map[row, col] = i
                magnitudes_map[row, col] = sqrt_magnitude_sq
                normalized_iterations_map[row, col] = i + 1 - np.log(np.log(magnitudes_map[row, col])) / np.log(power)
                final_angles_map[row, col] = np.arctan2(z_imag, z_real)
                dz_by_dz0_magnitude_sq = dz_by_dz0_real**2 + dz_by_dz0_imag**2
                if dz_by_dz0_magnitude_sq > 0:
                    final_derivative_magnitude_map[row, col] = np.log(np.sqrt(dz_by_dz0_magnitude_sq))
                    distance_map[row, col] = 2.0 * sqrt_magnitude_sq * np.log(sqrt_magnitude_sq) / np.sqrt(dz_by_dz0_magnitude_sq)
                    derivative_bailout_map[row, col] = sqrt_magnitude_sq * np.log(sqrt_magnitude_sq) / np.sqrt(dz_by_dz0_magnitude_sq)
                else:
                    final_derivative_magnitude_map[row, col] = 0.0
                    distance_map[row, col] = 0.0
                    derivative_bailout_map[row, col] = 0.0

                final_Z_real_map[row, col] = z_real
                final_Z_imag_map[row, col] = z_imag
                final_derivative_real_map[row, col] = dz_by_dz0_real
                final_derivative_imag_map[row, col] = dz_by_dz0_imag
                bailout_location_real_map[row, col] = z_real
                bailout_location_imag_map[row, col] = z_imag
                break

            # ORBIT TRAP LOGIC
            # Only compute if a trap is enabled and we are not on the first iteration
            if trap_type != 0 and i > 0:
                current_distance = 0.0

                if trap_type == 1: # Point Trap
                    trap_x = trap_params[1]
                    trap_y = trap_params[2]
                    current_distance = math.sqrt((z_real - trap_x)**2 + (z_imag - trap_y)**2)
                elif trap_type == 2: # Line Trap
                    current_distance = _distance_to_line_segment(z_real, z_imag, trap_params[1], trap_params[2], trap_params[3], trap_params[4])
                elif trap_type == 3: # Circle Trap
                    trap_x = trap_params[1]
                    trap_y = trap_params[2]
                    trap_radius = trap_params[3]
                    distance_from_center = math.sqrt((z_real - trap_x)**2 + (z_imag - trap_y)**2)
                    current_distance = abs(distance_from_center - trap_radius)
                elif trap_type == 4: # Square Trap
                    half_side = trap_params[3] / 2.0
                    x_dist = max(0.0, abs(z_real - trap_params[1]) - half_side)
                    y_dist = max(0.0, abs(z_imag - trap_params[2]) - half_side)
                    current_distance = math.sqrt(x_dist**2 + y_dist**2)
                elif trap_type == 5: # Triangle Trap
                    # Distance to each of the three line segments
                    dist1 = _distance_to_line_segment(z_real, z_imag, trap_params[1], trap_params[2], trap_params[3], trap_params[4])
                    dist2 = _distance_to_line_segment(z_real, z_imag, trap_params[3], trap_params[4], trap_params[5], trap_params[6])
                    dist3 = _distance_to_line_segment(z_real, z_imag, trap_params[5], trap_params[6], trap_params[1], trap_params[2])
                    current_distance = min(dist1, dist2, dist3)

                if current_distance < min_distance_to_trap_map[row, col]:
                    min_distance_to_trap_map[row, col] = current_distance
                    min_distance_iteration_map[row, col] = i
            
            # Hybrid Calculation for Derivative:
            if is_integer_power:
                if power == 2:
                    next_dz_by_dz0_real = 2 * (z_real * dz_by_dz0_real - z_imag * dz_by_dz0_imag)
                    next_dz_by_dz0_imag = 2 * (z_real * dz_by_dz0_imag + z_imag * dz_by_dz0_real)
                else:
                    z_mag = np.sqrt(z_real*z_real + z_imag*z_imag)
                    z_angle = np.arctan2(z_imag, z_real)
                    z_power_minus_1_mag = z_mag**(power-1)
                    z_power_minus_1_angle = z_angle * (power-1)
                    z_power_minus_1_real = z_power_minus_1_mag * np.cos(z_power_minus_1_angle)
                    z_power_minus_1_imag = z_power_minus_1_mag * np.sin(z_power_minus_1_angle)
                    next_dz_by_dz0_real = power * (z_power_minus_1_real * dz_by_dz0_real - z_power_minus_1_imag * dz_by_dz0_imag)
                    next_dz_by_dz0_imag = power * (z_power_minus_1_real * dz_by_dz0_imag + z_power_minus_1_imag * dz_by_dz0_real)
            else:
                z_mag = np.sqrt(z_real*z_real + z_imag*z_imag)
                z_angle = np.arctan2(z_imag, z_real)
                z_power_minus_1_mag = z_mag**(power-1)
                z_power_minus_1_angle = z_angle * (power-1)
                z_power_minus_1_real = z_power_minus_1_mag * np.cos(z_power_minus_1_angle)
                z_power_minus_1_imag = z_power_minus_1_mag * np.sin(z_power_minus_1_angle)
                next_dz_by_dz0_real = power * (z_power_minus_1_real * dz_by_dz0_real - z_power_minus_1_imag * dz_by_dz0_imag)
                next_dz_by_dz0_imag = power * (z_power_minus_1_real * dz_by_dz0_imag + z_power_minus_1_imag * dz_by_dz0_real)

            dz_by_dz0_real = next_dz_by_dz0_real
            dz_by_dz0_imag = next_dz_by_dz0_imag
            
            # Hybrid Calculation for Z:
            if is_integer_power:
                if power == 2:
                    next_z_real = z_real * z_real - z_imag * z_imag + c_real
                    next_z_imag = 2 * z_real * z_imag + c_imag
                else:
                    if power == 0:
                        z_power_real = 1.0
                        z_power_imag = 0.0
                    else:
                        z_power_real = z_real
                        z_power_imag = z_imag
                        for _ in range(int(power)-1):
                            temp_real = z_power_real
                            z_power_real = z_power_real * z_real - z_power_imag * z_imag
                            z_power_imag = temp_real * z_imag + z_power_imag * z_real

                    next_z_real = z_power_real + c_real
                    next_z_imag = z_power_imag + c_imag
            else:
                r_z = sqrt_magnitude_sq
                theta_z = np.arctan2(z_imag, z_real)
                new_r = r_z**power
                new_theta = power * theta_z
                next_z_real = new_r * np.cos(new_theta) + c_real
                next_z_imag = new_r * np.sin(new_theta) + c_imag

            z_real = next_z_real
            z_imag = next_z_imag

        # Record final values for points that didn't escape.
        if iterations_map[row, col] == iterations:
            final_angles_map[row, col] = np.arctan2(z_imag, z_real)
            dz_by_dz0_magnitude_sq = dz_by_dz0_real**2 + dz_by_dz0_imag**2
            if dz_by_dz0_magnitude_sq > 0:
                 final_derivative_magnitude_map[row, col] = np.log(np.sqrt(dz_by_dz0_magnitude_sq))
            else:
                 final_derivative_magnitude_map[row, col] = 0.0
            
            final_Z_real_map[row, col] = z_real
            final_Z_imag_map[row, col] = z_imag
            final_derivative_real_map[row, col] = dz_by_dz0_real
            final_derivative_imag_map[row, col] = dz_by_dz0_imag

    return (iterations_map,
            normalized_iterations_map,
            magnitudes_map,
            initial_angles_map,
            final_angles_map,
            distance_map,
            final_derivative_magnitude_map,
            min_distance_to_trap_map,
            min_distance_iteration_map,
            derivative_bailout_map,
            final_Z_real_map,
            final_Z_imag_map,
            final_derivative_real_map,
            final_derivative_imag_map,
            bailout_location_real_map,
            bailout_location_imag_map,
            final_Z_real_at_fixed_iteration_map,
            final_Z_imag_at_fixed_iteration_map)
from __future__ import annotations
import numpy as np

def normalize_maps(iterations_map: np.ndarray, 
                   magnitudes_map: np.ndarray, 
                   angles_map: np.ndarray,
                   iterations: int
                   ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Normalizes raw fractal map data for rendering and visualization.

    This function processes the raw iteration, magnitude, and angles maps to 
    produce normalized versions, all with values in the range [0, 1],
    suitable for use in color mapping algorithms. The magnitude map is
    transformed using a logarithmic scale to enhance detail in areas with
    low variation.

    Args:
        iterations_map (np.ndarray): A 2D NumPy array containing the raw iteration counts.
        magnitudes_map (np.ndarray): A 2D NumPy array containing the raw magnitudes of the
                                    complex numbers at escape.
        angles_map (np.ndarray): A 2D NumPy array containing the raw escape angles (phase) of Z.
        iterations (int): The maximum number of iterations used in the fractal calculation.

    Returns:
        tuple: (normalized_iterations_map, normalized_magnitudes_map, normalized_angles_map)
            normalized_iterations_map (np.ndarray): A 2D NumPy array of normalized iteration counts
                                    in the range [0, 1].
            normalized_magnitudes_map (np.ndarray): A 2D NumPy array of normalized magnitudes of the
                                    complex numbers at escape in the range [0, 1].
            normalized_angles_map (np.ndarray): A 2D NumPy array of normalized escape angles (phase) of Z
                                    in the range [0, 1].
    """
    normalized_iterations_map = iterations_map / iterations

    # --- Robust Magnitude Normalization ---
    # Sanitize the input magnitudes map first to handle NaN or Inf values
    # Replace any NaN values with 0.
    sanitized_magnitudes_map = np.nan_to_num(magnitudes_map, nan=0.0)
    # Replace any infinite values with a large, but finite number to avoid overflow.
    sanitized_magnitudes_map = np.clip(sanitized_magnitudes_map, a_min=None, a_max=np.finfo(float).max)
    
    # Clip to ensure all values are non-negative before applying log.
    clipped_magnitudes_map = np.clip(sanitized_magnitudes_map, 0, None)
    
    # Use log1p for numerical stability, which handles values near zero gracefully.
    log_magnitudes = np.log1p(clipped_magnitudes_map)

    min_log_mag = np.min(log_magnitudes)
    max_log_mag = np.max(log_magnitudes)
    
    # Avoid division by zero if all log_magnitudes are uniform.
    if (max_log_mag - min_log_mag) > 1e-9:
        normalized_magnitudes_map  = (log_magnitudes - min_log_mag) / (max_log_mag - min_log_mag)
    else:
        normalized_magnitudes_map  = np.zeros_like(log_magnitudes)

    # Leaves angles map in normalized radians, multiply by 360 for degrees
    normalized_angles_map = (angles_map / (2 * np.pi)) 

    return normalized_iterations_map, normalized_magnitudes_map, normalized_angles_map
import math
import numpy as np
from numba import njit

@njit
def _normalize_logarithmic(map_array: np.ndarray) -> np.ndarray:
    """
    Applies logarithmic and linear normalization to a map.
    """
    log_map = np.log1p(np.clip(map_array, 0, None))
    min_val = np.min(log_map)
    max_val = np.max(log_map)
    if max_val - min_val == 0:
        width = map_array.shape[0]
        height = map_array.shape[0]
        return np.zeros((height, width), dtype=np.float64)
    return (log_map - min_val) / (max_val - min_val)

@njit
def _normalize_linear(map_array: np.ndarray) -> np.ndarray:
    """
    Applies linear normalization to a map.
    """
    min_val = np.min(map_array)
    max_val = np.max(map_array)
    if max_val - min_val == 0:
        width = map_array.shape[0]
        height = map_array.shape[0]
        return np.zeros((height, width), dtype=np.float64)
    return (map_array - min_val) / (max_val - min_val)

@njit
def _normalize_by_max_val(map_array: np.ndarray, max_val: int) -> np.ndarray:
    """
    Normalizes a map by a maximum value.
    """
    return map_array / max_val

@njit
def _normalize_angles(map_array: np.ndarray) -> np.ndarray:
    """
    Normalizes angles in radians to the range [0, 1].
    """
    return np.where(map_array > 0, map_array / (2 * math.pi), 0)


def normalize_map(map_array: np.ndarray, 
                  map_name: str, 
                  max_iterations: int, 
                  fixed_iterations: int=20
                  ) -> np.ndarray:
    """
    Args:
        map_array (np.ndarray):
            A 2D NumPy array containing the raw, un-normalized fractal map data.
        map_name (str):
            The name of the map, used to select the correct normalization logic.
        max_iterations (int):
            The maximum number of iterations used in the fractal calculation.
            This is used for maps like `iterations_map`.
        fixed_iterations (int, optional):
            A specific iteration count for fixed-iteration maps, used for
            normalization when `map_name` is `final_Z_real_at_fixed_iteration_map`
            or `final_Z_imag_at_fixed_iteration_map`. Defaults to 20.

    Returns:
        np.ndarray:
            The normalized map array. For most maps, values will be in the
            range [0, 1]. For "raw" maps (e.g., `final_Z_real_map`), the
            original floating-point data is returned.
    """
    if map_name in ['final_Z_real_map', 
                    'final_Z_imag_map', 
                    'final_derivative_real_map', 
                    'final_derivative_imag_map',
                    'bailout_location_real_map',
                    'bailout_location_imag_map']:
        return map_array

    elif map_name in ['iterations_map', 'normalized_iterations_map']:
        return _normalize_by_max_val(map_array, max_iterations)

    elif map_name in ['final_Z_real_at_fixed_iteration_map',
                      'final_Z_imag_at_fixed_iteration_map']:
        return _normalize_by_max_val(map_array, fixed_iterations)
        
    elif map_name in ['distance_map', 
                      'min_distance_to_trap_map', 
                      'final_derivative_magnitude_map']:
        return _normalize_logarithmic(map_array)

    elif map_name in ['initial_angles_map', 'final_angles_map']:
        return _normalize_angles(map_array)

    else:
        return _normalize_linear(map_array)
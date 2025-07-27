import numpy as np

def generate_coords(
    x_min: float, 
    x_max: float, 
    y_min: float,
    y_max: float,
    resolution: int):
    """
    Generates 1D arrays of real (x) and imaginary (y) coordinates for a fractal grid.

    Args:
        x_min (float): Minimum real coordinate.
        x_max (float): Maximum real coordinate.
        y_min (float): Minimum imaginary coordinate.
        y_max (float): Maximum imaginary coordinate.
        resolution (int): The number of points along each dimension (e.g., 1024 for 1024x1024).

    Returns:
        tuple: (x_coords, y_coords)
            x_coords (np.ndarray): 1D array of real coordinates, dtype=float64.
            y_coords (np.ndarray): 1D array of imaginary coordinates, dtype=float64.
    """
    x_coords = np.linspace(x_min, x_max, resolution, dtype=np.float64)
    y_coords = np.linspace(y_min, y_max, resolution, dtype=np.float64)
    return x_coords, y_coords
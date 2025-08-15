def convert_to_center(x_min: float, 
                      x_max: float, 
                      y_min: float, 
                      y_max: float
                      ) -> tuple[float, float, float, float]:
    """
    Converts x y min/max to span/center coordiantes.

    Args:
        x_min: Min coordinate of the view along the real axis.
        x_max: Max coordinate of the view along the real axis.
        y_min: Min coordinate of the view along the imaginary axis.
        y_max: Max coordinate of the view along the imaginary axis.

    Returns:
        A tuple containing (x_center, x_span, y_center, y_span).
    """
    x_center = (x_min + x_max) / 2.0
    x_span = x_max - x_min
    y_center = (y_min + y_max) / 2.0
    y_span = y_max - y_min
    return x_center, x_span, y_center, y_span

def convert_to_minmax(x_center: float, 
                      x_span: float, 
                      y_center: float, 
                      y_span: float
                      ) -> tuple[float, float, float, float]:
    """
    Converts x y span/center to min/max coordinates.

    Args:
        x_center: Real coordinate of the center of the view.
        x_span: Total width of the view along the real axis.
        y_center: Imaginary coordinate of the center of the view.
        y_span: Total height of the view along the imaginary axis.

    Returns:
        A tuple containing (x_min, x_max, y_min, y_max).
    """
    x_min = x_center - (x_span / 2.0)
    x_max = x_center + (x_span / 2.0)
    y_min = y_center - (y_span / 2.0)
    y_max = y_center + (y_span / 2.0)
    return x_min, x_max, y_min, y_max

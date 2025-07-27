def convert_to_center(x_min, x_max, y_min, y_max):
    """
    Converts x y min/max to span/center coordiantes.

    Args:
        x_min: The min coordinate of the view along the real axis.
        x_max: The max coordinate of the view along the real axis.
        y_min: The min coordinate of the view along the imaginary axis.
        y_max: The max coordinate of the view along the imaginary axis.

    Returns:
        A tuple containing (x_center, y_center, x_span, y_span).
    """
    x_center = (x_min + x_max) / 2.0
    y_center = (y_min + y_max) / 2.0
    x_span = x_max - x_min
    y_span = y_max - y_min
    return x_center, y_center, x_span, y_span

def convert_to_minmax(x_center, y_center, x_span, y_span):
    """
    Converts x y span/center to min/max coordinates.

    Args:
        x_center: The real coordinate of the center of the view.
        y_center: The imaginary coordinate of the center of the view.
        x_span: The total width of the view along the real axis.
        y_span: The total height of the view along the imaginary axis.

    Returns:
        A tuple containing (x_min, x_max, y_min, y_max).
    """
    x_min = x_center - (x_span / 2.0)
    x_max = x_center + (x_span / 2.0)
    y_min = y_center - (y_span / 2.0)
    y_max = y_center + (y_span / 2.0)
    return x_min, x_max, y_min, y_max

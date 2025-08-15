from __future__ import annotations
import numpy as np
from skimage import color

# Module-level constants for color adjustments.
GAMMA_FACT = 0.5
BRIGHTNESS = 1.3
C_MAX_FOR_SRGB = 75  # The maximum Chroma value for the sRGB color gamut is ~75.

def _channel_helper(L: np.ndarray, 
                    C: np.ndarray, 
                    H: np.ndarray
                   ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Applies aesthetic and color-space-specific adjustments to normalized color channels.

    This helper function takes normalized L, C, and H maps and applies gamma,
    brightness, and chroma clipping to ensure the final values are suitable
    for the LCH color space and sRGB rendering. The Hue channel is scaled from
    a [0, 1] range to a [0, 360] range as required by the LCH color space.

    Args:
        L (np.ndarray): A 2D NumPy array for the Lightness channel, normalized to [0, 1].
        C (np.ndarray): A 2D NumPy array for the Chroma channel, normalized to [0, 1].
        H (np.ndarray): A 2D NumPy array for the Hue channel, normalized to [0, 1].

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: 
            A tuple containing the adjusted L, C, and H channels.
            - L (Lightness) is scaled and clipped to the range [0, 100].
            - C (Chroma) is scaled and clipped to the range [0, C_MAX_FOR_SRGB].
            - H (Hue) is scaled and clipped to the range [0, 360].
    """
    # Clip the Lightness channel to ensure no negative values exist before the power operation.
    # This specifically addresses the 'aim' color scheme where L is the angles map,
    # which can have tiny negative values due to floating point inaccuracies.
    L = np.clip(L, 0, None)

    # Scale Hue from [0, 1] to the required [0, 360] range for LCH color space.
    H = H * 360
    
    # Apply gamma correction and brightness to the Lightness channel.
    # The result is scaled and clipped to the [0, 100] range expected by LCH.
    L = np.clip((L ** GAMMA_FACT) * BRIGHTNESS * 100, 0, 100)
    
    # Scale the Chroma channel and clip it to the defined sRGB limit.
    C = np.clip(C * C_MAX_FOR_SRGB, 0, C_MAX_FOR_SRGB)
    
    # Ensure Hue is within the [0, 360] range after scaling.
    H = np.clip(H, 0, 360)

    return L, C, H

def _stack_lch(L: np.ndarray, 
               C: np.ndarray, 
               H: np.ndarray
               ) -> np.ndarray:
    """
    Internal helper function to stack LCH color maps and convert to RGB.

    This function combines the Lightness (L), Chroma (C), and Hue (H) 
    channels, which are NumPy arrays, into a single 3D LCH image. It then 
    converts this LCH image to the LAB color space, and finally to the 
    standard RGB color space for rendering.

    Args:
        L (np.ndarray): A 2D NumPy array representing the Lightness channel.
        C (np.ndarray): A 2D NumPy array representing the Chroma channel.
        H (np.ndarray): A 2D NumPy array representing the Hue channel.

    Returns:
        np.ndarray: A 3D NumPy array of shape (height, width, 3) ready for RGB rendering.
    """
    lch_img = np.stack([L, C, H], axis=-1)
    lch_lab = color.lch2lab(lch_img)
    lch_rgb = color.lab2rgb(lch_lab)
    return lch_rgb


def generate_colors(iterations_map: np.ndarray, 
                   magnitudes_map: np.ndarray, 
                   angles_map: np.ndarray,
                   color_scheme: str = 'ima'
                   ) -> np.ndarray:
    """
    Generates a color map using the LCH color space from normalized fractal data.

    This function takes the three normalized fractal maps (iterations, magnitudes, and angles) 
    and assigns them to the Lightness, Chroma, and Hue channels of the LCH color space 
    based on the specified color scheme. The resulting LCH image is then converted to RGB.
    This provides a flexible way to create different visual styles from the same fractal data.

    Args:
        iterations_map (np.ndarray): A 2D NumPy array containing the normalized iteration counts.
        magnitudes_map (np.ndarray): A 2D NumPy array containing the normalized magnitudes of the
                                     complex numbers at escape.
        angles_map (np.ndarray): A 2D NumPy array containing the normalized escape angles (phase) of Z.
        color_scheme (str): Specifies the combination of maps to generate the LCH color scheme. 
                           The three letters represent the assignment of the input maps to L, C, and H.
                           For example, 'ima' maps iterations to Lightness, magnitudes to Chroma, and angles to Hue.
                           The six supported schemes are 'ima', 'iam', 'mia', 'mai', 'aim', and 'ami'.

    Returns:
        np.ndarray: A 3D NumPy array of shape (height, width, 3) ready for RGB rendering.
    """
    if color_scheme == 'ima':
        L, C, H = iterations_map, magnitudes_map, angles_map
        L, C, H = _channel_helper(L, C, H)
        color_map = _stack_lch(L, C, H)
    elif color_scheme == 'iam':
        L, C, H = iterations_map, angles_map, magnitudes_map
        L, C, H = _channel_helper(L, C, H)
        color_map = _stack_lch(L, C, H)
    elif color_scheme == 'mia':
        L, C, H = magnitudes_map, iterations_map, angles_map
        L, C, H = _channel_helper(L, C, H)
        color_map = _stack_lch(L, C, H)
    elif color_scheme == 'mai':
        L, C, H = magnitudes_map, angles_map, iterations_map
        L, C, H = _channel_helper(L, C, H)
        color_map = _stack_lch(L, C, H)
    elif color_scheme == 'aim':
        L, C, H = angles_map, iterations_map, magnitudes_map
        L, C, H = _channel_helper(L, C, H)
        color_map = _stack_lch(L, C, H)
    elif color_scheme == 'ami':
        L, C, H = angles_map, magnitudes_map, iterations_map
        L, C, H = _channel_helper(L, C, H)
        color_map = _stack_lch(L, C, H)

    return color_map 
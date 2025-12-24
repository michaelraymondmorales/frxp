/**
 * Visual settings for the 3D mesh representation of the data.
 */
export const MESH_SETTINGS = {
    // Multiplier applied to the combinedHeightMap values to set the 
    // vertical scale (Y-axis) of the terrain mesh. 
    heightScale: 222,
    // Multiplier used to compress/stretch the normalizedIterationsMap 
    // values for texture coordinate lookup against the colorMapImage.
    colorScale: 0.2,
};

/**
 * Settings for the sun and environmental lighting.
 */
export const SUN_SETTINGS = {
    speed: 0.1,
    intensity: 3.0,
    lightRadius: 600,
    defaultColor: 0xFFF8E1,
};
import { useMemo, useRef, useLayoutEffect } from 'react';
import * as THREE from 'three';
import { MESH_SETTINGS } from '../configs/sceneConfig';

/**
 * Renders a 3D fractal terrain using Three.js planeGeometry.
 * * @component
 * @param {Object} props
 * @param {Object} props.fractalData - The raw data from the fractal API.
 * @param {Array<Array<number>>} props.fractalData.combinedHeightMap - 2D array of elevation data.
 * @param {Array<Array<number>>} props.fractalData.normalizedIterationsMap - 2D array of iteration counts.
 * @param {HTMLImageElement} props.fractalData.colorMapImage - The source image used for color lookup.
 */
const FractalMesh = ({ fractalData }) => {
    // 0. Unpack the fractalData into map constants
    const { combinedHeightMap, normalizedIterationsMap, colorMapImage } = fractalData;
    
    // 1. Create the Ref for the geometry
    const geometryRef = useRef();

    // 2. Data Calculation.
    const { positions, colors, gridWidth, gridHeight } = useMemo(() => {
        const height = combinedHeightMap.length; 
        const width = combinedHeightMap[0].length; 
        const vertexCount = width * height;
        
        // Create new Float32Arrays to hold the positons and colors.
        const posArray = new Float32Array(vertexCount * 3);
        const colArray = new Float32Array(vertexCount * 3);
        const colorTool = new THREE.Color();

        // Extract pixel data from the loaded color map image.
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d', { willReadFrequently: true });
        canvas.width = colorMapImage.width;
        canvas.height = colorMapImage.height;
        ctx.drawImage(colorMapImage, 0, 0);
        const colorMapPixels = ctx.getImageData(0, 0, canvas.width, canvas.height).data;

        for (let i = 0; i < height; i++) {
            for (let j = 0; j < width; j++) {
                // --- Positon Logic ---
                const index = (i * width) + j;
                const x = j - width / 2;
                const z = i - height / 2;
                const rawY = combinedHeightMap[i][j];
                // If height is not a finite number, set it to 0
                let y = (Number.isFinite(rawY) ? rawY : 0) * MESH_SETTINGS.heightScale;

                // Skirt Logic: Force edges to height 0 
                if (i === 0 || 
                    i === height - 1 || 
                    j === 0 || 
                    j === width - 1) {
                    y = 0;
                }

                posArray[index * 3] = x;
                posArray[index * 3 + 1] = y;
                posArray[index * 3 + 2] = z;

                // --- Coloring Logic ---
                const iterValue = normalizedIterationsMap[i][j];
                const iteration = Math.pow(iterValue, MESH_SETTINGS.colorScale);
                const colorIndex = Math.min(Math.floor(iteration * 255), 255);    
                // Look up the RGB values from the color map pixel data for the base color.
                const r = colorMapPixels[colorIndex * 4] / 255;
                const g = colorMapPixels[colorIndex * 4 + 1] / 255;
                const b = colorMapPixels[colorIndex * 4 + 2] / 255;
                // Set the final RGB values for the vertex.
                colorTool.setRGB(r, g, b);
                colArray[index * 3] = colorTool.r;
                colArray[index * 3 + 1] = colorTool.g;
                colArray[index * 3 + 2] = colorTool.b; 
            }
        }

        return { 
            positions: posArray, 
            colors: colArray, 
            gridWidth: width, 
            gridHeight: height 
        };
    }, [combinedHeightMap, normalizedIterationsMap, colorMapImage]);

    /**
     * Recalculates lighting normals whenever geometry positions change.
     * This ensures correct shading on the fractal peaks.
     */
    useLayoutEffect(() => {
        if (geometryRef.current) {
            geometryRef.current.computeVertexNormals();
        }
    }, [positions]);

    return (
        <mesh>
            {/* Attached the ref here so useLayoutEffect can access it */}
            <planeGeometry 
                ref={geometryRef}
                args={[gridWidth - 1, gridHeight - 1, gridWidth - 1, gridHeight - 1]}
            >
                <bufferAttribute
                    attach="attributes-position"
                    count={positions.length / 3}
                    array={positions}
                    itemSize={3}
                />
                <bufferAttribute
                    attach="attributes-color"
                    count={colors.length / 3}
                    array={colors}
                    itemSize={3}
                />
                <bufferAttribute 
                    attach="attributes-uv" 
                    count={0} 
                    array={new Float32Array(0)} 
                    itemSize={2} 
                />
            </planeGeometry>
            <meshLambertMaterial vertexColors side={THREE.DoubleSide} />
        </mesh>
    );
};

export default FractalMesh;
import Frxp3D from './Frxp3D';
import { useEffect, useState } from 'react';
import { useSearchParams } from "react-router-dom";
import { PLATEAUS_AND_VALLEYS } from './configs/noiseConfig';
import { createFractalMountains } from './utils/noiseUtils';

/**
 * @typedef {Object} FractalParams
 * @property {string} fractal_type - The type of fractal (e.g., 'Mandelbrot', 'Julia').
 * @property {number} x_center - The real component of the center point for the visualization.
 * @property {number} y_center - The imaginary component of the center point for the visualization.
 * @property {number} x_span - The width of the viewport in the complex plane.
 * @property {number} y_span - The height of the viewport in the complex plane.
 * @property {number} iterations - The maximum number of iterations for the fractal escape-time algorithm.
 * @property {number} power - The power coefficient for the fractal equation.
 * @property {number} resolution - The N x N pixel resolution of the generated map.
 * @property {number} bailout - The bailout radius squared.
 * @property {number} fixed_iteration - A specific iteration count used for certain coloring methods.
 * @property {number} trap_type - The type of geometric trap used for distance estimation.
 * @property {number} trap_x1 - X coordinate of trap point 1.
 * @property {number} trap_y1 - Y coordinate of trap point 1.
 * @property {number} trap_x2 - X coordinate of trap point 2.
 * @property {number} trap_y2 - Y coordinate of trap point 2.
 * @property {number} trap_x3 - X coordinate of trap point 3.
 * @property {number} trap_y3 - Y coordinate of trap point 3.
 */

/**
 * @typedef {Object} LoadedFractalData
 * @property {number[][]} combinedHeightMap - The final 2D height map array combining fractal distance and noise.
 * @property {number[][]} normalizedIterationsMap - The 2D array of normalized iteration counts.
 * @property {HTMLImageElement} colorMapImage - The loaded Image object for coloring the terrain.
 */

/**
 * App is the root component responsible for initializing the application,
 * managing global state, fetching fractal data from the API, processing the data (adding noise),
 * and passing the final configuration to the 3D visualization component (Frxp3D).
 * It reads initial parameters from the URL search query.
 * @component
 * @returns {JSX.Element} The Frxp3D visualization component or a loading indicator.
 */
const App = () => {

    // State variables to hold the current status message and the fractal data.
    const [fractalData, setFractalData] = useState(null);
    const [searchParams] = useSearchParams();
    const queryParams = Object.fromEntries(searchParams.entries());

    // --- API Configuration ---
    const API_URL = 'http://localhost:5000';

    /** @type {FractalParams} */
    const FRACTAL_PARAMS = {
        fractal_type: queryParams.fractal_type || 'Mandelbrot',
        x_center: parseFloat(queryParams.x_center) || -0.7436438,
        y_center: parseFloat(queryParams.y_center) || 0.1318259,
        x_span: parseFloat(queryParams.x_span) || 0.00003,
        y_span: parseFloat(queryParams.y_span) || 0.00003,
        iterations: parseInt(queryParams.iterations) || 2048,
        power: parseFloat(queryParams.power) || 2.0,
        resolution: parseInt(queryParams.resolution) || 1024,
        bailout: parseFloat(queryParams.bailout) || 4.0,
        fixed_iteration: parseInt(queryParams.fixed_iteration) || 333,
        trap_type: parseInt(queryParams.trap_type) || 3,
        trap_x1: parseFloat(queryParams.trap_x1) || 2.0,
        trap_y1: parseFloat(queryParams.trap_y1) || 0.0,
        trap_x2: parseFloat(queryParams.trap_x2) || -1.0,
        trap_y2: parseFloat(queryParams.trap_y2) || 1.5,
        trap_x3: parseFloat(queryParams.trap_x3) || -1.0,
        trap_y3: parseFloat(queryParams.trap_y3) || -1.5
     };

    /**
     * Converts a flat (1D) array of data points into a 2D grid/array.
     * This is necessary because the API returns map data as a single continuous buffer.
     * @param {Float32Array|number[]} flatArray - The 1D array of data (row by row).
     * @param {number} width - The number of columns (N).
     * @param {number} height - The number of rows (N).
     * @returns {number[][]} The 2D grid array (height x width).
     */
    const createGridFromFlatArray = (flatArray, width, height) => {
        const grid = [];
        for (let i = 0; i < height; i++) {
            const row = [];
            for (let j = 0; j < width; j++) {
                row.push(flatArray[i * width + j]);
            }
            grid.push(row);
        }
        return grid;
    };

    /**
     * Fetches a raw (Float32Array) fractal map (e.g., distance or iteration data) from the API.
     * It handles Gzip decompression if the data is compressed and includes caching status logging.
     * @async
     * @param {string} queryString - The URL query string containing fractal parameters.
     * @param {string} mapName - The name of the map to fetch (e.g., 'distance_map').
     * @returns {Promise<Float32Array>} A promise that resolves to the 1D Float32Array of the map data.
     * @throws {Error} Throws an error if the network request fails or the map cannot be downloaded.
     */
    const fetchFractalMap = async (queryString, mapName) => {
        let mapResponse = await fetch(`${API_URL}/get_map?${queryString}&map_name=${mapName}&map_type=raw`);
        if (!mapResponse.ok) {
            throw new Error(`Failed to download map: ${mapResponse.statusText}`);
        }
         console.log(`${mapResponse.status} Cached: raw ${mapName} ${queryString}`);

        const clonedMapResponse = mapResponse.clone();
        let decompressedBuffer;
        try {
            console.log(`Attempting to decompress raw ${mapName} data...`);
            const compressedStream = mapResponse.body;
            const decompressedStream = compressedStream.pipeThrough(new DecompressionStream('gzip'));    
            const chunks = [];
            const reader = decompressedStream.getReader();
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                chunks.push(value);
            }
            decompressedBuffer = new Blob(chunks).arrayBuffer();
            
        } catch (decompressionError) {
            console.log(`Decompression for raw ${mapName} failed, assuming data is already uncompressed. Error: ${decompressionError.message}`);
            decompressedBuffer = await clonedMapResponse.arrayBuffer();
        }

        const data = new Float32Array(await decompressedBuffer);
        console.log(`Successfully loaded ${data.length} data points for raw ${mapName}.`);
        return data;
    };

    /**
     * Fetches a PNG image map from the API.
     * It handles asynchronous task polling (status 202) if the map needs to be calculated first.
     * @async
     * @param {string} queryString - The URL query string containing fractal parameters.
     * @param {string} mapName - The name of the map to fetch (e.g., 'distance_map').
     * @returns {Promise<Blob>} A promise that resolves to a Blob object containing the PNG image data.
     * @throws {Error} Throws an error if the calculation fails or polling exceeds max attempts.
     */
    const fetchFractalImg = async (queryString, mapName) => {
        let mapResponse = await fetch(`${API_URL}/get_map?${queryString}&map_name=${mapName}&map_type=png`);
        if (mapResponse.status === 200) {
            console.log(`${mapResponse.status} Cached: png ${mapName} ${queryString}`);
        } else if (mapResponse.status === 202) {          
            console.log(`${mapResponse.status} Polling: png ${mapName} ${queryString}`);
            let mapResult = await mapResponse.json();      
            let taskId = mapResult.task_id;
            console.log(`Calculation started with Task ID: ${taskId}`);
            const maxPolls = 60; // Poll for up to 60 seconds
            let taskState;
            for (let i = 0; i < maxPolls; i++) {
                const statusResponse = await fetch(`${API_URL}/task_status/${taskId}`);
                const statusResult = await statusResponse.json();
                taskState = statusResult.state;
                console.log(`Poll ${i} status: ${taskState}`);
                
                if (taskState === 'SUCCESS') {
                    console.log(`Calculation complete, proceeding to download data.`);
                    mapResponse = await fetch(`${API_URL}/get_map?${queryString}&map_name=${mapName}&map_type=png`);
                    break;
                }
                if (taskState === 'FAILURE') {
                    throw new Error(`Calculation failed: ${statusResult.status}`);
                }
                await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
            }
        }
        const imageBlob = await mapResponse.blob();
        return imageBlob;
    };

    /**
     * Orchestrates the entire data loading and processing pipeline.
     * 1. Initiates the map calculation on the API server, polling if necessary.
     * 2. Fetches the raw distance map and raw normalized iteration map data.
     * 3. Loads the required color map image asset.
     * 4. Converts raw 1D data into 2D grids.
     * 5. Applies fBM noise generation (Simplex Noise) to the distance map.
     * 6. Sets the final processed data into the component state (`fractalData`).
     * @async
     * @returns {Promise<void>}
     * @throws {Error} Throws errors encountered during API calls, polling, or data processing.
     */
    const loadFractalData = async () => {
        try {
            const queryString = new URLSearchParams(FRACTAL_PARAMS).toString();
            const calcResponse = await fetch(`${API_URL}/calculate_map?${queryString}`);
            const calcResult = await calcResponse.json();
            
            if (!calcResponse.ok) {
                throw new Error(`API Error: ${calcResult.error || 'Unknown error'}`);
            }
            
            let taskId;
            if (calcResponse.status === 200) {
                console.log('Parameters cached, proceeding to download data.');
            } else if (calcResponse.status === 202) {
                taskId = calcResult.task_id;
                console.log(`Calculation polling started with Task ID: ${taskId}`);
                const maxPolls = 60;
                let taskState;
                for (let i = 0; i < maxPolls; i++) {
                    const statusResponse = await fetch(`${API_URL}/task_status/${taskId}`);
                    const statusResult = await statusResponse.json();
                    taskState = statusResult.state;
                    console.log(`Poll ${i} status: ${taskState}`);
                    if (taskState === 'SUCCESS') {
                        console.log('Calculation complete, proceeding to download data.');
                        break;
                    }
                    if (taskState === 'FAILURE') {
                        throw new Error(`Calculation failed: ${statusResult.status}`);
                    }
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
                if (taskState !== 'SUCCESS') {
                    throw new Error('Calculation did not complete in time.');
                }
            } else {
                throw new Error(`Invalid status from API: ${calcResult.status}`);
            }

            // A reusable function to load an image and return a Promise
            function loadImage(url) {
                return new Promise((resolve, reject) => {
                    const img = new Image();
                    img.onload = () => resolve(img);
                    img.onerror = (err) => reject(new Error('Failed to load image at ' + url));
                    img.src = url;
                });
            }

            // Call the reusable function for each map needed
            const [
                distanceMapData,
                normalizedIterationsMapData,
                colorMapImage
            ] = await Promise.all([
                fetchFractalMap(queryString, 'distance_map'),
                fetchFractalMap(queryString, 'normalized_iterations_map'),
                loadImage('assets/color-maps/badlands_color_map.png')
            ]);

            // Convert the 1D arrays to 2D grids
            const resolution = FRACTAL_PARAMS.resolution;
            const distanceMap = createGridFromFlatArray(distanceMapData, resolution, resolution);
            const normalizedIterationsMap = createGridFromFlatArray(normalizedIterationsMapData, resolution, resolution);

            // --- Generate the final heightmap with fBM noise ---
            console.log("Generating mountain terrain with Simplex noise...");
            const combinedHeightMap = createFractalMountains(distanceMap, PLATEAUS_AND_VALLEYS);

            console.log('All required data loading complete.');
            
            setFractalData({
                combinedHeightMap, 
                normalizedIterationsMap,
                colorMapImage
            });

        } catch (error) {
            console.error('An error occurred during data loading:', error);
        }
    };

    // Use a useEffect hook to run the data fetching function once on component mount.
    useEffect(() => {
        loadFractalData();
    }, []);

    return fractalData ? <Frxp3D fractalData={fractalData} /> : <p></p>
};

export default App;
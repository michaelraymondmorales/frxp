import Frxp3D from './Frxp3D';
import { useEffect, useState } from 'react';
import { useSearchParams } from "react-router-dom";
import { createFractalMountains } from './noiseUtils';
// The main application component.
// It fetches fractal data from the API and manages the UI state.
const App = () => {

    // State variables to hold the current status message and the fractal data.
    const [fractalData, setFractalData] = useState(null);
    const [searchParams] = useSearchParams();
    const queryParams = Object.fromEntries(searchParams.entries());

    // --- API Configuration ---
    const API_URL = 'http://localhost:5000';
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
    // (3, 2.0, 0.0, -1.0, 1.5, -1.0, -1.5)
    // A helper function to convert a 1D array to a 2D grid
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

    // --- New reusable function to fetch and process a single map ---
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

    // --- Core Data Loading Function (now simplified) ---
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

            // Now, we can call the reusable function for each map we need.
            const [
                distanceMapData,
                normalizedIterationsMapData,
                minDistanceIterationMapData,
                finalZRealMapData,
                finalZImagMapData,
                finalDerivativeMagnitudeMapData,
                finalZRealAtFixedIterationMapData,
                colorMapImage
                //derivativeBailoutBlob, // A Blob is used for png
            ] = await Promise.all([
                fetchFractalMap(queryString, 'distance_map'),
                fetchFractalMap(queryString, 'normalized_iterations_map'),
                fetchFractalMap(queryString, 'min_distance_iteration_map'),
                fetchFractalMap(queryString, 'final_Z_real_map'),
                fetchFractalMap(queryString, 'final_Z_imag_map'),
                fetchFractalMap(queryString, 'final_derivative_magnitude_map'),
                fetchFractalMap(queryString, 'final_Z_real_at_fixed_iteration_map'),
                loadImage('assets/color-maps/badlands_cosine_color_map_6.png')
                //fetchFractalImg(queryString, 'derivative_bailout_map')
            ]);

            // Convert the 1D arrays to 2D grids
            const resolution = FRACTAL_PARAMS.resolution;
            const distanceMap = createGridFromFlatArray(distanceMapData, resolution, resolution);
            const normalizedIterationsMap = createGridFromFlatArray(normalizedIterationsMapData, resolution, resolution);
            const minDistanceIterationMap = createGridFromFlatArray(minDistanceIterationMapData, resolution, resolution);
            const finalZRealMap = createGridFromFlatArray(finalZRealMapData, resolution, resolution);
            const finalZImagMap = createGridFromFlatArray(finalZImagMapData, resolution, resolution);
            const finalDerivativeMagnitudeMap = createGridFromFlatArray(finalDerivativeMagnitudeMapData, resolution, resolution);
            const finalZRealAtFixedIterationMap = createGridFromFlatArray(finalZRealAtFixedIterationMapData, resolution, resolution);
            // Convert png blob into img url
            //const derivativeBailoutMap = URL.createObjectURL(derivativeBailoutBlob);

            // A set of parameters for a "Jagged Peaks" terrain.
            const JAGGED_PEAKS_PARAMS = {
                baseNoiseScale: 0.0005,
                baseNoiseOctaves: 4,
                baseNoisePersistence: 0.4,
                baseNoiseLacunarity: 2.0,
                baseNoiseWeight: 0.5,
                detailNoiseScale: 0.005,
                detailNoiseOctaves: 8,
                detailNoisePersistence: 0.5,
                detailNoiseLacunarity: 2.2,
                detailNoiseWeight: 0.6
                };

            // A set of parameters for a "Rolling Hills" terrain.
            const ROLLING_HILLS_PARAMS = {
                baseNoiseScale: 0.0005,
                baseNoiseOctaves: 3,
                baseNoisePersistence: 0.6,
                baseNoiseLacunarity: 2.0,
                baseNoiseWeight: 0.8,
                detailNoiseScale: 0.005,
                detailNoiseOctaves: 6,
                detailNoisePersistence: 0.5,
                detailNoiseLacunarity: 2.0,
                detailNoiseWeight: 0.4
                };
            
            const PLATEAUS_AND_VALLEYS = {
                baseNoiseScale: 0.0005,
                baseNoiseOctaves: 4,
                baseNoisePersistence: 0.7,
                baseNoiseLacunarity: 2.0,
                baseNoiseWeight: 0.7,
                detailNoiseScale: 0.005,
                detailNoiseOctaves: 5,
                detailNoisePersistence: 0.6,
                detailNoiseLacunarity: 2.0,
                detailNoiseWeight: 0.5
                };

            // --- New Step: Generate the final heightmap with fBM noise ---
            console.log("Generating mountain terrain with Simplex noise...");
            const combinedHeightMap = createFractalMountains(distanceMap, PLATEAUS_AND_VALLEYS);

            console.log('All required data loading complete.');
            
            setFractalData({
                combinedHeightMap, 
                normalizedIterationsMap, 
                minDistanceIterationMap,
                finalZRealMap, 
                finalZImagMap, 
                finalDerivativeMagnitudeMap,
                finalZRealAtFixedIterationMap,
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
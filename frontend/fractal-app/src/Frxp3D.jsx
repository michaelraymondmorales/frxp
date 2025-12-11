import { useRef, useEffect } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// --- Configuration Constants ---
// Multiplier applied to the combinedHeightMap values to set the 
// vertical scale (Y-axis) of the terrain mesh.
const HEIGHT_SCALING_FACTOR = 222;
// Multiplier used to compress/stretch the normalizedIterationsMap 
// values for texture coordinate lookup against the colorMapImage.
const COLOR_SCALING_FACTOR = 0.2;

/**
 * @typedef {Object} FractalData
 * @property {number[][]} combinedHeightMap - The 2D array representing the final terrain height map.
 * @property {number[][]} normalizedIterationsMap - The 2D array of normalized iteration counts.
 * @property {HTMLImageElement} colorMapImage - The loaded color map image object.
 */

/**
 * Implements the 3D visualization using Three.js, responsible for setting up the 
 * scene, camera, renderer, creating the terrain mesh, and running the animation loop.
 * It manages all Three.js resource lifecycles using React Refs.
 * * @component
 * @param {object} props - The component props.
 * @param {FractalData} props.fractalData - The processed data maps received from the App component.
 * @returns {JSX.Element} A div container that holds the Three.js canvas.
 */
function Frxp3D({ fractalData }) {
    // --- Component References ---
    // React Refs hold persistent references to Three.js instances (Scene, Mesh, Renderer) 
    // and the component's underlying DOM element across the rendering lifecycle.
    const mountRef = useRef(null);      // The Canvas DOM element
    const isSetupRef = useRef(false);   // Guard against Strict Mode double invocation
    const sceneRef = useRef(null);      // The THREE.Scene object
    const cameraRef = useRef(null);     // The THREE.Camera object
    const rendererRef = useRef(null);   // The THREE.WebGLRenderer object
    const controlRef = useRef(null);    // The THREE.OrbitControls object
    const materialRef = useRef(null);   // The THREE.Material (Phong/Shader material)
    const meshRef = useRef(null);       // The THREE.Mesh (Fractal object)

    // State to hold the ID of the requestAnimationFrame call for cleanup.
    let animationFrameId = null;

    //Unpack the fractalData into map constants.
    const {
        combinedHeightMap,
        normalizedIterationsMap,
        colorMapImage
    } = fractalData;

    useEffect(() => {
        const currentMount = mountRef.current;

        // --- Scene Setup Guard  ---
        if (!currentMount || !fractalData || isSetupRef.current) {
            console.log('Mount or data not ready, or setup already running. Skipping Three.js setup.');
            return;
        }

        isSetupRef.current = true; // Set flag to block subsequent setup calls until cleanup resets it.

        // 0. Get Dimensions
        const width = currentMount.clientWidth;
        const height = currentMount.clientHeight;

        // 1. Scene Setup
        const scene = new THREE.Scene();
        sceneRef.current = scene;

        // 2. Camera Setup
        const camera = new THREE.PerspectiveCamera(
            75, // Field of view
            width / height, // Aspect ratio
            0.1, // Near clipping plane
            1650 // Far clipping plane
        );
        camera.position.set(0, 700, 0);
        camera.lookAt(new THREE.Vector3(0, 0, 0)); // Point camera at the origin.
        cameraRef.current = camera;

        // 3. Renderer Setup
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(width, height);
        currentMount.appendChild(renderer.domElement);
        rendererRef.current = renderer;

        // 4. Orbit Controls (for user interaction)
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.25;
        controls.minDistance = 100;
        controls.maxDistance = 1000;
        controls.target.set(0, 0, 0);
        controls.screenSpacePanning = true;
        controlRef.current = controls;

        // 5. Lighting
        const ambientLight = new THREE.AmbientLight(0x404040, 3.0); // Soft white light
        scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xFFF8E1, 3.0);
        directionalLight.position.set(-600, 0, 0);
        scene.add(directionalLight);
        const directionalLightRef = { current: directionalLight }; // Save the reference for use in animate().

        // 6. Generate 3D geometry and colors
        const gridHeight = combinedHeightMap.length;
        const gridWidth = combinedHeightMap[0].length;
        const geometry = new THREE.PlaneGeometry(gridWidth, gridHeight, gridWidth - 1, gridHeight - 1);
        geometry.rotateX(-Math.PI / 2); // Rotate to lay flat on the XZ plane.
        const positionAttribute = geometry.attributes.position; 

        // Create a new Float32Array to hold the vertex colors (RGB).
        const colors = new Float32Array(gridWidth * gridHeight * 3);
        const color = new THREE.Color();

        // Extract pixel data from the loaded color map image.
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = colorMapImage.width;
        canvas.height = colorMapImage.height;
        context.drawImage(colorMapImage, 0, 0);
        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
        const colorMapPixels = imageData.data;
        
        // Apply Heightmap and Skirt Logic
        for (let i = 0; i < gridHeight; i++) {
            for (let j = 0; j < gridWidth; j++) {
                // Set the Y-height of the vertex.
                const index = (i * gridWidth) + j;
                const height = combinedHeightMap[i][j] * HEIGHT_SCALING_FACTOR;

                // --- Skirt Logic: Force edges to height 0 ---
                if (
                    i === 0 ||
                    i === gridHeight - 1||
                    j === 0 ||
                    j === gridWidth - 1
                ) {
                    positionAttribute.setY(index, 0);
                } else {
                    positionAttribute.setY(index, height);
                }
                
                // --- Coloring Logic ---
                const iteration = Math.pow(normalizedIterationsMap[i][j], COLOR_SCALING_FACTOR)
                const colorIndex = Math.min(Math.floor(iteration * 256), 255);    
                // Look up the RGB values from the color map pixel data for the base color.
                const r = colorMapPixels[colorIndex * 4] / 255;
                const g = colorMapPixels[colorIndex * 4 + 1] / 255;
                const b = colorMapPixels[colorIndex * 4 + 2] / 255;

                color.setRGB(r, g, b);
                
                // Set the final RGB values for the vertex.
                colors[index * 3] = color.r;
                colors[index * 3 + 1] = color.g;
                colors[index * 3 + 2] = color.b; 
            }
        }
        
        // Tell Three.js that the geometry has been modified.
        positionAttribute.needsUpdate = true;

        // Recalculate normals for proper lighting.
        geometry.computeVertexNormals(); 

        // Set the color attribute for the geometry.
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        // 7. Create a mesh and position it correctly
        const material = new THREE.MeshPhongMaterial({ vertexColors: true, 
                                                       flatShading: false,
                                                       specular: 0x000000, 
                                                       shininess: 10 });
        materialRef.current = material;
        const mesh = new THREE.Mesh(geometry, material);
        scene.add(mesh);
        meshRef.current = mesh;

        // 8. Handle window resizing
        const handleResize = () => {
            const newWidth = currentMount.clientWidth;
            const newHeight = currentMount.clientHeight;
            camera.aspect = newWidth / newHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(newWidth, newHeight);
        };
        window.addEventListener('resize', handleResize);

        // 9. Animation Loop
        const animate = () => {
            animationFrameId = requestAnimationFrame(animate);

            // Get current time in seconds.
            const time = performance.now() * 0.001;

            // A factor to control the speed of the sun's movement.
            const speed = 0.1;

            // Use a sine wave to make the angle oscillate between 0 and PI
            // Math.sin(time * speed) produces a value from -1 to 1.
            // Adding 1 shifts it to a range of 0 to 2.
            // Multiplying by 0.5 scales it to a range of 0 to 1.
            // Finally, multiplying by Math.PI gets the angle in the desired range (0 to PI).
            const normalizedAngle = (Math.sin(time * speed) + 1) * 0.5
            const angle = normalizedAngle * Math.PI;

            // Update the light's position based on the angle
            // Using a simple circular path with the angle
            const sunRadius = 600;
            directionalLightRef.current.position.x = Math.cos(angle) * sunRadius;
            directionalLightRef.current.position.y = Math.sin(angle) * sunRadius;
            directionalLightRef.current.position.z = 0; // A constant Z position

            controls.update();
            renderer.render(scene, camera);
        };
        animate();

        // --- Cleanup Function ---
        return () => {
            // 1. Stop the animation loop
            if (animationFrameId) {
                cancelAnimationFrame(animationFrameId);
                animationFrameId = null;
            }
            
            // 2. Detach global listeners
            window.removeEventListener('resize', handleResize);
            
            // 3. Dispose of Controls (removes their event listeners)
            if (controlRef.current) {
                controlRef.current.dispose();
            }

            // 4. Traverse the scene and dispose of all resources
            if (sceneRef.current) {
                sceneRef.current.traverse((object) => {
                    if (object.isMesh) {
                        // Dispose of Geometry
                        if (object.geometry) object.geometry.dispose();

                        // Dispose of Material(s) and Textures
                        const materials = Array.isArray(object.material) ? object.material : [object.material];
                        
                        materials.forEach(m => {
                            if (m) {
                                // Dispose of textures attached to the material
                                if (m.map) m.map.dispose();
                                if (m.displacementMap) m.displacementMap.dispose();
                                if (m.lightMap) m.lightMap.dispose();
                                // Add more texture types as needed (e.g., normalMap, aoMap)
                                m.dispose(); // Dispose the material itself
                            }
                        });
                    }
                });

                // Remove all objects from the scene (ensuring all children are detached),
                // this is slightly redundant with traverse but safer for complex scenes.
                while(sceneRef.current.children.length > 0){ 
                    sceneRef.current.remove(sceneRef.current.children[0]);
                }
            }

            // 5. Dispose of the Renderer
            if (rendererRef.current) {
                rendererRef.current.dispose();
                
                // Remove the canvas element from the DOM.
                if (currentMount.contains(rendererRef.current.domElement)) {
                    currentMount.removeChild(rendererRef.current.domElement);
                }
            }

            // 6. Nullify all Refs to clean up the component state
            rendererRef.current = null;
            sceneRef.current = null;
            cameraRef.current = null;
            controlRef.current = null;
            meshRef.current = null;
            materialRef.current = null;
            
            // 7. Reset the guard flag, allowing the second Strict Mode cycle to proceed
            isSetupRef.current = false;
        };
    }, [fractalData]);

    return (
        <div ref={mountRef} style={{ width: '100vw', height: '100vh', overflow: 'hidden' }}>
        </div>
    );
}

export default Frxp3D;
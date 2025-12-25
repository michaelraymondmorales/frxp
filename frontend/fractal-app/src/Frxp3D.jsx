import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera } from '@react-three/drei';
import { useControls, folder, button } from 'leva';
import { SCENE_SETTINGS } from './configs/sceneConfig';
import MovingSun from './components/MovingSun';
import FractalMesh from './components/FractalMesh';

/**
 * Frxp3D - The 3D Scene Controller.
 * Acts as the bridge between the React application state and the R3F Canvas.
 * * @component
 * @param {Object} props
 * @param {Object} props.fractalData - The processed heightmap and iteration data.
 * @param {boolean} props.isGenerating - State flag to handle UI overlays during data updates.
 */
const Frxp3D = ({ fractalData }) => {
    const [settings, set] = useControls(() => ({
        // Folder 0: Global Reset
        'System Actions': folder({
            'Reset to Defaults': button(() => {
                set({
                    sunSpeed: SCENE_SETTINGS.sun.speed,
                    sunIntensity: SCENE_SETTINGS.sun.intensity,
                    sunRadius: SCENE_SETTINGS.sun.lightRadius,
                    ambientIntensity: SCENE_SETTINGS.ambient.intensity,
                    heightScale: SCENE_SETTINGS.mesh.heightScale,
                    colorScale: SCENE_SETTINGS.mesh.colorScale
                });
            })
        }, { collapsed: false}),

        // Folder 1: Sun Controls
        'Sun': folder({
            sunSpeed: { 
                value: SCENE_SETTINGS.sun.speed, 
                min: 0, max: 0.5, step: 0.01, label: 'Speed' 
            },
            sunRadius: {
                value: SCENE_SETTINGS.sun.lightRadius,
                min: 100, max: 1000, step: 25, label: 'Distance'
            },
            sunIntensity: { 
                value: SCENE_SETTINGS.sun.intensity, 
                min: 0, max: 5, step: 0.1, label: 'Brightness' 
            }
        }, { collapsed: false }),

        // Folder 2: Environment Controls
        'Environment': folder ({
            ambientIntensity: {
                value: SCENE_SETTINGS.ambient.intensity,
                min: 0, max: 5, step: 0.1, label: 'Brightness'
            }
        }, { collapsed: false }),

        // Folder 3: Terrain Controls
        'Terrain': folder({
            heightScale: { 
                value: SCENE_SETTINGS.mesh.heightScale, 
                min: 0, max: 500, step: 2, label: 'Height' 
            },
            colorScale: { 
                value: SCENE_SETTINGS.mesh.colorScale, 
                min: 0, max: 2, step: 0.1, label: 'Color' 
            }
        }, { collapsed: false })
    }));

    return (
        <div style={{ width: '100vw', height: '100vh' }}>
            <Canvas
                dpr= {[1, 1]}
                flat
                gl={{antialias: false,
                     alpha: false,
                     desynchronized: true,
                     powerPreference: "high-performance",
                     precision: "mediump",
                     toneMapping: 0, 
                     outputColorSpace: 'srgb' }}>
                
                {/* Camera Setup */}
                <PerspectiveCamera 
                    makeDefault 
                    position={[0, 700, 0]} 
                    fov={75} 
                    near={0.1} 
                    far={1650} 
                />

                {/* User Controls */}
                <OrbitControls 
                    dampingFactor={0.25} 
                    minDistance={100} 
                    maxDistance={1000} 
                />

                {/* Static Lighting */}
                <ambientLight  
                    intensity={settings.ambientIntensity}
                    color={SCENE_SETTINGS.ambient.defaultColor} 
                />
                
                {/* Dynamic Lighting */}
                <MovingSun 
                    speed={settings.sunSpeed} 
                    intensity={settings.sunIntensity}
                    radius={settings.sunRadius}
                    color={SCENE_SETTINGS.sun.defaultColor} 
                />

                {/* The Fractal */}
                <FractalMesh 
                    fractalData={fractalData}
                    heightScale={settings.heightScale}
                    colorScale={settings.colorScale}
                 />

            </Canvas>
        </div>
    );
};

export default Frxp3D;
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera } from '@react-three/drei';
import FractalMesh from './components/FractalMesh';
import MovingSun from './components/MovingSun';

/**
 * Frxp3D - The 3D Scene Controller.
 * Acts as the bridge between the React application state and the R3F Canvas.
 * * @component
 * @param {Object} props
 * @param {Object} props.fractalData - The processed heightmap and iteration data.
 * @param {boolean} props.isGenerating - State flag to handle UI overlays during data updates.
 */
const Frxp3D = ({ fractalData }) => {
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
                <ambientLight color={0x404040} intensity={3.0} />
                
                {/* Dynamic Lighting */}
                <MovingSun />

                {/* The Fractal */}
                <FractalMesh fractalData={fractalData} />

            </Canvas>
        </div>
    );
};

export default Frxp3D;
import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';


/**
 * MovingSun - Simulates a dynamic light source orbiting the terrain.
 * Uses a DirectionalLight to provide Gouraud shading (Lambert) across the fractal mesh.
 * * @component
 * @description
 * High-performance animation using the `useFrame` hook to bypass React's render cycle
 * for 60fps light movement.
 */
const MovingSun = ({speed, intensity, radius, color}) => {
    const lightRef = useRef();

    useFrame((state) => {
        if (!lightRef.current) return;

        // R3F provides the elapsed time automatically via the state clock
        const time = state.clock.elapsedTime;

        const normalizedAngle = (Math.sin(time * speed) + 1) * 0.5;
        const angle = normalizedAngle * Math.PI;

        // Update position directly on the ref
        lightRef.current.position.x = Math.cos(angle) * radius;
        lightRef.current.position.y = Math.sin(angle) * radius;
        lightRef.current.position.z = 0;
    });

    return (
        <directionalLight 
            ref={lightRef}
            color={color} 
            intensity={intensity} 
        />
    );
};

export default MovingSun;
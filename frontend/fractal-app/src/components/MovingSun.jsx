import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { SUN_SETTINGS } from '../configs/sceneConfig'

/**
 * MovingSun - Simulates a dynamic light source orbiting the terrain.
 * Uses a DirectionalLight to provide Gouraud shading (Lambert) across the fractal mesh.
 * * @component
 * @description
 * High-performance animation using the `useFrame` hook to bypass React's render cycle
 * for 60fps light movement.
 */
const MovingSun = () => {
    const lightRef = useRef();
    const sunSpeed = SUN_SETTINGS.speed;
    const sunRadius = SUN_SETTINGS.lightRadius;

    useFrame((state) => {
        if (!lightRef.current) return;

        // R3F provides the elapsed time automatically via the state clock
        const time = state.clock.elapsedTime;

        const normalizedAngle = (Math.sin(time * sunSpeed) + 1) * 0.5;
        const angle = normalizedAngle * Math.PI;

        // Update position directly on the ref
        lightRef.current.position.x = Math.cos(angle) * sunRadius;
        lightRef.current.position.y = Math.sin(angle) * sunRadius;
        lightRef.current.position.z = 0;
    });

    return (
        <directionalLight 
            ref={lightRef}
            color={SUN_SETTINGS.defaultColor} 
            intensity={SUN_SETTINGS.intensity} 
        />
    );
};

export default MovingSun;
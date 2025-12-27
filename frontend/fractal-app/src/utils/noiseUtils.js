// A self-contained implementation of Simplex Noise for generating procedural terrain.
// Based on the work of Stefan Gustavson.

// Pre-calculated gradient vectors used for calculating the dot product with the distance vector
// from the current point to the simplex corners. These 12 gradient vectors (each represented
// by three components, [x, y, z], where the third is often irrelevant in 2D) are selected 
// based on the permutation table (permMod12).
const grad3 = new Float32Array([1, 1, 0, -1, 1, 0, 1, -1, 0, -1, -1, 0, 1, 0, 1, -1, 0, 1, 1, 0, -1, -1, 0, -1, 0, 1, 1, 0, -1, 1, 0, 1, -1, 0, -1, -1]);

/**
 * Calculates the dot product of a 2D gradient vector (g) and a 2D distance vector (x, y).
 * In 2D Simplex Noise, the gradient vector is taken from grad3.
 * @param {Float32Array} g A subarray of grad3, representing a 2D gradient vector [gx, gy, gz].
 * @param {number} x The x-component of the distance vector.
 * @param {number} y The y-component of the distance vector.
 * @returns {number} The dot product (gx * x + gy * y).
 */
function dot(g, x, y) {
    return g[0] * x + g[1] * y;
}

/**
 * A class to generate 2D Simplex Noise, an algorithm for creating smooth, random noise
 * useful for procedural generation of textures, terrain, and movement.
 */
export class SimplexNoise {
    /**
     * Initializes the Simplex Noise generator with a permutation table based on a seed.
     * @param {number} [seed=Date.now()] The seed value to ensure reproducible noise patterns.
     */
    constructor(seed = Date.now()) {
        const p = new Uint8Array(256);
        const perm = new Uint8Array(512);
        const permMod12 = new Uint8Array(512);

        // Seeded RNG for a reproducible but unique permutation table.
        const rng = (function() {
            let s = seed % 2147483647;
            if (s <= 0) s += 2147483646;
            return function() {
                s = (s * 16807) % 2147483647;
                return (s - 1) / 2147483646;
            };
        })();

        // Create the permutation table.
        for (let i = 0; i < 256; i++) {
            p[i] = Math.floor(rng() * 256);
        }

        // Extend the permutation table.
        for (let i = 0; i < 512; i++) {
            perm[i] = p[i & 255];
            permMod12[i] = perm[i] % 12;
        }

        this.perm = perm;
        this.permMod12 = permMod12;
    }

    /**
     * Generates a 2D noise value for a given coordinate (xin, yin).
     * The output value is smoothly interpolated and ranges approximately from -1.0 to 1.0.
     * @param {number} xin The x-coordinate for the noise lookup.
     * @param {number} yin The y-coordinate for the noise lookup.
     * @returns {number} The noise value at (xin, yin), scaled by 70.0.
     */
    noise2D(xin, yin) {
        const F2 = 0.5 * (Math.sqrt(3.0) - 1.0);
        const G2 = (3.0 - Math.sqrt(3.0)) / 6.0;
        let n0, n1, n2;

        let s = (xin + yin) * F2;
        let i = Math.floor(xin + s);
        let j = Math.floor(yin + s);

        let t = (i + j) * G2;
        let X0 = i - t;
        let Y0 = j - t;
        let x0 = xin - X0;
        let y0 = yin - Y0;

        let i1, j1;
        if (x0 > y0) {
            i1 = 1;
            j1 = 0;
        } else {
            i1 = 0;
            j1 = 1;
        }

        let x1 = x0 - i1 + G2;
        let y1 = y0 - j1 + G2;
        let x2 = x0 - 1.0 + 2.0 * G2;
        let y2 = y0 - 1.0 + 2.0 * G2;

        i &= 255;
        j &= 255;
        let gi0 = this.permMod12[i + this.perm[j]] * 3;
        let gi1 = this.permMod12[i + i1 + this.perm[j + j1]] * 3;
        let gi2 = this.permMod12[i + 1 + this.perm[j + 1]] * 3;

        let t0 = 0.5 - x0 * x0 - y0 * y0;
        if (t0 < 0) {
            n0 = 0.0;
        } else {
            t0 *= t0;
            n0 = t0 * t0 * dot(grad3.subarray(gi0), x0, y0);
        }

        let t1 = 0.5 - x1 * x1 - y1 * y1;
        if (t1 < 0) {
            n1 = 0.0;
        } else {
            t1 *= t1;
            n1 = t1 * t1 * dot(grad3.subarray(gi1), x1, y1);
        }

        let t2 = 0.5 - x2 * x2 - y2 * y2;
        if (t2 < 0) {
            n2 = 0.0;
        } else {
            t2 *= t2;
            n2 = t2 * t2 * dot(grad3.subarray(gi2), x2, y2);
        }

        return 70.0 * (n0 + n1 + n2);
    }
}

/**
 * Generates a fractal noise value using multiple octaves of Simplex noise.
 * @param {Object} noiseGen The SimplexNoise instance.
 * @param {number} x The x coordinate.
 * @param {number} y The y coordinate.
 * @param {Object} params The parameters for noise generation.
 * @returns {number} The combined noise value.
 */
function getNoiseValue(noiseGen, x, y, { scale, octaves, persistence, lacunarity }) {
    let noiseValue = 0;
    let amplitude = 1.0;
    let frequency = 1.0;
    for (let i = 0; i < octaves; i++) {
        noiseValue += noiseGen.noise2D(x * scale * frequency, y * scale * frequency) * amplitude;
        amplitude *= persistence;
        frequency *= lacunarity;
    }
    return noiseValue;
}

/**
 * Generates a standalone noise map by layering base and detail simplex noise octaves.
 * Optimized for GPU upload via a flat Float32Array.
 * * @param {number} width - Map width (resolution).
 * @param {number} height - Map height (resolution). 
 * @param {Object} [params={}] - Optional noise configuration.
 * @param {number} [params.baseNoiseScale=0.0005] - Frequency scale of the primary noise layer.
 * @param {number} [params.baseNoiseOctaves=4] - Detail layers for primary noise.
 * @param {number} [params.baseNoisePersistence=0.5] - Amplitude decay per octave (base).
 * @param {number} [params.baseNoiseLacunarity=2.0] - Frequency growth per octave (base).
 * @param {number} [params.detailNoiseScale=0.005] - Frequency scale of the secondary detail layer.
 * @param {number} [params.detailNoiseOctaves=8] - Detail layers for secondary noise.
 * @param {number} [params.detailNoisePersistence=0.6] - Amplitude decay per octave (detail).
 * @param {number} [params.detailNoiseLacunarity=2.0] - Frequency growth per octave (detail).
 * @returns {Float32Array} A flat array of combined noise values.
 */
export const generateNoiseMap = (width, height, {
    baseNoiseScale = 0.0005,
    baseNoiseOctaves = 4,
    baseNoisePersistence = 0.5,
    baseNoiseLacunarity = 2.0,
    detailNoiseScale = 0.005,
    detailNoiseOctaves = 8,
    detailNoisePersistence = 0.6,
    detailNoiseLacunarity = 2.0,
} = {}) => {
    const size = width * height;
    const noiseData = new Float32Array(size);
    const baseNoiseGen = new SimplexNoise();
    const detailNoiseGen = new SimplexNoise(Date.now() + 1); // Use a different seed for a unique pattern.

    let x = 0;
    let y = 0;

    for (let i = 0; i < size; i++) {
        // Generate the base and detail noise values.
        const baseNoiseValue = getNoiseValue(baseNoiseGen, x, y, {
            scale: baseNoiseScale,
            octaves: baseNoiseOctaves,
            persistence: baseNoisePersistence,
            lacunarity: baseNoiseLacunarity
        });

        const detailNoiseValue = getNoiseValue(detailNoiseGen, x, y, {
            scale: detailNoiseScale,
            octaves: detailNoiseOctaves,
            persistence: detailNoisePersistence,
            lacunarity: detailNoiseLacunarity
        });

        // Sum the raw values, weighting and masking are deferred to the shader.
        noiseData[i] = baseNoiseValue + detailNoiseValue;
        
        // Manual increment is faster than Math.floor/modulo in long loops.
        x++;
        if (x >= width) {
            x = 0;
            y++;
        }
    }

    return noiseData;
};
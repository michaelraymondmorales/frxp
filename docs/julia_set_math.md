# Assume we are inside the Numba-jitted loop, processing a single pixel (r, col)
# zr and zi are the current real and imaginary parts of Z for this pixel.

# 1. Calculate the magnitude squared of the current complex number Z = zr + zi*j
#    magnitude_sq = zr*zr + zi*zi
#    (This line is usually calculated earlier to check for bailout, but its value is used here)

# 2. Convert the current complex number Z (zr + zi*j) from Cartesian to Polar Coordinates:
#    A complex number Z can be represented as Z = r * (cos(theta) + i * sin(theta))
#    where 'r' is the magnitude (distance from origin) and 'theta' is the angle (argument).

r_z = np.sqrt(magnitude_sq)
#    'r_z' (radius_z) is the magnitude of the current complex number Z.
#    It's the square root of (real_part^2 + imaginary_part^2).

theta_z = np.arctan2(zi, zr)
#    'theta_z' (angle_z) is the argument (angle) of the current complex number Z.
#    np.arctan2(y, x) is preferred over np.arctan(y/x) because it correctly handles
#    all four quadrants and the cases where x is zero, giving an angle in radians
#    from -pi to +pi.

# 3. Perform the Exponentiation (Z^power) using Polar Coordinates:
#    This is where the magic happens, based on De Moivre's Theorem for complex numbers:
#    If Z = r * (cos(theta) + i * sin(theta)), then Z^power = (r^power) * (cos(power * theta) + i * sin(power * theta))

new_r = r_z**power
#    'new_r' is the magnitude of the *next* complex number (Z^power).
#    You simply raise the current magnitude (r_z) to the desired 'power'.

new_theta = power * theta_z
#    'new_theta' is the angle of the *next* complex number (Z^power).
#    You simply multiply the current angle (theta_z) by the 'power'.

# 4. Convert the result (Z^power) back from Polar to Cartesian Coordinates:
#    Now we have the magnitude (new_r) and angle (new_theta) of Z^power.
#    We convert it back to its real and imaginary parts.

#    The real part is new_r * cos(new_theta)
#    The imaginary part is new_r * sin(new_theta)

# 5. Add the Julia Set Constant 'c' (c_real + c_imag*j):
#    The Julia set iteration formula is Z_new = Z^power + c.
#    We've just calculated Z^power (as its real and imaginary components).
#    Now we add the constant 'c' to get the next Z value.

next_zr = new_r * np.cos(new_theta) + c_real
#    'next_zr' is the real part of the *next* complex number in the sequence.

next_zi = new_r * np.sin(new_theta) + c_imag
#    'next_zi' is the imaginary part of the *next* complex number in the sequence.

# 6. Update the Z_real and Z_imag arrays for the next iteration:
Z_real[r, col] = next_zr
Z_imag[r, col] = next_zi
#    These lines store the newly calculated real and imaginary parts back into
#    the arrays, so they can be used as the 'current Z' in the next iteration (i+1).

Why this approach is used for Z^power:

    Mathematical Simplicity: Raising a complex number to a power n in Cartesian form (a + bi)^n quickly becomes very complicated and involves binomial expansion for n > 2. In polar form, it's just r^n and n*theta.

    Numerical Stability: For higher powers, direct Cartesian calculation can sometimes suffer from numerical instability or overflow more easily than the polar method, especially with floating-point numbers.

    Generality: This method works perfectly for any integer power (or even non-integer powers if you extend the math, though Julia sets typically use integer powers).

    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    np.arctan(x): The Single-Argument Inverse Tangent

    What it does: np.arctan(x) calculates the inverse tangent of a single ratio x. Mathematically, this is equivalent to arctan(xy​).

    Input: It takes one argument, which is assumed to be the ratio of the y-component to the x-component.

    Output Range: The output of np.arctan(x) is restricted to the range of (−2π​,2π​) radians (or −90∘ to 90∘). This corresponds to the first and fourth quadrants only.

    The Problem (Ambiguity):

        If you have a point (x,y), say (1,1), its angle is 45∘ (π/4). np.arctan(1/1) gives 45∘.

        Now consider a point (−1,−1). Its true angle is 225∘ (5π/4 or −3π/4). However, np.arctan((-1)/(-1)) simplifies to np.arctan(1), which still gives 45∘. You've lost the information about which quadrant the original point was in because the signs of x and y were combined into a single ratio.

        Division by Zero: It will raise an error or return NaN (Not a Number) if the x-component (the denominator x) is zero, which happens for points directly on the positive or negative imaginary axis.

Think of it like: You're only telling the function the slope of a line, but not which direction along that line you're going from the origin.

np.arctan2(y, x): The Two-Argument Inverse Tangent

    What it does: np.arctan2(y, x) calculates the inverse tangent using two separate arguments: the y-coordinate (numerator) and the x-coordinate (denominator). It uses the signs of both y and x to correctly determine the quadrant of the angle.

    Input: It takes two arguments: y (the imaginary part or vertical component) and x (the real part or horizontal component).

    Output Range: The output of np.arctan2(y, x) covers the full range of (−π,π] radians (or −180∘ to 180∘). This allows it to correctly represent angles in all four quadrants.

    The Solution (No Ambiguity):

        For (1,1), np.arctan2(1, 1) gives 45∘.

        For (−1,−1), np.arctan2(-1, -1) correctly gives −135∘ (or −3π/4 radians), which is the angle in the third quadrant.

        Handles Zero Denominator: It correctly handles cases where x is zero:

            np.arctan2(1, 0) gives 90∘ (π/2).

            np.arctan2(-1, 0) gives −90∘ (−π/2).

            np.arctan2(0, 0) typically returns 0 (or NaN depending on strictness, but NumPy handles it gracefully).

Think of it like: You're telling the function the exact coordinates of a point, so it knows precisely where it is relative to the origin and can give you the correct angle.

Why np.arctan2 is Recommended (Specifically for Fractals/Complex Numbers):

    Correct Quadrant Information (Crucial for Phase):

        In complex numbers, the angle (or phase) is fundamental. A complex number Z=x+yi corresponds to a point (x,y) in the complex plane. Its angle can be in any of the four quadrants.

        For operations like ZP=rP∗(cos(Pθ)+i∗sin(Pθ)) (De Moivre's Theorem), having the correct θ (angle) is absolutely essential. If θ is off by 180∘ because arctan couldn't distinguish between (1,1) and (−1,−1), your fractal calculations would be completely wrong.

        For phase coloring, you need the true angle to map it consistently to a color cycle.

    Robustness (No Division by Zero):

        Your fractal calculation involves points across the entire complex plane, including those where the real part (Z_real) might momentarily be zero. np.arctan2 handles these cases gracefully, preventing errors that np.arctan would cause.

    Full Angle Range:

        The (−π,π] range is ideal for representing angles in a continuous way around the origin, which is exactly what's needed for the behavior of complex numbers in fractal iterations.

In summary, while np.arctan is useful for calculating angles from known slopes, np.arctan2 is the gold standard for finding the angle of a point (x,y) or a complex number x+yi because it correctly handles all quadrants and edge cases, providing the true and unambiguous angle. For fractal generation, its use is non-negotiable for mathematical correctness.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We first calculate the magnitude and angle of the current complex number Zn​:

    rz​=∣Zn​∣=zreal2​+zimag2​​

    θz​=arg(Zn​)=arctan2(zimag​,zreal​)

Next, we use these polar coordinates to compute ZnP−1​:

    rpower​=rzP−1​

    θpower​=(P−1)⋅θz​

    zpower_real​=rpower​⋅cos(θpower​)

    zpower_imag​=rpower​⋅sin(θpower​)

Finally, we use these results to update the derivative:

    dCdZn+1​​real​=P⋅(zpower_real​⋅dzreal​−zpower_imag​⋅dzimag​)+1

    dCdZn+1​​imag​=P⋅(zpower_real​⋅dzimag​+zpower_imag​⋅dzreal​)
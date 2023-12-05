#!/usr/bin/env python3

# Command line program to create svg apollonian circles

# Copyright (c) 2014 Ludger Sandig
# This file is part of apollon.

# Apollon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Apollon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Apollon.  If not, see <http://www.gnu.org/licenses/>.

import math
from apollon import ApollonianGasket

def ag_to_svg(circles, colors, tresh=0.00005):
    """
    Convert a list of circles to svg, optionally color them.
    @param circles: A list of L{Circle}s
    @param colors: A L{ColorMap} object
    @param tresh: Only circles with a radius greater than the product of tresh and maximal radius are saved
    """
    svg = []
    
    tresh = .000005
    print ('>>', tresh)
    
    # Find the biggest circle, which hopefully is the enclosing one
    # and has a negative radius because of this. Note that this does
    # not have to be the case if we picked an unlucky set of radii at
    # the start. If that was the case, we're screwed now.
    
    big = min(circles, key=lambda c: c.r.real)

    # Move biggest circle to front so it gets drawn first
    circles.remove(big)
    circles.insert(0, big)

    if big.r.real < 0:
        # Bounding box from biggest circle, lower left corner and two
        # times the radius as width
        corner = big.m - ( abs(big.r) + abs(big.r) * 1j )
        vbwidth = abs(big.r)*2
        width = 500 # Hardcoded!

        # Line width independent of circle size
        lw = (vbwidth/width)

        svg.append('<svg xmlns="http://www.w3.org/2000/svg" width="%f" height="%f" viewBox="%f %f %f %f">\n' % (width, width, corner.real, corner.imag, vbwidth, vbwidth))

        # Keep stroke width relative
        svg.append('<g stroke-width="%f">\n' % lw)

        # Iterate through circle list, circles with radius<radmin
        # will not be saved because they are too small for printing.
        radmin = tresh * abs(big.r)
        print(radmin)

        for c in circles:
            if abs(c.r) > radmin:
                fill = colors.color_for(abs(c.r))
                svg.append(( '<circle cx="%f" cy="%f" r="%f" fill="%s" stroke="black"/>\n' % (c.m.real, c.m.imag, abs(c.r), fill)))

        svg.append('</g>\n')
        svg.append('</svg>\n')

    return ''.join(svg)

def impossible_combination(c1, c2, c3):
    # If any curvatures x, y, z satisfy the equation
    # x = 2*sqrt(y*z) + y + z
    # then no fourth enclosing circle can be genereated, because it
    # would be a line.
    # We need to see for c1, c2, c3 if they could be "x".
    
    impossible = False
    
    sets = [(c1,c2,c3), (c2,c3,c1), (c3,c1,c2)]
    
    for (x, y, z) in sets:
        if x == 2*math.sqrt(y*z) + y + z:
            impossible = True
    
    return impossible

def main(c1=3.,c2=2.,c3=2.,depth=5):
    # Sanity checks
    for c in [c1, c2,c3]:
        if c == 0:
            print("Error: curvature or radius can't be 0")
            exit(1)
    if impossible_combination(c1, c2, c3):
        print("Error: no apollonian gasket possible for these curvatures")
        exit(1)

    ag = ApollonianGasket(c1, c2, c3)
 
    ag.generate(depth)

    # Get smallest and biggest radius
    smallest = abs(min(ag.genCircles, key=lambda c: abs(c.r.real)).r.real)
    biggest = abs(max(ag.genCircles, key=lambda c: abs(c.r.real)).r.real)

    return ag.genCircles
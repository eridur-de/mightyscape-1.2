#!/usr/bin/env python3
'''
Copyright (C) 2013 Matthew Dockrey  (gfish @ cyphertext.net)

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

Based on gears.py by Aaron Spike and Tavmjong Bah
'''

import inkex
from math import *
from lxml import etree

def rotate(p, t):
    return (p[0] * cos(t) - p[1] * sin(t), p[0] * sin(t) + p[1] * cos(t))

def SVG_move(p, t):
    pp = rotate(p, t)
    return 'M ' + str(pp[0]) + ',' + str(pp[1]) + '\n'

def SVG_line(p, t):
    pp = rotate(p, t)
    return 'L ' + str(pp[0]) + ',' + str(pp[1]) + '\n'

def SVG_circle(p, r, sweep, t):
    pp = rotate(p, t)
    return 'A ' + str(r) + ',' + str(r) + ' 0 0,' + str(sweep) + ' ' + str(pp[0]) + ',' + str(pp[1]) + '\n'

def SVG_curve(p, c1, c2, t):
    pp = rotate(p, t)
    c1p = rotate(c1, t)
    c2p = rotate(c2, t)
    return 'C ' + str(pp[0]) + ',' + str(pp[1]) + ' ' + str(c1p[0]) + ',' + str(c1p[1]) + ' ' + str(c2p[0]) + ',' + str(c2p[1]) + '\n'

def SVG_curve2(p1, c11, c12, p2, c21, c22, t):
    p1p = rotate(p1, t)
    c11p = rotate(c11, t)
    c12p = rotate(c12, t)
    p2p = rotate(p2, t)
    c21p = rotate(c21, t)
    c22p = rotate(c22, t)
    return 'C ' + str(p1p[0]) + ',' + str(p1p[1]) + ' ' + str(c11p[0]) + ',' + str(c11p[1]) + ' ' + str(c12p[0]) + ',' + str(c12p[1]) + ' ' + str(p2p[0]) + ',' + str(p2p[1]) + ' ' + str(c21p[0]) + ',' + str(c21p[1]) + ' ' + str(c22p[0]) + ',' + str(c22p[1]) + '\n'

def SVG_close():
    return 'Z\n'

class Sprocket(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("-t", "--teeth", type=int, default=24, help="Number of teeth")
        pars.add_argument("-s", "--size", default="ANSI #40", help="Chain size (common values ANSI #35, ANSI #40, ANSI #60)")

    def get_pitch(self, size):
        return self.svg.unittouu({
            'ANSI #25': '6.35mm',
            'ANSI #35': '9.53mm',
            'ANSI #40': '12.70mm',
            'ANSI #41': '12.70mm',
            'ANSI #50': '15.88mm',
            'ANSI #60': '19.05mm',
            'ANSI #80': '25.40mm',
            'ANSI #100': '31.75mm',
            'ANSI #120': '38.10mm',
            'ANSI #140': '44.45mm',
            'ANSI #160': '50.80mm',
            'ANSI #180': '57.15mm',
            'ANSI #200': '63.50mm',
            'ANSI #240': '76.20mm'
            }[size])

    def get_roller_diameter(self, size):
        return self.svg.unittouu({
            'ANSI #25': '3.30mm',
            'ANSI #35': '5.08mm',
            'ANSI #40': '7.77mm',
            'ANSI #41': '7.92mm',
            'ANSI #50': '10.16mm',
            'ANSI #60': '11.91mm',
            'ANSI #80': '15.88mm',
            'ANSI #100': '19.05mm',
            'ANSI #120': '22.23mm',
            'ANSI #140': '25.40mm',
            'ANSI #160': '28.58mm',
            'ANSI #180': '37.08mm',
            'ANSI #200': '39.67mm',
            'ANSI #240': '47.63mm'
            }[size])

    def invertX(self, p):
        return (-p[0], p[1])

    def effect(self):
        size = self.options.size

        P = self.get_pitch(size)
        N = self.options.teeth
        PD = P / sin(pi / N)
        PR = PD / 2

        # Equations taken from
        # http://www.gearseds.com/files/design_draw_sprocket_5.pdf
        # Also referenced:
        # http://en.wikipedia.org/wiki/Roller_chain (of course)
        # and
        # Chains for Power Transmission and Material Handling:
        # Design and Applications Handbook
        # American Chain Association, 1982

        Dr = self.get_roller_diameter(size)
        Ds = 1.0005 * Dr + self.svg.unittouu('0.003in')
        R = Ds / 2 # seating curve radius
        A = radians(35 + 60 / N)
        B = radians(18 - 56 / N)
        ac = 0.8 * Dr
        M = ac * cos(A)
        T = ac * sin(A)
        E = 1.3025 * Dr + self.svg.unittouu('0.0015in') # transition radius
        ab = 1.4 * Dr
        W = ab * cos(pi / N)
        V = ab * sin(pi / N)
        F = Dr * (0.8 * cos(radians(18 - 56 / N)) + 1.4 * cos(radians(17 - 64 / N)) - 1.3025) - self.svg.unittouu('0.0015in') # topping curve radius
        
        svg = ""

        t_inc = 2.0 * pi / float(N)
        thetas = [(x * t_inc) for x in range(N)]

        for theta in thetas:
            # Seating curve center
            seatC = (0, -PR)

            # Transitional curve center
            c = (M, -PR - T)

            # Calculate line cx, angle A from x axis
            # Y = mX + b
            cx_m = -tan(A) # Negative because we're in -Y space
            cx_b = c[1] - cx_m * c[0]

            # Calculate intersection of cx with circle S to get point x
            # http://math.stackexchange.com/questions/228841/how-do-i-calculate-the-intersections-of-a-straight-line-and-a-circle
            qA = cx_m * cx_m + 1
            qB = 2 * (cx_m * cx_b - cx_m * seatC[1] - seatC[0])
            qC = seatC[1] * seatC[1] - R * R + seatC[0] * seatC[0] - 2 * cx_b * seatC[1] + cx_b * cx_b
            cx_X = (-qB - sqrt(qB * qB - 4 * qA * qC)) / (2 * qA)

            # Seating curve/Transitional curve junction
            x = (cx_X, cx_m * cx_X + cx_b)

            # Calculate line cy, angle B past cx
            cy_m = -tan(A - B)
            cy_b = c[1] - cy_m * c[0]

            # Calculate point y (E along cy from c)
            # http://www.physicsforums.com/showthread.php?t=419561
            yX = c[0] - E / sqrt(1 + cy_m * cy_m)

            # Transitional curve/Tangent line junction
            y = (yX, cy_m * yX + cy_b)

            # Solve for circle T with radius E which passes through x and y
            # http://mathforum.org/library/drmath/view/53027.html
            # http://stackoverflow.com/questions/12264841/determine-circle-center-based-on-two-points-radius-known-with-solve-optim
            z = ((x[0] + y[0]) / 2, (x[1] + y[1]) / 2)
            x_diff = y[0] - x[0]
            y_diff = y[1] - x[1]
            q = sqrt(x_diff * x_diff + y_diff * y_diff)
            tX = z[0] + sqrt(E * E - (q / 2) * (q / 2)) * (x[1] - y[1]) / q
            tY = z[1] + sqrt(E * E - (q / 2) * (q / 2)) * (y[0] - x[0]) / q

            # Transitional curve center
            tranC = (tX, tY)

            # Tangent line -- tangent to transitional curve at point y
            tanl_m = -(tranC[0] - y[0]) / (tranC[1] - y[1])
            tanl_b = -y[0] * tanl_m + y[1]
            t_off = (y[0] - 10, tanl_m * (y[0] - 10) + tanl_b)
 
            # Topping curve center
            topC = (-W, -PR + V)

            # Adjust F to force topping curve tangent to tangent line
            F = abs(topC[1] - tanl_m * topC[0] - tanl_b) / sqrt(tanl_m * tanl_m + 1) * 1.0001 # Final fudge needed to overcome numerical instability

            # Find intersection point between topping curve and tangent line
            ttA = tanl_m * tanl_m + 1
            ttB = 2 * (tanl_m * tanl_b - tanl_m * topC[1] - topC[0])
            ttC = topC[1] * topC[1] - F * F + topC[0] * topC[0] - 2 * tanl_b * topC[1] + tanl_b * tanl_b
            tanl_X = (-ttB - sqrt(ttB * ttB - 4 * ttA * ttC)) / (2 * ttA)

            # Tagent line/Topping curve junction
            tanl = (tanl_X, tanl_m * tanl_X + tanl_b)

            # Calculate tip line, angle t_inc/2 from Y axis
            tip_m = -tan(pi / 2 + t_inc / 2) # Negative because we're in -Y space
            tip_b = 0

            # Calculate intersection of tip line with topping curve
            tA = tip_m * tip_m + 1
            tB = 2 * (tip_m * tip_b - tip_m * topC[1] - topC[0])
            tC = topC[1] * topC[1] - F * F + topC[0] * topC[0] - 2 * tip_b * topC[1] + tip_b * tip_b
            tip_X = (-tB - sqrt(tB * tB - 4 * tA * tC)) / (2 * tA)

            # Topping curve top
            tip = (tip_X, tip_m * tip_X + tip_b)

            # Set initial location if needed
            if (theta == 0):
                svg += SVG_move(tip, theta)

            svg += SVG_circle(tanl, F, 1, theta) # Topping curve left
            svg += SVG_line(y, theta) # Tangent line left
            svg += SVG_circle(x, E, 0, theta) # Transitional curve left
            svg += SVG_circle(self.invertX(x), R, 0, theta) # Seating curve
            svg += SVG_circle(self.invertX(y), E, 0, theta) # Transitionl curve right
            svg += SVG_line(self.invertX(tanl), theta) # Tangent line right
            svg += SVG_circle(self.invertX(tip), F, 1, theta) # Topping curve right

        svg += SVG_close()
            
        # Insert as a new element
        sprocket_style = { 'stroke': '#000000',
                           'stroke-width': self.svg.unittouu(str(0.1) + "mm"),
                           'fill': 'none'
                           }
        g_attribs = {inkex.addNS('label','inkscape'): 'Sprocket ' + size + "-" + str(N),
                     'transform': 'translate(' + str(self.svg.namedview.center[0]) + ',' + str(self.svg.namedview.center[1]) + ')',
                     'style' : str(inkex.Style(sprocket_style)),
                     'd' : svg  }
        g = etree.SubElement(self.svg.get_current_layer(), inkex.addNS('path','svg'), g_attribs)

if __name__ == '__main__':
    Sprocket().run()
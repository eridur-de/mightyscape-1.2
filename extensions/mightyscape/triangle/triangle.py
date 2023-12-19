#! /usr/bin/python3
#
# Copyright (C) 2007 John Beard john.j.beard@gmail.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
This extension allows you to draw a triangle given certain information
 about side length or angles.

Measurements of the triangle

         C(x_c,y_c)
        /`__
       / a_c``--__
      /           ``--__ s_a
 s_b /                  ``--__
    /a_a                    a_b`--__
   /--------------------------------``B(x_b, y_b)
  A(x_a,y_a)         s_b
"""

import sys
from math import acos, asin, cos, pi, sin, sqrt

import inkex

X, Y = range(2)

def draw_SVG_tri(point1, point2, point3, offset, width, name, parent):
    style = {'stroke': '#000000', 'stroke-width': str(width), 'fill': 'none'}
    elem = parent.add(inkex.PathElement())
    elem.update(**{
        'style': style,
        'inkscape:label': name,
         'd': 'M ' + str(point1[X] + offset[X]) + ',' + str(point1[Y] + offset[Y]) +
              ' L ' + str(point2[X] + offset[X]) + ',' + str(point2[Y] + offset[Y]) +
              ' L ' + str(point3[X] + offset[X]) + ',' + str(point3[Y] + offset[Y]) +
              ' L ' + str(point1[X] + offset[X]) + ',' + str(point1[Y] + offset[Y]) + ' z'})
    return elem


def angle_from_3_sides(a, b, c):  # return the angle opposite side c
    cosx = (a * a + b * b - c * c) / (2 * a * b)  # use the cosine rule
    return acos(cosx)


def third_side_from_enclosed_angle(s_a, s_b, a_c):  # return the side opposite a_c
    c_squared = s_a * s_a + s_b * s_b - 2 * s_a * s_b * cos(a_c)
    if c_squared > 0:
        return sqrt(c_squared)
    else:
        return 0  # means we have an invalid or degenerate triangle (zero is caught at the drawing stage)


def pt_on_circ(radius, angle):  # return the x,y coordinate of the polar coordinate
    x = radius * cos(angle)
    y = radius * sin(angle)
    return [x, y]


def v_add(point1, point2):  # add an offset to coordinates
    return [point1[X] + point2[X], point1[Y] + point2[Y]]


def is_valid_tri_from_sides(a, b, c):  # check whether triangle with sides a,b,c is valid
    return (a + b) > c and (a + c) > b and (b + c) > a and a > 0 and b > 0 and c > 0  # two sides must always be greater than the third
    # no zero-length sides, no degenerate case


def draw_tri_from_3_sides(s_a, s_b, s_c, offset, width, parent):  # draw a triangle from three sides (with a given offset
    if is_valid_tri_from_sides(s_a, s_b, s_c):
        a_b = angle_from_3_sides(s_a, s_c, s_b)

        a = (0, 0)  # a is the origin
        b = v_add(a, (s_c, 0))  # point B is horizontal from the origin
        c = v_add(b, pt_on_circ(s_a, pi - a_b))  # get point c
        c[1] = -c[1]

        offx = max(b[0], c[0]) / 2  # b or c could be the furthest right
        offy = c[1] / 2  # c is the highest point
        offset = (offset[0] - offx, offset[1] - offy)  # add the centre of the triangle to the offset

        draw_SVG_tri(a, b, c, offset, width, 'Triangle', parent)
    else:
        inkex.errormsg('Invalid Triangle Specifications.')


class Triangle(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--unit", default="mm", help="Units")
        pars.add_argument("--s_a", type=float, default=100.0, help="Side Length a")
        pars.add_argument("--s_b", type=float, default=100.0, help="Side Length b")
        pars.add_argument("--s_c", type=float, default=100.0, help="Side Length c")
        pars.add_argument("--a_a", type=float, default=60.0, help="Angle a")
        pars.add_argument("--a_b", type=float, default=30.0, help="Angle b")
        pars.add_argument("--a_c", type=float, default=90.0, help="Angle c")
        pars.add_argument("--mode", default='3_sides', help="Side Length c")

    def effect(self):
        tri = self.svg.get_current_layer()
        offset = self.svg.namedview.center
        self.options.s_a = self.svg.unittouu(str(self.options.s_a) + self.options.unit)
        self.options.s_b = self.svg.unittouu(str(self.options.s_b) + self.options.unit)
        self.options.s_c = self.svg.unittouu(str(self.options.s_c) + self.options.unit)
        stroke_width = self.svg.unittouu('1px')

        if self.options.mode == '3_sides':
            s_a = self.options.s_a
            s_b = self.options.s_b
            s_c = self.options.s_c
            draw_tri_from_3_sides(s_a, s_b, s_c, offset, stroke_width, tri)

        elif self.options.mode == 's_ab_a_c':
            s_a = self.options.s_a
            s_b = self.options.s_b
            a_c = self.options.a_c * pi / 180  # in rad

            s_c = third_side_from_enclosed_angle(s_a, s_b, a_c)
            draw_tri_from_3_sides(s_a, s_b, s_c, offset, stroke_width, tri)

        elif self.options.mode == 's_ab_a_a':
            s_a = self.options.s_a
            s_b = self.options.s_b
            a_a = self.options.a_a * pi / 180  # in rad

            if (a_a < pi / 2.0) and (s_a < s_b) and (s_a > s_b * sin(a_a)):  # this is an ambiguous case
                ambiguous = True  # we will give both answers
            else:
                ambiguous = False

            sin_a_b = s_b * sin(a_a) / s_a

            if (sin_a_b <= 1) and (sin_a_b >= -1):  # check the solution is possible
                a_b = asin(sin_a_b)  # acute solution
                a_c = pi - a_a - a_b
                error = False
            else:
                sys.stderr.write('Error:Invalid Triangle Specifications.\n')  # signal an error
                error = True

            if not error and (a_b < pi) and (a_c < pi):  # check that the solution is valid, if so draw acute solution
                s_c = third_side_from_enclosed_angle(s_a, s_b, a_c)
                draw_tri_from_3_sides(s_a, s_b, s_c, offset, stroke_width, tri)

            if not error and ((a_b > pi) or (a_c > pi) or ambiguous):  # we want the obtuse solution
                a_b = pi - a_b
                a_c = pi - a_a - a_b
                s_c = third_side_from_enclosed_angle(s_a, s_b, a_c)
                draw_tri_from_3_sides(s_a, s_b, s_c, offset, stroke_width, tri)

        elif self.options.mode == 's_a_a_ab':
            s_a = self.options.s_a
            a_a = self.options.a_a * pi / 180  # in rad
            a_b = self.options.a_b * pi / 180  # in rad

            a_c = pi - a_a - a_b
            s_b = s_a * sin(a_b) / sin(a_a)
            s_c = s_a * sin(a_c) / sin(a_a)

            draw_tri_from_3_sides(s_a, s_b, s_c, offset, stroke_width, tri)

        elif self.options.mode == 's_c_a_ab':
            s_c = self.options.s_c
            a_a = self.options.a_a * pi / 180  # in rad
            a_b = self.options.a_b * pi / 180  # in rad

            a_c = pi - a_a - a_b
            s_a = s_c * sin(a_a) / sin(a_c)
            s_b = s_c * sin(a_b) / sin(a_c)

            draw_tri_from_3_sides(s_a, s_b, s_c, offset, stroke_width, tri)


if __name__ == '__main__':
    Triangle().run()

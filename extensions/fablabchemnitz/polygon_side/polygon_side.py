#!/usr/bin/env python3
#
# Copyright (C) [2021] [Matt Cottam], [mpcottam@raincloud.co.uk]
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
#
# Create a Polygon given a number of sides and side length.
#

import math
import inkex
from inkex import PathElement
from inkex import units
import re

# Formula to find the circumradius ( centre to apex ) required to create
# for a given number of sectors to return desired side length

def radius_from_side_and_sectors(side_length, sectors, found_units, unit_choice):
    conversions = {
        'in': 96.0,
        'pt': 1.3333333333333333,
        'px': 1.0,
        'mm': 3.779527559055118,
        'cm': 37.79527559055118,
        'm': 3779.527559055118,
        'km': 3779527.559055118,
        'Q': 0.94488188976378,
        'pc': 16.0,
        'yd': 3456.0,
        'ft': 1152.0,
        '': 1.0,  # Default px
    }

    # Try to convert from detected units into pixels

    if unit_choice == 2:
        try:
            pixel_conversion_factor = conversions[found_units]
        except:
            pixel_conversion_factor = 1

    else:
        pixel_conversion_factor = 1

    radius = (side_length / (2 * (math.sin(math.pi / sectors)))) / pixel_conversion_factor

    path = svg_poly(0, 0, radius, sectors)

    return path


# All points of a regular polygon lie on a circle
# Calculate points on circle for given number of sides

def svg_poly(cx, cy, radius, sectors):
    x_start = cx
    y_start = cy - radius

    angle = 0

    y_start = cy / 2 + (radius * (math.sin(angle)))
    x_start = cx / 2 + (radius * (math.cos(angle)))

    path = f'M {x_start} {y_start}'

    for sector in range(1, sectors + 1):
        angle = (sector * math.pi) / (sectors / 2)

        y = cy / 2 + (radius * (math.sin(angle)))
        x = cx / 2 + (radius * (math.cos(angle)))

        path = path + f' L {x} {y} '

        x_start = x
        y_start = y

    return path + ' z'


class makepoly(inkex.GenerateExtension):

    def add_arguments(self, pars):
        pars.add_argument("--number_of_sides", type=int, dest="sectors", default=6)
        pars.add_argument("--length_of_sides", type=float, dest="side_length", default=25)
        pars.add_argument("--unit_choice", type=int, dest="unit_choice", default=25)

    container_label = 'Side Poly'

    def generate(self):
        found_units = self.svg.unit

        path = radius_from_side_and_sectors(self.options.side_length, self.options.sectors, found_units,
                                            self.options.unit_choice)

        style = {'stroke': '#000000', 'fill': 'none', 'stroke-width': str(self.svg.unittouu('1px'))}
        poly_path = PathElement()
        poly_path.style = style
        poly_path.path = path

        yield poly_path


if __name__ == '__main__':
    makepoly().run()

#! /usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
from math import pi, sin, cos

import inkex

from Path import Path
from Pattern import Pattern


# Select name of class, inherits from Pattern
# TODO:
# 1) Implement __init__ method to get all custom options and then call Pattern's __init__
# 2) Implement generate_path_tree to define all of the desired strokes


class SupportRing(Pattern):

    def __init__(self):
        """ Constructor
        """
        Pattern.__init__(self)  # Must be called in order to parse common options

        # save all custom parameters defined on .inx file
        self.add_argument('--sides', type=self.int, default=3)
        self.add_argument('--radius_external', type=self.float, default=10.0)
        self.add_argument('--inverted', type=self.bool, default=False)
        self.add_argument('--single_stroke', type=self.bool, default=True)
        self.add_argument('--radius_ratio', type=self.float, default=0.5)
        self.add_argument('--radius_type', type=self.str, default='polygonal')
        self.add_argument('--radius_draw', type=self.bool, default=True)
        self.add_argument('--connector_length', type=self.float, default=3.0)
        self.add_argument('--connector_thickness', type=self.float, default=3.0)
        self.add_argument('--head_length', type=self.float, default=1.0)
        self.add_argument('--head_thickness', type=self.float, default=1.0)
        self.add_argument('--pattern', type=self.str, default='support ring')

    def generate_path_tree(self):
        """ Specialized path generation for your origami pattern
        """
        # retrieve conversion factor for selected unit
        unit_factor = self.calc_unit_factor()

        # retrieve saved parameters, and apply unit factor where needed

        inverted = self.options.inverted
        sign = -1 if inverted else 1
        single_stroke = self.options.single_stroke
        radius_external = self.options.radius_external * unit_factor
        radius_type = self.options.radius_type
        radius_ratio = self.options.radius_ratio
        radius_internal = radius_external / radius_ratio if inverted else radius_external * radius_ratio
        # dradius = abs(radius_external-radius_internal)
        sides = self.options.sides
        connector_length = self.options.connector_length * unit_factor
        connector_thickness = self.options.connector_thickness * unit_factor
        head_length = self.options.head_length * unit_factor
        head_thickness = self.options.head_thickness * unit_factor

        angle = pi / sides
        length_external = 2 * radius_external * sin(angle)
        length_internal = length_external / radius_ratio if inverted else length_external * radius_ratio

        external_points = [(-length_external/2, 0),
                           (-connector_thickness / 2, 0),
                           (-connector_thickness / 2, -connector_length*sign),
                           (-connector_thickness / 2 - head_thickness / 2, -connector_length*sign),
                           (-connector_thickness / 2, -(connector_length + head_length)*sign),
                           (0, -(connector_length + head_length)*sign),
                           (+connector_thickness / 2, -(connector_length + head_length)*sign),
                           (+connector_thickness / 2 + head_thickness / 2, -connector_length*sign),
                           (+connector_thickness / 2, -connector_length*sign),
                           (+connector_thickness / 2, 0),
                           (length_external/2, 0)]

        internal_points = [(0, 0), (length_internal, 0)]

        external_lines_0 = Path(external_points, 'm') + (length_external / 2, 0)
        external_lines = [external_lines_0]

        for i in range(sides-1):
            x, y = external_lines[-1].points[-1]
            external_lines.append(external_lines_0*(1, 2*(i+1)*angle) + (x, y))

        if single_stroke:
            external_lines = Path(Path.get_points(external_lines), 'm')

        self.path_tree = [external_lines]

        if self.options.radius_draw == True:

            # center point of main strokes
            outer_average = Path.get_average_point(external_lines)

            if radius_type == 'polygonal':
                internal_lines_0 = Path(internal_points, 'm')
                internal_lines = [internal_lines_0]
                for i in range(sides - 1):
                    x, y = internal_lines[-1].points[-1]
                    internal_lines.append(internal_lines_0*(1, 2*(i+1)*angle) + (x, y))

                # move to center
                inner_average = Path.get_average_point(internal_lines)
                delta = ((outer_average[0] - inner_average[0]),
                         (outer_average[1] - inner_average[1]))

                if single_stroke:
                    internal_lines = Path(Path.get_points(internal_lines), 'm')

                internal_lines = Path.list_add(internal_lines, delta)
            elif radius_type == 'circular':

                internal_lines = Path(outer_average, radius=radius_internal, style='m')

            self.path_tree.append(internal_lines)








# Main function, creates an instance of the Class and calls self.draw() to draw the origami on inkscape
# self.draw() is either a call to inkex.affect() or to svg.run(), depending on python version
if __name__ == '__main__':
    e = SupportRing()  # remember to put the name of your Class here!
    e.draw()

#! /usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
from math import pi

import inkex

from Path import Path
from Pattern import Pattern


# Select name of class, inherits from Pattern
# TODO:
# 1) Implement __init__ method to get all custom options and then call Pattern's __init__
# 2) Implement generate_path_tree to define all of the desired strokes


class Template(Pattern):

    def __init__(self):
        """ Constructor
        """
        Pattern.__init__(self)  # Must be called in order to parse common options

        # save all custom parameters defined on .inx file
        self.add_argument('--pattern', type=self.str, default='template1')
        self.add_argument('--length', type=self.float, default=10.0)
        self.add_argument('--angle', type=self.int, default=0)
        self.add_argument('--fold_angle_valley', type=self.int, default=180)

    def generate_path_tree(self):
        """ Specialized path generation for your origami pattern
        """
        # retrieve conversion factor for selected unit
        unit_factor = self.calc_unit_factor()

        # retrieve saved parameters, and apply unit factor where needed
        length = self.options.length * unit_factor
        vertex_radius = self.options.vertex_radius * unit_factor
        pattern = self.options.pattern
        angle = self.options.angle * pi / 180
        fold_angle_valley = self.options.fold_angle_valley

        # create all Path instances defining strokes
        # first define its points as a list of tuples...
        left_right_stroke_points = [(length / 2, 0),
                   (length / 2, length)]
        up_down_stroke_points = [(0, length / 2),
                                    (length, length / 2)]

        # doing the same for diagonals
        diagonal_1_stroke_points = [(0, 0),
                                    (length, length)]
        diagonal_2_stroke_points = [(0, length),
                                    (length, 0)]

        # ... and then create the Path instances, defining its type ('m' for mountain, etc...)
        if pattern == 'template1':
            up_down = [Path(left_right_stroke_points, 'm', fold_angle = 180.),
                         Path(up_down_stroke_points, 'm', fold_angle = 180.)]

            diagonals = [Path(diagonal_1_stroke_points, 'v', fold_angle = fold_angle_valley),
                       Path(diagonal_2_stroke_points, 'v', fold_angle = fold_angle_valley)]

        else:
            up_down = [Path(left_right_stroke_points, 'v', fold_angle = fold_angle_valley),
                         Path(up_down_stroke_points, 'v', fold_angle = fold_angle_valley)]

            diagonals = [Path(diagonal_1_stroke_points, 'm', fold_angle = 180.),
                       Path(diagonal_2_stroke_points, 'm', fold_angle = 180. )]

        vertices = []
        for i in range(3):
            for j in range(3):
                vertices.append(Path(((i/2.) * length, (j/2.) * length), style='p', radius=vertex_radius))

        # multiplication is implemented as a rotation, and list_rotate implements rotation for list of Path instances
        vertices = Path.list_rotate(vertices, angle, (1 * length, 1 * length))
        up_down = Path.list_rotate(up_down, angle, (1 * length, 1 * length))
        diagonals = Path.list_rotate(diagonals, angle, (1 * length, 1 * length))

        # if Path constructor is called with more than two points, a single stroke connecting all of then will be
        # created. Using method generate_separated_paths, you can instead return a list of separated strokes
        # linking each two points

        # create a list for edge strokes
        # create path from points to be able to use the already built rotate method
        edges = Path.generate_square(length, length, 'e', rotation = angle)
        edges = Path.list_rotate(edges, angle, (1 * length, 1 * length))

        # IMPORTANT: the attribute "path_tree" must be created at the end, saving all strokes
        self.path_tree = [up_down, diagonals, vertices]

        # IMPORTANT: at the end, save edge points as "self.edge_points", to simplify selection of single or multiple
        # strokes for the edge
        self.edge_points = edges.points

        # if you decide not to declare "self.edge_points", then the edge must be explicitly created in the path_tree:
        # self.path_tree = [mountains, valleys, vertices, edges]

        # FINAL REMARKS:
        # division is implemented as a reflection, and list_reflect implements it for a list of Path instances
        # here's a commented example:
        # line_reflect = (0 * length, 2 * length, 1 * length, 1 * length)
        # mountains = Path.list_reflect(mountains, line_reflect)
        # valleys = Path.list_reflect(valleys, line_reflect)
        # edges = Path.list_reflect(edges, line_reflect)

# Main function, creates an instance of the Class and calls self.draw() to draw the origami on inkscape
# self.draw() is either a call to inkex.affect() or to svg.run(), depending on python version
if __name__ == '__main__':
    e = Template()  # remember to put the name of your Class here!
    e.draw()

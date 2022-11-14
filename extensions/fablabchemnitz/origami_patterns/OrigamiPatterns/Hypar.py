#! /usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np

from math import pi, tan, sqrt, sin, cos

import inkex

from Path import Path
from Pattern import Pattern


class Hypar(Pattern):

    def __init__(self):
        """ Constructor
        """
        Pattern.__init__(self)  # Must be called in order to parse common options

        # save all custom parameters defined on .inx file
        self.add_argument('--pattern', type=self.str, default='template1')
        self.add_argument('--radius', type=self.float, default=10.0)
        self.add_argument('--sides', type=self.int, default=4)
        self.add_argument('--rings', type=self.int, default=7)
        self.add_argument('--simplify_center', type=self.bool, default=0)

    def generate_path_tree(self):
        """ Specialized path generation for your origami pattern
        """
        # retrieve saved parameters
        unit_factor = self.calc_unit_factor()
        vertex_radius = self.options.vertex_radius * unit_factor
        pattern = self.options.pattern
        radius = self.options.radius * unit_factor
        sides = self.options.sides
        rings = self.options.rings
        simplify_center = self.options.simplify_center
        sin_ = sin(pi / float(sides))
        a = radius*sin_  # half of length of polygon side
        H = radius*sqrt(1 - sin_**2)

        polygon = Path.generate_polygon(sides, radius, 'e')

        # # OLD diagonals generation with universal creases
        # diagonals = []
        # for i in range(sides):
        #     diagonals.append(Path([(0, 0), polygon.points[i]], 'u'))
        # points = [(x, y) for x, y in polygon.points]
        # diagonals = diagonals + [Path.generate_separated_paths(points, 'm')]

        # # modify center if needed
        # if simplify_center:
        #     for i in range(sides):
        #         if i % 2 == 0:
        #             p2 = diagonals[i].points[1]
        #             diagonals[i].points[0] = (1. / (rings + 1) * p2[0], 1. / (rings + 1) * p2[1])

        # separate generic closed ring to create edges
        self.edge_points = polygon.points

        # vertex and diagonal lines creation
        vertex_line = []
        diagonal_line = []
        for i in range(1, rings + 2):
            y1 = a * (float(i - 1) / (rings + 1.))
            x1 = H * float(i - 1) / (rings + 1.)
            y2 = a * (float(i) / (rings + 1.))
            x2 = H * float(i) / (rings + 1.)
            vertex_line.append((Path((x2, y2), style='p', radius=vertex_radius)))
            diagonal_line.append((Path([(x1, y1), (x2, y2)], style='m' if i % 2 else 'v')))

        # rotation of vertices and diagonals for completing the drawing
        diagonals = []
        vertices = [Path((0, 0), style='p', radius=vertex_radius)]
        for i in range(sides):
            vertices = vertices+Path.list_rotate(vertex_line, i * 2 * pi / float(sides))
            diagonals = diagonals+[Path.list_rotate(diagonal_line, i * 2 * pi / float(sides))]

        # modify center if needed
        if simplify_center:
            for i in range(sides):
                if i % 2 == 0:
                    del diagonals[i][0]

        # inkex.debug(len(diagonals))
        # inkex.debug(len(diagonals[0]))
        # diagonals = diagonals + diagonal

        # scale generic closed ring to create inner rings
        inner_rings = []
        for i in range(rings + 1):
            inner_rings.append(polygon * (float(i)/(rings+1)))
            inner_rings[i].style = 'v' if i % 2 else 'm'

        # create points for zig zag pattern
        zig_zags = []
        if pattern != "classic":
            zig_zag = []
            for i in range(1, rings + 1):
                y_out = a * ((i + 1.) / (rings + 1.))
                y_in = a * (float(i) / (rings + 1.))
                x_out = H * (i + 1.) / (rings + 1.)
                x_in = H * float(i) / (rings + 1.)

                if pattern == "alternate_asymmetric" and i % 2:
                    zig_zag.append(Path([(x_in, -y_in), (x_out, +y_out)], style='u'))
                else:
                    zig_zag.append(Path([(x_in, +y_in), (x_out, -y_out)], style='u'))

            # reflect zig zag pattern to create all sides
            zig_zags.append(zig_zag)
            for i in range(sides - 1):
                points = diagonals[i][0].points
                zig_zags.append(Path.list_reflect(zig_zags[i], points[0], points[1]))

        self.translate = (radius, radius)
        self.path_tree = [diagonals, zig_zags, inner_rings, vertices]

# Main function, creates an instance of the Class and calls inkex.affect() to draw the origami on inkscape
if __name__ == '__main__':
    e = Hypar()  # remember to put the name of your Class here!
    e.draw()

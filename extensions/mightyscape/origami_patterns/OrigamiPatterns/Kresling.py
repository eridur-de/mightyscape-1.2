#! /usr/bin/env python
# -*- coding: utf-8 -*-
from math import pi, sin, cos, tan, acos, sqrt
import inkex
import os

from Path import Path
from Pattern import Pattern


class Kresling(Pattern):

    def __init__(self):
        """ Constructor
        """
        Pattern.__init__(self)  # Must be called in order to parse common options

        self.add_argument('--pattern', type=self.str, default="kresling")
        self.add_argument('--lines', type=self.int, default=1)
        self.add_argument('--sides', type=self.int, default=3)
        self.add_argument('--add_attachment', type=self.bool, default=False)
        self.add_argument('--attachment_percentage', type=self.float, default=100.)
        self.add_argument('--mirror_cells', type=self.bool, default=False)

    @staticmethod
    def generate_kresling_zigzag(sides, radius, angle_ratio, add_attachment):

        theta = (pi / 2.) * (1 - 2. / sides)
        l = 2. * radius * cos(theta * (1. - angle_ratio))
        a = 2. * radius * sin(pi / sides)
        # b = sqrt(a * a + l * l - 2 * a * l * cos(angle_ratio * theta))
        # phi = abs(acos((l * l + b * b - a * a) / (2 * l * b)))
        # gamma = pi / 2 - angle_ratio * theta - phi
        dy = l * sin(theta * angle_ratio)
        dx = l * cos(theta * angle_ratio) - a

        points = []
        styles = []

        for i in range(sides):
            points.append((i * a, 0))
            points.append(((i + 1) * a + dx, -dy))
            styles.append('v')
            if i != sides - 1:
                styles.append('m')
            elif add_attachment:
                points.append((sides * a, 0))
                styles.append('m')

        path = Path.generate_separated_paths(points, styles)
        return path

    def generate_path_tree(self):
        """ Specialized path generation for Waterbomb tesselation pattern
        """
        unit_factor = self.calc_unit_factor()
        vertex_radius = self.options.vertex_radius * unit_factor
        lines = self.options.lines
        sides = self.options.sides
        radius = self.options.radius * unit_factor
        angle_ratio = self.options.angle_ratio
        mirror_cells = self.options.mirror_cells

        theta = (pi/2.)*(1 - 2./sides)
        l = 2.*radius*cos(theta*(1.-angle_ratio))
        a = 2.*radius*sin(pi/sides)
        # b = sqrt(a*a + l*l - 2*a*l*cos(angle_ratio*theta))
        # phi = abs(acos((l*l + b*b - a*a)/(2*l*b)))
        # gamma = pi/2 - angle_ratio*theta - phi
        # dy = b*cos(gamma)
        # dx = b*sin(gamma)
        dy = l * sin(theta * angle_ratio)
        dx = l * cos(theta * angle_ratio) - a

        add_attachment = self.options.add_attachment
        attachment_percentage = self.options.attachment_percentage/100.
        attachment_height = a*(attachment_percentage-1)*tan(angle_ratio*theta)

        vertices = []
        for i in range(sides + 1):
            for j in range(lines + 1):
                if mirror_cells:
                    vertices.append(Path((dx*((lines - j)%2) + a*i, dy*j), style='p', radius=vertex_radius))
                else:
                    vertices.append(Path((dx*(lines - j) + a*i, dy*j), style='p', radius=vertex_radius))

        # create a horizontal grid, then offset each line according to angle
        grid_h = Path.generate_hgrid([0, a * sides], [0, dy * lines], lines, 'm')

        if not mirror_cells:
            # shift every mountain line of the grid to the right by increasing amounts
            grid_h = Path.list_add(grid_h, [(i * dx, 0) for i in range(lines - 1, 0, -1)])
        else:
            # shift every OTHER mountain line of the grid a bit to the right
            grid_h = Path.list_add(grid_h, [((i%2)*dx, 0) for i in range(lines-1, 0, -1)])
            if add_attachment:
                for i in range(lines%2, lines-1, 2):
                    # hacky solution, changes length of every other mountain line
                    grid_h[i].points[1-i%2] = (grid_h[i].points[1-i%2][0] + a*attachment_percentage, grid_h[i].points[1-i%2][1])

        # create MV zigzag for Kresling pattern
        zigzag = Kresling.generate_kresling_zigzag(sides, radius, angle_ratio, add_attachment)
        zigzags = []

        # duplicate zigzag pattern for desired number of cells
        if not mirror_cells:
            for i in range(lines):
                zigzags.append(Path.list_add(zigzag, (i * dx, (lines - i) * dy)))
        else:
            zigzag_mirror = Path.list_reflect(zigzag, (0, lines * dy / 2), (dx, lines * dy / 2))
            for i in range(lines):
                if i % 2 == 1:
                    zigzags.append(Path.list_add(zigzag_mirror, (0, -(lines - i + (lines-1)%2) * dy)))
                else:
                    zigzags.append(Path.list_add(zigzag, (0, (lines - i) * dy)))

        # create edge strokes
        if not mirror_cells:
            self.edge_points = [
                (a * sides             , dy * lines),  # bottom right
                (0                     , dy * lines),  # bottom left
                (dx * lines            , 0),  # top left
                (dx * lines + a * sides, 0)]  # top right

            if add_attachment:
                for i in range(lines):
                    x = dx * (lines - i) + a * (sides + attachment_percentage)
                    self.edge_points.append((x, dy * i))
                    self.edge_points.append((x, dy * i - attachment_height))
                    if i != lines - 1:
                        self.edge_points.append((x-dx-a*attachment_percentage, dy * (i + 1)))
                        pass

        else:
            self.edge_points = [(a * sides + (lines % 2)*dx, 0)]

            for i in range(lines+1):
                self.edge_points.append([((lines+i) % 2)*dx, dy*i])

            self.edge_points.append([a * sides + ((lines+i) %2)*dx, lines*dy])

            if add_attachment:
                for i in range(lines + 1):

                    if not i%2 == 0:
                        self.edge_points.append([a*sides + (i%2)*(dx+a*attachment_percentage), dy*(lines - i) - (i%2)*attachment_height])
                        self.edge_points.append([a*sides + (i%2)*(dx+a*attachment_percentage), dy*(lines - i)])
                        if (i != lines):
                            self.edge_points.append([a * sides + (i % 2) * (dx + a * attachment_percentage), dy * (lines - i) + (i % 2) * attachment_height])
                    else:
                        self.edge_points.append([a * sides + (i % 2) * (dx + a * attachment_percentage), dy * (lines - i)])
            else:
                for i in range(lines + 1):
                    self.edge_points.append([a*sides + (i%2)*dx, dy*(lines - i)])

        self.path_tree = [grid_h, zigzags, vertices]


if __name__ == '__main__':

    e = Kresling()
    e.draw()

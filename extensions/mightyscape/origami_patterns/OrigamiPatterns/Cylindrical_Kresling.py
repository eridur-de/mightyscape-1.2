#! /usr/bin/env python
# -*- coding: utf-8 -*-
from math import pi, sin, asin, cos, tan, acos, sqrt
import inkex
import os

from Path import Path
from Pattern import Pattern
from Cylindrical import Cylindrical


class Kresling(Cylindrical):

    def __init__(self):
        """ Constructor
        """
        Cylindrical.__init__(self)  # Must be called in order to parse common options

        self.add_argument('--pattern', type=self.str, default="kresling")

        self.add_argument('--measure_value', type=self.float, default=10.0)
        self.add_argument('--measure_type', type=self.str, default=60)
        self.add_argument('--parameter_type', type=self.str, default=60)
        self.add_argument('--radial_ratio', type=self.float, default=0.5)
        self.add_argument('--angle_ratio', type=self.float, default=0.5)
        self.add_argument('--lambdatheta', type=self.float, default=45)

    def parse_parameters(self):
        n = self.options.sides
        theta = pi * (n - 2) / (2 * n)
        # define ratio parameter
        parameter = self.options.parameter_type
        if parameter == 'radial_ratio':
            radial_ratio = self.options.radial_ratio
            max_radial_ratio = sin((pi / 4) * (1. - 2. / n))
            if radial_ratio > max_radial_ratio:
                inkex.errormsg(
                    _("For polygon of {} sides, the maximal radial ratio is = {}".format(n, max_radial_ratio)))
                radial_ratio = max_radial_ratio
            self.options.angle_ratio = 1 - 2 * n * asin(radial_ratio) / ((n - 2) * pi)

        elif parameter == 'lambdatheta':
            lambdatheta = self.options.lambdatheta
            angle_min = 45. * (1 - 2. / n)
            angle_max = 2 * angle_min
            if lambdatheta < angle_min:
                inkex.errormsg(_(
                    "For polygon of {} sides, phi must be between {} and {} degrees, \nsetting lambda*theta = {}\n".format(
                        n, angle_min, angle_max, angle_min)))
                lambdatheta = angle_min
            elif lambdatheta > angle_max:
                inkex.errormsg(_(
                    "For polygon of {} sides, phi must be between {} and {} degrees, \nsetting lambda*theta = {}\n".format(
                        n, angle_min, angle_max, angle_max)))
                lambdatheta = angle_max
            self.options.angle_ratio = lambdatheta * n / (90. * (n - 2.))

        # define some length
        mtype = self.options.measure_type
        mvalue = self.options.measure_value
        angle_ratio = self.options.angle_ratio
        if mtype == 'a':
            radius = 0.5 * mvalue / (sin(pi / n))
        if mtype == 'b':
            A = cos(theta * (1 - angle_ratio))
            B = sin(pi / n)
            C = cos(theta * angle_ratio)
            radius = 0.5 * mvalue / sqrt(A ** 2 + B ** 2 - 2 * A * B * C)
        elif mtype == 'l':
            radius = 0.5 * mvalue / cos(theta * (1 - angle_ratio))
        elif mtype == 'radius_external':
            radius = mvalue
        elif mtype == 'radius_internal':
            radius = mvalue / (sin(theta * (1 - angle_ratio)))
        elif mtype == 'diameter_external':
            radius = 0.5 * mvalue
        elif mtype == 'diameter_internal':
            radius = 0.5 * mvalue / sin(theta * (1 - angle_ratio))

        if self.options.pattern == 'mirrowed':
            self.options.mirror_cells = True
        else:
            self.options.mirror_cells = False
        self.options.radius = radius

    def generate_cell(self):
        """ Generate the the origami cell
        """
        # retrieve conversion factor for selected unit
        unit_factor = self.calc_unit_factor()
        rows = self.options.rows
        sides = self.options.sides
        cols = self.options.cols
        radius = self.options.radius * unit_factor
        width = self.options.width * unit_factor
        # vertex_radius = self.options.vertex_radius * unit_factor

        angle_ratio = self.options.angle_ratio
        mirror_cells = self.options.mirror_cells

        theta = (pi/2.)*(1 - 2./sides)
        l = 2.*radius*cos(theta*(1.-angle_ratio))
        dy = l * sin(theta * angle_ratio)
        dx = l * cos(theta * angle_ratio) - width

        # init dict that holds everything
        cell_data = {}

        # divider (supposed to be the same)
        cell_data['divider'] = Path([(0, 0), (width * cols, 0)], style='m')

        # IMPORTANT: left edges from TOP to BOTTOM
        edge_left = [Path([(0, 0), (dx, dy)], style='e')]
        if mirror_cells:
            edge_left.append(Path([(0, 0), (-dx, dy)], style='e'))
        cell_data['edge_left'] = [edge_left[i % (1 + mirror_cells)] for i in range(rows)]

        # IMPORTANT: right edges from BOTTOM to TOP
        edge_right = [Path([(cols * width + dx, dy), (cols * width, 0)], style='e')]
        if mirror_cells:
            edge_right.append(Path([(cols * width - dx, dy), (cols * width, 0)], style='e'))
        cell_data['edge_right'] = [edge_right[i % (1 + mirror_cells)] for i in range(rows)]

        # rest of cell
        zigzags = [Kresling.generate_kresling_zigzag(sides, cols, radius, angle_ratio)]
        if mirror_cells:
            zigzags.append(Path.list_reflect(zigzags[0], (0, dy / 2), (dx, dy / 2)))
            zigzags[1] = Path.list_add(zigzags[1], (-dx, 0))

        cell_data['interior'] = [zigzags[i % (1 + mirror_cells)] for i in range(rows)]

        return cell_data

    @staticmethod
    def generate_kresling_zigzag(sides, cols, radius, angle_ratio):
    # def generate_kresling_zigzag(sides, radius, angle_ratio, add_attachment):

        theta = (pi / 2.) * (1 - 2. / sides)
        l = 2. * radius * cos(theta * (1. - angle_ratio))
        a = 2. * radius * sin(pi / sides)
        dy = l * sin(theta * angle_ratio)
        dx = l * cos(theta * angle_ratio) - a

        points = []
        styles = []

        for i in range(cols):
            points.append((i * a, 0))
            points.append(((i + 1) * a + dx, dy))
            styles.append('v')
            if i != cols - 1:
                styles.append('m')
            # elif add_attachment:
            #     points.append((sides * a, 0))
            #     styles.append('m')

        path = Path.generate_separated_paths(points, styles)
        return path

if __name__ == '__main__':

    e = Kresling()
    e.draw()

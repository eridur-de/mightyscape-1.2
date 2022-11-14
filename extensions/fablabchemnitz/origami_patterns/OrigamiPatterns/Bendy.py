#! /usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
from math import pi, sin, cos, tan, asin, acos, atan, sqrt

import inkex

from Path import Path
from Pattern import Pattern

# Select name of class, inherits from Pattern
# TODO:
# 1) Implement __init__ method to get all custom options and then call Pattern's __init__
# 2) Implement generate_path_tree to define all of the desired strokes
MIN = 0.0001


class Bendy_Straw(Pattern):

    def __init__(self):
        """ Constructor
        """
        Pattern.__init__(self)  # Must be called in order to parse common options

        # save all custom parameters defined on .inx file
        self.add_argument('--pattern', type=self.str, default='bendy_straw')
        self.add_argument('--pattern_type', type=self.str, default='origami')
        self.add_argument('--parameter_type', type=self.str, default='angles')
        self.add_argument('--n', type=self.int, default=6)
        self.add_argument('--lines', type=self.int, default=3)
        self.add_argument('--radius', type=self.float, default=25.0)
        # self.add_argument('--attachment_length', type=self.float, default=3.0)
        # self.add_argument('--attachment_length', type=self.int, default=20)
        self.add_argument('--radial_ratio', type=self.float, default=0.75)
        # self.add_argument('--alpha1', type=self.float, default=45.0)
        # self.add_argument('--alpha2', type=self.float, default=45.0)
        self.add_argument('--alpha1', type=self.int, default=45)
        self.add_argument('--alpha2', type=self.int, default=35)
        self.add_argument('--h1', type=self.float, default=1)
        self.add_argument('--h2', type=self.float, default=2)

        self.add_argument('--vertex_base_outer_bool', type=self.bool, default=False)
        self.add_argument('--vertex_base_inner_bool', type=self.bool, default=False)
        self.add_argument('--vertex_radius_outer_bool', type=self.bool, default=False)
        self.add_argument('--vertex_radius_inner_bool', type=self.bool, default=False)

        self.add_argument('--add_attachment', type=self.bool, default=False)

        # slot options for support ring
        self.add_argument('--base_height', type=self.float, default=5.0)
        self.add_argument('--add_base_slot', type=self.bool, default=False)
        self.add_argument('--center_base_slot', type=self.bool, default=False)
        self.add_argument('--base_slot_height', type=self.float, default=3.0)
        self.add_argument('--base_slot_width', type=self.float, default=3.0)
        self.add_argument('--distance', type=self.float, default=3.0)
        self.add_argument('--add_distance_slot', type=self.bool, default=False)
        self.add_argument('--distance_slot_height', type=self.float, default=3.0)
        self.add_argument('--distance_slot_width', type=self.float, default=3.0)

    def generate_path_tree(self):
        """ Specialized path generation for your origami pattern
        """
        # retrieve conversion factor for selected unit
        unit_factor = self.calc_unit_factor()
        vertex_radius = self.options.vertex_radius * unit_factor

        # retrieve saved parameters, and apply unit factor where needed
        pattern_type = self.options.pattern_type
        n = self.options.n
        lines = self.options.lines
        radial_ratio = self.options.radial_ratio
        R = self.options.radius * unit_factor
        distance = self.options.distance * unit_factor
        base_height = self.options.base_height * unit_factor
        # add_attachment = self.options.add_attachment
        # attachment_length = self.options.attachment_length * unit_factor
        r = R * radial_ratio

        if (self.options.parameter_type == 'angles'):
            alpha1 = self.options.alpha1 * pi / 180
            alpha2 = self.options.alpha2 * pi / 180
        elif (self.options.parameter_type == 'heights'):
            alpha1 = atan(self.options.h1 * unit_factor / (R - r))
            alpha2 = atan(self.options.h2 * unit_factor / (R - r))

        # calculating pattern parameters
        l1 = (R - r) / cos(alpha1)
        l2 = (R - r) / cos(alpha2)
        A = 2 * R * sin(pi / n)
        # attachment_length = 0.01 * self.options.attachment_length * A
        a = A * radial_ratio
        dx = (A - a) / 2
        beta1 = acos(cos(alpha1) * sin(pi / n))
        beta2 = acos(cos(alpha2) * sin(pi / n))
        b1 = l1 * sin(beta1)
        b2 = l2 * sin(beta2)
        height = (b1 + b2) * lines + distance * (lines - 1)

        if self.options.add_attachment:
            n = n+1

        #
        # big horizontal mountains grid
        #
        mountain_horizontal_stroke = Path([(0, base_height), (A * n, base_height)], 'm')
        horizontal_grid_mountain = []
        for i in range(1, lines):
            horizontal_grid_mountain.append(
                mountain_horizontal_stroke + (0, distance * (i - 1) + b1 * (i + 0) + b2 * (i + 0)))
            horizontal_grid_mountain.append(
                mountain_horizontal_stroke + (0, distance * (i + 0) + b1 * (i + 0) + b2 * (i + 0)))
        if distance < MIN:
            horizontal_grid_mountain = horizontal_grid_mountain[::2]
        if base_height > MIN:
            horizontal_grid_mountain.insert(0, mountain_horizontal_stroke)
            horizontal_grid_mountain.append(
                mountain_horizontal_stroke + (0, distance * (lines - 1) + b1 * lines + b2 * lines))

        # reverse every other horizontal stroke for faster laser-cutting
        for i in range(len(horizontal_grid_mountain)):
            if (i % 2 == 0):
                horizontal_grid_mountain[i].points.reverse()

        #
        # diamond shapes
        #

        # full diamond patterns styles, depending on pattern type
        style_diag_left = 'm'
        style_diag_right = 'm'
        style_diag = 'v'
        style_vert = 'm'
        style_hori_left = 'm'
        style_hori_right = 'm'
        if pattern_type == 'origami' or pattern_type == 'origami_bent':
            style_hori_left = 'v'
            style_diag_left = 'n'
            style_diag_right = 'v'
        elif pattern_type == 'origami2':
            style_hori_right = 'v'
            style_diag_left = 'v'
            style_diag_right = 'n'
        elif pattern_type == 'kirigami1':
            style_vert = 'v'
            style_hori_left = 'c'
            style_hori_right = 'c'
        elif pattern_type == 'kirigami2':
            style_diag_left = 'c'
            style_diag_right = 'c'
            style_hori_left = 'n'
            style_hori_right = 'n'
            style_vert = 'n'

        # diamond pattern with strokes of different styles
        stroke_base = Path([(0, 0), (0, base_height)], 'm')
        diamond_diagonals_left = Path([(0, base_height), (-dx, base_height + b1), (0, base_height + b1 + b2)],
                                      style_diag_left)
        diamond_diagonals_right = Path([(0, base_height + b1 + b2), (dx, base_height + b1), (0, base_height)],
                                       style_diag_right)
        diamond_vertical = Path([(0, base_height), (0, base_height + b1 + b2)], style_vert)
        stroke_distance = Path([(0, base_height + b1 + b2), (0, distance + base_height + b1 + b2)], 'm')
        diamond_horizontal_left = Path([(-dx, 0), (0, 0)], style_hori_left)
        diamond_horizontal_right = Path([(0, 0), (dx, 0)], style_hori_right)

        diamond = [diamond_diagonals_left, diamond_diagonals_right, diamond_vertical]

        if pattern_type == 'origami_bent':
            bent_diagonal = Path([(0, base_height + b1 + b2), (dx, base_height + b1), (0, base_height)], 'm')
            bent_horizontal = Path([(0, 0), (dx, 0)], 'v')
            line_bent = []


        # drawing lines with the diamond shapes
        line_left = []
        line_middle = []
        line_right = []
        if base_height > MIN:
            line_middle.append(stroke_base)
            if pattern_type == 'origami_bent':
                line_bent.append(stroke_base)
        for i in range(lines):
            delta = (0, (distance + b1 + b2) * i)
            if pattern_type != 'kirigami2':
                line_left.append(diamond_diagonals_right + delta)
            line_middle = line_middle + Path.list_add(diamond, delta)
            if pattern_type != 'kirigami2':
                line_right.append(diamond_diagonals_left + delta)
            if distance > MIN and i < lines - 1:
                line_middle.append(stroke_distance + delta)

            if pattern_type == 'origami_bent':
                line_bent = line_bent + [bent_diagonal + delta]
                if distance > MIN and i < lines - 1:
                    line_bent.append(stroke_distance + delta)

        if base_height > MIN:
            line_middle.append(stroke_base + (0, base_height + height))
            if pattern_type == 'origami_bent':
                line_bent.append(stroke_base + (0, base_height + height))

        # creating full diamond patterns
        line_left = line_left[::-1]
        diamond_patterns_full = [line_left]
        for i in range(n - 1):
            delta = (A * (i + 1), 0)
            if pattern_type == 'origami_bent' and i == 2:
                diamond_patterns_full.append(Path.list_add(line_bent, delta))
            else:
                diamond_patterns_full.append(Path.list_add(line_middle, delta))
        diamond_patterns_full.append(Path.list_add(line_right, (A * n, 0)))

        #
        # small horizontal alternate style grid
        #
        valley_points = [(dx, 0),
                         (dx + a, 0)]
        valley_stroke = Path(valley_points, 'v')
        if pattern_type == 'kirigami2':
            horizontal_line = []
        else:
            horizontal_line = [diamond_horizontal_right + (0, 0)]
        for i in range(n):
            if not (pattern_type == 'origami_bent' and i == 3):
                horizontal_line.append(valley_stroke + ((a + 2 * dx) * i, 0))
            if (pattern_type != 'kirigami2'):
                if not (pattern_type == 'origami_bent' and i == 3):
                    horizontal_line.append(diamond_horizontal_left + (A + (a + 2 * dx) * i, 0))
                if pattern_type == 'origami_bent' and i==2:
                    horizontal_line.append(bent_horizontal + (A + (a + 2 * dx) * i, 0))
                elif i < n - 1:
                    horizontal_line.append(diamond_horizontal_right + (A + (a + 2 * dx) * i, 0))
        horizontal_grid_alternate = []
        for i in range(lines):
            horizontal_grid_alternate.append(
                Path.list_add(horizontal_line, (0, base_height + distance * (i + 0) + b1 * (i + 1) + b2 * (i + 0))))

        # reverse every other horizontal stroke for faster laser-cutting
        for i in range(len(horizontal_grid_alternate)):
            if (i % 2 == 0):
                horizontal_grid_alternate[i] = Path.list_invert(horizontal_grid_alternate[i])

        # for i in range(len(horizontal_grid_alternate)):
        #     inkex.debug(i)
        #     Path.debug_points(horizontal_grid_alternate[i])
        #     inkex.debug('\n')

        #
        # edge drawing
        #
        self.edge_points = [(0, 0)]
        self.edge_points.append((A * n, 0))

        # rectangles for attachments at base and between cells

        # add upper base attachment
        self.edge_points.append((A * n, base_height))

        # draw attachment between cells and inside cells
        for i in range(lines):
            self.edge_points.append((A * n + 0, base_height + (b1 + b2) * (i + 0) + distance * i))
            if pattern_type == 'kirigami2':
                self.edge_points.append((A * n - dx, base_height + b1 * (i + 1) + (b2 + distance) * i))
            self.edge_points.append((A * n + 0, base_height + (b1 + b2) * (i + 1) + distance * i))

        self.edge_points.append((A * n, height + 2 * base_height))
        self.edge_points.append((0, height + 2 * base_height))

        # if full kirigami selected, cut left side next to cells
        if pattern_type == 'kirigami2':
            for i in range(lines):
                self.edge_points.append((0, height + base_height - (b1 + b2) * (i + 0) - distance * i))
                self.edge_points.append((dx, height + base_height - b2 * (i + 1) - (b1 + distance) * i))
                self.edge_points.append((0, height + base_height - (b1 + b2) * (i + 1) - distance * i))

        #
        # slots drawing
        #
        center_slot = self.options.center_base_slot
        base_slots = []
        if self.options.add_base_slot:
            base_slot_height = self.options.base_slot_height
            base_slot_width = self.options.base_slot_width
            if base_slot_height > base_height or base_slot_width > A:
                inkex.debug('Base slot dimensions are too big')
                base_slot_height = min(base_height, base_slot_height)
                base_slot_width = min(A, base_slot_width)
            if base_slot_height > 0 and base_slot_width > 0:
                points = [(0,     0),
                          (0,     base_slot_height),
                          (base_slot_width, base_slot_height),
                          (base_slot_width, 0,)]
                base_slot = Path(points, 'c', closed=True) + ((A - base_slot_width)/2, (base_height - base_slot_height)/(1+center_slot))
                base_slots_line = []
                for i in range(n):
                    base_slots_line.append(base_slot + (A*i, 0))
                base_slots = [base_slots_line]
                base_slots.append(Path.list_add(base_slots_line, (0, height+base_slot_height + (base_height - base_slot_height)*center_slot)))

        dist_slots = []
        if self.options.add_distance_slot:
            dist_slot_height = self.options.distance_slot_height
            dist_slot_width = self.options.distance_slot_width
            if dist_slot_height > distance or dist_slot_width > A:
                inkex.debug('Dimensions of slots between cells are too big')
                dist_slot_height = min(distance, dist_slot_height)
                dist_slot_width = min(A, dist_slot_width)

            if dist_slot_height > 0 and dist_slot_width > 0:
                points = [(0,     0),
                          (0,     dist_slot_height),
                          (dist_slot_width, dist_slot_height),
                          (dist_slot_width, 0,)]
                dist_slot = Path(points, 'c', closed=True) + ((A - dist_slot_width)/2, base_height+b1+b2 + (distance - dist_slot_height)/2)
                dist_slots_line = []
                for i in range(n):
                    dist_slots_line.append(dist_slot + (A*i, 0))

                for i in range(lines-1):
                    dist_slots.append(Path.list_add(dist_slots_line, (0, i*(b1+b2+distance))))



        # sending lines  to draw
        self.path_tree = [horizontal_grid_mountain, horizontal_grid_alternate, diamond_patterns_full, base_slots, dist_slots]

        #
        # vertices drawing
        #
        # outer base vertices?
        if self.options.vertex_base_outer_bool:
            self.vertex_points = self.vertex_points + [(A * i, height + base_height * 2) for i in range(n + 1)]
            self.vertex_points = self.vertex_points + [(A*i, 0) for i in range(n+1)]

        # inner base vertices?
        if self.options.vertex_base_inner_bool:
            self.vertex_points = self.vertex_points + [(A*i, base_height) for i in range(n+1)]
            self.vertex_points = self.vertex_points + [(A*i, height+base_height) for i in range(n+1)]
            for j in range(lines-1):
                    self.vertex_points = self.vertex_points + [(A*i, base_height+((b1+b2)*(j+1))+distance*j) for i in range(n+1)] + \
                                                              [(A*i, base_height+((b1+b2)*(j+1))+distance*(j+1)) for i in range(n+1)]

        # radius vertices?
        if self.options.vertex_radius_outer_bool and pattern_type != 'kirigami2':
            for j in range(lines):
                i_range = list(range(3)) + list(range(3+(pattern_type=='origami_bent'), n + 1))
                self.vertex_points = self.vertex_points + [(A * i, base_height + b1*(j+1) + (b2+distance)*j) for i in i_range]
        if self.options.vertex_radius_inner_bool:
            for j in range(lines):
                if pattern_type != 'origami2':
                    # pass
                    self.vertex_points = self.vertex_points + [(dx + A * i, base_height + b1*(j+1) + (b2+distance)*j) for i in range(n)]
                if pattern_type[:7] != 'origami':
                    # pass
                    self.vertex_points = self.vertex_points + [(-dx + A * (i + 1), base_height + b1 * (j + 1) + (b2 + distance) * j) for i in range(n)]
            # for j in range(lines):




        # self.vertex_points = self.vertex_points + vertices_base

        # self.vertex_points = self.vertex_points + self.edge_points
        # diamond_patterns_full_simple = Path.list_simplify(diamond_patterns_full)
        # for path in diamond_patterns_full:
        #     # path = Path.list_simplify(path)
        #     # path = Path.list_simplify(path[0])
        #     if path.style != 'n':
        #         self.vertex_points = self.vertex_points + path.points



#

# Main function, creates an instance of the Class and calls self.draw() to draw the origami on inkscape
# self.draw() is either a call to inkex.affect() or to svg.run(), depending on python version
if __name__ == '__main__':
    e = Bendy_Straw()  # remember to put the name of your Class here!
    e.draw()

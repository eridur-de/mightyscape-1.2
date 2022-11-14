#! /usr/bin/env python
# -*- coding: utf-8 -*-
import math
import numpy as np
from math import pi

import inkex

from Path import Path
from Pattern import Pattern


# Select name of class, inherits from Pattern
# TODO:
# 1) Implement __init__ method to get all custom options and then call Pattern's __init__
# 2) Implement generate_path_tree to define all of the desired strokes

def reflections_diag(path):
    new_paths = [path]
    new_paths = new_paths + Path.list_reflect(new_paths, (0, 0), (1, 1))
    return new_paths + Path.list_reflect(new_paths, (0, 0), (1, -1))

def reflections_rect(path):
    new_paths = [path]
    new_paths = new_paths + Path.list_reflect(new_paths, (0, 0), (0, 1))
    return new_paths + Path.list_reflect(new_paths, (0, 0), (1, 0))

def recenter(paths, dist):
    # paths_new = Path.list_simplify(paths)
    paths_new = Path.list_rotate(paths, pi/4)
    return Path.list_add(paths_new, (dist, dist))

class MasuBox(Pattern):

    def __init__(self):
        """ Constructor
        """
        Pattern.__init__(self)  # Must be called in order to parse common options

        # save all custom parameters defined on .inx file
        self.add_argument('--pattern', type=self.str, default='boxes_masu')
        self.add_argument('--width', type=self.float, default=10.0)
        self.add_argument('--height', type=self.float, default=10.0)
        self.add_argument('--width_delta', type=self.float, default=0.0)
        self.add_argument('--width_delta_bool', type=self.bool, default=False)

    def generate_path_tree(self):
        """ Specialized path generation for your origami pattern
        """
        # retrieve conversion factor for selected unit
        unit_factor = self.calc_unit_factor()

        # retrieve saved parameters, and apply unit factor where needed
        width = self.options.width * unit_factor
        height = self.options.height * unit_factor
        if self.options.width_delta_bool:
            width_delta = self.options.width_delta * unit_factor
            width += width_delta
            height -= width_delta/2
        length = math.sqrt(2)*(width + 2*height)
        half_fold = 90 if self.options.simulation_mode else 180

        # bottom of box
        ring_inner = Path.generate_square(width, width, center = [0,0], style = 'm', fold_angle=half_fold)

        # ring making the corners
        lengths = [height, width, height]
        points = Path.get_square_points(sum(lengths), sum(lengths), [0,0])
        styles = ['vmv','mmm']
        ring_middle = [Path([points[i], points[(i + 1)%4]], 'm').
                           break_path(lengths, styles[i % 2]) for i in range(4)]

        # arms along width and length
        points = [(-width / 2, -(width / 2 + 0 * height)),
                  (-width / 2, -(width / 2 + 1 * height)),
                  (-width / 2, -(width / 2 + 2 * height)),
                  (+width / 2, -(width / 2 + 2 * height)),
                  (+width / 2, -(width / 2 + 1 * height)),
                  (+width / 2, -(width / 2 + 0 * height))]

        arms_ = [Path.list_create_from_points(points, 'mmvmm', fold_angles = [180, 180, half_fold, 180, 180]),
                 Path.list_create_from_points(points, 'mvvvm', half_fold)]
        arms = [Path.list_rotate(arms_[i % 2], i * pi / 2) for i in range(4)]

        # tiny corner diagonals
        diag = Path([(width/2, width/2), (width/2 + height, width/2 + height)], 'v')
        corner_diagonals = [diag * (1, i*pi/2) for i in range(4)]

        self.edge_points = Path.get_square_points(length, length)

        self.path_tree = [ring_inner, ring_middle, arms, corner_diagonals]
        self.path_tree = recenter(self.path_tree, length/2)

# Main function, creates an instance of the Class and calls self.draw() to draw the origami on inkscape
# self.draw() is either a call to inkex.affect() or to svg.run(), depending on python version
if __name__ == '__main__':
    e = MasuBox()  # remember to put the name of your Class here!
    e.draw()

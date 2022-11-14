#! /usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
from abc import abstractmethod
from math import pi, sin, cos, tan, asin, acos, atan, sqrt

import inkex

from Path import Path
from Pattern import Pattern
from Cylindrical import Cylindrical


# Select name of class, inherits from Pattern
# TODO:
# 1) Implement __init__ method to get all custom options and then call Pattern's __init__
# 2) Implement generate_path_tree to define all of the desired strokes

class Template(Cylindrical):

    def __init__(self):
        """ Constructor
        """
        Cylindrical.__init__(self)  # Must be called in order to parse common options

        # save all custom parameters defined on .inx file
        self.add_argument('--pattern', type=self.str, default='cylindrical_template')
        self.add_argument('--length', type=self.float, default=10.)
        self.add_argument('--angle', type=self.int, default=0)

    def generate_cell(self):
        """ Generate the the origami cell
        """
        # retrieve conversion factor for selected unit
        unit_factor = self.calc_unit_factor()
        sides = self.options.sides
        cols = self.options.cols
        rows = self.options.rows

        length = self.options.length * unit_factor
        angle = self.options.angle * unit_factor
        width = self.options.width * unit_factor # use pre-calculated width

        dx = length * sin(pi * angle / 180)
        dy = length * cos(pi * angle / 180)

        # init dict that holds everything
        cell_data = {}

        # divider can be set for performance, or it can be calculated automatically, supposing a mountain fold
        # cell_data['divider'] = Path([(0,0), (width*cols, 0)], style='m')

        # Only left or right edges can be implemented, or both for performance
        # IMPORTANT: left edges from TOP to BOTTOM
        cell_data['edge_left'] = [Path([(0,0), (dx, dy)], style='e')]*rows

        # # IMPORTANT: right edges from BOTTOM to TOP
        # cell_data['edge_right'] = [Path([(cols*width + dx, dy), (cols*width, 0)], style='e')]*rows

        # rest of cell
        single = [Path([(0, 0), (width + dx, dy)], 'v'), Path([(width + dx, dy), (width, 0)], 'm')]
        pattern = [Path.list_add(single, (width*i, 0)) for i in range(cols)]
        pattern = Path.list_simplify(pattern)
        cell_data['interior'] = [pattern]*rows

        return cell_data


# Main function, creates an instance of the Class and calls self.draw() to draw the origami on inkscape
# self.draw() is either a call to inkex.affect() or to svg.run(), depending on python version
if __name__ == '__main__':
    e = Template()  # remember to put the name of your Class here!
    e.draw()

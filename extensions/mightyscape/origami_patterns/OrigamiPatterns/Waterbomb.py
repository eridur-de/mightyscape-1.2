#! /usr/bin/env python
# -*- coding: utf-8 -*-
import math
import numpy as np

import inkex

from Path import Path
from Pattern import Pattern

# TODO:
# Add fractional column number option


class Waterbomb(Pattern):
    
    def __init__(self):
        """ Constructor
        """
        Pattern.__init__(self)  # Must be called in order to parse common options

        self.add_argument('--pattern', type=self.str, default='waterbomb')
        self.add_argument('--pattern_first_line', type=self.str, default='waterbomb')
        self.add_argument('--pattern_last_line', type=self.str, default='waterbomb')
        self.add_argument('--lines', type=self.int, default=8)
        self.add_argument('--columns', type=self.int, default=16)
        self.add_argument('--length', type=self.float, default=10.0)
        self.add_argument('--phase_shift', type=self.bool, default=True)
    
    def generate_path_tree(self):
        """ Specialized path generation for Waterbomb tesselation pattern
        """
        unit_factor = self.calc_unit_factor()
        length = self.options.length * unit_factor
        vertex_radius = self.options.vertex_radius * unit_factor
        cols = self.options.columns
        lines = self.options.lines
        phase_shift = self.options.phase_shift
        pattern_first_line = self.options.pattern_first_line
        pattern_last_line = self.options.pattern_last_line

        # create vertices
        vertex_line_types = [[Path(((i / 2.) * length, 0), style='p', radius=vertex_radius) for i in range(2*cols + 1)],
                             [Path((i * length, 0), style='p', radius=vertex_radius) for i in range(cols + 1)],
                             [Path(((i + 0.5) * length, 0), style='p', radius=vertex_radius) for i in range(cols)]]

        vertices = []
        for i in range(2*lines + 1):
            if i % 2 == 0 or (pattern_first_line == 'magic_ball' and i == 1) or (pattern_last_line == 'magic_ball' and i == 2*lines - 1):
                type = 0
            elif(int(i/2 + phase_shift)) % 2 == 0:
                type = 1
            else:
                type = 2
            vertices = vertices + Path.list_add(vertex_line_types[type], (0, 0.5*i*length))

        # create a list for the horizontal creases and another for the vertical creases
        # alternate strokes to minimize laser cutter path
        corr_fist_line = length/2 if pattern_first_line == 'magic_ball' else 0
        corr_last_line = length/2 if pattern_last_line == 'magic_ball' else 0
        grid = [Path.generate_hgrid([0, length*cols],    [0,      length*lines],  lines, 'm'),
                Path.generate_vgrid([0, length*cols], [corr_fist_line, length*lines-corr_last_line], 2*cols, 'm')]

        vgrid_a = Path.generate_vgrid([0, length * cols], [0, length / 2], 2 * cols, 'v')
        vgrid_b = Path.list_add(vgrid_a, (0, (lines - 0.5) * length))
        if pattern_first_line == 'magic_ball' and pattern_last_line == 'magic_ball':
            grid[1] = [[vgrid_a[i], grid[1][i], vgrid_b[i]] if i % 2 == 0 else
                       [vgrid_b[i], grid[1][i], vgrid_a[i]] for i in range(len(grid[1]))]
        elif pattern_first_line == 'magic_ball':
            grid[1] = [[vgrid_a[i], grid[1][i]] if i % 2 == 0 else
                       [grid[1][i], vgrid_a[i]] for i in range(len(grid[1]))]
        elif pattern_last_line == 'magic_ball':
            grid[1] = [[grid[1][i], vgrid_b[i]] if i % 2 == 0 else
                       [vgrid_b[i], grid[1][i]] for i in range(len(grid[1]))]

        # create generic valley Path lines, one pointing up and other pointing down
        valley_types = [Path([(i * length / 2, (1 - i % 2) * length / 2) for i in range(2 * cols + 1)], 'v'),
                        Path([(    i*length/2,         (i % 2)*length/2) for i in range(2 * cols + 1)], 'v')]

        # define which lines must be of which type, according to parity and options
        senses = np.array([bool((i % 2+i)/2 % 2) for i in range(2*lines)])
        senses = 1*senses # converts bool array to 0's and 1's
        if phase_shift:
            senses = np.invert(senses)
        if pattern_first_line == "magic_ball":
            senses[0] = ~senses[0]
        if pattern_last_line == "magic_ball":
            senses[-1] = ~senses[-1]
        valleys = [valley_types[senses[i]] + (0, i * length / 2) for i in range(2*lines)]

        # convert first and last lines to mountains if magic_ball
        if pattern_first_line == "magic_ball":
            valleys[0].style = 'm'
        if pattern_last_line == "magic_ball":
            valleys[-1].style = 'm'

        # invert every two lines to minimize laser cutter movements
        for i in range(1, 2*lines, 2):
            valleys[i].invert()

        self.edge_points = [(0*length*cols, 0*length*lines),   # top left
                       (1*length*cols, 0*length*lines),   # top right
                       (1*length*cols, 1*length*lines),   # bottom right
                       (0*length*cols, 1*length*lines)]  # bottom left
        
        self.path_tree = [grid, valleys, vertices]


if __name__ == '__main__':

    e = Waterbomb()
    e.draw()

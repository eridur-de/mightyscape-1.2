#! /usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
from math import pi

import inkex
import math
from Path import Path
from Boxes_Masu import MasuBox
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
    

class MasuBoxSquare(MasuBox):

    def __init__(self):
        """ Constructor
        """
        MasuBox.__init__(self)  # Must be called in order to parse common options

        # save all custom parameters defined on .inx file
        self.add_argument('--length', type=self.float, default=10.0)

    def generate_path_tree(self):
        """ Specialized path generation for your origami pattern
        """
        # retrieve saved parameters, and apply unit factor where needed
        self.options.width = self.options.length / (2 * math.sqrt(2))
        self.options.height = self.options.width/2
        self.options.width_delta = 0.0
        self.options.width_delta_bool = False
        MasuBox.generate_path_tree(self)


# Main function, creates an instance of the Class and calls self.draw() to draw the origami on inkscape
# self.draw() is either a call to inkex.affect() or to svg.run(), depending on python version
if __name__ == '__main__':
    e = MasuBoxSquare()  # remember to put the name of your Class here!
    e.draw()

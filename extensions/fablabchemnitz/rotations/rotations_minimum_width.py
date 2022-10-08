#! /usr/bin/env python3
'''
Copyright (C) 2019 Grant Patterson <grant@revoltlabs.co>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

import gettext
import sys
import inkex
import rotate_helper
from inkex import Transform

debug = False

error = lambda msg: inkex.errormsg(gettext.gettext(msg))
if debug:
    stderr = lambda msg: sys.stderr.write(msg + '\n')
else:
    stderr = lambda msg: None

class RotationsMinimumWidth(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--precision", type=int, default=3, help="Precision")
    
    def effect(self):
        for node in self.svg.selected.values():
            min_width_angle = rotate_helper.optimal_rotations(node, self.options.precision)[0]
            if min_width_angle is not None:
                node.transform = rotate_helper.rotate_matrix(node, min_width_angle) @ node.transform

if __name__ == '__main__':
    RotationsMinimumWidth().run()
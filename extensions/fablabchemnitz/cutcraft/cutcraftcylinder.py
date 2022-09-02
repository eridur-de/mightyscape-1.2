#!/usr/bin/env python3

import inkex
from cutcraftshape import CutCraftShape
import cutcraft.platforms as cp
from cutcraft.shapes import Cylinder

class CutCraftCylinder(CutCraftShape):
    def __init__(self):
        CutCraftShape.__init__(self)
        self.arg_parser.add_argument("--vertices", type=int, default=3, help="Number of vertices")
        self.arg_parser.add_argument("--levels", type=int, default=3, help="Number of levels")
        self.arg_parser.add_argument("--supports", type=int, default=3, help="Number of supports")
        self.arg_parser.add_argument("--supwidth", type=float, default=6.0, help="Support Width")
        self.arg_parser.add_argument("--height", type=float, default=60.0, help="Cylinder height")
        self.arg_parser.add_argument("--outer", type=float, default=60.0, help="Diameter of cylinder")
        self.arg_parser.add_argument("--inner", type=float, default=30.0, help="Diameter of central hole - 0.0 for no hole")

    def effect(self):
        CutCraftShape.effect(self)

        vertices = self.options.vertices
        levels = self.options.levels
        supports = self.options.supports
        supwidth = self.svg.unittouu( str(self.options.supwidth) + self.unit )
        height = self.svg.unittouu( str(self.options.height) + self.unit )
        outer = self.svg.unittouu( str(self.options.outer) + self.unit )
        inner = self.svg.unittouu( str(self.options.inner) + self.unit )

        if outer<=inner:
            self._error("ERROR: Outer diameter must be greater than inner diameter.")
            exit()

        shape = Cylinder(height, outer/2.0, inner/2.0, vertices, supports, supwidth/2.0, supwidth, levels,
                         self.thickness, self.kerf)

        self.pack(shape)

if __name__ == '__main__':
    CutCraftCylinder().run()
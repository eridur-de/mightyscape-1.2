#!/usr/bin/env python3

import inkex
from cutcraftshape import CutCraftShape
import cutcraft.platforms as cp
from cutcraft.shapes import RollerBot

class CutCraftRollerBot(CutCraftShape):
    def __init__(self):
        CutCraftShape.__init__(self)
        self.arg_parser.add_argument("--supwidth", type=float, default=6.0, help="Support Width")

    def effect(self):
        CutCraftShape.effect(self)

        supwidth = self.svg.unittouu( str(self.options.supwidth) + self.unit )

        # Constants in the current RollerBot design.
        wheelradius = self.svg.unittouu( str(100.0) + "mm" )
        upperradius = self.svg.unittouu( str(92.0) + "mm" )
        lowerradius = self.svg.unittouu( str(82.0) + "mm" )
        facesize = self.svg.unittouu( str(50.0) + "mm" )
        barsize = self.svg.unittouu( str(25.4) + "mm" )
        scale = self.svg.unittouu( str(1.0) + "mm" )

        primarygapwidth = self.svg.unittouu( str(70.0) + "mm" ) # Must be greater than width of Raspberry PI / Arduino.
        secondarygapwidth = self.svg.unittouu( str(25.0) + "mm" )
        width = primarygapwidth*2.0 + secondarygapwidth*2.0 + self.thickness*5.0

        shape = RollerBot(width, supwidth, wheelradius, upperradius, lowerradius,
                          facesize, barsize, primarygapwidth, secondarygapwidth, scale,
                          self.thickness, self.kerf)

        self.pack(shape)

if __name__ == '__main__':
    CutCraftRollerBot().run()
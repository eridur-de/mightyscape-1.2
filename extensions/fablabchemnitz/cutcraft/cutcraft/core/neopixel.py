# Copyright (C) 2018 Michael Matthews
#
#   This file is part of CutCraft.
#
#   CutCraft is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   CutCraft is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with CutCraft.  If not, see <http://www.gnu.org/licenses/>.

from .point import Point
from .trace import Trace
from .part import Part
from math import pi, sin, cos, sqrt

class NeoPixel(Part):
    rings = [[1, 0.0], [6, 16.0/2.0], [12, 30.0/2.0]]
    size = 5.5

    """ Line class defined by start and end Points. """
    def __init__(self, style='rings', origin=Point(0.0, 0.0), scale=1.0, rotate=0.0):
        super(NeoPixel, self).__init__()
        self.scale = scale

        if style=='rings':
            for ring in self.rings:
                pixels = ring[0]
                radius = ring[1] * self.scale
                for pixel in range(pixels):
                    a = rotate + pi*2 * pixel / pixels
                    seg = self._pixel(origin + Point(sin(a) * radius, cos(a) * radius),
                                      pi/4 + a)
                    self += seg
        elif style=='strip':
            xo = origin.x
            yo = origin.y
            xsize = 25.4*2.0*self.scale
            size = self.size*self.scale
            seg = Trace() + \
                  Point(xo-xsize/2.0, yo+size/2.0) + \
                  Point(xo-xsize/2.0, yo-size/2.0) + \
                  Point(xo+xsize/2.0, yo-size/2.0) + \
                  Point(xo+xsize/2.0, yo+size/2.0)
            seg.close()
            self += seg
        return

    def _pixel(self, position, rotation):
        seg = Trace()
        xo = position.x
        yo = position.y
        size = sqrt(2.0*(self.size*self.scale)**2)
        for corner in range(4):
            # Points added in counterclockwise direction as this is an inner cut.
            a = rotation-2.0*pi*corner/4.0
            seg += Point(xo + sin(a) * size/2.0, yo + cos(a) * size/2.0)
        seg.close()
        return seg

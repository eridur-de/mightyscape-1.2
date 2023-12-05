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

from math import ceil, floor
from .point import Point

class Rectangle(object):
    """ Rectangle class defined by top-left and bottom-right Points. """
    def __init__(self, point1, point2):
        # Correct the input points in case they are not topleft, bottomright as expected.
        self.topleft = Point(min(point1.x, point2.x), min(point1.y, point2.y))
        self.bottomright = Point(max(point1.x, point2.x), max(point1.y, point2.y))
        return

    def size(self):
        # Calculate the size as: width, height.
        return self.bottomright.x-self.topleft.x, self.bottomright.y-self.topleft.y

    def area(self):
        width, height = self.size()
        return width*height

    def expanded(self):
        # Expand the current Rectangle out to integer boundary.
        return Rectangle(Point(floor(self.topleft.x), floor(self.topleft.y)),
                         Point(ceil(self.bottomright.x), ceil(self.bottomright.y)))

    def svg(self):
        # Generate SVG string for this rectangle.
        ptx = [self.topleft.x, self.bottomright.x, self.bottomright.x, self.topleft.x]
        pty = [self.topleft.y, self.topleft.y, self.bottomright.y, self.bottomright.y]
        return "M {} {} ".format(ptx[0], pty[0]) + \
               " ".join(["L {} {}".format(x, y) for x, y in zip(ptx[1:], pty[1:])]) + \
               " L {} {}".format(ptx[0], pty[0])

    def __eq__(self, other):
        return (self.topleft == other.topleft and self.bottomright == other.bottomright )

    def __ne__(self, other):
        return (self.topleft != other.topleft or self.bottomright != other.bottomright)

    def __repr__(self):
        return "Rectangle(" + repr(self.topleft) + ", " + repr(self.bottomright) + ")"

    def __str__(self):
        return "(" + str(self.topleft) + ", " + str(self.bottomright) + ")"

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
from math import sqrt

def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
     # Required as Inkscape does not include math.isclose().
     return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

class Line(object):
    """ Line class defined by start and end Points. """
    def __init__(self, point1, point2):
        self.pts = (point1, point2)
        self.x = [point1.x, point2.x]
        self.y = [point1.y, point2.y]
        return

    def _line(self):
        # Convert line segment into a line equation (infinite length).
        p1 = self.pts[0]
        p2 = self.pts[1]
        A = (p1.y - p2.y)
        B = (p2.x - p1.x)
        C = (p1.x*p2.y - p2.x*p1.y)
        return A, B, -C

    def intersection(self, other):
        # Find the intersection of the lines (infinite length - not segments)
        L1 = self._line()
        L2 = other._line()
        D  = L1[0] * L2[1] - L1[1] * L2[0]
        Dx = L1[2] * L2[1] - L1[1] * L2[2]
        Dy = L1[0] * L2[2] - L1[2] * L2[0]
        if D != 0:
            x = Dx / D
            y = Dy / D
            return Point(x, y)
        else:
            return None

    def normal(self):
        # Return the unit normal
        dx = self.x[1] - self.x[0]
        dy = self.y[1] - self.y[0]

        d = sqrt(dx*dx + dy*dy)
        if d == 0:
            raise ValueError("cutcraft.line: parameter 'normal' could not be calculated. Check your entered parameters.")
        return dx/d, -dy/d

    def addkerf(self, kerf):
        nx, ny = self.normal()
        offset = Point(ny*kerf, nx*kerf)
        self.pts = (self.pts[0] + offset, self.pts[1] + offset)
        self.x = [self.pts[0].x, self.pts[1].x]
        self.y = [self.pts[0].y, self.pts[1].y]

    def __eq__(self, other):
        return (self.pts == other.pts)

    def __ne__(self, other):
        return (self.pts != other.pts)

    def __repr__(self):
        return "Line(" + repr(self.pts[0]) + ", " + repr(self.pts[1]) + ")"

    def __str__(self):
        return "(" + str(self.pts[0]) + ", " + str(self.pts[1]) + ")"

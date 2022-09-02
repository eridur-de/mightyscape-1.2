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

from math import pi, atan2, cos, sin, sqrt

def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    # Required as Inkscape uses old version of Python that does not include math.isclose().
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

def iscloselist(a, b):
    # Functionality of isclose() for lists of values.
    return all([isclose(aval, bval) for aval, bval in zip(a, b)])

def intersection(radius, angle=None, x=None, y=None):
    # With a circle of a given radius determine the intercepts for an angle, x or y coordinate.
    if angle:
        # Returns (x,y) tuple of intercept.
        return (cos(angle)*radius, sin(angle)*radius)
    elif x:
        y = sqrt((radius)**2 - x**2)
        return (y, atan2(y, x))
    elif y:
        x = sqrt((radius)**2 - y**2)
        return (x, atan2(y, x))
    else:
        raise ValueError("Invalid values passed to intersection().")

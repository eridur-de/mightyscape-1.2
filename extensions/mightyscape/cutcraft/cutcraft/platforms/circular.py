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

from ..core.point import Point
from ..core.part import Part
from ..core.circle import Circle
from .platform import Platform
from math import pi

class Circular(Platform):
    """ Circular Platform. """
    def __init__(self, radius, inradius, segments, cuts, cutdepth, start=0.0, end=pi*2, rotation=0.0,
                 origin=Point(0.0, 0.0), thickness=0.0):
        super(Circular, self).__init__(thickness)
        self.radius = radius
        self.inradius = inradius
        self.segments = segments
        outer = Circle(self.radius, segments, cuts, cutdepth=cutdepth, start=start, end=end,
                       rotation=rotation, origin=origin, thickness=thickness)
        outer.close()
        inner = Circle(self.inradius, segments, 0, start=start, end=end,
                       rotation=rotation, origin=origin, thickness=thickness)
        inner.close()
        self.traces.append(outer)
        self.traces.append(reversed(inner))

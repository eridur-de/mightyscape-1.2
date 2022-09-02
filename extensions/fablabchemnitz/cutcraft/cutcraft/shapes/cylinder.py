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

from ..core.part import Part
from ..platforms.circular import Circular
from ..supports.pier import Pier
from .shape import Shape

class Cylinder(Shape):
    """ List of segments that make up a part. """
    def __init__(self, height, radius, inradius, segments, cuts, cutdepth, supwidth, platforms,
                 thickness, kerf):
        super(Cylinder, self).__init__(thickness, kerf)

        self.platforms = []
        self.piers = []

        # List of vertical positions for the platforms
        levels = [float(p)/float(platforms-1)*(height-thickness) for p in range(platforms)]

        for level in levels:
            p = Circular(radius, inradius, segments, cuts, cutdepth, thickness=thickness)
            self.platforms.append((p, level))
            self.parts.append((p, level))

        for _ in range(cuts):
            p = Pier(height, supwidth, supwidth-cutdepth, [(level, 0.0) for level in levels], thickness=thickness)
            self.piers.append((p, None))
            self.parts.append((p, None))

        if kerf:
            for part, _ in self.parts:
                part.applykerf(kerf)

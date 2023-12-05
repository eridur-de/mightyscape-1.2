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
from .shape import Shape

class Cone(Shape):
    """ List of segments that make up a part. """
    def __init__(self, height, radius1, radius2, segments, cuts, cutdepth, platforms,
                 thickness, kerf):
        super(Cone, self).__init__(thickness, kerf)

#        levels = [p/(platforms-1)*height for p in range(platforms)]
#        radii = [radius1 + (radius2-radius1)*p/(platforms-1) for p in range(platforms)]

#        for level, radius in zip(levels, radii):
#            p = cc.Part()
#            p += cp.Circular(radius, segments, cuts, cutdepth, thickness=thickness, kerf=kerf).part
#            self.parts.append((p, level))

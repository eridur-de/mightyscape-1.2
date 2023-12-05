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
from ..platforms.rollerframe import RollerFrame
from ..supports.pier import Pier
from .shape import Shape

class RollerBot(Shape):
    """ List of segments that make up a part. """
    def __init__(self, width, supwidth, wheelradius, upperradius, lowerradius,
                 facesize, barsize, primarygapwidth, secondarygapwidth, scale,
                 thickness, kerf):
        super(RollerBot, self).__init__(thickness, kerf)

        self.platforms = []
        self.piers = []

        cutdepth = supwidth / 3.0

        for level in range(9):
#        for level in range(7):
            p = RollerFrame(supwidth, wheelradius, upperradius, lowerradius,
                            facesize, barsize, primarygapwidth, secondarygapwidth,
                            scale, level, thickness=thickness)
            self.platforms.append((p, 0.0))
            self.parts.append((p, 0.0))

        levels = [0.0, secondarygapwidth+thickness,
                secondarygapwidth+primarygapwidth+thickness*2.0,
                secondarygapwidth+primarygapwidth*2.0+thickness*3.0,
                secondarygapwidth*2.0+primarygapwidth*2.0+thickness*4.0 ]
        height = secondarygapwidth*2.0+primarygapwidth*2.0+thickness*5.0

        for _ in range(9):
            p = Pier(height, supwidth, supwidth-cutdepth, [(level, 0.0) for level in levels], thickness=thickness)
            self.piers.append((p, None))
            self.parts.append((p, None))

        levels = [0.0, secondarygapwidth+thickness ]
        height = secondarygapwidth+thickness*2.0

        for _ in range(4):
            p = Pier(height, supwidth, supwidth-cutdepth, [(level, 0.0) for level in levels], thickness=thickness)
            self.piers.append((p, None))
            self.parts.append((p, None))

        if kerf:
            for part, _ in self.parts:
                part.applykerf(kerf)

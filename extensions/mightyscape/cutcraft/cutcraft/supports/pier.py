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

from ..core.trace import Trace
from .support import Support
from ..util import isclose

class Pier(Support):
    """ List of segments that make up a part. """
    def __init__(self, height, depth, cutdepth, levels, thickness):
        super(Pier, self).__init__(height, thickness)

        self.depth = depth
        self.cutdepth = cutdepth

        # The 'levels' list is defined as follows:
        # [(height1, x-offset1), (height2, x-offset2), ...]
        # where the values are:
        #   height<n>: The height of the bottom of the platform (0.0=at base level, height-thickness=at top level).
        #   x-offset<n>: The distance from the core axis for this level.  Used to create slopes and curves.

        ys, xs = zip(*sorted(levels))
        if any([(h2) - (h1) < 3*thickness for h1, h2
                in zip(ys[:-1], ys[1:])]):
            raise RuntimeError("Pier levels are too close.  Try decreasing the number of levels.")

        self.topcut = isclose(ys[-1], height-thickness)
        self.bottomcut = isclose(ys[0], 0.0)
        self.vertical = all([isclose(x1, x2) for x1, x2 in zip(xs[:-1], xs[1:])])

        # Starting at the bottom inner point, trace up the uncut side.
        if self.vertical:
            tx = [0.0, 0.0]
            ty = [0.0, height]
        else:
            tx = list(xs)
            ty = list(ys[:-1]) + [height]

        # Add the top points.
        xtop = xs[0]
        xbottom = xs[-1]
        if self.topcut:
            tx.extend([xtop+depth-cutdepth, xtop+depth-cutdepth, xtop+depth])
            ty.extend([height, height-thickness, height-thickness])
        else:
            tx.extend([xtop+depth])
            ty.extend([height])

        if self.topcut and self.bottomcut:
            xs = xs[1:-1]
            ys = ys[1:-1]
        elif self.topcut:
            xs = xs[:-1]
            ys = ys[:-1]
        elif self.bottomcut:
            xs = xs[1:]
            ys = ys[1:]

        for y, x in zip(reversed(ys), reversed(xs)):
            tx.extend([x+depth, x+depth-cutdepth, x+depth-cutdepth, x+depth])
            ty.extend([y+thickness, y+thickness, y, y])

        if self.bottomcut:
            tx.extend([xbottom+depth, xbottom+depth-cutdepth, xbottom+depth-cutdepth, xbottom])
            ty.extend([thickness, thickness, 0.0, 0.0])
        else:
            tx.extend([xbottom+depth, xbottom])
            ty.extend([0.0, 0.0])

        self.traces.append(Trace(x=tx, y=ty))

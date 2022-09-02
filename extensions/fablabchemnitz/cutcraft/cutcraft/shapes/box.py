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
from ..core.point import Point
from ..core.trace import Trace
from ..core.fingerjoint import FingerJoint
from .shape import Shape

class Box(Shape):
    """ List of segments that make up a part. """
    def __init__(self, width, depth, height, thickness, kerf, top=True, bottom=True,
                       left=True, right=True, front=True, back=True):
        super(Box, self).__init__(thickness, kerf)

        self.width = width
        self.depth = depth
        self.height = height

        self.faces = []
        self.parts = []

        for face in range(6):
            p = self._face(face, width, depth, height, thickness, top, bottom, left, right, front, back)
            self.faces.append((p, face))
            self.parts.append((p, face))

        if kerf:
            for part, _ in self.parts:
                part.applykerf(kerf)

    def _face(self, face, width, depth, height, thickness, top, bottom, left, right, front, back):
        faces = (top, bottom, left, right, front, back)

        # Check if the requested face is active for this box.
        if faces[face] == False:
            return None

        wjoint = FingerJoint(width, thickness*2.0, 'width', thickness=thickness)
        djoint = FingerJoint(depth, thickness*2.0, 'depth', thickness=thickness)
        hjoint = FingerJoint(height, thickness*2.0, 'height', thickness=thickness)

        if face in (0, 1):
            t = Trace(x=[thickness], y=[thickness])
            for i, pos in enumerate(djoint.fingers[1:-1]):
                if i%2==0:
                    t += Point(pos, thickness)
                    t += Point(pos, 0.0)
                else:
                    t += Point(pos, 0.0)
                    t += Point(pos, thickness)
            t += Point(depth-thickness, thickness)
            for i, pos in enumerate(wjoint.fingers[1:-1]):
                if i%2==0:
                    t += Point(depth-thickness, pos)
                    t += Point(depth, pos)
                else:
                    t += Point(depth, pos)
                    t += Point(depth-thickness, pos)
            t += Point(depth-thickness, width-thickness)
            for i, pos in enumerate(reversed(djoint.fingers[1:-1])):
                if i%2==0:
                    t += Point(pos, width-thickness)
                    t += Point(pos, width)
                else:
                    t += Point(pos, width)
                    t += Point(pos, width-thickness)
            t += Point(thickness, width-thickness)
            for i, pos in enumerate(reversed(wjoint.fingers[1:-1])):
                if i%2==0:
                    t += Point(thickness, pos)
                    t += Point(0.0, pos)
                else:
                    t += Point(0.0, pos)
                    t += Point(thickness, pos)
        elif face in (2, 3):
            t = Trace(x=[0.0], y=[0.0])
            for i, pos in enumerate(djoint.fingers[1:-1]):
                if i%2==0:
                    t += Point(pos, 0.0)
                    t += Point(pos, thickness)
                else:
                    t += Point(pos, thickness)
                    t += Point(pos, 0.0)
            t += Point(depth, 0.0)
            for i, pos in enumerate(hjoint.fingers[1:-1]):
                if i%2==0:
                    t += Point(depth, pos)
                    t += Point(depth-thickness, pos)
                else:
                    t += Point(depth-thickness, pos)
                    t += Point(depth, pos)
            t += Point(depth, height)
            for i, pos in enumerate(reversed(djoint.fingers[1:-1])):
                if i%2==0:
                    t += Point(pos, height)
                    t += Point(pos, height-thickness)
                else:
                    t += Point(pos, height-thickness)
                    t += Point(pos, height)
            t += Point(0.0, height)
            for i, pos in enumerate(reversed(hjoint.fingers[1:-1])):
                if i%2==0:
                    t += Point(0.0, pos)
                    t += Point(thickness, pos)
                else:
                    t += Point(thickness, pos)
                    t += Point(0.0, pos)
            pass
        elif face in (4, 5):
            t = Trace(x=[thickness], y=[0.0])
            for i, pos in enumerate(wjoint.fingers[1:-1]):
                if i%2==0:
                    t += Point(pos, 0.0)
                    t += Point(pos, thickness)
                else:
                    t += Point(pos, thickness)
                    t += Point(pos, 0.0)
            t += Point(width-thickness, 0.0)
            for i, pos in enumerate(hjoint.fingers[1:-1]):
                if i%2==0:
                    t += Point(width-thickness, pos)
                    t += Point(width, pos)
                else:
                    t += Point(width, pos)
                    t += Point(width-thickness, pos)
            t += Point(width-thickness, height)
            for i, pos in enumerate(reversed(wjoint.fingers[1:-1])):
                if i%2==0:
                    t += Point(pos, height)
                    t += Point(pos, height-thickness)
                else:
                    t += Point(pos, height-thickness)
                    t += Point(pos, height)
            t += Point(thickness, height)
            for i, pos in enumerate(reversed(hjoint.fingers[1:-1])):
                if i%2==0:
                    t += Point(thickness, pos)
                    t += Point(0.0, pos)
                else:
                    t += Point(0.0, pos)
                    t += Point(thickness, pos)
            pass

        t.close()

        return Part() + t

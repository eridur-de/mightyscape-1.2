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
from .line import Line
from .trace import Trace
from ..util import isclose
from math import pi, sin, cos, asin

class Circle(Trace):
    def __init__(self, radius, segments, cuts, cutdepth=0.0, start=0.0, end=pi*2.0, rotation=0.0,
                 origin=Point(0.0, 0.0), thickness=0.0, kerf=0.0):
        super(Circle, self).__init__()
        self.thickness = thickness
        self.kerf = kerf

        partial = True if start != 0.0 or end != pi*2.0 else False

        if cuts==0:
            c = 0.0
        else:
            if self.thickness <= 0.0:
                raise ValueError("cutcraft.circle: parameter 'thickness' not set when 'cuts' greater than zero.")
            if cutdepth <= 0.0:
                raise ValueError("cutcraft.circle: parameter 'cutdepth' not set when 'cuts' greater than zero.")
            c = asin(self.thickness/2/radius)
        if partial:
            angles = [[rotation+start+(end-start)/segments*seg, 'SEG'] for seg in range(segments+1)] + \
                     [[rotation+start+(end-start)/(cuts+1)*cut-c, '<CUT'] for cut in range(1, cuts+1)] + \
                     [[rotation+start+(end-start)/(cuts+1)*cut+c, 'CUT>'] for cut in range(1, cuts+1)]
        else:
            angles = [[rotation+end/segments*seg, 'SEG'] for seg in range(segments)] + \
                     [[rotation+end/cuts*cut-c, '<CUT'] for cut in range(cuts)] + \
                     [[rotation+end/cuts*cut+c, 'CUT>'] for cut in range(cuts)]
        angles = sorted(angles)
        if angles[0][1] == 'CUT>':
            angles = angles[1:] + [angles[0]]

        for i, angle in enumerate(angles):
            angle.append(self._cnext(angles, i, 'SEG'))
            angle.append(self._cprev(angles, i, 'SEG'))
            angle.append(self._cnext(angles, i, 'CUT>') if angle[1]=='<CUT' else None)
            angle.append(self._cprev(angles, i, '<CUT') if angle[1]=='CUT>' else None)

        for i, angle in enumerate(angles):
            if angle[1] == 'SEG':
                angle.append([self._pos(angle[0], radius)])

        for i, angle in enumerate(angles):
            if angle[1] != 'SEG':
                mult = -1 if angle[1] == '<CUT' else 1
                a = angle[0] - mult*c
                a2 = a + mult*pi/2
                # Line from previous to next segment point.
                line1 = Line(angles[angle[2]][6][0], angles[angle[3]][6][0])
                # Line from origin offset by thickness.
                p1 = self._pos(a2, self.thickness/2)
                p2 = p1 + self._pos(a, radius)
                line2 = Line(p1, p2)
                pintersect = line1.intersection(line2)
                pinset = pintersect + self._pos(a, -cutdepth)
                if angle[1] == '<CUT':
                    angle.append([pintersect, pinset])
                else:
                    angle.append([pinset, pintersect])
                    d1 = pinset.distance(Point(0.0,0.0))
                    d2 = angles[angle[5]][6][1].distance(Point(0.0,0.0))

                    if d1<d2:
                        angles[angle[5]][6][1] = pinset - self._pos(a2, self.thickness)
                    elif d2<d1:
                        angle[6][0] = angles[angle[5]][6][1] + self._pos(a2, self.thickness)
                        pass

        incut = False
        for i, angle in enumerate(angles):
            atype = angle[1]

            if atype=='<CUT':
                incut = True
            elif atype=='CUT>':
                incut = False

            if atype != 'SEG' or (atype == 'SEG' and not incut):
                for pos in angle[6]:
                    x = origin.x + pos.x
                    y = origin.y + pos.y
                    if len(self.x)==0 or not (isclose(x, self.x[-1]) and isclose(y, self.y[-1])):
                        self.x.append(x)
                        self.y.append(y)

        return

    def _cnext(self, angles, i, item):
        if i>=len(angles):
            i=-1
        for j, angle in enumerate(angles[i+1:]):
            if angle[1] == item:
                return i+1+j
        for j, angle in enumerate(angles):
            if angle[1] == item:
                return j
        return None

    def _cprev(self, angles, i, item):
        if i<=0:
            i=len(angles)
        for j, angle in enumerate(angles[:i][::-1]):
            if angle[1] == item:
                return i-j-1
        for j, angle in enumerate(angles[::-1]):
            if angle[1] == item:
                return j
        return None

    def _pos(self, angle, radius):
        return Point(sin(angle)*radius, cos(angle)*radius)

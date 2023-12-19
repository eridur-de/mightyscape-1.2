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

from math import floor

class FingerJoint(object):
    def __init__(self, length, fingerwidth, style, thickness=0.0):
        super(FingerJoint, self).__init__()

        self.thickness = thickness

        if style in ('depth','height'):
            self.fingers = [0.0] + \
                           [pos + fingerwidth*2.0 for pos in self._fingers(length-fingerwidth*4.0, fingerwidth)] + \
                           [length]
        elif style=='width':
            self.fingers = [pos + thickness for pos in self._fingers(length-thickness*2.0, fingerwidth)]
        else:
            raise ValueError("cutcraft.core.fingerjoin: invalid value of '{}' for parameter 'style'.".format(style))

        return

    def _fingers(self, length, fingerwidth):
        count = int(floor(length / fingerwidth))
        count = count-1 if count%2==0 else count
        return [length/count*c for c in range(count+1)]

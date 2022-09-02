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

from copy import deepcopy
from .point import Point
from .rectangle import Rectangle
from .trace import Trace

class Part(object):
    """ List of traces that make up a part. """
    def __init__(self):
        self.traces = []
        return

    def close(self):
        """ Close each traces back to their start. """
        for trace in self.traces:
            trace.close()
        return

    def applykerf(self, kerf):
        """ Apply an offset to allow for the kerf when cutting. """
        for trace in self.traces:
            trace.applykerf(kerf)
        return

    def svg(self):
        # Generate SVG string for this part.
        return " ".join([trace.svg() for trace in self.traces])

    def bbox(self):
        bboxes = [trace.bbox() for trace in self.traces]
        x = [p1.x for p1, p2 in bboxes] + [p2.x for p1, p2 in bboxes]
        y = [p1.y for p1, p2 in bboxes] + [p2.y for p1, p2 in bboxes]
        return Rectangle(Point(min(x), min(y)), Point(max(x), max(y)))

    def area(self):
        bbox = self.bbox()
        return bbox.area()

    def size(self):
        bbox = self.bbox()
        return bbox.size()

    def __add__(self, other):
        p = Part()
        if isinstance(other, Part):
            p.traces = self.traces + deepcopy(other.traces)
        elif isinstance(other, Trace):
            p.traces = deepcopy(self.traces)
            p.traces.append(other)
        elif isinstance(other, Point):
            p.traces = self.traces
            for trace in p.traces:
                trace.offset(other)
        else:
            raise RuntimeError("Can only add a Part, Trace or Point to an existing Part.")
        return p

    def __iadd__(self, other):
        if isinstance(other, Part):
            self.traces.extend(other.traces)
        elif isinstance(other, Trace):
            self.traces.append(deepcopy(other))
        elif isinstance(other, Point):
            for trace in self.traces:
                trace.offset(other)
        else:
            raise RuntimeError("Can only add a Part, Trace or Point to an existing Part.")
        return self

    def __repr__(self):
        return "Part" + str(self)

    def __str__(self):
        l = len(self.traces)
        return "(" + str(l) + " trace" + ("s" if l>1 else "") + ")"

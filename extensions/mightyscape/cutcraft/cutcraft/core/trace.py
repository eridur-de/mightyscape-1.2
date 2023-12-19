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
from ..util import isclose, iscloselist

class Trace(object):
    """ List of coordinates that make a boundary. """
    def __init__(self, x=None, y=None):
        self.x = [] if x is None else x
        self.y = [] if y is None else y
        self.closed = False
        return

    def close(self):
        """ Close the trace back to the start. """
        if not self.closed:
            if isclose(self.x[0], self.x[-1]) and isclose(self.y[0], self.y[-1]):
                # Start and end should be the same.
                self.x[-1] = self.x[0]
                self.y[-1] = self.y[0]
            else:
                # Add new end point to close the loop.
                self.x.append(self.x[0])
                self.y.append(self.y[0])
            self.closed = True
        return

    def applykerf(self, kerf):
        """ Apply an offset to allow for the kerf when cutting. """
        self.close()

        # Convert the points to lines.
        lines = [Line(Point(x1, y1), Point(x2, y2)) for x1, y1, x2, y2 in
                 zip(self.x[:-1], self.y[:-1], self.x[1:], self.y[1:])]

        # Add the kerf to the lines.
        for line in lines:
            line.addkerf(kerf)

        # Extract the line intersections as the new points.
        pts = [line1.intersection(line2) for line1, line2 in zip(lines, lines[-1:] + lines[:-1])]
        self.clear()
        self.x += [pt.x for pt in pts]
        self.y += [pt.y for pt in pts]
        self.x += self.x[:1]
        self.y += self.y[:1]
        return

    def offset(self, pt):
        """ Move a trace by an x/y offset. """
        self.x = [x + pt.x for x in self.x]
        self.y = [y + pt.y for y in self.y]

    def clear(self):
        self.x = []
        self.y = []

    def svg(self):
        # Generate SVG string for this trace.
        if len(self.x)<2:
            return ""
        return "M {} {} ".format(self.x[0], self.y[0]) + \
               " ".join(["L {} {}".format(x, y) for x, y in zip(self.x[1:], self.y[1:])])

    def bbox(self):
        return Point(min(self.x), min(self.y)), Point(max(self.x), max(self.y))

    def __len__(self):
        return len(self.x)

    def __eq__(self, other):
        return (iscloselist(self.x,other.x) and iscloselist(self.y, other.y))

    def __ne__(self, other):
        return (not iscloselist(self.x, other.x) or not iscloselist(self.y, other.y))

    def __add__(self, other):
        new = Trace()
        if isinstance(other, Point):
            new.x = self.x + [other.x]
            new.y = self.y + [other.y]
        elif isinstance(other, Trace):
            new.x = self.x + other.x
            new.y = self.y + other.y
        else:
            raise RuntimeError("Can only add a Trace or Point to an existing Trace.")
        return new

    def __iadd__(self, other):
        if isinstance(other, Point):
            self.x.append(other.x)
            self.y.append(other.y)
        elif isinstance(other, Trace):
            self.x += other.x
            self.y += other.y
        else:
            raise RuntimeError("Can only add a Trace or Point to an existing Trace.")
        return self

    def __repr__(self):
        return "Trace(" + str(self.x) + ", " + str(self.y) + ")"

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"

    def __getitem__(self, key):
        """ Used to override the slice functionality (eg: reversing). """
        new = Trace()
        new.x = self.x[key]
        new.y = self.y[key]
        return new

    def __setitem__(self, key, value):
        """ Used to override the slice functionality. """
        if isinstance(value, Point):
            self.x[key] = value.x
            self.y[key] = value.y
        else:
            raise RuntimeError("Can only update a single item in an existing Trace.")
        return self

    def __delitem__(self, key):
        """ Used to override the slice functionality (eg: reversing). """
        del self.x[key]
        del self.y[key]
        return self

    def __reversed__(self):
        """ Used to override the slice functionality (eg: reversing). """
        new = Trace()
        new.x = list(reversed(self.x))
        new.y = list(reversed(self.y))
        return new

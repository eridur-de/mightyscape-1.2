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
from ..core.trace import Trace
from ..core.circle import Circle
from ..core.fingerjoint import FingerJoint
from ..core.neopixel import NeoPixel
from .platform import Platform
from ..util import intersection
from math import pi, sqrt, asin, atan

#import inkex

class RollerFrame(Platform):
    """ RollerBot Platform. """
    def __init__(self, supwidth, wheelradius, upperradius, lowerradius,
                 facesize, barsize, primarygapwidth, secondarygapwidth,
                 scale, part_id, thickness=0.0):
        super(RollerFrame, self).__init__(thickness)
        self.supwidth = supwidth
        self.barsize = barsize

        cutdepth = supwidth / 3.0
        barradius = sqrt(2.0*(barsize/2.0)**2)

        facewidth = primarygapwidth*2.0 + thickness*3.0
        faceheight = facesize + thickness
        fjoint = FingerJoint(faceheight, thickness*2.0, 'height', thickness=thickness)  # Face
        bjoint = FingerJoint(faceheight, thickness*2.0, 'depth', thickness=thickness)   # Base
        wjoint = FingerJoint(facewidth, thickness*2.0, 'width', thickness=thickness)    # Length

        if part_id<5:
            # The circular segments for the main body structure.

            # Outer section.
            x = barsize/2.0
            y = sqrt(lowerradius**2 - x**2)
            a = atan(x/y)
            outer = Circle(upperradius, 72, 5, cutdepth=cutdepth, start=0.0, end=pi, thickness=thickness) + \
                    Point(0.0, -upperradius + cutdepth) + \
                    Point(-thickness, -upperradius + cutdepth) + \
                    Point(-thickness, -upperradius) + \
                    Point(-barsize/2.0, -upperradius) + \
                    Circle(lowerradius, 72, 4, cutdepth=cutdepth, start=pi+a, end=pi*2-a, thickness=thickness) + \
                    Point(-barsize/2.0, upperradius) + \
                    Point(-thickness, upperradius) + \
                    Point(-thickness, upperradius - cutdepth) + \
                    Point(0.0, upperradius - cutdepth)
            outer.close()
            self.traces.append(outer)

            if part_id in (0,4):
                # Central Motor Position.
                inner = Trace() + \
                        Point(-barsize/2.0, -barsize/2.0) + \
                        Point(-barsize/2.0, barsize/2.0) + \
                        Point(-barsize/6.0, barsize/2.0) + \
                        Point(-barsize/6.0, barsize/2.0-thickness/2.0) + \
                        Point(barsize/6.0, barsize/2.0-thickness/2.0) + \
                        Point(barsize/6.0, barsize/2.0) + \
                        Point(barsize/2.0, barsize/2.0) + \
                        Point(barsize/2.0, -barsize/2.0) + \
                        Point(barsize/6.0, -barsize/2.0) + \
                        Point(barsize/6.0, -barsize/2.0+thickness/2.0) + \
                        Point(-barsize/6.0, -barsize/2.0+thickness/2.0) + \
                        Point(-barsize/6.0, -barsize/2.0)
                inner.close()
                self.traces.append(reversed(inner))

            # Outer parts are complete, inner parts have cutouts.
            if part_id in (1,2,3):
                # Central Motor Position and Bar.
                inner = Trace() + \
                        Point(-barsize/2.0*1.3, -barsize/2.0) + \
                        Point(-barsize/2.0*1.3, -barsize/2.0*0.55) + \
                        Point(-barsize/2.0, -barsize/2.0*0.55) + \
                        Point(-barsize/2.0, barsize/2.0*0.55) + \
                        Point(-barsize/2.0*1.3, barsize/2.0*0.55) + \
                        Point(-barsize/2.0*1.3, barsize/2.0) + \
                        Point(barsize/2.0, barsize/2.0) + \
                        Point(barsize/2.0, barsize/10.0) + \
                        Point(barsize/2.0*1.2, barsize/20.0) + \
                        Point(barsize/2.0*1.2, -barsize/20.0) + \
                        Point(barsize/2.0, -barsize/10.0) + \
                        Point(barsize/2.0, -barsize/2.0)
                inner.close()
                self.traces.append(reversed(inner))

                # Upper segment cut-outs.
                x = supwidth/2.0
                y = sqrt((upperradius-supwidth)**2 - x**2)
                a_outer = atan(x/y)
                y = sqrt((barradius+supwidth)**2 - x**2)
                a_inner = atan(x/y)

                inner = self._segment(upperradius-supwidth, barradius+supwidth,
                                      0, 1, cutdepth, 0.0, a_outer, a_inner)
                self.traces.append(reversed(inner))

                fa = (pi/2.0 - self._faceangle(facesize, upperradius)) / 2.0
                (fx, fy) = intersection(upperradius, angle=fa)
                if 0:
                    inner = Trace() + \
                            Point(fx, -fy) + \
                            Point(fy, -fy) + \
                            Point(fy, -fx)
                    inner.close()
                    self.traces.append(reversed(inner))

                oy = fy-thickness*2.0
                (ox, oa) = intersection(upperradius, y=oy)
                if 0:
                    inner = Trace() + \
                            Point(ox, -oy) + \
                            Point(oy, -oy) + \
                            Point(oy, -ox)
                    inner.close()
                    self.traces.append(reversed(inner))

                iy = oy
                (ix, ia) = intersection(upperradius-supwidth, y=iy)

                if part_id==2:
                    inner = Circle(upperradius-supwidth, 18, 0, cutdepth=cutdepth,
                                   start=pi/3+a_outer, end=pi-a_outer,
                                   thickness=self.thickness) + \
                            reversed(Circle(barradius+supwidth, 18, 0, cutdepth=cutdepth,
                                            start=pi/3+a_inner, end=pi-a_inner,
                                            thickness=self.thickness))
                    inner.close()
                    self.traces.append(reversed(inner))

                    # Temporary cut to remove where the face will be installed.
                    oy = fy-thickness
                    (ox, oa) = intersection(upperradius, y=oy)
                    inner = Trace() + \
                            Point(ox, -ox) + \
                            Point(oy, -ox) + \
                            Point(oy, -oy) + \
                            Point(ox, -oy)
                    inner.close()
                    self.traces.append(reversed(inner))

                else:
                    inner = Circle(upperradius-supwidth, 18, 0, cutdepth=cutdepth,
                                   start=pi/3*1+a_outer, end=pi/2+ia,
                                   thickness=self.thickness) + \
                            reversed(Circle(barradius+supwidth, 18, 0, cutdepth=cutdepth,
                                            start=pi/3*1+a_inner, end=pi/3*2-a_inner,
                                            thickness=self.thickness))
                    inner.close()
                    self.traces.append(reversed(inner))

                    ia = pi/2 - ia
                    (ix, iy) = intersection(upperradius-supwidth, angle=ia)

                    inner = Circle(upperradius-supwidth, 18, 0, cutdepth=cutdepth,
                                   start=pi/2+ia, end=pi/3*3-a_outer,
                                   thickness=self.thickness) + \
                            reversed(Circle(barradius+supwidth, 18, 0, cutdepth=cutdepth,
                                            start=pi/3*2+a_inner, end=pi/3*3-a_inner,
                                            thickness=self.thickness)) + \
                            Point(ix, -ix)
                    inner.close()
                    self.traces.append(reversed(inner))

                    # Face and base cutout slots.
                    cy = fy-thickness
                    for (x1, x2) in zip(fjoint.fingers[1::2],fjoint.fingers[2::2]):
                        inner = Trace() + \
                                Point(cy+x1, -cy) + \
                                Point(cy+x2, -cy) + \
                                Point(cy+x2, -cy-thickness) + \
                                Point(cy+x1, -cy-thickness)
                        inner.close()
                        self.traces.append(reversed(inner))
                    for (y1, y2) in zip(bjoint.fingers[1::2],bjoint.fingers[2::2]):
                        inner = Trace() + \
                                Point(cy, -cy-y2) + \
                                Point(cy, -cy-y1) + \
                                Point(cy+thickness, -cy-y1) + \
                                Point(cy+thickness, -cy-y2)
                        inner.close()
                        self.traces.append(reversed(inner))

                if 0:
                    if part_id==2:
                        for seg in range(2):
                            segnext = seg*2+1
                            inner = self._segment(upperradius-supwidth, barradius+supwidth,
                                                seg, segnext, cutdepth, 0.0, a_outer, a_inner)
                            self.traces.append(reversed(inner))
                    else:
                        for seg in range(3):
                            segnext = seg+1
                            inner = self._segment(upperradius-supwidth, barradius+supwidth,
                                                seg, segnext, cutdepth, 0.0, a_outer, a_inner)
                            self.traces.append(reversed(inner))

                # Lower segment cut-outs.
                x = supwidth/2.0
                y = sqrt((lowerradius-supwidth)**2 - x**2)
                a_outer = atan(x/y)
                y = sqrt((barradius+supwidth)**2 - x**2)
                a_inner = atan(x/y)

                for seg in range(3):
                    segnext = seg+1
                    inner = self._segment(lowerradius-supwidth, barradius+supwidth,
                                        seg, segnext, cutdepth, pi, a_outer, a_inner)
                    self.traces.append(reversed(inner))

            if part_id in (1,2,3):
                r_mid = barradius+supwidth + ((upperradius-supwidth) - (barradius+supwidth))/2.0
                self._slot(barsize/2.0 + supwidth/2.0, cutdepth*1.5, cutdepth)
                self._slot(barsize/2.0 + supwidth/2.0, -cutdepth*1.5, cutdepth)
                self._slot(barsize/2.0 + supwidth/2.0, r_mid+cutdepth*1.5, cutdepth)
                self._slot(barsize/2.0 + supwidth/2.0, r_mid-cutdepth*1.5, cutdepth)

        elif part_id in (5,6):
            # The board supports.
            x = primarygapwidth
            y = ((upperradius-supwidth) + (barradius+supwidth))/2.0 + supwidth*2.0
            t = Trace() + \
                Point(0.0, 0.0) + \
                Point(0.0, supwidth-cutdepth*2.0) + \
                Point(-cutdepth, supwidth-cutdepth*2.0) + \
                Point(-cutdepth, supwidth-cutdepth*1.0) + \
                Point(0.0, supwidth-cutdepth*1.0) + \
                Point(0.0, supwidth*2.0-cutdepth*2.0) + \
                Point(-cutdepth, supwidth*2.0-cutdepth*2.0) + \
                Point(-cutdepth, supwidth*2.0-cutdepth*1.0) + \
                Point(0.0, supwidth*2.0-cutdepth*1.0) + \
                Point(0.0, y-supwidth*2.0+cutdepth*1.0) + \
                Point(-cutdepth, y-supwidth*2.0+cutdepth*1.0) + \
                Point(-cutdepth, y-supwidth*2.0+cutdepth*2.0) + \
                Point(0.0, y-supwidth*2.0+cutdepth*2.0) + \
                Point(0.0, y-supwidth+cutdepth*1.0) + \
                Point(-cutdepth, y-supwidth+cutdepth*1.0) + \
                Point(-cutdepth, y-supwidth+cutdepth*2.0) + \
                Point(0.0, y-supwidth+cutdepth*2.0) + \
                Point(0.0, y) + \
                Point(x, y) + \
                Point(x, y-supwidth-cutdepth*1.0) + \
                Point(x+cutdepth, y-supwidth-cutdepth*1.0) + \
                Point(x+cutdepth, y-supwidth-cutdepth*2.0) + \
                Point(x, y-supwidth-cutdepth*2.0) + \
                Point(x, supwidth-cutdepth*1.0) + \
                Point(x+cutdepth, supwidth-cutdepth*1.0) + \
                Point(x+cutdepth, supwidth-cutdepth*2.0) + \
                Point(x, supwidth-cutdepth*2.0) + \
                Point(x, 0.0)
            t.close()
            self.traces.append(t)

        elif part_id==7:
            # The face components.
            t = Trace(x=[thickness], y=[thickness])
            for i, pos in enumerate(fjoint.fingers[1:-1]):
                if i%2==0:
                    t += Point(pos, thickness)
                    t += Point(pos, 0.0)
                else:
                    t += Point(pos, 0.0)
                    t += Point(pos, thickness)
            t += Point(faceheight, thickness)
            t += Point(faceheight, facewidth-thickness)
            for i, pos in enumerate(reversed(fjoint.fingers[1:-1])):
                if i%2==0:
                    t += Point(pos, facewidth-thickness)
                    t += Point(pos, facewidth)
                else:
                    t += Point(pos, facewidth)
                    t += Point(pos, facewidth-thickness)
            t += Point(thickness, facewidth-thickness)
            for i, pos in enumerate(reversed(wjoint.fingers[1:-1])):
                if i%2==0:
                    t += Point(thickness, pos)
                    t += Point(0.0, pos)
                else:
                    t += Point(0.0, pos)
                    t += Point(thickness, pos)
            t.close()
            self.traces.append(t)
        
        elif part_id==8:
            t = Trace(x=[thickness], y=[0.0])
            t += Point(facewidth-thickness, 0.0)
            for i, pos in enumerate(bjoint.fingers[1:-1]):
                if i%2==0:
                    t += Point(facewidth-thickness, pos)
                    t += Point(facewidth, pos)
                else:
                    t += Point(facewidth, pos)
                    t += Point(facewidth-thickness, pos)
            t += Point(facewidth-thickness, faceheight)
            for i, pos in enumerate(reversed(wjoint.fingers[1:-1])):
                if i%2==0:
                    t += Point(pos, faceheight)
                    t += Point(pos, faceheight-thickness)
                else:
                    t += Point(pos, faceheight-thickness)
                    t += Point(pos, faceheight)
            t += Point(thickness, faceheight)
            for i, pos in enumerate(reversed(bjoint.fingers[1:-1])):
                if i%2==0:
                    t += Point(thickness, pos)
                    t += Point(0.0, pos)
                else:
                    t += Point(0.0, pos)
                    t += Point(thickness, pos)
            t.close()
            self.traces.append(t)

            for eye in range(2):
                np = NeoPixel(style='rings', origin=Point(facewidth/4.0*(1+eye*2), faceheight/2.5), scale=scale, rotate=pi/2)
                self.traces.extend(np.traces)
            np = NeoPixel(style='strip', origin=Point(facewidth/2.0, faceheight*0.80), scale=scale)
            self.traces.extend(np.traces)

            # Camera
            csize = 8.5*scale
            t = Trace() + \
                Point(facewidth/2.0 - csize/2.0, faceheight/2.5 - csize/2.0) + \
                Point(facewidth/2.0 + csize/2.0, faceheight/2.5 - csize/2.0) + \
                Point(facewidth/2.0 + csize/2.0, faceheight/2.5 + csize/2.0) + \
                Point(facewidth/2.0 - csize/2.0, faceheight/2.5 + csize/2.0)
            t.close()
            self.traces.append(t)

    def _faceangle(self, size, radius):
        # Returns total angle required for a face.
        o = sqrt(2.0*(size**2))*0.5
        h = radius
        return 2.0*asin(o/h)

    def _segment(self, r_outer, r_inner, seg, segnext, cutdepth, a_offset, a_outer, a_inner):
        # Create an inner segment cutout.
        t = Circle(r_outer, 18, 0, cutdepth=cutdepth,
                    start=a_offset+pi/3*seg+a_outer, end=a_offset+pi/3*segnext-a_outer,
                    thickness=self.thickness) + \
            reversed(Circle(r_inner, 18, 0, cutdepth=cutdepth,
                            start=a_offset+pi/3*seg+a_inner, end=a_offset+pi/3*segnext-a_inner,
                            thickness=self.thickness))
        if a_offset == 0.0 and seg == 0:
            r_mid = r_inner + (r_outer - r_inner)/2.0
            t += Trace() + \
                 Point(self.supwidth / 2.0, r_mid - self.supwidth) + \
                 Point(self.barsize/2.0 + self.supwidth, r_mid - self.supwidth) + \
                 Point(self.barsize/2.0 + self.supwidth, r_mid + self.supwidth) + \
                 Point(self.supwidth / 2.0, r_mid + self.supwidth)
        t.close()
        return t

    def _slot(self, x, y, cutdepth):
        slot = Trace() + \
               Point(x-self.thickness/2.0, y+cutdepth/2.0) + \
               Point(x+self.thickness/2.0, y+cutdepth/2.0) + \
               Point(x+self.thickness/2.0, y-cutdepth/2.0) + \
               Point(x-self.thickness/2.0, y-cutdepth/2.0)
        slot.close()
        self.traces.append(reversed(slot))

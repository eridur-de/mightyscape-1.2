#!/usr/bin/env python3
'''
Copyright (C) 2018 Tao Wei taowei@buffalo.edu

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''
import inkex
import math
import svgpathtools
from lxml import etree

KAPPA = 4/3. * (math.sqrt(2)-1)

def cround(cnumber, ndigits):
    return round(cnumber.real, ndigits) + round(cnumber.imag, ndigits)*1j

def round_seg(seg, ndigits):
    seg.start = cround(seg.start, ndigits)
    seg.end = cround(seg.end, ndigits)
    return seg
        
def round_path(p, ndigits=6):
    """fix for precision issue"""
    for seg in p:
        round_seg(seg, ndigits)
    return p

def remove_zero_length_segments(p, eps=1e-6):
    "z will add a zero length line segment"
    return svgpathtools.Path(*filter(lambda seg: seg.length() > eps, p))

def iscontinuous(p):
    for seg1, seg2 in zip(p[:-1], p[1:]):
        if abs(seg1.end-seg2.start) >= 1e-6:
            return False
    return True

def isclosedac(p):
    return abs(p.start-p.end) < 1e-6

def isclosed(p):
    assert iscontinuous(p)
    return isclosedac(p)
    
from svgpathtools.path import Line, CubicBezier, QuadraticBezier, Arc

def d_str(self, useSandT=False, use_closed_attrib=False, rel=False):
    """Returns a path d-string for the path object.
    For an explanation of useSandT and use_closed_attrib, see the
    compatibility notes in the README."""

    if use_closed_attrib:
        self_closed = self.iscontinuous() and self.isclosed()
        if self_closed:
            segments = self[:-1]
        else:
            segments = self[:]
    else:
        self_closed = False
        segments = self[:]

    current_pos = None
    parts = []
    previous_segment = None
    end = self[-1].end

    for segment in segments:
        seg_start = segment.start
        # If the start of this segment does not coincide with the end of
        # the last segment or if this segment is actually the close point
        # of a closed path, then we should start a new subpath here.
        if current_pos != seg_start or \
                (self_closed and seg_start == end and use_closed_attrib):
            if rel:
                _seg_start = seg_start - current_pos if current_pos is not None else seg_start
            else:
                _seg_start = seg_start
            parts.append('M {},{}'.format(_seg_start.real, _seg_start.imag))

        if isinstance(segment, Line):
            if rel:
                _seg_end = segment.end - seg_start
            else:
                _seg_end = segment.end
            parts.append('L {},{}'.format(_seg_end.real, _seg_end.imag))
        elif isinstance(segment, CubicBezier):
            if useSandT and segment.is_smooth_from(previous_segment,
                                                   warning_on=False):
                if rel:
                    _seg_control2 = segment.control2 - seg_start
                    _seg_end = segment.end - seg_start
                else:
                    _seg_control2 = segment.control2
                    _seg_end = segment.end
                args = (_seg_control2.real, _seg_control2.imag,
                        _seg_end.real, _seg_end.imag)
                parts.append('S {},{} {},{}'.format(*args))
            else:
                if rel:
                    _seg_control1 = segment.control1 - seg_start
                    _seg_control2 = segment.control2 - seg_start
                    _seg_end = segment.end - seg_start
                else:
                    _seg_control1 = segment.control1
                    _seg_control2 = segment.control2
                    _seg_end = segment.end
                args = (_seg_control1.real, _seg_control1.imag,
                        _seg_control2.real, _seg_control2.imag,
                        _seg_end.real, _seg_end.imag)
                parts.append('C {},{} {},{} {},{}'.format(*args))
        elif isinstance(segment, QuadraticBezier):
            if useSandT and segment.is_smooth_from(previous_segment,
                                                   warning_on=False):
                if rel:
                    _seg_end = segment.end - seg_start
                else:
                    _seg_end = segment.end
                args = _seg_end.real, _seg_end.imag
                parts.append('T {},{}'.format(*args))
            else:
                if rel:
                    _seg_control = segment.control - seg_start
                    _seg_end = segment.end - seg_start
                else:
                    _seg_control = segment.control
                    _seg_end = segment.end
                args = (_seg_control.real, _seg_control.imag,
                        _seg_end.real, _seg_end.imag)
                parts.append('Q {},{} {},{}'.format(*args))

        elif isinstance(segment, Arc):
            if rel:
                _seg_end = segment.end - seg_start
            else:
                _seg_end = segment.end
            args = (segment.radius.real, segment.radius.imag,
                    segment.rotation,int(segment.large_arc),
                    int(segment.sweep),_seg_end.real, _seg_end.imag)
            parts.append('A {},{} {} {:d},{:d} {},{}'.format(*args))
        current_pos = segment.end
        previous_segment = segment

    if self_closed:
        parts.append('Z')

    s = ' '.join(parts)
    return s if not rel else s.lower()
        
class FilletAndChamfer(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("-t", "--fillet_type", default="fillet", help="Selects whether using fillet or chamfer")
        pars.add_argument("-R", "--radius", type=float, default=60.0, help="The radius")
        pars.add_argument('--unit', default='px', help='units of measurement')
        pars.add_argument("--remove", type=inkex.Boolean, default=False, help="If True, control object will be removed")
        
    def addEle(self, ele, parent, props):
        # https://inkscape.org/~pacogarcia/%E2%98%85new-version-of-shapes-extension
        elem = etree.SubElement(parent, ele)
        for n in props: elem.set(n,props[n])
        return elem
    
    def circle(self, c, r):
        return svgpathtools.parse_path("m %f,%f a %f,%f 0 0 1 -%f,%f %f,%f 0 0 1 -%f,-%f %f,%f 0 0 1 %f,-%f %f,%f 0 0 1 %f,%f z" % tuple((c.real+r, c.imag) + (r,)*16))
        
    def _calc_fillet_for_joint(self, p, i):
        seg1 = p[(i) % len(p)]
        seg2 = p[(i+1) % len(p)]
        
        ori_p = svgpathtools.Path(seg1, seg2)
        new_p = svgpathtools.Path()
        
        # ignore the node if G1 continuity
        tg1 = seg1.unit_tangent(1.0)
        tg2 = seg2.unit_tangent(0.0)
        cosA = abs(tg1.real * tg2.real + tg1.imag * tg2.imag)
        if abs(cosA - 1.0) < 1e-6:
            new_p.append(seg1.cropped(self._prev_t, 1.0))
            self._prev_t = 0.0
            if self._very_first_t is None:
                self._very_first_t = 1.0
            if not isclosedac(p) and i == len(p) - 2:
                new_p.append(seg2.cropped(0.0, 1.0)) # add last segment if not closed
        else:
            cir = self.circle(seg1.end, self.options.radius)
    #        new_p.extend(cir)
    
            intersects = ori_p.intersect(cir)
            if len(intersects) != 2:
                inkex.errormsg("Some fillet or chamfer may not be drawn: %d intersections!" % len(intersects))
                new_p.append(seg1.cropped(self._prev_t, 1.0))
                self._prev_t = 0.0
                if self._very_first_t is None:
                    self._very_first_t = 1.0
                if not isclosedac(p) and i == len(p) - 2:
                    new_p.append(seg2.cropped(0.0, 1.0)) # add last segment if not closed
            else:
                cb = []; segs = []; ts = []
                for (T1, seg1, t1), (T2, seg2, t2) in intersects:
                    c1 = seg1.point(t1)
                    tg1 = seg1.unit_tangent(t1) * (self.options.radius * KAPPA)
                    cb.extend([c1, tg1])
                    segs.append(seg1); ts.append(t1)
                    
    #                cir1 = self.circle(c1, self.options.radius * KAPPA)
    #                new_p.extend(cir1)
    #                new_p.append(svgpathtools.Line(c1, c1+tg1))
                    
                assert len(cb) == 4
                new_p.append(segs[0].cropped(self._prev_t, ts[0]))
                if self.options.fillet_type == 'fillet':
                    fillet = svgpathtools.CubicBezier(cb[0], cb[0]+cb[1], cb[2]-cb[3], cb[2])
                else:
                    fillet = svgpathtools.Line(cb[0], cb[2])
                new_p.append(fillet)
                self._prev_t = ts[1]
                if self._very_first_t is None:
                    self._very_first_t = ts[0]
                
                if isclosedac(p) and i == len(p) - 1:
                    new_p.append(segs[1].cropped(ts[1], self._very_first_t)) # update first segment if closed
                elif not isclosedac(p) and i == len(p) - 2:
                    new_p.append(segs[1].cropped(ts[1], 1.0)) # add last segment if not closed
                
#            # fix for the first segment
#            if p.isclosed():
#                new_p[0] = p[0].cropped(ts[1], self._very_first_t)
            
#            new_p.append(segs[0].cropped(ts[0], 1.0))
#            new_p.append(segs[1].cropped(0.0, ts[1]))
#            if self.options.fillet_type == 'fillet':
#                fillet = svgpathtools.CubicBezier(cb[0], cb[0]+cb[1], cb[2]-cb[3], cb[2])
#            else:
#                fillet = svgpathtools.Line(cb[0], cb[2])
#            new_p.append(fillet.reversed())
            
        return new_p
    
    def add_fillet_to_path(self, d):
        p = svgpathtools.parse_path(d)
        p = remove_zero_length_segments(p) # for z, a zero length line segment is possibly added
        
        if len(p) <= 1:
            return d
        
        new_p = svgpathtools.Path()
        self._prev_t = 0 # used as cache
        self._very_first_t = None # update first segment if closed
        if isclosedac(p):
            for i in range(len(p)):
                new_p.extend(self._calc_fillet_for_joint(p, i))
            if not isclosedac(new_p):
                del new_p[0] # remove first segment if closed
        else:
            for i in range(len(p)-1):
                new_p.extend(self._calc_fillet_for_joint(p, i)) 
        new_p = round_path(new_p, 6)
        # inkex.errormsg(d_str(new_p, use_closed_attrib=True, rel=True))
        return d_str(new_p, use_closed_attrib=True, rel=True)

    def effect(self):
        self.options.radius = self.svg.unittouu(str(self.options.radius) + self.options.unit) 
        
        if self.options.radius == 0:
            return
        
        for id, node in self.svg.selected.items():
            _shape = etree.QName(node.tag).localname
            if _shape != "path":
                inkex.errormsg("Fillet and chamfer only operates on path: %s is %s" % (id, _shape))
            else:
                # inkex.errormsg(etree.tostring(node))
                attrib = {k:v for k,v in node.attrib.items()}
                attrib['d'] = self.add_fillet_to_path(attrib['d'])
                self.addEle(inkex.addNS('path','svg'), node.getparent(), attrib)

        if self.options.remove:
            node.delete()
				
if __name__ == '__main__':
    FilletAndChamfer().run()
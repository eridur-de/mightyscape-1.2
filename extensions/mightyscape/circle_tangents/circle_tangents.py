#!/usr/bin/env python3

'''
    Copyright (C) 2012 Rhys Owen, rhysun@gmail.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

        A
        |\
        | \
        |  \
        |   \
        |    \
       b|     \h
        |      \
        |       \
        |_       \
        |_|_______\
       C     a     B
'''

import inkex
from inkex.paths import Path
from inkex import Transform
from math import *
from lxml import etree

def poltocar(r, rad, negx=False, negy=False):
    # converts polar coords to cartesian
    x = r * cos(rad)
    y = r * sin(rad)
    if negx and not negy:
        return [-x, y]
    elif not negx and negy:
        return [x, -y]
    elif not negx and not negy:
        return [-x, -y]
    else:
        return [x, y]

def deuclid(x1, y1, x2, y2):
    # euclidean distance between two cartesian coords
    squarex = (x1 - x2)**2
    squarey = (y1 - y2)**2
    d = sqrt(squarex + squarey)
    return d

def getAngle(b, h):
    angle = asin(b / h)
    return angle

def aLength(b, h):
    a = sqrt(h**2-b**2)
    return a


def getPathData(obj):
    if obj.get("d"):# If the circle has been converted to a path object
        d = obj.get("d")
        p = Path(d)
        if obj.get("transform"):
            trans = Transform(obj.get("transform"))
            scalex = trans[0][0]
            scaley = trans[1][1]
            data = {'rx' : p[1][1][0]*scalex,
                    'ry' : p[1][1][1]*scaley,
                    'x' : (trans[0][0]*p[0][1][0])+(trans[0][1]*p[0][1][1])+trans[0][2]-(p[1][1][0]*scalex),
                    'y' : (trans[1][0]*p[0][1][0])+(trans[1][1]*p[0][1][1])+trans[1][2]}
        else:
            data = {'rx': p[1][1][0],
                    'ry': p[1][1][1],
                    'x' : p[0][1][0]-p[1][1][0],
                    'y' : p[0][1][1]}
    elif obj.get("r"):# For a pure circle object
        r = obj.get("r")
        cx = obj.get("cx")
        cy = obj.get("cy")
        data = {'rx' : float(r),
                'ry' : float(r),
                'x' : float(cx),
                'y' : float(cy)}
    elif obj.get("rx"):# For ellipses
        rx = obj.get("rx")
        ry = obj.get("ry")
        cx = obj.get("cx")
        cy = obj.get("cy")
        data = {'rx' : float(rx),
                'ry' : float(ry),
                'x' : float(cx),
                'y' : float(cy)}
    else:
        stockErrorMsg("4")

    return data

class CircleTangents(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--position", default="inner",  help="Choose either inner or outer tangent lines")
        pars.add_argument("--selector", default="both",  help="Choose which tangents you want to get")
        pars.add_argument("--use_style_from_first", type=inkex.Boolean, default=False,  help="Use style from first selected")
        
    def effect(self):
        if len(self.options.ids) != 2:
            inkex.errormsg("Please select exactly two circles and try again!")
            return
            
        c1object = self.svg.selected[self.options.ids[0]]
        c2object = self.svg.selected[self.options.ids[1]]

        if c1object.tag != inkex.addNS('circle','svg') or c2object.tag != inkex.addNS('circle','svg'):
            self.msg("One or both objects are not svg:circle elements!")
            return

        c1 = getPathData(c1object)
        c2 = getPathData(c2object)

        # Create a third 'virtual' circle
        if c1['rx'] <= c2['rx']:
            c3x = c2['x']
            c3y = c2['y']
            if self.options.position == "outer":
                c3r = c2['rx'] - c1['rx']
            else:
                c3r = c2['rx'] + c1['rx']
            cyfA = [c1['x'], c1['y']]
            cyfB = [c2['x'], c2['y']]
        elif c1['rx'] > c2['rx']:
            c3x = c1['x']
            c3y = c1['y']
            if self.options.position == "outer":
                c3r = c1['rx'] - c2['rx']
            else:
                c3r = c1['rx'] + c2['rx']
            cyfA = [c2['x'], c2['y']]
            cyfB = [c1['x'], c1['y']]

        # Test whether the circles are actually circles!
        if c1['rx'] != c1['ry'] or c2['rx'] != c2['ry']:
            inkex.errormsg("One or both objects may be elliptical. Ensure you have circles!")
            return

        # Hypotenus of the triangle - Euclidean distance between c1 x, y and c2 x, y.
        h = deuclid(c1['x'], c1['y'], c2['x'], c2['y'])
        b = c3r
        B = None
        try:
            B = getAngle(b, h)
        except ValueError as e:
            if self.options.position == "inner":
                inkex.errormsg("Error calculating angle. Maybe your circles are overlapping each other")
            else:
                inkex.errormsg("Error calculating angle.")
            return
        a = aLength(b, h)
        # Angle of hypotenuse to x-axis
        E = getAngle(max(c1['y'], c2['y']) - min(c1['y'], c2['y']), h)

        # To test if the smallest circle is lower than the other
        if cyfB[1] <= cyfA[1]:
            negx = False
        else:
            negx = True

        # To test if it's the smallest circle to the right of the other
        if cyfB[0] <= cyfA[0]:
            negy = False
        else:
            negy = True

        angleTop = -B+E
        angleBottom = B+E
        if self.options.position == "outer":# External
            perpTop = -(pi/2)
            perpBottom = pi/2
        else:# Internal
            perpTop = pi/2
            perpBottom = -(pi/2)

        # Top coordinates of the top line
        cyfC = poltocar(a, angleTop, negx, negy)
        # Information for converting top 90grade coordinates
        conversionTop = poltocar(min(c1['rx'], c2['rx']), perpTop+angleTop, negx, negy)#1.5707964 1.57079632679

        # Bottom line coordinates
        cyfD = poltocar(a, angleBottom, negx, negy)
        # Information for converting the bottom 90 degree coordinates
        conversionBottom = poltocar(min(c1['rx'], c2['rx']), perpBottom+angleBottom, negx, negy)

        # Draw a line
        llx1 = cyfA[0]
        lly1 = cyfA[1]
        if self.options.use_style_from_first is True:
            llsteil = (c1object.get("style")) #note: if the selected objects do not contain a stroke width the tangents will be invisible!
        else:
            llsteil = "stroke:#000000; stroke-width:1px; fill:none;"

        # Line 1
        if self.options.selector == "first" or self.options.selector == "both":
            ll1x2 = cyfC[0]
            ll1y2 = cyfC[1]
            parent = c1object.getparent()
            attribsLine1 = {'style':llsteil,
                            inkex.addNS('label','inkscape'):"line1",
                            'd':'m '+str(llx1+conversionTop[0])+','+str(lly1+conversionTop[1])+' l '+str(ll1x2)+','+str(ll1y2)}
            elfen1 = etree.SubElement(parent, inkex.addNS('path','svg'), attribsLine1 )

        #Line 2
        if self.options.selector == "second" or self.options.selector == "both":
            ll2x2 = cyfD[0]
            ll2y2 = cyfD[1]
            parent = c1object.getparent()
            attribsLine1 = {'style':llsteil,
                            inkex.addNS('label','inkscape'):"line2",
                            'd':'m '+str(llx1+conversionBottom[0])+','+str(lly1+conversionBottom[1])+' l '+str(ll2x2)+','+str(ll2y2)}
            etree.SubElement(parent, inkex.addNS('path','svg'), attribsLine1 )

if __name__ == '__main__':
    CircleTangents().run()
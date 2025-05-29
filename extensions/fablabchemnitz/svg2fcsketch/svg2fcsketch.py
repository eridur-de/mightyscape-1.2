#! /usr/bin/python3
'''
(C) 2018 juergen@fabmail.org
Distribute under GPL-2.0 or ask.

References:
 https://github.com/FreeCAD/FreeCAD/blob/master/src/Mod/Sketcher/TestSketcherApp.py
 /usr/lib/freecad-daily/Mod/Sketcher/SketcherExample.py
 https://en.wikipedia.org/wiki/Rytz%27s_construction#Computer_aided_solution
 http://wiki.inkscape.org/wiki/index.php/Python_modules_for_extensions
 https://en.wikipedia.org/wiki/Composite_B%C3%A9zier_curve
 https://en.wikipedia.org/wiki/B-spline#Relationship_to_piecewise/composite_B%C3%A9zier

v0.1 jw, initial draft refactoring inksvg to make it fit here.
v0.2 jw, Introducing class SketchPathGen to seperate the sketch generator from the svg parser.
v0.3 jw, correct _coord_from_svg() size and offset handling. Suppress
         silly version printing, that would ruin an inkscape extension.
V0.4 jw, Added GuiDocument.xml for visibility and camera defaults.
         Using BoundBox() to compute camera placement.
V0.5 jw, objEllipse() done correctly with _ellipse_vertices2d()
V0.6 jw, objArc() done. ArcOfCircle() is a strange beast with rotation and mirroring.
V0.7 jw, pathString() done.
V0.8 jw, imported class SubPathTracker() from src/examples/sketch_spline.py

-----------------------

inksvg.py - parse an svg file into a plain list of paths.

(C) 2017 juergen@fabmail.org, authors of eggbot and others.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
# This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#################
2017-12-04 jw, v1.0  Refactored class InkSvg from cookiecutter extension
2017-12-07 jw, v1.1  Added roundedRectBezier()
2017-12-10 jw, v1.3  Added styleDasharray() with stroke-dashoffset
2017-12-14 jw, v1.4  Added matchStrokeColor()
2017-12-21 jw, v1.5  Changed getPathVertices() to construct a to self.paths list, instead of
                     a dictionary. (Preserving native ordering)
2017-12-22 jw, v1.6  fixed "use" to avoid errors with unknown global symbal 'composeTransform'
2017-12-25 jw, v1.7  Added getNodeStyle(), cssDictAdd(), expanded matchStrokeColor() to use
                     inline style defs. Added a warning message for not-implemented CSS styles.
               v1.7a Added getNodeStyleOne() made getNodeStyle() recurse through parents.
2018-03-10 jw, v1.7b Added search paths to find inkex.
               v1.7c Refactoring for simpler interface without subclassing.
                     Added load(), getElementsByIds() methods.
2018-03-21 jw, v1.7d Added handleViewBox() to load().
                     Added traverse().
'''

from optparse import OptionParser
import os
import sys
import math
sys_platform = sys.platform.lower()
if sys_platform.startswith('win'):
  sys.path.append('C:\\Program Files\\Inkscape\\share\\extensions')
elif sys_platform.startswith('darwin'):
  sys.path.append('~/.config/inkscape/extensions')
else:   # Linux
  sys.path.append('/usr/share/inkscape/extensions/')
  sys.path.append('/usr/lib/freecad-python3/lib/')

verbose=-1       # -1=quiet, 0=normal, 1=babble
epsilon = 0.00001
if verbose <= 0:
  os.dup2(1,99)         # hack to avoid silly version string printing.
  f = open("/dev/null", "w")
  os.dup2(f.fileno(), 1)

# The version printing code has
# src/App/Application.cpp: if (!(mConfig["Verbose"] == "Strict"))
# but we cannot call SetConfig('Verbose', 'Strict') early enough.
from FreeCAD import Base, BoundBox
sys.stdout.flush()      # push silly version string into /dev/null
if verbose <= 0:
  f.close()
  os.dup2(99,1)         # back in cansas.

import Part, Sketcher   # causes SEGV if Base is not yet imported from FreeCAD
import gettext
import re
import inkex
from inkex import Transform, CubicSuperPath
import cspsubdiv
import bezmisc
from lxml import etree

class PathGenerator():
    """
    A PathGenerator has methods for different svg objects. It compiles an
    internal representation of them all, handling transformations and linear
    interpolation of curved path segments.

    The base class PathGenerator is dummy (abstract) class that raises an
    NotImplementedError() on each method entry point. It serves as documentation for
    the generator interface.
    """
    def __init__(self):
        self._svg = None

    def registerSvg(self, svg):
        self._svg = svg
        svg.stats = self.stats

    def pathString(self, d, node, mat):
        """
        d is expected formatted as an svg path string here.
        """
        raise NotImplementedError("See example inksvg.LinearPathGen.pathString()")

    def pathList(self, d, node, mat):
        """
        d is expected as an [[cmd, [args]], ...] arrray
        """
        raise NotImplementedError("See example inksvg.LinearPathGen.pathList()")

    def objRect(x, y, w, h, node, mat):
        raise NotImplementedError("See example inksvg.LinearPathGen.objRect()")

    def objRoundedRect(self, x, y, w, h, rx, ry, node, mat):
        raise NotImplementedError("See example inksvg.LinearPathGen.objRoundedRect()")

    def objEllipse(self, cx, xy, rx, ry, node, mat):
        raise NotImplementedError("See example inksvg.LinearPathGen.objEllipse()")

    def objArc(self, d, cx, cy, rx, ry, st, en, cl, node, mat):
        """
        SVG does not have an arc element. Inkscape creates officially a path element,
        but also (redundantly) provides the original arc values.
        Implementations can choose to work with the path d and ignore the rest,
        or work with the cx, cy, rx, ry, ... parameters and ignore d.
        Note: the parameter closed=True/False is actually derived from looking at the last
        command of path d. Hackish, but there is no 'sodipodi:closed' element, or similar.
        """
        raise NotImplementedError("See example inksvg.LinearPathGen.objArc()")

class LinearPathGen(PathGenerator):

    def __init__(self, smoothness=0.2):
        self.smoothness = max(0.0001, smoothness)

    def pathString(self, d, node, mat):
        """
        d is expected formatted as an svg path string here.
        """
        inkex.utils.debug("calling getPathVertices",  self.smoothness)
        self._svg.getPathVertices(d, node, mat, self.smoothness)

    def pathList(self, d, node, mat):
        """
        d is expected as an [[cmd, [args]], ...] arrray
        """
        return self.pathString(str(d.path), node, mat)

    def objRect(x, y, w, h, node, mat):
        """
        Manually transform

           <rect x="X" y="Y" width="W" height="H"/>

        into

           <path d="MX,Y lW,0 l0,H l-W,0 z"/>

        I.e., explicitly draw three sides of the rectangle and the
        fourth side implicitly
        """
        a = []
        a.append(['M ', [x, y]])
        a.append([' l ', [w, 0]])
        a.append([' l ', [0, h]])
        a.append([' l ', [-w, 0]])
        a.append([' Z', []])
        self.pathList(a, node, matNew)

    def objRoundedRect(self, x, y, w, h, rx, ry, node, mat):
        inkex.utils.debug("calling roundedRectBezier")
        d = self._svg.roundedRectBezier(x, y, w, h, rx, ry)
        self._svg.getPathVertices(d, node, mat, self.smoothness)

    def objEllipse(self, cx, xy, rx, ry, node, mat):
        """
        Convert circles and ellipses to a path with two 180 degree
        arcs. In general (an ellipse), we convert

          <ellipse rx="RX" ry="RY" cx="X" cy="Y"/>

        to

          <path d="MX1,CY A RX,RY 0 1 0 X2,CY A RX,RY 0 1 0 X1,CY"/>

        where

          X1 = CX - RX
          X2 = CX + RX

        Note: ellipses or circles with a radius attribute of value 0
        are ignored
        """
        x1 = cx - rx
        x2 = cx + rx
        d = 'M %f,%f '     % (x1, cy) + \
            'A %f,%f '     % (rx, ry) + \
            '0 1 0 %f,%f ' % (x2, cy) + \
            'A %f,%f '     % (rx, ry) + \
            '0 1 0 %f,%f'  % (x1, cy)
        self.pathString(d, node, matNew)

    def objArc(self, d, cx, cy, rx, ry, st, en, cl, node, mat):
        """
        We ignore the cx, cy, rx, ry data, and are happy that inkscape
        also provides the same information as a path.
        """
        self.pathString(d, node, matNew)
class InkSvg():
    """
    Usage example with subclassing:

    #
    #    class ThunderLaser(inkex.Effect):
    #            def __init__(self):
    #                    inkex.localize()
    #                    inkex.Effect.__init__(self)
    #            def effect(self):
    #                    svg = InkSvg(document=self.document, pathgen=LinearPathGen(smoothness=0.2))
    #                    svg.handleViewBox()
    #                    svg.recursivelyTraverseSvg(self.document.getroot(), svg.docTransform)
    #                    for tup in svg.paths:
    #                            node = tup[0]
    #                            ...
    #    e = ThunderLaser()
    #    e.affect()
    #

    Simple usage example with method invocation:

    #    svg = InkSvg(pathgen=LinearPathGen(smoothness=0.01))
    #    svg.load(svgfile)
    #    svg.traverse([ids...])
    #    inkex.utils.debug(svg.pathgen.path)

    """
    __version__ = "1.7c"
    DEFAULT_WIDTH = 100
    DEFAULT_HEIGHT = 100

    # imports from inkex
    NSS = inkex.NSS

    def getElementsByIds(self, ids):
        """
        ids be a string of a comma seperated values, or a list of strings.
        Returns a list of xml nodes.
        """
        if not self.document:
          raise ValueError("no document loaded.")
        if isinstance(ids, (bytes, str)): ids = [ ids ]   # handle some scalars
        ids = ','.join(ids).split(',')                    # merge into a string and re-split

        ## OO-Fail:
        # cannot use inkex.getElementById() -- it returns only the first element of each hit.
        # cannot use inkex.getselected() -- it returns the last element of each hit only.
        """Collect selected nodes"""
        nodes = []
        for id in ids:
          if id != '':    # empty strings happen after splitting...
            path = '//*[@id="%s"]' % id
            el_list = self.document.xpath(path, namespaces=InkSvg.NSS)
            if el_list:
              for node in el_list:
                nodes.append(node)
            else:
              raise ValueError("id "+id+" not found in the svg document.")
        return nodes


    def load(self, filename):
        inkex.localization.localize()
        # OO-Fail: cannot call inkex.Effect.parse(), Effect constructor has so many side-effects.
        stream = open(filename, 'r')
        p = etree.XMLParser(huge_tree=True)
        self.document = etree.parse(stream, parser=p)
        stream.close()
        # initialize a coordinate system that can be picked up by pathgen.
        self.handleViewBox()

    def traverse(self, ids=None):
        """
        Recursively traverse the SVG document. If ids are given, all matching nodes
        are taken as start positions for traversal. Otherwise traveral starts at
        the root node of the document.
        """
        selected = []
        if ids is not None:
          selected = self.getElementsByIds(ids)
        if len(selected):
          # Traverse the selected objects
          for node in selected:
            transform = self.recursivelyGetEnclosingTransform(node)
            self.recursivelyTraverseSvg([node], transform)
        else:
          # Traverse the entire document building new, transformed paths
          self.recursivelyTraverseSvg(self.document.getroot(), self.docTransform)


    def getNodeStyleOne(self, node):
        """
        Finds style declarations by .class, #id or by tag.class syntax,
        and of course by a direct style='...' attribute.
        """
        sheet = ''
        selectors = []
        classes = node.get('class', '')         # classes == None can happen here.
        if classes is not None and classes != '':
            selectors = ["."+cls for cls in re.split(r'[\s,]+', classes)]
            selectors += [node.tag+sel for sel in selectors]
        node_id = node.get('id', '')
        if node_id is not None and node_id != '':
            selectors += [ "#"+node_id ]
        for sel in selectors:
            if sel in self.css_dict:
                sheet += '; '+self.css_dict[sel]
        style = node.get('style', '')
        if style is not None and style != '':
            sheet += '; '+style
        return dict(inkex.Style.parse_str(sheet))

    def getNodeStyle(self, node):
        combined_style = {}
        parent = node.getparent()
        if parent.tag == inkex.addNS('g','svg') or parent.tag == 'g':
            combined_style = self.getNodeStyle(parent)
        style = self.getNodeStyleOne(node)
        for s in style:
            combined_style[s] = style[s]        # overwrite or add
        return combined_style


    def styleDasharray(self, path_d, node):
        """
        Check the style of node for a stroke-dasharray, and apply it to the
        path d returning the result.  d is returned unchanged, if no
        stroke-dasharray was found.

        ## Extracted from inkscape extension convert2dashes; original
        ## comments below.
        ## Added stroke-dashoffset handling, made it a universal operator
        ## on nodes and 'd' paths.

        This extension converts a path into a dashed line using 'stroke-dasharray'
        It is a modification of the file addnodes.py

        Copyright (C) 2005,2007 Aaron Spike, aaron@ekips.org
        Copyright (C) 2009 Alvin Penner, penner@vaxxine.com
        """

        def tpoint(p1, p2, t = 0.5):
            x1 = p1[0]
            y1 = p1[1]
            x2 = p2[0]
            y2 = p2[1]
            return [x1+t*(x2-x1),y1+t*(y2-y1)]
        def cspbezsplit(sp1, sp2, t = 0.5):
            m1=tpoint(sp1[1],sp1[2],t)
            m2=tpoint(sp1[2],sp2[0],t)
            m3=tpoint(sp2[0],sp2[1],t)
            m4=tpoint(m1,m2,t)
            m5=tpoint(m2,m3,t)
            m=tpoint(m4,m5,t)
            return [[sp1[0][:],sp1[1][:],m1], [m4,m,m5], [m3,sp2[1][:],sp2[2][:]]]
        def cspbezsplitatlength(sp1, sp2, l = 0.5, tolerance = 0.001):
            bez = (sp1[1][:],sp1[2][:],sp2[0][:],sp2[1][:])
            t = bezmisc.beziertatlength(bez, l, tolerance)
            return cspbezsplit(sp1, sp2, t)
        def cspseglength(sp1,sp2, tolerance = 0.001):
            bez = (sp1[1][:],sp1[2][:],sp2[0][:],sp2[1][:])
            return bezmisc.bezierlength(bez, tolerance)

        style = self.getNodeStyle(node)
        if not style.has_key('stroke-dasharray'):
            return path_d
        dashes = []
        if style['stroke-dasharray'].find(',') > 0:
            dashes = [float (dash) for dash in style['stroke-dasharray'].split(',') if dash]
        if not dashes:
            return path_d

        dashoffset = 0.0
        if style.has_key('stroke-dashoffset'):
            dashoffset = float(style['stroke-dashoffset'])
            if dashoffset < 0.0: dashoffset = 0.0
            if dashoffset > dashes[0]: dashoffset = dashes[0]   # avoids a busy-loop below!

        p = CubicSuperPath(d)
        new = []
        for sub in p:
            idash = 0
            dash = dashes[0]
            # inkex.utils.debug("initial dash length: ", dash, dashoffset)
            dash = dash - dashoffset
            length = 0
            new.append([sub[0][:]])
            i = 1
            while i < len(sub):
                dash = dash - length
                length = cspseglength(new[-1][-1], sub[i])
                while dash < length:
                    new[-1][-1], next, sub[i] = cspbezsplitatlength(new[-1][-1], sub[i], dash/length)
                    if idash % 2:           # create a gap
                        new.append([next[:]])
                    else:                   # splice the curve
                        new[-1].append(next[:])
                    length = length - dash
                    idash = (idash + 1) % len(dashes)
                    dash = dashes[idash]
                if idash % 2:
                    new.append([sub[i]])
                else:
                    new[-1].append(sub[i])
                i+=1
        return CubicSuperPath(new).to_path(curves_only=True)

    def matchStrokeColor(self, node, rgb, eps=None, avg=True):
        """
        Return True if the line color found in the style attribute of elem
        does not differ from rgb in any of the components more than eps.
        The default eps with avg=True is 64.
        With avg=False the default is eps=85 (33% on a 0..255 scale).

        In avg mode, the average of all three color channel differences is
        compared against eps. Otherwise each color channel difference is
        compared individually.

        The special cases None, False, True for rgb are interpreted logically.
        Otherwise rgb is expected as a list of three integers in 0..255 range.
        Missing style attribute or no stroke element is interpreted as False.
        Unparseable stroke elements are interpreted as 'black' (0,0,0).
        Hexadecimal stroke formats of '#RRGGBB' or '#RGB' are understood
        as well as 'rgb(100%, 0%, 0%) or 'red'.
        """
        if eps is None:
          eps = 64 if avg == True else 85
        if rgb is None or rgb is False: return False
        if rgb is True: return True
        style = self.getNodeStyle(node)
        s = style.get('stroke', '')
        if s == '': return False
        c = inkex.Color(s).to_rgb()
        if sum:
           s = abs(rgb[0]-c[0]) + abs(rgb[1]-c[1]) + abs(rgb[2]-c[2])
           if s < 3*eps:
             return True
           return False
        if abs(rgb[0]-c[0]) > eps: return False
        if abs(rgb[1]-c[1]) > eps: return False
        if abs(rgb[2]-c[2]) > eps: return False
        return True

    def cssDictAdd(self, text):
        """
        Represent css cdata as a hash in css_dict.
        Implements what is seen on: http://www.blooberry.com/indexdot/css/examples/cssembedded.htm
        """
        text=re.sub(r'^\s*(<!--)?\s*', '', text)
        while True:
            try:
                (keys, rest) = text.split('{', 1)
            except:
                break
            keys = re.sub(r'/\*.*?\*/', ' ', keys)   # replace comments with whitespace
            keys = re.split(r'[\s,]+', keys)         # convert to list
            while '' in keys:
                keys.remove('')                     # remove empty elements (at start or end)
            (val,text) = rest.split('}', 1)
            val = re.sub(r'/\*.*?\*/', '', val)      # replace comments nothing in values
            val = re.sub(r'\s+', ' ', val).strip()   # normalize whitespace
            for k in keys:
                if not k in self.css_dict:
                    self.css_dict[k] = val
                else:
                    self.css_dict[k] += '; '+val


    def roundedRectBezier(self, x, y, w, h, rx, ry=0):
        """
        Draw a rectangle of size w x h, at start point x, y with the corners rounded by radius
        rx and ry. Each corner is a quarter of an ellipsis, where rx and ry are the horizontal
        and vertical dimenstion.
        A pathspec according to https://www.w3.org/TR/SVG/paths.html#PathDataEllipticalArcCommands
        is returned. Very similar to what inkscape would do when converting object to path.
        Inkscape seems to use a kappa value of 0.553, higher precision is used here.

        x=0, y=0, w=200, h=100, rx=50, ry=30 produces in inkscape
        d="m 50,0 h 100 c 27.7,0 50,13.38 50,30 v 40 c 0,16.62 -22.3,30 -50,30
           H 50 C 22.3,100 0,86.62 0,70 V 30 C 0,13.38 22.3,0 50,0 Z"
        It is unclear, why there is a Z, the last point is identical with the first already.
        It is unclear, why half of the commands use relative and half use absolute coordinates.
        We do it all in relative coords, except for the initial M, and we ommit the Z.
        """
        if rx < 0: rx = 0
        if rx > 0.5*w: rx = 0.5*w
        if ry < 0: ry = 0
        if ry > 0.5*h: ry = 0.5*h
        if ry < 0.0000001: ry = rx
        k = 0.5522847498307933984022516322796     # kappa, handle length for a 4-point-circle.
        d  = "M %f,%f h %f " % (x+rx, y, w-rx-rx)                      # top horizontal to right
        d += "c %f,%f %f,%f %f,%f " % (rx*k,0, rx,ry*(1-k), rx,ry)     # top right ellipse
        d += "v %f " % (h-ry-ry)                                       # right vertical down
        d += "c %f,%f %f,%f %f,%f " % (0,ry*k, rx*(k-1),ry, -rx,ry)    # bottom right ellipse
        d += "h %f " % (-w+rx+rx)                                      # bottom horizontal to left
        d += "c %f,%f %f,%f %f,%f " % (-rx*k,0, -rx,ry*(k-1), -rx,-ry) # bottom left ellipse
        d += "v %f " % (-h+ry+ry)                                      # left vertical up
        d += "c %f,%f %f,%f %f,%f" % (0,-ry*k, rx*(1-k),-ry, rx,-ry)   # top left ellipse
        return d


    def subdivideCubicPath(self, sp, flat, i=1):
        '''
        [ Lifted from eggbot.py with impunity ]

        Break up a bezier curve into smaller curves, each of which
        is approximately a straight line within a given tolerance
        (the "smoothness" defined by [flat]).

        This is a modified version of cspsubdiv.cspsubdiv(): rewritten
        because recursion-depth errors on complicated line segments
        could occur with cspsubdiv.cspsubdiv().
        '''

        while True:
            while True:
                if i >= len(sp):
                    return

                p0 = sp[i - 1][1]
                p1 = sp[i - 1][2]
                p2 = sp[i][0]
                p3 = sp[i][1]

                b = (p0, p1, p2, p3)

                if cspsubdiv.maxdist(b) > flat:
                    break

                i += 1

            one, two = bezmisc.beziersplitatt(b, 0.5)
            sp[i - 1][2] = one[1]
            sp[i][0] = two[2]
            p = [one[2], one[3], two[1]]
            sp[i:1] = [p]

    def parseLengthWithUnits(self, str, default_unit='px'):
        '''
        Parse an SVG value which may or may not have units attached
        This version is greatly simplified in that it only allows: no units,
        units of px, and units of %.  Everything else, it returns None for.
        There is a more general routine to consider in scour.py if more
        generality is ever needed.
        With inkscape 0.91 we need other units too: e.g. svg:width="400mm"
        '''

        u = default_unit
        s = str.strip()
        if s[-2:] in ('px', 'pt', 'pc', 'mm', 'cm', 'in', 'ft'):
            u = s[-2:]
            s = s[:-2]
        elif s[-1:] in ('m', '%'):
            u = s[-1:]
            s = s[:-1]

        try:
            v = float(s)
        except:
            return None, None

        return v, u


    def __init__(self, document=None, svgfile=None, smoothness=0.2, pathgen=LinearPathGen(smoothness=0.2)):
        """
        Usage: ...
        """
        self.dpi = 96.0
        self.px_used = False            # raw px unit depends on correct dpi.
        self.xmin, self.xmax = (1.0E70, -1.0E70)
        self.ymin, self.ymax = (1.0E70, -1.0E70)

        # CAUTION: smoothness here is deprecated. it belongs into pathgen, if.
        # CAUTION: smoothness == 0.0 leads to a busy-loop.
        self.smoothness = max(0.0001, smoothness)    # 0.0001 .. 5.0
        self.pathgen = pathgen
        pathgen.registerSvg(self)

        # List of paths we will construct.  Path lists are paired with the SVG node
        # they came from.  Such pairing can be useful when you actually want
        # to go back and update the SVG document, or retrieve e.g. style information.
        self.paths = []

        # cssDictAdd collects style definitions here:
        self.css_dict = {}

        # For handling an SVG viewbox attribute, we will need to know the
        # values of the document's <svg> width and height attributes as well
        # as establishing a transform from the viewbox to the display.

        self.docWidth = float(self.DEFAULT_WIDTH)
        self.docHeight = float(self.DEFAULT_HEIGHT)
        self.docTransform = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]

        # Dictionary of warnings issued.  This to prevent from warning
        # multiple times about the same problem
        self.warnings = {}

        if document:
            self.document = document
            if svgfile:
                inkex.errormsg('Warning: ignoring svgfile. document given too.')
        elif svgfile:
            self.document = self.load(svgfile)

    def getLength(self, name, default):

        '''
        Get the <svg> attribute with name "name" and default value "default"
        Parse the attribute into a value and associated units.  Then, accept
        units of cm, ft, in, m, mm, pc, or pt.  Convert to pixels.

        Note that SVG defines 90 px = 1 in = 25.4 mm.
        Note: Since inkscape 0.92 we use the CSS standard of 96 px = 1 in.
        '''
        str = self.document.getroot().get(name)
        if str:
            return self.lengthWithUnit(str)
        else:
            # No width specified; assume the default value
            return float(default)

    def lengthWithUnit(self, strn, default_unit='px'):
        v, u = self.parseLengthWithUnits(strn, default_unit)
        if v is None:
            # Couldn't parse the value
            return None
        elif (u == 'mm'):
            return float(v) * (self.dpi / 25.4)
        elif (u == 'cm'):
            return float(v) * (self.dpi * 10.0 / 25.4)
        elif (u == 'm'):
            return float(v) * (self.dpi * 1000.0 / 25.4)
        elif (u == 'in'):
            return float(v) * self.dpi
        elif (u == 'ft'):
            return float(v) * 12.0 * self.dpi
        elif (u == 'pt'):
            # Use modern "Postscript" points of 72 pt = 1 in instead
            # of the traditional 72.27 pt = 1 in
            return float(v) * (self.dpi / 72.0)
        elif (u == 'pc'):
            return float(v) * (self.dpi / 6.0)
        elif (u == 'px'):
            self.px_used = True
            return float(v)
        else:
            # Unsupported units
            return None

    def getDocProps(self):

        '''
        Get the document's height and width attributes from the <svg> tag.
        Use a default value in case the property is not present or is
        expressed in units of percentages.

        This initializes:
        * self.basename
        * self.docWidth
        * self.docHeight
        * self.dpi
        '''

        sodipodi_docname = self.document.getroot().get(
            "{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}docname")
        if sodipodi_docname is None:
            sodipodi_docname = "inkscape"
        self.basename = re.sub(r"\.SVG", "", sodipodi_docname, flags=re.I)
        self.docHeight = self.getLength('height', self.DEFAULT_HEIGHT)
        self.docWidth = self.getLength('width', self.DEFAULT_WIDTH)

        if (self.docHeight is None) or (self.docWidth is None):
            return False
        else:
            return True

    def handleViewBox(self):

        '''
        Set up the document-wide transform in the event that the document has
        an SVG viewbox

        This initializes:
        * self.basename
        * self.docWidth
        * self.docHeight
        * self.dpi
        * self.docTransform
        '''

        if self.getDocProps():
            viewbox = self.document.getroot().get('viewBox')
            if viewbox:
                vinfo = viewbox.strip().replace(',', ' ').split(' ')
                if (vinfo[2] != 0) and (vinfo[3] != 0):
                    sx = self.docWidth  / float(vinfo[2])
                    sy = self.docHeight / float(vinfo[3])
                    self.docTransform = Transform('scale(%f,%f)' % (sx, sy)).matrix

    def getPathVertices(self, path, node=None, transform=None, smoothness=None):

        '''
        Decompose the path data from an SVG element into individual
        subpaths, each subpath consisting of absolute move to and line
        to coordinates.  Place these coordinates into a list of polygon
        vertices.

        The result is appended to self.paths as a two-element tuple of the
        form (node, path_list). This preserves the native ordering of
        the SVG file as much as possible, while still making all attributes
        if the node available when processing the path list.
        '''

        if not smoothness:
            smoothness = self.smoothness        # self.smoothness is deprecated.

        if (not path) or (len(path) == 0):
            # Nothing to do
            return None

        if node is not None:
            path = self.styleDasharray(path, node)

        # parsePath() may raise an exception.  This is okay
        sp = path.path.to_arrays()
        if (not sp) or (len(sp) == 0):
            # Path must have been devoid of any real content
            return None

        # Get a cubic super path
        p = CubicSuperPath(sp).to_path(curves_only=True)
        if (not p) or (len(p) == 0):
            # Probably never happens, but...
            return None

        if transform:
            path.transform = transform

        # Now traverse the cubic super path
        subpath_list = []
        subpath_vertices = []

        for sp in p:

            # We've started a new subpath
            # See if there is a prior subpath and whether we should keep it
            if len(subpath_vertices):
                subpath_list.append([subpath_vertices, [sp_xmin, sp_xmax, sp_ymin, sp_ymax]])

            subpath_vertices = []
            self.subdivideCubicPath(sp, float(smoothness))

            # Note the first point of the subpath
            first_point = sp[0][1]
            subpath_vertices.append(first_point)
            sp_xmin = first_point[0]
            sp_xmax = first_point[0]
            sp_ymin = first_point[1]
            sp_ymax = first_point[1]

            n = len(sp)

            # Traverse each point of the subpath
            for csp in sp[1:n]:

                # Append the vertex to our list of vertices
                pt = csp[1]
                subpath_vertices.append(pt)

                # Track the bounding box of this subpath
                if pt[0] < sp_xmin:
                    sp_xmin = pt[0]
                elif pt[0] > sp_xmax:
                    sp_xmax = pt[0]
                if pt[1] < sp_ymin:
                    sp_ymin = pt[1]
                elif pt[1] > sp_ymax:
                    sp_ymax = pt[1]

            # Track the bounding box of the overall drawing
            # This is used for centering the polygons in OpenSCAD around the
            # (x,y) origin
            if sp_xmin < self.xmin:
                self.xmin = sp_xmin
            if sp_xmax > self.xmax:
                self.xmax = sp_xmax
            if sp_ymin < self.ymin:
                self.ymin = sp_ymin
            if sp_ymax > self.ymax:
                self.ymax = sp_ymax

        # Handle the final subpath
        if len(subpath_vertices):
            subpath_list.append([subpath_vertices, [sp_xmin, sp_xmax, sp_ymin, sp_ymax]])

        if len(subpath_list) > 0:
            self.paths.append( (node, subpath_list) )


    def recursivelyTraverseSvg(self, aNodeList, matCurrent=None, parent_visibility="visible"):

        '''
        [ This too is largely lifted from eggbot.py ]

        Recursively walk the SVG document aNodeList, building polygon vertex lists
        for each graphical element we support. The list is generated in self.paths
        as a list of tuples [ (node, path_list), (node, path_list), ...] ordered
        natively by their order of appearance in the SVG document.

        Rendered SVG elements:
            <circle>, <ellipse>, <line>, <path>, <polygon>, <polyline>, <rect>

        Supported SVG elements:
            <group>, <use>

        Ignored SVG elements:
            <defs>, <eggbot>, <metadata>, <namedview>, <pattern>,
            processing directives

        All other SVG elements trigger an error (including <text>)
        '''
        if matCurrent is None:
            matCurrent = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]

        for node in aNodeList:

            # Ignore invisible nodes
            visibility = node.get('visibility', parent_visibility)
            if visibility == 'inherit':
                visibility = parent_visibility
            if visibility == 'hidden' or visibility == 'collapse':
                continue

            # FIXME: should we inherit styles from parents?
            s = self.getNodeStyle(node)
            if s.get('display', '') == 'none': continue

            # first apply the current matrix transform to this node's transform
            matNew = Transform(matCurrent) @ Transform(Transform(node.get("transform")).matrix)
            
            if node.tag == inkex.addNS('g', 'svg') or node.tag == 'g':

                self.recursivelyTraverseSvg(node, matNew, visibility)

            elif node.tag == inkex.addNS('use', 'svg') or node.tag == 'use':

                # A <use> element refers to another SVG element via an
                # xlink:href="#blah" attribute.  We will handle the element by
                # doing an XPath search through the document, looking for the
                # element with the matching id="blah" attribute.  We then
                # recursively process that element after applying any necessary
                # (x,y) translation.
                #
                # Notes:
                #  1. We ignore the height and width attributes as they do not
                #     apply to path-like elements, and
                #  2. Even if the use element has visibility="hidden", SVG
                #     still calls for processing the referenced element.  The
                #     referenced element is hidden only if its visibility is
                #     "inherit" or "hidden".

                refid = node.get(inkex.addNS('href', 'xlink'))
                if not refid:
                    continue

                # [1:] to ignore leading '#' in reference
                path = '//*[@id="%s"]' % refid[1:]
                refnode = node.xpath(path)
                if refnode:
                    x = float(node.get('x', '0'))
                    y = float(node.get('y', '0'))
                    # Note: the transform has already been applied
                    if (x != 0) or (y != 0):
                        matNew2 = Transform(matNew) @ Transform(Transform("translate({0:f},{1:f})".format(x, y)))
                    else:
                        matNew2 = matNew
                    visibility = node.get('visibility', visibility)
                    self.recursivelyTraverseSvg(refnode, matNew2, visibility)

            elif node.tag == inkex.addNS('path', 'svg'):

                path_data = node.get('d', '')
                if node.get(inkex.addNS('type', 'sodipodi'), '') == 'arc':
                    cx = float(node.get(inkex.addNS('cx', 'sodipodi'), '0'))
                    cy = float(node.get(inkex.addNS('cy', 'sodipodi'), '0'))
                    rx = float(node.get(inkex.addNS('rx', 'sodipodi'), '0'))
                    ry = float(node.get(inkex.addNS('ry', 'sodipodi'), '0'))
                    st = float(node.get(inkex.addNS('start', 'sodipodi'), '0'))
                    en = float(node.get(inkex.addNS('end', 'sodipodi'), '0'))
                    cl = path_data.strip()[-1] in ('z', 'Z')
                    self.pathgen.objArc(path_data, cx, cy, rx, ry, st, en, cl, node, matNew)
                else:
                    ### sodipodi:type="star" also comes here. TBD later, if need be.
                    self.pathgen.pathString(path_data, node, matNew)

            elif node.tag == inkex.addNS('rect', 'svg') or node.tag == 'rect':

                # Create a path with the outline of the rectangle
                # Adobe Illustrator leaves out 'x'='0'.
                x = float(node.get('x', '0'))
                y = float(node.get('y', '0'))
                w = float(node.get('width', '0'))
                h = float(node.get('height', '0'))
                rx = float(node.get('rx', '0'))
                ry = float(node.get('ry', '0'))

                if rx > 0.0 or ry > 0.0:
                    if   ry < 0.0000001: ry = rx
                    elif rx < 0.0000001: rx = ry
                    self.pathgen.objRoundedRect(x, y, w, h, rx, ry, node, matNew)
                else:
                    self.pathgen.objRect(x, y, w, h, node, matNew)

            elif node.tag == inkex.addNS('line', 'svg') or node.tag == 'line':

                # Convert
                #
                #   <line x1="X1" y1="Y1" x2="X2" y2="Y2/>
                #
                # to
                #
                #   <path d="MX1,Y1 LX2,Y2"/>

                x1 = float(node.get('x1'))
                y1 = float(node.get('y1'))
                x2 = float(node.get('x2'))
                y2 = float(node.get('y2'))
                if (not x1) or (not y1) or (not x2) or (not y2):
                    continue
                a = []
                a.append(['M ', [x1, y1]])
                a.append([' L ', [x2, y2]])
                self.pathgen.pathList(a, node, matNew)

            elif node.tag == inkex.addNS('polyline', 'svg') or node.tag == 'polyline':

                # Convert
                #
                #  <polyline points="x1,y1 x2,y2 x3,y3 [...]"/>
                #
                # to
                #
                #   <path d="Mx1,y1 Lx2,y2 Lx3,y3 [...]"/>
                #
                # Note: we ignore polylines with no points

                pl = node.get('points', '').strip()
                if pl == '':
                    continue

                pa = pl.split()
                d = "".join(["M " + pa[i] if i == 0 else " L " + pa[i] for i in range(0, len(pa))])
                self.pathgen.pathString(d, node, matNew)

            elif node.tag == inkex.addNS('polygon', 'svg') or node.tag == 'polygon':

                # Convert
                #
                #  <polygon points="x1,y1 x2,y2 x3,y3 [...]"/>
                #
                # to
                #
                #   <path d="Mx1,y1 Lx2,y2 Lx3,y3 [...] Z"/>
                #
                # Note: we ignore polygons with no points

                pl = node.get('points', '').strip()
                if pl == '':
                    continue

                pa = pl.split()
                d = "".join(["M " + pa[i] if i == 0 else " L " + pa[i] for i in range(0, len(pa))])
                d += " Z"
                self.pathgen.pathString(d, node, matNew)

            elif node.tag == inkex.addNS('ellipse', 'svg') or node.tag == 'ellipse' or \
                 node.tag == inkex.addNS('circle', 'svg')  or node.tag == 'circle':

                if node.tag == inkex.addNS('ellipse', 'svg') or node.tag == 'ellipse':
                    rx = float(node.get('rx', '0'))
                    ry = float(node.get('ry', '0'))
                else:
                    rx = float(node.get('r', '0'))
                    ry = rx
                if rx == 0 or ry == 0:
                    continue

                cx = float(node.get('cx', '0'))
                cy = float(node.get('cy', '0'))
                self.pathgen.objEllipse(cx, cy, rx, ry, node, matNew)

            elif node.tag == inkex.addNS('pattern', 'svg') or node.tag == 'pattern':
                pass

            elif node.tag == inkex.addNS('metadata', 'svg') or node.tag == 'metadata':
                pass

            elif node.tag == inkex.addNS('defs', 'svg') or node.tag == 'defs':
                self.recursivelyTraverseSvg(node, matNew, visibility)

            elif node.tag == inkex.addNS('desc', 'svg') or node.tag == 'desc':
                pass

            elif node.tag == inkex.addNS('namedview', 'sodipodi') or node.tag == 'namedview':
                pass

            elif node.tag == inkex.addNS('eggbot', 'svg') or node.tag == 'eggbot':
                pass

            elif node.tag == inkex.addNS('text', 'svg') or node.tag == 'text':
                texts = []
                plaintext = ''
                for tnode in node.iterfind('.//'):  # all subtree
                    if tnode is not None and tnode.text is not None:
                        texts.append(tnode.text)
                if len(texts):
                    plaintext = "', '".join(texts).encode('latin-1')
                    inkex.errormsg('Warning: text "%s"' % plaintext)
                    inkex.errormsg('Warning: unable to draw text, please convert it to a path first.')

            elif node.tag == inkex.addNS('title', 'svg') or node.tag == 'title':
                pass

            elif node.tag == inkex.addNS('image', 'svg') or node.tag == 'image':
                if 'image' not in self.warnings:
                    inkex.errormsg(
                        gettext.gettext(
                            'Warning: unable to draw bitmap images; please convert them to line art first.  '
                            'Consider using the "Trace bitmap..." tool of the "Path" menu.  Mac users please '
                            'note that some X11 settings may cause cut-and-paste operations to paste in bitmap copies.'))
                    self.warnings['image'] = 1

            elif node.tag == inkex.addNS('pattern', 'svg') or node.tag == 'pattern':
                pass

            elif node.tag == inkex.addNS('radialGradient', 'svg') or node.tag == 'radialGradient':
                # Similar to pattern
                pass

            elif node.tag == inkex.addNS('linearGradient', 'svg') or node.tag == 'linearGradient':
                # Similar in pattern
                pass

            elif node.tag == inkex.addNS('style', 'svg') or node.tag == 'style':
                # This is a reference to an external style sheet and not the
                # value of a style attribute to be inherited by child elements
                #
                #   <style type="text/css">
                #    <![CDATA[
                #     .str0 {stroke:red;stroke-width:20}
                #     .fil0 {fill:none}
                #    ]]>
                #
                # FIXME: test/test_styles.sh fails without this.
                # This is input for self.getNodeStyle()
                if node.get('type', '') == "text/css":
                    self.cssDictAdd(node.text)
                else:
                    inkex.errormsg("Warning: Corel-style CSS definitions ignored. Parsing element 'style' with type='%s' not implemented." % node.get('type', ''))

            elif node.tag == inkex.addNS('cursor', 'svg') or node.tag == 'cursor':
                pass

            elif node.tag == inkex.addNS('color-profile', 'svg') or node.tag == 'color-profile':
                # Gamma curves, color temp, etc. are not relevant to single
                # color output
                pass

            elif not isinstance(node.tag, basestring):
                # This is likely an XML processing instruction such as an XML
                # comment.  lxml uses a function reference for such node tags
                # and as such the node tag is likely not a printable string.
                # Further, converting it to a printable string likely won't
                # be very useful.
                pass

            else:
                inkex.errormsg('Warning: unable to draw object <%s>, please convert it to a path first.' % node.tag)
                pass

    def recursivelyGetEnclosingTransform(self, node):

        '''
        Determine the cumulative transform which node inherits from
        its chain of ancestors.
        '''
        node = node.getparent()
        if node is not None:
            parent_transform = self.recursivelyGetEnclosingTransform(node)
            node_transform = node.get('transform', None)
            if node_transform is None:
                return parent_transform
            else:
                tr = Transform(node_transform)
                if parent_transform is None:
                    return tr
                else:
                    return parent_transform @ tr
        else:
            return self.docTransform

parser = OptionParser(usage="\n    %prog [options] SVGFILE [OUTFILE]\n\nTry --help for details.")
parser.add_option("-o", "--outfile", dest="outfile", help="write FCStd to OUTPUT. Default: stdout (unless it is a tty)", metavar="OUTPUT")
parser.add_option("-i", "--id", "--ids", dest="ids", action="append", type="string", default=[], help="Select svg object(s) by id attribute. Use multiple times or combine with comma. Default: root object, aka all")
parser.add_option("--tab", dest="tab", type="string")
parser.add_option("--selected-nodes", dest="selected_nodes", action="append", type="string", default=[], help="id:subpath:position of selected nodes, if any") # TODO: check if inkscape is really passing us these
parser.add_option("-V", "--version",
                         action="store_true", dest="version", default=False,
                         help="Print version numbers only.")
parser.add_option("-v", "--verbose",
                         action="store_true", dest="verbose", default=False,
                         help="Be verbose. Default: silent.")
parser.add_option("-e", "--expose-internal-geometry", type="string", dest="expose_internal_geometry", default="false",
                         help="Expose internal geometry for Splines and Ellipses. Default: False.")
(options, args) = parser.parse_args()

if options.version:
  inkex.utils.debug("InkSvg %s\n%s %s\n" % (InkSvg.__version__, sys.argv[0], __version__))
  sys.exit(0)
if len(args) < 1:
  parser.error("Input svg file missing.")

svgfile = args[0]

outdir = '.'
if len(args) > 1:
  fcstdfile = args[1]
else:
  if options.outfile:
    fcstdfile = options.outfile
  else:
    fcstdfile = re.sub(r'\.svg$', '.FCStd', svgfile, re.I)
docname = re.sub(r'\.fcstd$', '', fcstdfile, re.I)
docname = re.sub(r'^.*/', '', docname)

if not options.outfile:
  if sys.stdout.isatty():
    inkex.utils.debug("ERROR: stdout isatty. Please use option --outfile or redirect stdout.")
    sys.exit(1)

class SubPathTracker():
  """
  Track status of a subpath. In SVG, a path consists of disconnected subpaths.
  Each subpath consists of a connected list of straight lines or cubic spline segments.

  A SubPathTracker object remembers the first and last last point of a subpath.
  When adding a line() or cubic(), it continues the current subpath
  assuming same_point(last_point, p1) == True, otherwise it is an error.

  Control points of splines have circles in construction mode on them. All the same size.
  End points of lines don't have these, unless they are also control points of adjacent splines.

  If any two or three of the control points coincide, duplicate circles are avoided, an coincidence restrictions are added instead.
  We never convert a cubic spline to a quadratic spline, as they are slightly different in shape.

  Adjacent ends of segments have coincidence restrictions on them, no matter if the segments are of type line or type cubic.
  Duplicate circles on adjacent ends of two cubics are avoided.

  If the very last point of a subpath coincides with the very first point, a coincidence restriction is added, and duplicate circles
  are again avoided.

  Other coincidences within the subpath are ignored and may prodice duplicate circles (serving their own purpose each).


  Example spline syntax seen in the Python-Console of FreeCaD 0.18 when drawing a cubic spline manually:

  addGeometry(Part.Circle(App.Vector(-85,192,0),App.Vector(0,0,1),10),True)    # 3
  addGeometry(Part.Circle(App.Vector(-107,160,0),App.Vector(0,0,1),10),True)   # 4
  addConstraint(Sketcher.Constraint('Radius',3,7.000000))
  addConstraint(Sketcher.Constraint('Equal',3,4))
  addGeometry(Part.Circle(App.Vector(-20,161,0),App.Vector(0,0,1),10),True)    # 5
  addConstraint(Sketcher.Constraint('Equal',3,5))
  addGeometry(Part.Circle(App.Vector(-42,193,0),App.Vector(0,0,1),10),True)    # 6
  addConstraint(Sketcher.Constraint('Equal',3,6))
  addGeometry(Part.BSplineCurve([App.Vector(-85,192),App.Vector(-107,160),App.Vector(-20,161),App.Vector(-42,193)],
              None,None,False,3,None,False),False)

  Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',3,3,7,0)
  Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',4,3,7,1)
  Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',5,3,7,2)
  Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',6,3,7,3)
  exposeInternalGeometry(7) # 7
  """

  def __init__(self, sketch, same_point, expose_int=True, circ_r=10, debug=False):
    self.ske = sketch
    self.expose_int = expose_int
    self.same_point = same_point

    self.first_point = None
    self.first_point_idx = None
    self.first_point_circ_idx = None

    self.first_circ_idx = None          # maintained by _find_or_add_circ()
    self.last_point_circ_idx = None
    self.last_point_idx = None
    self.last_point = None
    self.circ_r = circ_r
    self.debug = debug


  def line(self, p1, p2, closing=False):
    if self.same_point(p1, p2):
      return
    idx = int(self.ske.GeometryCount)
    if self.first_point is None:
      self.first_point = p1
      self.first_point_idx = (idx,1)
      self.first_point_circ_idx = None

    self.ske.addGeometry([Part.LineSegment(p1, p2)])
    if self.debug: inkex.utils.debug('line: idx={}'.format(idx))

    if self.last_point is not None and self.same_point(self.last_point, p1):
      if self.debug: inkex.utils.debug('line: Coincident', self.last_point_idx[0], self.last_point_idx[1], idx, 1)
      self.ske.addConstraint(Sketcher.Constraint('Coincident', self.last_point_idx[0], self.last_point_idx[1], idx, 1))
    if closing and self.same_point(self.first_point, p2):
      if self.debug: inkex.utils.debug('line: Coincident Z', idx, 2, self.first_point_idx[0], self.first_point_idx[1])
      self.ske.addConstraint(Sketcher.Constraint('Coincident', idx, 2, self.first_point_idx[0], self.first_point_idx[1]))

    self.last_point = p2
    self.last_point_idx = (idx,2)
    self.last_point_circ_idx = None


  def _find_or_add_circ(self, pt, ptlist, constr=True):
    """
    When adding a constuction circle to a control point in a spline, this method
    checks the ptlist for already exising circles.
    ptlist is a list of tuples, consisting of coordinates and index.

    The index if the circle is returned.
    Caller is responsible to add newly created circles to the ptlist of subsequent invocations.
    """

    if self.debug: inkex.utils.debug("_find_or_add_circ: pt=%s, ptlist=%s" % (pt,ptlist))
    for old in ptlist:
      if self.debug: inkex.utils.debug(" test %s against %s idx=%s" % (pt, old[0], old[1]))
      if old is not None and old[0] is not None and old[1] is not None and self.same_point(old[0], pt):
        if self.debug: inkex.utils.debug(" -> return idx=%s" % (old[1]))
        return old[1]
    idx = int(self.ske.GeometryCount)
    self.ske.addGeometry(Part.Circle(pt, Normal=Base.Vector(0,0,1), Radius=self.circ_r), constr)
    if self.first_circ_idx is None:
      self.ske.addConstraint(Sketcher.Constraint('Radius', idx, self.circ_r))
      self.first_circ_idx = idx
    else:
      self.ske.addConstraint(Sketcher.Constraint('Equal',  idx, self.first_circ_idx))
    return idx


  def cubic(self, p1,h1,h2,p2, closing=False):
    """
    If closing==True, we check for hitting self.first_point
    If we are sure that no intermediate points coincide with the first_point, we can always pass closing=True.
    """

    if ((self.same_point(h1, p1) or self.same_point(h1, p2)) and
        (self.same_point(h2, p2) or self.same_point(h2, p1))):
      self.line(p1, p2, closing)
      return
    idx = int(self.ske.GeometryCount)
    self.ske.addGeometry(Part.BSplineCurve([p1, h1, h2, p2],None,None,False,3,None,False),False)
    if self.debug: inkex.utils.debug("cubic(self, p1=%s,h1=%s,h2=%s,p2=%s, closing=%s) -> idx=%s" % (p1,h1,h2,p2, closing, idx))

    # 4 circles in construction mode
    p1_circ_idx = self._find_or_add_circ(p1, [(self.last_point,self.last_point_circ_idx)])
    if self.first_point is None:
      self.first_point = p1
      self.first_point_idx = (idx,1)
      self.first_point_circ_idx = p1_circ_idx

    ptlist = [(p1,p1_circ_idx)]
    h1_circ_idx = self._find_or_add_circ(h1, ptlist)

    ptlist.append((h1,h1_circ_idx))
    h2_circ_idx = self._find_or_add_circ(h2, ptlist)

    ptlist.append((h2,h2_circ_idx))
    if closing: ptlist.append((self.first_point,self.first_point_circ_idx))
    p2_circ_idx = self._find_or_add_circ(p2, ptlist)

    conList = []
    # register the 4 circles as the 4 control points. Helps tuning...
    conList.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',p1_circ_idx,3,idx,0))
    conList.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',h1_circ_idx,3,idx,1))
    conList.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',h2_circ_idx,3,idx,2))
    conList.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',p2_circ_idx,3,idx,3))
    self.ske.addConstraint(conList)

    if self.expose_int:
      self.ske.exposeInternalGeometry(idx)

    if self.debug: inkex.utils.debug("cubic: test self.same_point(self.last_point=%s, p1=%s)" % (self.last_point, p1))
    if self.last_point is not None and self.same_point(self.last_point, p1):
      if self.debug: inkex.utils.debug("cubic: Coincident", self.last_point_idx[0], self.last_point_idx[1], idx, 1)
      if self.last_point_circ_idx == p1_circ_idx:
        # Be very careful with duplicate constraints. FreeCAD does not like that at all!
        if self.debug: inkex.utils.debug(" -> skipped, they coincide already, as they share a circle")
        pass
      else:
        self.ske.addConstraint(Sketcher.Constraint('Coincident', self.last_point_idx[0], self.last_point_idx[1], idx, 1))
    if closing and self.same_point(self.first_point, p2):
      if self.debug: inkex.utils.debug('cubic: Coincident Z', idx, 2, self.first_point_idx[0], self.first_point_idx[1])
      if self.first_point_circ_idx == p2_circ_idx:
        # Be very careful with duplicate constraints. FreeCAD does not like that at all!
        if self.debug: inkex.utils.debug(" -> skipped, they coincide already, as they share a circle")
      else:
        self.ske.addConstraint(Sketcher.Constraint('Coincident', idx, 2, self.first_point_idx[0], self.first_point_idx[1]))

    self.last_point = p2
    self.last_point_idx = (idx,2)
    self.last_point_circ_idx = p2_circ_idx

class SketchPathGen(PathGenerator):
  """
  Generate XML code for a FreeCAD sketch.
  """
  def __init__(self, ske, yflip=True, expose_int=True):
    self.ske = ske
    self.m = None
    self.yflip = yflip
    self.expose_int = expose_int
    self.bbox = BoundBox()

    # prepare counters how many objects of each type we generate.
    self.stats = {}
    for s in ('pathList', 'pathString', 'objRect', 'objRoundedRect',
              'objArc', 'objEllipse'):
      self.stats[s] = 0


  def _coord_from_svg(self, m=None):
    """
    Use SVG properties set by InkSVG.handleViewBox()
    to define the transformation matrix from dpi'ish SVG space
    into metric FreeCAD space.
    """
    xs = 1.0
    if self._svg.docTransform is not None:
      xs = self._svg.docTransform[0][0]
      if abs(xs) < epsilon:
        xs = 1.0        # avoid divison by zero.
    ys = xs
    if self.yflip: ys = -ys

    if m is None: m = self.m
    m.move(0, -self._svg.docHeight, 0)
    m.scale(1/xs, 1/ys, 1)
    return m

  def _ellipse_vertices2d(self, C, P, Q):
    """
    Compute two vertices of the ellipse, major and minor axis.
    Given two conjugated half diameters P, Q.
    Vectors are expected as FreeCAD Base.Vector() assuming that all Z=0.

    Using a computation derived from Rytz's construction as
    seen in https://en.wikipedia.org/wiki/Rytz%27s_construction.
    Returns (V1, V2, V3, V4) where V1-V4 is the diameter of the major axis
    and V2-V3 is the diameter of the minor axis.
    """
    f0 = C
    f1 = P-C
    f2 = Q-C
    # det = (f1*f1 - f2*f2) / ( 2 * f1 * f2 )     # raise NaN, if flat.
    idet = (2*f1*f2) / (f1*f1 - f2*f2) # raise NaN, if flat or colinear.

    def math_cot(a): return 1/math.tan(a)

    def p(t): return f0 + f1 * math.cos(t) + f2 * math.sin(t)

    # cot(2*t0) = det
    # tan(2*t0) = 1/det
    # tan(2*t0) = idet
    # 2*t0 = atan(idet)
    t0 = 0.5* math.atan(idet)
    V1 = p(t0)
    V2 = p(t0 + 0.5*math.pi)
    V3 = p(t0 - 0.5*math.pi)
    V4 = p(t0 + math.pi)
    if (V1-V4).Length < (V2-V3).Length:
      # V1-V4 should be the major axis.
      (V1,V4, V2,V3) = (V2,V3, V1,V4)
    return (V1, V2, V3, V4)


  def _decompose_matrix2d(self, m=None):
    """
    Decompose a 4x4 matrix into 2d translation vector,
    2d scale vector, and rotation angle.

    Inspired by https://math.stackexchange.com/questions/13150/extracting-rotation-scale-values-from-2d-transformation-matrix
    """
    if m is None: m = self.m
    a =  m.A11
    b =  m.A12
    xc = m.A14          # FIXME: check if correct in _matrix_from_svg()
    c =  m.A21
    d =  m.A22
    yc = m.A24          # FIXME: check if correct in _matrix_from_svg()
    sign_a = -1 if a < 0 else 1
    sign_d = -1 if d < 0 else 1

    sx = sign_a * math.sqrt(a*a + b*b)
    sy = sign_d * math.sqrt(c*c + d*d)

    sign = math.atan(-c / a)
    rad  = math.acos(a / sx)
    deg  = rad * 180. / math.pi
    if (deg > 90 and sign > 0) or (deg < 90 and sign < 0):
      deg = 360 - deg
    rad = deg / 180. * math.pi

    return (Base.Vector(xc, yc), Base.Vector(sx, sy), (rad, deg))


  def _matrix_from_svg(self, svgmat, coordcvt=True):
    svgmat = svgmat.matrix
    """
    Convert a 2D matrix from SVG into a FreeCAD 3D Matrix.
    e.g. mat = [[0.9659258262890683, 0.25881904510252074, 0.0],
               [-0.25881904510252074, 0.9659258262890683, 0.0]]

    If coordcvt is True, then coordinate system conversion from
    SVG to FreeCAD is applied to the matrix. Otherwise only datatype
    conversion is performed.

    Returns:
    e.g. Matrix ((0.965926,0.258819,0,0),(-0.258819,0.965926,0,0),(0,0,1,0),(0,0,0,1))
    """
    # FIXME: is the handling of svgmat[*][2] correct?
    self.m = Base.Matrix(svgmat[0][0], svgmat[0][1], 0, svgmat[0][2],
                         svgmat[1][0], svgmat[1][1], 0, svgmat[1][2])

    if coordcvt:
      self._coord_from_svg()
    return self.m


  def _from_svg(self, x, y, m=None, bbox=True):
    """
    Converts a 2D Vector from SVG into a FreeCAD 3D vector applying Base.Matrix m.
    """
    if m is None: m = self.m
    v = m.multiply(Base.Vector(x, y, 0))
    if bbox: self.bbox.add(v)
    return v

  def _same_point(self, p1, p2, eps=epsilon):
    if p1 is None or p2 is None: return True
    if abs(p1[0]-p2[0]) > eps: return False
    if abs(p1[1]-p2[1]) > eps: return False
    return True

  def _round_sigdigs(self, val, n=2):
    """
    Rounds the value to at most n significant digits.
    0.00426221  -> 0.0043
    3.78        -> 3.8
    997         -> 1000
    994         -> 990
    """
    n = int(max(1, n))
    exp10 = math.floor(math.log10(abs(val))) if val != 0 else 0
    decimal_shifter = float(10**exp10)
    val = round(val/decimal_shifter, n-1)
    # this final round is mathematically useless, but
    # avoids _round_sigdigs(0.000491) -> 0.0004900000000000001
    return round(val*decimal_shifter, int(-exp10+n-1))

  def _average_handle_length(self, sp):
    (tra,sca,rot) = self._decompose_matrix2d()
    sca = 0.5 * (abs(sca[0]) + abs(sca[1]))

    tot = 0
    cnt = 0
    for tri in sp:
      (h1, p, h2) = tri
      if not self._same_point(h1, p):
        tot += math.sqrt( (h1[0]-p[0])*(h1[0]-p[0]) + (h1[1]-p[1])*(h1[1]-p[1]) )
        cnt += 1
      if not self._same_point(h2, p):
        tot += math.sqrt( (h2[0]-p[0])*(h2[0]-p[0]) + (h2[1]-p[1])*(h2[1]-p[1]) )
        cnt += 1
    if (cnt > 0 and tot > 0):
      return self._round_sigdigs(sca*tot/cnt, 2)
    return self._round_sigdigs(sca*10, 2)


  def pathString(self, d, node, mat):
    """
    d is expected formatted as an svg path string here.
    d = "M 30.994048,129.93452 72.571427,88.357143 V 129.93452 H 127" means
    path = [
      [
        #       handle_0                 point                handle_1
        [[30.994048, 129.93452], [30.994048, 129.93452], [30.994048, 129.93452]],
        [[72.571427, 88.357143], [72.571427, 88.357143], [72.571427, 88.357143]],
        [[72.571427, 129.93452], [72.571427, 129.93452], [72.571427, 129.93452]],
        [[127.0, 129.93452],     [127.0, 129.93452],     [127.0, 129.93452]]
      ]
    ]
    """
    self._matrix_from_svg(mat)
    path = CubicSuperPath(d)
    for subpath in path:
      spt = SubPathTracker(self.ske, lambda a,b: self._same_point(a, b), self.expose_int,
                           circ_r=0.1*self._average_handle_length(subpath), debug=(verbose > 0))

      # These are the off by one's: four points -> three lines -> two constraints.
      j = 0
      while j < len(subpath)-1:
        (h0,p1,h1) = subpath[j]
        j = j+1
        while j < len(subpath):
          (h2,p2,h3) = subpath[j]
          if not self._same_point(p1, p2):
            break               # no null-segments, please!
          j += 1
        if j >= len(subpath):
          break                 # nothing left.

        spt.cubic( self._from_svg(p1[0], p1[1]), self._from_svg(h1[0], h1[1]),
                   self._from_svg(h2[0], h2[1]), self._from_svg(p2[0], p2[1]), closing=(j+1 == len(subpath)) )

      self.stats['pathString'] += 1     # count subpaths


  def pathList(self, d, node, mat):
    """
    d is expected as an [[cmd, [args]], ...] arrray
    """
    inkex.utils.debug(d, node, mat)
    i = int(self.ske.GeometryCount)      # 0
    geo = []
    geo.append(Part.LineSegment(Base.Vector(4,8,0),Base.Vector(9,8,0)))
    geo.append(Part.LineSegment(Base.Vector(9,8,0),Base.Vector(9,2,0)))
    self.ske.addGeometry(geo, False)
    inkex.utils.debug("GeometryCount changed from %d to %d" % (i, int(self.ske.GeometryCount)))
    inkex.utils.debug("not impl. simplePath: ", d, node, mat)


  def objRoundedRect(self, x, y, w, h, rx, ry, node, mat):
    """
    Construct four arcs, one for each corner, and
    connect them with line segments, if space permits.
    Connect them directly otherwise.
    """
    if rx == 0: rx = ry
    if ry == 0: ry = rx
    if rx < epsilon or ry < epsilon:
      return self.objRect(x, y, w, h, node, mat)
    if 2*rx > w-epsilon: rx = 0.5*(w-epsilon)   # avoid Part.OCCError: Both points are equal" on LineSegment #12
    if 2*ry > h-epsilon: ry = 0.5*(h-epsilon)

    if verbose > 0: inkex.utils.debug("objRoundedRect: ", x, y, w, h, rx, ry, node.get('id'), mat)

    self._matrix_from_svg(mat)
    i = int(self.ske.GeometryCount)
    ske.addGeometry([
      # construction outline of the box
      Part.LineSegment(self._from_svg(x  ,y  ), self._from_svg(x+w,y  )),               # 0
      Part.LineSegment(self._from_svg(x+w,y  ), self._from_svg(x+w,y+h)),               # 1
      Part.LineSegment(self._from_svg(x+w,y+h), self._from_svg(x  ,y+h)),               # 2
      Part.LineSegment(self._from_svg(x  ,y+h), self._from_svg(x  ,y  )),               # 3
      # construction four corners
      Part.LineSegment(self._from_svg(x+rx,y   ), self._from_svg(x+rx,y+ry)),           # 4
      Part.LineSegment(self._from_svg(x+rx,y+ry), self._from_svg(x   ,y+ry)),           # 5
      Part.LineSegment(self._from_svg(x+w-rx,y   ), self._from_svg(x+w-rx,y+ry)),       # 6
      Part.LineSegment(self._from_svg(x+w-rx,y+ry), self._from_svg(x+w   ,y+ry)),       # 7
      Part.LineSegment(self._from_svg(x+w-rx,y+h   ), self._from_svg(x+w-rx,y+h-ry)),   # 8
      Part.LineSegment(self._from_svg(x+w-rx,y+h-ry), self._from_svg(x+w   ,y+h-ry)),   # 9
      Part.LineSegment(self._from_svg(x+rx,y+h   ), self._from_svg(x+rx,y+h-ry)),       # 10
      Part.LineSegment(self._from_svg(x+rx,y+h-ry), self._from_svg(x   ,y+h-ry))        # 11
    ], True)
    self.ske.addConstraint([
      ## outer construction corners
      Sketcher.Constraint('Coincident', i+0,2, i+1,1),
      Sketcher.Constraint('Coincident', i+1,2, i+2,1),
      Sketcher.Constraint('Coincident', i+2,2, i+3,1),
      Sketcher.Constraint('Coincident', i+3,2, i+0,1),
      ## inner construction corners
      Sketcher.Constraint('Coincident', i+4,2, i+5,1),
      Sketcher.Constraint('Coincident', i+6,2, i+7,1),
      Sketcher.Constraint('Coincident', i+8,2, i+9,1),
      Sketcher.Constraint('Coincident', i+10,2, i+11,1),
      ## inner construction equality
      Sketcher.Constraint('Equal', i+4, i+6),
      Sketcher.Constraint('Equal', i+4, i+8),
      Sketcher.Constraint('Equal', i+4, i+10),
      Sketcher.Constraint('Equal', i+5, i+7),
      Sketcher.Constraint('Equal', i+5, i+9),
      Sketcher.Constraint('Equal', i+5, i+11),
      ## corner cube outlines construction
      Sketcher.Constraint('PointOnObject',i+4,1, i+0),
      Sketcher.Constraint('PointOnObject',i+5,2, i+3),
      Sketcher.Constraint('PointOnObject',i+6,1, i+0),
      Sketcher.Constraint('PointOnObject',i+7,2, i+1),
      Sketcher.Constraint('PointOnObject',i+8,1, i+2),
      Sketcher.Constraint('PointOnObject',i+9,2, i+1),
      Sketcher.Constraint('PointOnObject',i+10,1, i+2),
      Sketcher.Constraint('PointOnObject',i+11,2, i+3),
      ## horizontal construction
      Sketcher.Constraint('Parallel', i, i+2),
      Sketcher.Constraint('Parallel', i, i+5),
      Sketcher.Constraint('Parallel', i, i+7),
      Sketcher.Constraint('Parallel', i, i+9),
      Sketcher.Constraint('Parallel', i, i+11),
      ## vertical construction
      Sketcher.Constraint('Parallel', i+1, i+3),
      Sketcher.Constraint('Parallel', i+1, i+4),
      Sketcher.Constraint('Parallel', i+1, i+6),
      Sketcher.Constraint('Parallel', i+1, i+8),
      Sketcher.Constraint('Parallel', i+1, i+10)
    ])
    ske.addGeometry([
      # sides of the rect
      Part.LineSegment(self._from_svg(x+rx  ,y     ), self._from_svg(x+w-rx,y     )),   # 12
      Part.LineSegment(self._from_svg(x+w   ,y+ry  ), self._from_svg(x+w   ,y+h-ry)),   # 13
      Part.LineSegment(self._from_svg(x+w-rx,y+h   ), self._from_svg(x+rx  ,y+h   )),   # 14
      Part.LineSegment(self._from_svg(x     ,y+h-ry), self._from_svg(x     ,y+ry  ))    # 15
    ])
    # arcs top left, top right, botton right, bottom left.
    # circles rotate counter clockwise. pi/2 is north, pi is west, 2*pi is east
    a_tl = self.objArc("", x+rx  , y+ry,   rx, ry, -2/2.*math.pi, -1/2.*math.pi, False, node, mat)
    a_tr = self.objArc("", x-rx+w, y+ry,   rx, ry, -1/2.*math.pi,  0/2.*math.pi, False, node, mat)
    a_br = self.objArc("", x-rx+w, y-ry+h, rx, ry,  0/2.*math.pi,  1/2.*math.pi, False, node, mat)
    a_bl = self.objArc("", x+rx  , y-ry+h, rx, ry,  1/2.*math.pi,  2/2.*math.pi, False, node, mat)
    if True:
      self.ske.addConstraint([
        # connect the corners to the edges. smooth
        Sketcher.Constraint('Tangent', a_tl[1][0],a_tl[1][1], i+12,1),
        Sketcher.Constraint('Tangent', i+12,2, a_tr[0][0],a_tr[0][1]),
        Sketcher.Constraint('Tangent', a_tr[1][0],a_tr[1][1], i+13,1),
        Sketcher.Constraint('Tangent', i+13,2, a_br[0][0],a_br[0][1]),
        Sketcher.Constraint('Tangent', a_br[1][0],a_br[1][1], i+14,1),
        Sketcher.Constraint('Tangent', i+14,2, a_bl[0][0],a_bl[0][1]),
        Sketcher.Constraint('Tangent', a_bl[1][0],a_bl[1][1], i+15,1),
        Sketcher.Constraint('Tangent', i+15,2, a_tl[0][0],a_bl[0][1]),
      ])
    if False:
      self.ske.addConstraint([
        # stitch the rounded rect to the construction grid
        Sketcher.Constraint('Coincident', i+12,1, i+4,1),
        Sketcher.Constraint('Coincident', i+12,2, i+6,1),
        Sketcher.Constraint('Coincident', i+13,1, i+7,2),
        Sketcher.Constraint('Coincident', i+13,2, i+9,2),
        Sketcher.Constraint('Coincident', i+14,1, i+8,1),
        Sketcher.Constraint('Coincident', i+14,2, i+10,1),
        Sketcher.Constraint('Coincident', i+15,1, i+11,2),
        Sketcher.Constraint('Coincident', i+15,2, i+5,2)
      ])
    if False and a_tr[3] is not None:         # ArcOfCirle has no majAxis
      self.ske.addConstraint([
        # make all major axis parallel, and same length
        Sketcher.Constraint('Parallel', a_tr[3], a_tl[3]),
        Sketcher.Constraint('Equal',    a_tr[3], a_tl[3]),
        Sketcher.Constraint('Parallel', a_tr[3], a_bl[3]),
        Sketcher.Constraint('Equal',    a_tr[3], a_bl[3]),
        Sketcher.Constraint('Parallel', a_tr[3], a_br[3]),
        # Sketcher.Constraint('Equal',    a_tr[3], a_br[3])     # makes everything immobole
      ])

    self.stats['objRect'] += 1


  def objRect(self, x, y, w, h, node, mat):
    self._matrix_from_svg(mat)
    i = int(self.ske.GeometryCount)
    self.ske.addGeometry([
      Part.LineSegment(self._from_svg(x  ,y  ), self._from_svg(x+w,y  )),
      Part.LineSegment(self._from_svg(x+w,y  ), self._from_svg(x+w,y+h)),
      Part.LineSegment(self._from_svg(x+w,y+h), self._from_svg(x  ,y+h)),
      Part.LineSegment(self._from_svg(x  ,y+h), self._from_svg(x  ,y  ))
    ], False)
    self.ske.addConstraint([
      Sketcher.Constraint('Coincident', i+0,2, i+1,1),
      Sketcher.Constraint('Coincident', i+1,2, i+2,1),
      Sketcher.Constraint('Coincident', i+2,2, i+3,1),
      Sketcher.Constraint('Coincident', i+3,2, i+0,1),
      Sketcher.Constraint('Parallel', i+2, i+0),
      Sketcher.Constraint('Parallel', i+3, i+1)
    ])
    self.stats['objRect'] += 1


  def objEllipse(self, cx, cy, rx, ry, node, mat):
    """
    We distinguish two cases. If it looks like a circle (after transformation),
    we produce a Circle, else we produce an Ellipse.
    The difference is clearly visible as we exposeInternalGeometry() of the Ellipse.
    """
    ### CAUTION: Keep in sync with objArc() below.
    self._matrix_from_svg(mat)
    c = self._from_svg(cx, cy, bbox=False)
    ori = self._from_svg(0, 0, bbox=False)
    vrx = self._from_svg(rx, 0, bbox=False) - ori
    vry = self._from_svg(0, ry, bbox=False) - ori
    i = int(self.ske.GeometryCount)

    if abs(vrx.Length - vry.Length) < epsilon:
      # it is a circle.
      self.bbox.add(c+vrx+vry)
      self.bbox.add(c-vrx-vry)
      self.ske.addGeometry([ Part.Circle(Center=c, Normal=Base.Vector(0,0,1), Radius=vrx.Length) ])
      self.stats['objEllipse'] += 1
    else:
      # major axis is defined by Center and S1,
      # major radius is the distance between Center and S1,
      # minor radius is the distance between S2 and the major axis.
      s1 = self._from_svg(cx+rx, cy, bbox=False)
      s2 = self._from_svg(cx, cy+ry, bbox=False)
      (V1,V2,V3,V4) = self._ellipse_vertices2d(c, s1, s2)
      self.bbox.add(V1)
      self.bbox.add(V2)
      self.bbox.add(V3)
      self.bbox.add(V4)
      self.ske.addGeometry([ Part.Ellipse(S1=V1, S2=V2, Center=c), ])
      if self.expose_int: self.ske.exposeInternalGeometry(i)
      self.stats['objEllipse'] += 1


  def objArc(self, d, cx, cy, rx, ry, st, en, closed, node, mat):
    """
    We ignore the path d, and produce a nice arc object.
    We distinguish two cases. If it looks like a circle, we produce ArcOfCircle,
    else we produce ArcOfEllipse.

    To find the arc end points, we use the value() property of the Circle and Ellipse
    objects. With Circle we have to take care of mirror and rotation ourselves.

    If closed, we connect the two ends to the center with lines. The connections
    are secured with constraints.
    Radii are currently not secured with constraints.
    """
    ### CAUTION: Keep in sync with objEllipse() above.
    # inkex.utils.debug("objArc: st,en,closed", st, en, closed)
    self._matrix_from_svg(mat)
    c = self._from_svg(cx, cy, bbox=False)
    ori = self._from_svg(0, 0, bbox=False)
    vrx = self._from_svg(rx, 0, bbox=False) - ori
    vry = self._from_svg(0, ry, bbox=False) - ori
    i = self.ske.GeometryCount
    (st_idx,en_idx) = (1,2)
    majAxisIdx = None

    if abs(vrx.Length - vry.Length) < epsilon:
      # it is a circle.
      self.bbox.add(c+vrx+vry)
      self.bbox.add(c-vrx-vry)
      ce = Part.Circle(Center=c, Normal=Base.Vector(0,0,1), Radius=vrx.Length)

      # Circles are immune to rotation and mirorring. Apply this manually.
      if self.yflip:
        (st,en) = (-en,-st)                     ## coord system is mirrored.
      else:
        (st,en) = (en,st)                       ## hmm.
        inkex.utils.debug("FIXME: ArcOfCircle() with yflip=False needs debugging.")
      r = Base.Matrix()
      r.rotateZ(st)
      pst = r.multiply(vrx)
      st = pst.getAngle(Base.Vector(1,0,0))     # ce.rotateZ() is a strange beast.
      pst = pst + c
      r = Base.Matrix()
      r.rotateZ(en)
      pen = r.multiply(vrx)
      en = pen.getAngle(Base.Vector(1,0,0))     # ce.rotateZ() is a strange beast.
      pen = pen + c

      self.ske.addGeometry([ Part.ArcOfCircle(ce, st, en) ])
      self.stats['objArc'] += 1

    else:
      # major axis is defined by Center and S1,
      # major radius is the distance between Center and S1,
      # minor radius is the distance between S2 and the major axis.
      s1 = self._from_svg(cx+rx, cy, bbox=False)
      s2 = self._from_svg(cx, cy+ry, bbox=False)
      (V1,V2,V3,V4) = self._ellipse_vertices2d(c, s1, s2)
      self.bbox.add(V1)
      self.bbox.add(V2)
      self.bbox.add(V3)
      self.bbox.add(V4)
      i = int(self.ske.GeometryCount)
      ce = Part.Ellipse(S1=V1, S2=V2, Center=c)
      self.ske.addGeometry([ Part.ArcOfEllipse(ce, st, en) ])
      if self.expose_int: self.ske.exposeInternalGeometry(i)
      majAxisIdx = i+1          # CAUTION: is that a safe assumption?
      self.stats['objArc'] += 1
      ## CAUTION: with yflip=True sketcher reverses the endpoints of
      ##          an ArcOfEllipse to: en=1, st=2
      ##          ArcOfCircle seems unaffected.
      if self.yflip: (st_idx,en_idx) = (2,1)
      r = Base.Matrix()
      r.rotateZ(st)
      pst = r.multiply(vrx) + c
      r = Base.Matrix()
      r.rotateZ(en)
      pen = r.multiply(vrx) + c

    j = self.ske.GeometryCount
    if closed:
      self.ske.addGeometry([
        Part.LineSegment(ce.value(en),c),
        Part.LineSegment(c,ce.value(st)) ])

      if True:          # when debugging deformations, switch off constriants first.
        self.ske.addConstraint([
          Sketcher.Constraint('Coincident', i+0,en_idx, j+0,1),   # arc with line
          Sketcher.Constraint('Coincident', j+1,2, i+0,st_idx),   # line with arc
          Sketcher.Constraint('Coincident', j+0,2, j+1,1),        # line with line
          Sketcher.Constraint('Coincident', j+0,2, i+0,3) ])      # line with center

    if False:    # some debugging circles.
      self.ske.addGeometry([
        # Part.Circle(Center=pst, Normal=Base.Vector(0,0,1), Radius=2),
        # Part.Circle(Center=pen, Normal=Base.Vector(0,0,1), Radius=3),
        # Part.Circle(Center=ce.value(st), Normal=Base.Vector(0,0,1), Radius=4),
        Part.Circle(Center=ce.value(en), Normal=Base.Vector(0,0,1), Radius=5)
        ], True)

    # we return the start, end and center points, as triple (sketcher_index, sketcher_index_point, Vector)
    return ((i+0, st_idx, ce.value(st)), (i+0, en_idx, ce.value(en)), (i+0, 3, c), majAxisIdx)

fcdoc = FreeCAD.newDocument(docname)
ske = fcdoc.addObject('Sketcher::SketchObject', 'Sketch_'+docname)

svg = InkSvg(pathgen=SketchPathGen(ske, yflip=True, expose_int=((options.expose_internal_geometry+"0")[0] not in "Ff0")))
svg.load(svgfile)       # respin of inkex.affect()
svg.traverse(options.ids)

if verbose > 0:
  inkex.utils.debug("InkSvg %s" % (InkSvg.__version__))
if verbose >= 0:
  inkex.utils.debug(svg.stats)
# inkex.utils.debug(svg.docTransform, svg.docWidth, svg.docHeight, svg.dpi)

# inkex.utils.debug(ske)
#fcdoc.recompute()

if not options.outfile:
  import tempfile
  fcstdfile = tempfile.mktemp(prefix=docname, suffix='.FCStd')

fcdoc.saveAs(fcstdfile)
## Add GuiDocument.xml to the zip archive of fcstdfile
## to switch on default visibilitiy, and set a default camera.
camera_xml = ''
if True:        # switch off, if this causes errors. Nice to have.
  bb = svg.pathgen.bbox
  if verbose >= 0: inkex.utils.debug(bb)
  cx = bb.Center.x   # 35.246845 # bbox center
  cy = bb.Center.y   # 37.463238 # bbox center
  cz = bb.DiagonalLength * 0.5  # 51.437702 # focal distance: 1/2 of bbox diagonal
  zd = cz * 0.001             # 0.05 # +/- for far/near distance
  camera_xml = """<Camera settings="  OrthographicCamera { viewportMapping ADJUST_CAMERA position %f %f %f orientation 0 0 1  0 nearDistance %f farDistance %f aspectRatio 1 focalDistance %f height %f } "/>""" % (cx,cy,cz, cz-zd, cz+zd, cz, 2*cz)
guidoc_xml = """<?xml version='1.0' encoding='utf-8'?>
<Document SchemaVersion="1"><!-- as seen in FreeCAD 0.17 -->
    <ViewProviderData Count="1">
        <ViewProvider name="%s" expanded="0">
            <Properties Count="1">
                <Property name="Visibility" type="App::PropertyBool">
                    <Bool value="true"/>
                </Property>
            </Properties>
        </ViewProvider>
    </ViewProviderData>
    %s
</Document>
""" % ('Sketch_'+docname, camera_xml)

try:
  import zipfile
  z = zipfile.ZipFile(fcstdfile, 'a')
  z.writestr('GuiDocument.xml', guidoc_xml)
  z.close()
except:
  inkex.utils.debug(guidoc_xml)
  inkex.utils.debug("Warning: Failed to add GuiDocument.xml to %s -- camera and visibility are undefined." % fcstdfile)

if verbose > -1:
  inkex.utils.debug("%s written." % fcstdfile)

if not options.outfile:   
  out = open(fcstdfile,'rb')
  sys.stdout.buffer.write(out.read())
  out.close()
  os.unlink(fcstdfile)
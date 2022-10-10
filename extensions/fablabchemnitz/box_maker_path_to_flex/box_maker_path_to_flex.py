#!/usr/bin/env python3


# paths2flex.py

# This is an Inkscape extension to generate boxes with sides as flex which follow a path selected in inkscape 
# The Inkscape objects must first be converted to paths (Path > Object to Path).
# Some paths may not work well -- if the curves are too small for example.

# Written by Thierry Houdoin (thierry@fablab-lannion.org), december 2018
# This work is largely inspred from path2openSCAD.py, written by Daniel C. Newman

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import math
import os.path
import inkex
import re
from lxml import etree
from inkex import bezier
from inkex.paths import Path, CubicSuperPath

DEFAULT_WIDTH = 100
DEFAULT_HEIGHT = 100

objStyle = str(inkex.Style(
    {'stroke': '#000000',
    'stroke-width': 0.1,
    'fill': 'none'
    }))

objStyleStart = str(inkex.Style(
    {'stroke': '#FF0000',
    'stroke-width': 0.1,
    'fill': 'none'
    }))


class inkcape_draw_cartesian:
    def __init__(self, Offset, group):
        self.offsetX = Offset[0]
        self.offsetY = Offset[1]
        self.Path = ''
        self.group = group
    
    def MoveTo(self, x, y):
    #Retourne chaine de caractères donnant la position du point avec des coordonnées cartesiennes
        self.Path += ' M ' + str(round(x-self.offsetX, 3)) + ',' + str(round(y-self.offsetY, 3))

    def LineTo(self, x, y):
    #Retourne chaine de caractères donnant la position du point avec des coordonnées cartesiennes
        self.Path += ' L ' + str(round(x-self.offsetX, 3)) + ',' + str(round(y-self.offsetY, 3))

    def Line(self, x1, y1, x2, y2):
    #Retourne chaine de caractères donnant la position du point avec des coordonnées cartesiennes
        self.Path += ' M ' + str(round(x1-self.offsetX, 3)) + ',' + str(round(y1-self.offsetY, 3)) + ' L ' + str(round(x2-self.offsetX, 3)) + ',' + str(round(y2-self.offsetY, 3))
    
    def GenPath(self):
        line_attribs = {'style': objStyle, 'd': self.Path}
        etree.SubElement(self.group, inkex.addNS('path', 'svg'), line_attribs)

    def GenPathStart(self):
        line_attribs = {'style': objStyleStart, 'd': self.Path}
        etree.SubElement(self.group, inkex.addNS('path', 'svg'), line_attribs)


class Line:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c
    def __str__(self):
        return "Line a="+str(self.a)+" b="+str(self.b)+" c="+str(self.c)
    
    def Intersect(self, Line2):
        ''' Return the point which is at the intersection between the two lines
        '''
        det = Line2.a * self.b - self.a*Line2.b;
        if abs(det) < 1e-6:         # Line are parallel, return None
            return None
        return ((Line2.b*self.c - Line2.c*self.b)/det, (self.a*Line2.c - Line2.a*self.c)/det)

    def square_line_distance(self, pt):
        ''' 
        Compute the distance between point and line
        Distance between point and line is (a * pt.x + b * pt.y + c)*(a * pt.x + b * pt.y + c)/(a*a + b*b)
        '''
        return (self.a * pt[0] + self.b * pt[1] + self.c)*(self.a * pt[0]+ self.b * pt[1] + self.c)/(self.a*self.a + self.b*self.b)
        
class Segment(Line):
    def __init__(self, A, B):
        self.xA = A[0]
        self.xB = B[0]
        self.yA = A[1]
        self.yB = B[1]
        self.xm = min(self.xA, self.xB)
        self.xM = max(self.xA, self.xB)
        self.ym = min(self.yA, self.yB)
        self.yM = max(self.yA, self.yB)
        Line.__init__(self, A[1] - B[1], B[0] - A[0], A[0] * B[1] - B[0] * A[1])

    def __str__(self):
        return "Segment "+str([A,B])+ " a="+str(self.a)+" b="+str(self.b)+" c="+str(self.c)

    def InSegment(self, Pt):
        if  Pt[0] < self.xm or Pt[0] > self.xM:
            return 0     #  Impossible lower than xmin or greater than xMax
        if  Pt[1] < self.ym or Pt[1] > self.yM:
            return 0     #  Impossible lower than ymin or greater than yMax
        return 1

    def __str__(self):
        return "Seg"+str([(self.xA, self.yA), (self.xB, self.yB)])+" Line a="+str(self.a)+" b="+str(self.b)+" c="+str(self.c)

def pointInBBox(pt, bbox):

    '''
    Determine if the point pt=[x, y] lies on or within the bounding
    box bbox=[xmin, xmax, ymin, ymax].
    '''

    # if (x < xmin) or (x > xmax) or (y < ymin) or (y > ymax)
    if (pt[0] < bbox[0]) or (pt[0] > bbox[1]) or \
        (pt[1] < bbox[2]) or (pt[1] > bbox[3]):
        return False
    else:
        return True

def bboxInBBox(bbox1, bbox2):

    '''
    Determine if the bounding box bbox1 lies on or within the
    bounding box bbox2.  NOTE: we do not test for strict enclosure.

    Structure of the bounding boxes is

    bbox1 = [ xmin1, xmax1, ymin1, ymax1 ]
    bbox2 = [ xmin2, xmax2, ymin2, ymax2 ]
    '''

    # if (xmin1 < xmin2) or (xmax1 > xmax2) or (ymin1 < ymin2) or (ymax1 > ymax2)

    if (bbox1[0] < bbox2[0]) or (bbox1[1] > bbox2[1]) or \
        (bbox1[2] < bbox2[2]) or (bbox1[3] > bbox2[3]):
        return False
    else:
        return True

def pointInPoly(p, poly, bbox=None):

    '''
    Use a ray casting algorithm to see if the point p = [x, y] lies within
    the polygon poly = [[x1,y1],[x2,y2],...].  Returns True if the point
    is within poly, lies on an edge of poly, or is a vertex of poly.
    '''

    if (p is None) or (poly is None):
        return False

    # Check to see if the point lies outside the polygon's bounding box
    if not bbox is None:
        if not pointInBBox(p, bbox):
            return False

    # Check to see if the point is a vertex
    if p in poly:
        return True

    # Handle a boundary case associated with the point
    # lying on a horizontal edge of the polygon
    x = p[0]
    y = p[1]
    p1 = poly[0]
    p2 = poly[1]
    for i in range(len(poly)):
        if i != 0:
            p1 = poly[i-1]
            p2 = poly[i]
        if (y == p1[1]) and (p1[1] == p2[1]) and \
            (x > min(p1[0], p2[0])) and (x < max(p1[0], p2[0])):
            return True

    n = len(poly)
    inside = False

    p1_x,p1_y = poly[0]
    for i in range(n + 1):
        p2_x,p2_y = poly[i % n]
        if y > min(p1_y, p2_y):
            if y <= max(p1_y, p2_y):
                if x <= max(p1_x, p2_x):
                    if p1_y != p2_y:
                        intersect = p1_x + (y - p1_y) * (p2_x - p1_x) / (p2_y - p1_y)
                        if x <= intersect:
                            inside = not inside
                    else:
                        inside = not inside
        p1_x,p1_y = p2_x,p2_y

    return inside

def polyInPoly(poly1, bbox1, poly2, bbox2):

    '''
    Determine if polygon poly2 = [[x1,y1],[x2,y2],...]
    contains polygon poly1.

    The bounding box information, bbox=[xmin, xmax, ymin, ymax]
    is optional.  When supplied it can be used to perform rejections.
    Note that one bounding box containing another is not sufficient
    to imply that one polygon contains another.  It's necessary, but
    not sufficient.
    '''

    # See if poly1's bboundin box is NOT contained by poly2's bounding box
    # if it isn't, then poly1 cannot be contained by poly2.

    if (not bbox1 is None) and (not bbox2 is None):
        if not bboxInBBox(bbox1, bbox2):
            return False

    # To see if poly1 is contained by poly2, we need to ensure that each
    # vertex of poly1 lies on or within poly2

    for p in poly1:
        if not pointInPoly(p, poly2, bbox2):
            return False

    # Looks like poly1 is contained on or in Poly2

    return True

def subdivideCubicPath(sp, flat, i=1):

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

            if bezier.maxdist(b) > flat:
                break

            i += 1

        one, two = bezier.beziersplitatt(b, 0.5)
        sp[i - 1][2] = one[1]
        sp[i][0] = two[2]
        p = [one[2], one[3], two[1]]
        sp[i:1] = [p]
        
# Second degree equation solver.
# Return a tuple with the two real solutions, raise an error if there is no real solution
def Solve2nd(a, b, c):
    delta = b**2 - 4*a*c
    if (delta < 0):
        print("No real solution")
        return none
    x1 = (-b + math.sqrt(delta))/(2*a)
    x2 = (-b - math.sqrt(delta))/(2*a)
    return (x1, x2)

#   Compute distance between two points
def distance2points(x0, y0, x1, y1):
    return math.hypot(x0-x1,y0-y1)
    
class BoxMakerPathToFlex(inkex.EffectExtension):

    def add_arguments(self, pars):
        self.knownUnits = ['in', 'pt', 'px', 'mm', 'cm', 'm', 'km', 'pc', 'yd', 'ft']
        pars.add_argument('--unit', default = 'mm', help = 'Unit, should be one of ')
        pars.add_argument('--thickness', type = float, default = '3.0', help = 'Material thickness')
        pars.add_argument('--zc', type = float, default = '50.0', help = 'Flex height')
        pars.add_argument('--notch_interval', type = int, default = '2', help = 'Interval between notches')
        pars.add_argument('--max_size_flex', type = float, default = '1000.0', help = 'Max size of a single band of flex, above this limit it will be cut')
        pars.add_argument('--Mode_Debug', type = inkex.Boolean, default = 'false', help = 'Output Debug information in file')

        # Dictionary of paths we will construct.  It's keyed by the SVG node
        # it came from.  Such keying isn't too useful in this specific case,
        # but it can be useful in other applications when you actually want
        # to go back and update the SVG document
        self.paths = {}
        
        self.flexnotch = []
        # Debug Output file
        self.fDebug = None

        # Dictionary of warnings issued.  This to prevent from warning
        # multiple times about the same problem
        self.warnings = {}
        
        #Get bounding rectangle
        self.xmin, self.xmax = (1.0E70, -1.0E70)
        self.ymin, self.ymax = (1.0E70, -1.0E70)
        self.cx = float(DEFAULT_WIDTH) / 2.0
        self.cy = float(DEFAULT_HEIGHT) / 2.0

        def unittouu(self, unit):
            return inkex.unittouu(unit)

    def DebugMsg(self, s):
        if self.fDebug:
            self.fDebug.write(s)

    # Generate long vertical lines for flex
    #   Parameters : StartX, StartY, size, nunmber of lines and +1 if lines goes up and -1 down
    def GenLinesFlex(self, StartX, StartY, Size, nLine, UpDown, path):
        for i in range(nLine):
            path.Line(StartX, StartY, StartX, StartY + UpDown*Size)
            self.DebugMsg("GenLinesFlex from "+str((StartX, StartY))+" to "+str((StartX, StartY + UpDown*Size))+'\n')
            StartY += UpDown*(Size+2)


    # Generate the path link to a flex step
    #
    def generate_step_flex(self, step, size_notch, ShortMark, LongMark, nMark, index):
        path = inkcape_draw_cartesian(self.OffsetFlex, self.group)
        #External part of the notch, fraction of total notch
        notch_useful = 2.0 / (self.notchesInterval + 2) 
        # First, link towards next step
        # Line from ((step+1)*size_notch, 0) to ((step+0.5)*size_notch, 0 
        path.Line((step+1)*size_notch, 0, (step+notch_useful)*size_notch, 0)
        if  self.flexnotch[index] == 0:
            ShortMark = 0
        # Then ShortLine from ((step+notch_useful)*size_notch, ShortMark) towards ((step+notch_useful)*size_notch, -Thickness)
        path.Line((step+notch_useful)*size_notch, ShortMark,(step+notch_useful)*size_notch, -self.thickness)
        # Then notch
        path.LineTo(step*size_notch, -self.thickness)
        # Then short mark towards other side (step*size_notch, shortmark)
        path.LineTo(step*size_notch, ShortMark)
        if ShortMark != 0:          #Only if there is flex
            # Then line towards center
            self.GenLinesFlex(step*size_notch, ShortMark + 2, (self.height - 2*ShortMark - 2.0)/(nMark-1) - 2.0, nMark-1, 1, path)
        # Then notch
        path.Line(step*size_notch, self.height - ShortMark, step*size_notch, self.height + self.thickness)
        path.LineTo((step+notch_useful)*size_notch, self.height + self.thickness)
        path.LineTo((step+notch_useful)*size_notch, self.height - ShortMark)
        if ShortMark != 0:
            #Then nMark-1 Lines
            self.GenLinesFlex((step+notch_useful)*size_notch, self.height - ShortMark - 2, (self.height - 2*ShortMark - 2.0)/(nMark-1) - 2.0, nMark-1, -1, path)
            #Then Long lines internal to notch
            self.GenLinesFlex((step+notch_useful/2)*size_notch, 1 - self.thickness, (self.height + 2.0*self.thickness)/nMark - 2, nMark, 1, path)
        # link towards next One
        path.Line((step+notch_useful)*size_notch,  self.height, (step+1)*size_notch, self.height)
        if ShortMark != 0:
            # notchesInterval *nMark Long lines up to next notch or 2 shorts and nMark-1 long
            i = 1
            while i < self.notchesInterval:
                pos = (i + 2.0) / (self.notchesInterval + 2.0)
                if i % 2 :
                    #odd draw from bottom to top, nMark lines
                    self.GenLinesFlex((step+pos)*size_notch, self.height - 1, self.height /nMark - 2.0, nMark, -1, path)
                else:
                    # even draw from top to bottom nMark+1 lines, 2 short and nMark-1 Long
                    path.Line((step+pos)*size_notch, 3, (step+pos)*size_notch, ShortMark)
                    self.GenLinesFlex((step+pos)*size_notch, ShortMark + 2, (self.height - 2*ShortMark - 2.0)/(nMark-1) - 2.0, nMark-1, 1, path)
                    path.Line((step+pos)*size_notch, self.height - ShortMark, (step+pos)*size_notch, self.height - 3)
                i += 1
            # Write path to inkscape
        path.GenPath()
        
    def GenerateStartFlex(self, size_notch, ShortMark, LongMark, nMark, index):
        '''
        Draw the start pattern
        The notch is only 1 mm wide, to enable putting both start and end notch in the same hole in the cover
        '''
        path = inkcape_draw_cartesian(self.OffsetFlex, self.group)
        #External part of the notch, fraction of total notch
        notch_useful = 1.0 / (self.notchesInterval + 2) 
        notch_in = self.notchesInterval / (self.notchesInterval + 2.0) 
        # First, link towards next step
        # Line from (, 0) to 0, 0 
        path.Line(-notch_in*size_notch, 0, 0, 0)
        if  self.flexnotch[index] == 0:
            ShortMark = 0
        # Then ShortLine from (-notch_in*size_notch, ShortMark) towards -notch_in*size_notch, Thickness)
        path.Line(-notch_in*size_notch, ShortMark, -notch_in*size_notch, -self.thickness)
        # Then notch (beware, only size_notch/4 here) 
        path.LineTo((notch_useful-1)*size_notch, -self.thickness)
        # Then edge, full length
        path.LineTo((notch_useful-1)*size_notch, self.height+self.thickness)
        # Then notch
        path.LineTo(-notch_in*size_notch, self.height + self.thickness)
        path.LineTo(-notch_in*size_notch, self.height - ShortMark + 1)
        if ShortMark != 0:
            #Then nMark - 1 Lines
            self.GenLinesFlex(-notch_in*size_notch, self.height - ShortMark - 2, (self.height - 2*ShortMark - 2.0)/(nMark-1) - 2.0, nMark-1, -1, path)
        # link towards next One
        path.Line(-notch_in*size_notch,  self.height, 0, self.height)
        if ShortMark != 0:
            # notchesInterval *nMark Long lines up to next notch or 2 shorts and nMark-1 long
            i = 1
            while i < self.notchesInterval:
                pos = (i - self.notchesInterval) / (self.notchesInterval + 2.0)
                if i % 2 :
                    #odd draw from bottom to top, nMark lines
                    self.GenLinesFlex(pos*size_notch, self.height - 1, self.height /nMark - 2.0, nMark, -1, path)
                else:
                    # even draw from top to bottom nMark+1 lines, 2 short and nMark-1 Long
                    path.Line(pos*size_notch, 3, pos*size_notch, ShortMark)
                    self.GenLinesFlex(pos*size_notch, ShortMark + 2, (self.height - 2*ShortMark - 2.0)/(nMark-1) - 2.0, nMark-1, 1, path)
                    path.Line(pos*size_notch, self.height - ShortMark, pos*size_notch, self.height - 3)
                i += 1
        path.GenPath()


    def GenerateEndFlex(self, step, size_notch, ShortMark, LongMark, nMark, index):
        path = inkcape_draw_cartesian(self.OffsetFlex, self.group)
        delta_notch = 1.0 / (self.notchesInterval + 2.0)
        if  self.flexnotch[index] == 0:
            ShortMark = 0
        # ShortLine from (step*size_notch, ShortMark) towards step*size_notch, -Thickness)
        path.Line(step*size_notch, ShortMark, step*size_notch, -self.thickness)
        # Then notch (beware, only 1mm here) 
        path.LineTo((step+delta_notch)*size_notch, -self.thickness)
        # Then edge, full length
        path.LineTo((step+delta_notch)*size_notch, self.height+self.thickness)
        # Then notch
        path.LineTo(step*size_notch, self.height + self.thickness)
        path.LineTo(step*size_notch, self.height - ShortMark)
        if ShortMark != 0:
            #Then nMark - 1 Lines
            self.GenLinesFlex(step*size_notch, self.height - ShortMark - 2, (self.height - 2*ShortMark - 2.0)/(nMark-1) - 2.0, nMark-1, -1, path)
        path.GenPath()


    def GenFlex(self, parent, num_notch, size_notch, xOffset, yOffset):
        group = etree.SubElement(parent, 'g')
        self.group = group
        #Compute number of vertical lines. Each long mark should be at most 50mm long to avoid failures
        nMark = int(self.height / 50) + 1
        nMark = max(nMark, 2)   # At least 2 marks
        #Then compute number of flex bands
        FlexLength = num_notch * size_notch
        nb_flex_band = int (FlexLength // self.max_flex_size) + 1
        notch_per_band = num_notch / nb_flex_band + 1
        self.DebugMsg("Generate flex structure with "+str(nb_flex_band)+" bands, "+str(num_notch)+" notches, offset ="+str((xOffset, yOffset))+'\n')
        #Sizes of short and long lines to make flex
        LongMark = (self.height / nMark) - 2.0          #Long Mark equally divide the height
        ShortMark = LongMark/2                          # And short mark should lay at center of long marks
        idx_notch = 0
        while num_notch > 0:
            self.OffsetFlex = (xOffset, yOffset)
            self.GenerateStartFlex(size_notch, ShortMark, LongMark, nMark, idx_notch)
            idx_notch += 1
            notch = 0
            if notch_per_band > num_notch:
                notch_per_band = num_notch      #for the last one
            while notch < notch_per_band - 1:
                self.generate_step_flex(notch, size_notch, ShortMark, LongMark, nMark, idx_notch)
                notch += 1
                idx_notch += 1
            num_notch -= notch_per_band
            if num_notch == 0:
                self.GenerateEndFlex(notch, size_notch, ShortMark, LongMark, nMark, 0)
            else:
                self.GenerateEndFlex(notch, size_notch, ShortMark, LongMark, nMark, idx_notch)
            xOffset -= size_notch * notch_per_band + 10
            
    def getPathVertices(self, path, node=None):

        '''
        Decompose the path data from an SVG element into individual
        subpaths, each subpath consisting of absolute move to and line
        to coordinates.  Place these coordinates into a list of polygon
        vertices.
        '''
        self.DebugMsg("Entering getPathVertices, len="+str(len(path))+"\n")
        if (not path) or (len(path) == 0):
            # Nothing to do
            return None

        # parsePath() may raise an exception.  This is okay
        simple_path = Path(path).to_arrays()
        if (not simple_path) or (len(simple_path) == 0):
            # Path must have been devoid of any real content
            return None
        self.DebugMsg("After parsePath in getPathVertices, len="+str(len(simple_path))+"\n")
        self.DebugMsg("  Path = "+str(simple_path)+'\n')

        # Get a cubic super path
        cubic_super_path = CubicSuperPath(simple_path)
        if (not cubic_super_path) or (len(cubic_super_path) == 0):
            # Probably never happens, but...
            return None
        self.DebugMsg("After CubicSuperPath in getPathVertices, len="+str(len(cubic_super_path))+"\n")


        # Now traverse the cubic super path
        subpath_list = []
        subpath_vertices = []
        index_sp = 0
        for sp in cubic_super_path:

            # We've started a new subpath
            # See if there is a prior subpath and whether we should keep it
            self.DebugMsg("Processing SubPath"+str(index_sp)+" SubPath List len="+str(len(subpath_list))+"  Vertices list length="+str(len(subpath_vertices)) +"\n")

            if len(subpath_vertices):
                subpath_list.append(subpath_vertices)

            subpath_vertices = []
            self.DebugMsg("Before subdivideCubicPath len="+str(len(sp)) +"\n")
            self.DebugMsg("   Bsp="+str(sp)+'\n')
            subdivideCubicPath(sp, 0.1)
            self.DebugMsg("After subdivideCubicPath len="+str(len(sp)) +"\n")
            self.DebugMsg("   Asp="+str(sp)+'\n')

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
                #self.DebugMsg("Append subpath_vertice '"+str(pt)+"len="+str(len(subpath_vertices)) +"\n")


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
            # This is used for centering the polygons in OpenSCAD around the (x,y) origin
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
            subpath_list.append(subpath_vertices)

        if len(subpath_list) > 0:
            self.paths[node] = subpath_list

        '''
        self.DebugMsg("After getPathVertices\n")
        index_i = 0
        for i in self.paths[node]:
            index_j = 0
            for j in i:
                self.DebugMsg('Path '+str(index_i)+"  élément "+str(index_j)+" = "+str(j)+'\n')
                index_j += 1
            index_i += 1
        '''

    def DistanceOnPath(self, p, pt, index):
        '''
        Return the distances before and after the point pt on the polygon p
        The point pt is in the segment index of p, that is between p[index] and p[index+1]
        '''
        i = 0
        before = 0
        after = 0
        while i < index:
            #   First walk through polygon up to p[index]
            before += distance2points(p[i+1][0], p[i+1][1], p[i][0], p[i][1])
            i += 1
        #For the segment index compute the part before and after
        before += distance2points(pt[0], pt[1], p[index][0], p[index][1])
        after += distance2points(pt[0], pt[1], p[index+1][0], p[index+1][1])
        i = index + 1
        while i < len(p)-1:
            after += distance2points(p[i+1][0], p[i+1][1], p[i][0], p[i][1])
            i += 1
        return (before, after)
            
    # Compute position of next notch.
    #   Next notch will be on the path p, and at a distance notch_size from previous point
    #   Return new index in path p
    def compute_next_notch(self, notch_points, p, Angles_p, last_index_in_p, notch_size):
        index_notch = len(notch_points)
        #   Coordinates of last notch
        Ox = notch_points[index_notch - 1][0]
        Oy = notch_points[index_notch - 1][1]
        CurAngle = Angles_p[last_index_in_p-1]
        #self.DebugMsg("Enter cnn:last_index_in_p="+str(last_index_in_p)+" CurAngle="+str(round(CurAngle*180/math.pi))+"  Segment="+str((p[last_index_in_p-1], p[last_index_in_p]))+" Length="+str(distance2points(p[last_index_in_p-1][0], p[last_index_in_p-1][1], p[last_index_in_p][0], p[last_index_in_p][1]))+"\n")
        DeltaAngle = 0
        while last_index_in_p < (len(p) - 1) and distance2points(Ox, Oy, p[last_index_in_p][0], p[last_index_in_p][1]) < notch_size + DeltaAngle*self.thickness/2.0:
            Diff_angle = Angles_p[last_index_in_p] - CurAngle
            if Diff_angle > math.pi:
                Diff_angle -= 2*math.pi
            elif Diff_angle < -math.pi:
                Diff_angle += 2*math.pi
            Diff_angle = abs(Diff_angle)
            DeltaAngle += Diff_angle
            CurAngle = Angles_p[last_index_in_p]
            #self.DebugMsg("cnn:last_index_in_p="+str(last_index_in_p)+" Angle="+str(round(Angles_p[last_index_in_p]*180/math.pi))+" Diff_angle="+str(round(Diff_angle*180/math.pi))+" DeltaAngle="+str(round(DeltaAngle*180/math.pi))+" Distance="+str(distance2points(Ox, Oy, p[last_index_in_p][0], p[last_index_in_p][1]))+"/"+str(notch_size + DeltaAngle*self.thickness/2.0)+"\n")
            last_index_in_p += 1            # Go to next point in polygon

            
        # Starting point for the line x0, y0 is p[last_index_in_p-1]
        x0 = p[last_index_in_p-1][0]
        y0 = p[last_index_in_p-1][1]
        # End point for the line x1, y1 is p[last_index_in_p]
        x1 = p[last_index_in_p][0]
        y1 = p[last_index_in_p][1]
        
        Distance_notch = notch_size + DeltaAngle*self.thickness/2.0
        #self.DebugMsg(" compute_next_notch("+str(index_notch)+") Use Segment="+str(last_index_in_p)+" DeltaAngle="+str(round(DeltaAngle*180/math.pi))+"°, notch_size="+str(notch_size)+" Distance_notch="+str(Distance_notch)+'\n')

        # The actual notch position will be on the line between last_index_in_p-1 and last_index_in_p and at a distance Distance_notch of Ox,Oy
        # The intersection of a line and a circle could be computed as a second degree equation in a general case
        # Specific case, when segment is vertical
        if abs(x1-x0) <0.001:
            # easy case, x= x0 so y = sqrt(d2 - x*x)
            solx1 = x0
            solx2 = x0
            soly1 = Oy + math.sqrt(Distance_notch**2 - (x0 - Ox)**2)
            soly2 = Oy - math.sqrt(Distance_notch**2 - (x0 - Ox)**2)
        else:
            Slope = (y1 - y0) / (x1 - x0)
            # The actual notch position will be on the line between last_index_in_p-1 and last_index_in_p and at a distance notch size of Ox,Oy
            # The intersection of a line and a circle could be computed as a second degree equation
            # The coefficients of this equation are computed below
            a = 1.0 + Slope**2
            b = 2*Slope*y0 - 2*Slope**2*x0 - 2*Ox - 2*Slope*Oy
            c = Slope**2*x0**2 + y0**2 -2*Slope*x0*y0 + 2*Slope*x0*Oy - 2*y0*Oy + Ox**2 + Oy**2 - Distance_notch**2
            solx1, solx2 = Solve2nd(a, b, c)
            soly1 = y0 + Slope*(solx1-x0)
            soly2 = y0 + Slope*(solx2-x0)
        # Now keep the point which is between (x0,y0) and (x1, y1)
        # The distance between (x1,y1) and the "good" solution will be lower than the distance between (x0,y0) and (x1,y1)
        distance1 = distance2points(x1, y1, solx1, soly1)
        distance2 = distance2points(x1, y1, solx2, soly2)
        if distance1 < distance2:
            #Keep solx1
            solx = solx1
            soly = soly1
        else:
            #Keep solx2
            solx = solx2
            soly = soly2
        notch_points.append((solx, soly, last_index_in_p-1))
        if abs(distance2points(solx, soly, Ox, Oy) - Distance_notch) > 1:
            #Problem
            self.DebugMsg("Problem in compute_next_notch: x0,y0 ="+str((x0,y0))+" x1,y1="+str((x1,y1))+'\n')      
            self.DebugMsg("Len(p)="+str(len(p))+'\n')      
            self.DebugMsg("Slope="+str(Slope)+'\n') 
            self.DebugMsg("solx1="+str(solx1)+" soly1="+str(soly1)+" soly1="+str(solx2)+" soly1="+str(soly2)+'\n')
            self.DebugMsg(str(index_notch)+": Adding new point ("+str(solx)+","+ str(soly) + "), distance is "+ str(distance2points(solx, soly, Ox, Oy))+ " New index in path :"+str(last_index_in_p)+'\n')

        #self.DebugMsg(str(index_notch)+": Adding new point ("+str(solx)+","+ str(soly) + "), distance is "+ str(distance2points(solx, soly, Ox, Oy))+ " New index in path :"+str(last_index_in_p)+'\n')
        return last_index_in_p
    
    def DrawPoly(self, p, parent):
        group = etree.SubElement(parent, 'g')
        Newpath = inkcape_draw_cartesian((self.xmin - self.xmax - 10, 0), group)
        self.DebugMsg('DrawPoly First element (0) : '+str(p[0])+ ' Call MoveTo('+ str(p[0][0])+','+str(p[0][1])+'\n')
        Newpath.MoveTo(p[0][0], p[0][1])
        n = len(p)
        index = 1
        for point in p[1:n]:
            Newpath.LineTo(point[0], point[1])
            index += 1
        Newpath.GenPath()

    def Simplify(self, poly, max_error):
        ''' 
        Simplify the polygon, remove vertices which are aligned or too close from others
        The parameter give the max error, below this threshold, points will be removed
        return the simplified polygon, which is modified in place
        ''' 
        #First point
        LastIdx = 0
        limit = max_error * max_error   #Square because distance will be square !
        i = 1
        while i < len(poly)-1:
            #Build segment between Vertex[i-1] and Vertex[i+1]
            Seg = Segment(poly[LastIdx], poly[i+1])
            #self.DebugMsg("Pt["+str(i)+"]/"+str(len(poly))+" ="+str(poly[i])+" Segment="+str(Seg)+"\n")
            # Compute square of distance between Vertex[i] and Segment
            dis_square = Seg.square_line_distance(poly[i])
            if dis_square < max_error:
                # Too close, remove this point
                poly.pop(i) #and do NOT increment index
                #self.DebugMsg("Simplify, removing pt "+str(i)+"="+str(poly[i])+" in Segment : "+str(Seg)+" now "+str(len(poly))+" vertices\n")
            else:
                LastIdx = i
                i += 1   #Increment index
        # No need to process last point, it should NOT be modified and stay equal to first one
        return poly
       
    def MakePolyCCW(self, p):
        '''
        Take for polygon as input and make it counter clockwise.
        If already CCW, just return the polygon, if not reverse it
        To determine if polygon is CCW, compute area. If > 0 the polygon is CCW
        '''
        area = 0
        for i in range(len(p)-1):
            area += p[i][0]*p[i+1][1] - p[i+1][0]*p[i][1]
        self.DebugMsg("poly area = "+str(area/2)+"\n")
        if area < 0:
           # Polygon is cloackwise, reverse
            p.reverse()
            self.DebugMsg("Polygon was clockwise, reverse it\n")
        return p

    def ComputeAngles(self, p):
        '''
        Compute a list with angles of all edges of the polygon
        Return this list
        '''
        angles = []
        for i in range(len(p)-1):
            a = math.atan2(p[i+1][1] - p[i][1], p[i+1][0] - p[i][0])
            angles.append(a)       
        #   Last value is not defined as Pt n-1 = Pt 0, set it to angle[0]
        angles.append(angles[0])
        return angles
    
    def writeModifiedPath(self, node, parent):
        ''' 
        Take the paths (polygons) computed from previous step and generate 
        1) The input path with notches
        2) The flex structure associated with the path with notches (same length and number of notches)
        '''
        path = self.paths[node]
        if (path is None) or (len(path) == 0):
            return
        self.DebugMsg('Enter writeModifiedPath, node='+str(node)+' '+str(len(path))+' paths, global Offset'+str((self.xmin - self.xmax - 10, 0))+'\n')
        
        # First, if there are several paths, checks if one path is included in the first one.
        # If not exchange such as the first one is the bigger one.
        # All paths which are not the first one will have notches reverted to be outside the polygon instead of inside the polygon.
        # On the finbal paths, these notches will always be inside the form.
        if len(path) > 1:
            OrderPathModified = True 
            # Arrange paths such as greater one is first, all others 
            while OrderPathModified:
                OrderPathModified = False
                for i in range(1, len(path)):
                    if polyInPoly(path[i], None, path[0], None):
                        self.DebugMsg("Path "+str(i)+" is included in path 0\n")
                    elif polyInPoly(path[0], None, path[i], None):
                        self.DebugMsg("Path "+str(i)+" contains path 0, exchange\n")
                        path[0], path[i] = path[i], path[0]
                        OrderPathModified = True
                        
        index_path = 0
        xFlexOffset = self.xmin - 2*self.xmax - 20
        yFlexOffset = self.height - self.ymax - 10
        for p in path:
            self.DebugMsg('Processing Path, '+str(index_path)+" Len(path)="+str(len(p))+'\n')
            self.DebugMsg('p='+str(p)+'\n')
            reverse_notch = False
            if index_path > 0 and polyInPoly(p, None, path[0], None):
                reverse_notch = True            #   For included path, reverse notches
            #Simplify path, remove unnecessary vertices
            p = self.Simplify(p, 0.1)
            self.DebugMsg("---After simplification, path has "+str(len(p))+" vertices\n")            
            #Ensure that polygon is counter clockwise
            p = self.MakePolyCCW(p)
            self.DrawPoly(p, parent)
            #Now compute path length. Path length is the sum of length of edges
            length_path = 0
            n = len(p)
            index = 1
            while index < n:
                length_path += math.hypot((p[index][0] - p[index-1][0]), (p[index][1] - p[index-1][1]))
                index += 1

            angles = self.ComputeAngles(p)
            # compute the sum of angles difference and check that it is 2*pi
            SumAngle = 0.0
            for i in range(len(p)-1):
                Delta_angle = angles[i+1] - angles[i]
                if Delta_angle > math.pi:
                    Delta_angle -= 2*math.pi
                elif Delta_angle < -math.pi:
                    Delta_angle += 2*math.pi
                Delta_angle = abs(Delta_angle)
                self.DebugMsg("idx="+str(i)+" Angle1 ="+str(round(angles[i]*180/math.pi,3))+" Angle 2="+str(round(angles[i+1]*180/math.pi,3))+" Delta angle="+str(round(Delta_angle*180/math.pi, 3))+"°\n")
                SumAngle += Delta_angle
            self.DebugMsg("Sum of angles="+str(SumAngle*180/math.pi)+"°\n")

            # Flex length will be path length - thickness*SumAngle/2 to keep flex aligned on the shortest path
            flex_length = length_path - self.thickness*SumAngle/2

            self.DebugMsg('Path length ='+str(length_path)+" Flex length ="+str(flex_length)+"  Difference="+str(length_path-flex_length)+'\n')

            #Default notch size is notchesInterval + 2mm 
            #Actual notch size will be adjusted to match the length
            notch_number = int(round(flex_length / (self.notchesInterval + 2), 0))
            notch_size = flex_length / notch_number
            self.DebugMsg('Number of notches ='+str(notch_number)+' ideal notch size =' + str(round(notch_size,3)) +'\n')
            
 
            # Compute position of the points on the path that will become notches
            # Starting at 0, each point will be at distance actual_notch_size from the previous one, at least on one side of the notch (the one with the smallest distance)
            # On the path (middle line) the actual distance will be notch_size + thickness*delta_angle/2 where delta angle is the difference between the angle at starting point and end point
            # As notches are not aligned to vertices, the actual length of the path will be different from the computed one (lower in fact)
            # To avoid a last notch too small, we will repeat the process until the size of the last notch is OK (less than .1mm error)
            # Use an algorithm which corrects the notch_size by computing previous length of the last notch

            nb_try = 0
            size_last_notch = 0
            oldSize = 0
            BestDifference = 9999999
            BestNotchSize = notch_size
            mode_linear = False
            delta_notch = -0.01             #In most cases, should reduce notch size
            while nb_try < 100:
                notch_points = [ (p[0][0], p[0][1], 0) ]        # Build a list of tuples with corrdinates (x,y) and offset within polygon which is 0 the the starting point
                index = 1                                       # Notch index
                last_index_in_p = 1                             # Start at 1, index 0 is the current one
                self.DebugMsg("Pass "+str(nb_try)+" First point ("+str(p[0][0])+","+ str(p[0][1]) + '  notch_size='+str(notch_size)+'\n')
                while index < notch_number:
                    #Compute next notch point and append it to the list
                    last_index_in_p = self.compute_next_notch(notch_points, p, angles, last_index_in_p, notch_size)
                    #before, after = self.DistanceOnPath(p, notch_points[index], last_index_in_p-1)
                    #self.DebugMsg(" Notch "+str(index)+" placed in "+str(notch_points[index])+" distance before ="+str(before)+" after="+str(after)+"  total="+str(before+after)+'\n')
                    index += 1
                size_last_notch = distance2points(p[n-1][0], p[n-1][1],  notch_points[index-1][0], notch_points[index-1][1])
                self.DebugMsg("Last notch size :"+str(size_last_notch)+'\n')
                if abs(notch_size - size_last_notch) < BestDifference:
                    BestNotchSize = notch_size
                    BestDifference = abs(notch_size - size_last_notch)
                if abs(notch_size - size_last_notch) <= 0.1:
                    break
                # Change size_notch, cut small part in each notch
                # The 0.5 factor is used to avoid non convergent series (too short then too long...)
                if  mode_linear:
                    if notch_size > size_last_notch and delta_notch > 0:
                        delta_notch -= delta_notch*0.99
                    elif notch_size < size_last_notch and delta_notch < 0:
                        delta_notch -= delta_notch*0.99
                    notch_size += delta_notch
                    self.DebugMsg("Linear mode, changing delta_notch size :"+str(delta_notch)+" --> notch_size="+str(notch_size)+'\n')
                else:
                    if notch_size > size_last_notch and delta_notch > 0:
                        delta_notch = -0.5*delta_notch
                        self.DebugMsg("Changing delta_notch size :"+str(delta_notch)+'\n')
                    elif notch_size < size_last_notch and delta_notch < 0:
                        delta_notch = -0.5*delta_notch
                        self.DebugMsg("Changing delta_notch size :"+str(delta_notch)+'\n')
                    notch_size += delta_notch
                    if abs(delta_notch) <  0.002:
                        mode_linear = True

                # Change size_notch, cut small part in each notch
                oldSize = notch_size
                # The 0.5 factor is used to avoid non convergent series (too short then too long...)
                notch_size -= 0.5*(notch_size - size_last_notch)/notch_number
                nb_try += 1

            if nb_try >= 100:
                self.DebugMsg("Algorithm doesn't converge, use best results :"+str(BestNotchSize)+" which gave last notch size difference "+str(BestDifference)+'\n')
                notch_size =  BestNotchSize
   
            # Now draw the actual notches 
            group = etree.SubElement(parent, 'g')
            # First draw a start line which will help to position flex.
            Startpath = inkcape_draw_cartesian(((self.xmin - self.xmax - 10), 0), group)
            index_in_p = notch_points[0][2]
            AngleSlope = math.atan2(p[index_in_p+1][1] - p[index_in_p][1], p[index_in_p+1][0] - p[index_in_p][0])
            #Now compute both ends of the notch, 
            AngleOrtho = AngleSlope + math.pi/2
            Line_Start = (notch_points[0][0] + self.thickness/2*math.cos(AngleOrtho), notch_points[0][1] + self.thickness/2*math.sin(AngleOrtho))
            Line_End = (notch_points[0][0] - self.thickness/2*math.cos(AngleOrtho), notch_points[0][1] - self.thickness/2*math.sin(AngleOrtho))
            self.DebugMsg("Start line Start"+str(Line_Start)+" End("+str(Line_End)+" Start inside "+str(pointInPoly(Line_Start, p))+ " End inside :"+str(pointInPoly(Line_End, p))+'\n')
            #Notch End should be inside the path and Notch Start outside... If not reverse
            if pointInPoly(Line_Start, p):
                Line_Start, Line_End = Line_End, Line_Start
                AngleOrtho += math.pi
            elif not pointInPoly(Line_End, p):
                #Specific case, neither one is in Polygon (Open path ?), take the lowest Y as Line_End
                if Line_End[1] > Line_Start[0]:
                    Line_Start, Line_End = Line_End, Line_Start
                    AngleOrtho += math.pi
            #Now compute a new Start, inside the polygon Start = 3*End - 2*Start
            newLine_Start = (3*Line_End[0] - 2*Line_Start[0], 3*Line_End[1] - 2*Line_Start[1])
            Startpath.MoveTo(newLine_Start[0], newLine_Start[1])
            Startpath.LineTo(Line_End[0], Line_End[1])
            self.DebugMsg("Draw StartLine start from "+str((newLine_Start[0], newLine_Start[1]))+" to "+str((Line_End[0], Line_End[1]))+'\n')
            Startpath.GenPathStart()
            
            #Then draw the notches
            Newpath = inkcape_draw_cartesian(((self.xmin - self.xmax - 10), 0), group)
            self.DebugMsg("Generate path with "+str(notch_number)+" notches, offset ="+str(((self.xmin - self.xmax - 10), 0))+'\n')
            isClosed = distance2points(p[n-1][0], p[n-1][1], p[0][0], p[0][1]) < 0.1
            # Each notch is a tuple with (X, Y, index_in_p). index_in_p will be used to compute slope of line of the notch
            # The notch will be thickness long, and there will be a part 'inside' the path and a part 'outside' the path
            # The longest part will be outside
            index = 0
            NX0 = 0
            NX1 = 0
            NX2 = 0
            NX3 = 0
            NY0 = 0
            NY1 = 0
            NY2 = 0
            NY3 = 0
            N_Angle = 0
            Notch_Pos = []
            while index < notch_number:
                # Line slope of the path at notch point is
                index_in_p = notch_points[index][2]
                N_Angle = angles[index_in_p]
                AngleSlope = math.atan2(p[index_in_p+1][1] - p[index_in_p][1], p[index_in_p+1][0] - p[index_in_p][0])
                self.DebugMsg("Draw notch "+str(index)+" Slope is "+str(AngleSlope*180/math.pi)+'\n')
                self.DebugMsg("Ref="+str(notch_points[index])+'\n')
                self.DebugMsg("Path points:"+str((p[index_in_p][0], p[index_in_p][1]))+', '+ str((p[index_in_p+1][0], p[index_in_p+1][1]))+'\n')
                #Now compute both ends of the notch, 
                AngleOrtho = AngleSlope + math.pi/2
                Notch_Start = (notch_points[index][0] + self.thickness/2*math.cos(AngleOrtho), notch_points[index][1] + self.thickness/2*math.sin(AngleOrtho))
                Notch_End = (notch_points[index][0] - self.thickness/2*math.cos(AngleOrtho), notch_points[index][1] - self.thickness/2*math.sin(AngleOrtho))
                self.DebugMsg("Notch "+str(index)+": Start"+str(Notch_Start)+" End("+str(Notch_End)+" Start inside "+str(pointInPoly(Notch_Start, p))+ " End inside :"+str(pointInPoly(Notch_End, p))+'\n')
                #Notch End should be inside the path and Notch Start outside... If not reverse
                if pointInPoly(Notch_Start, p):
                    Notch_Start, Notch_End = Notch_End, Notch_Start
                    AngleOrtho += math.pi
                elif not pointInPoly(Notch_End, p):
                    #Specific case, neither one is in Polygon (Open path ?), take the lowest Y as Notch_End
                    if Notch_End[1] > Notch_Start[0]:
                        Notch_Start, Notch_End = Notch_End, Notch_Start
                        AngleOrtho += math.pi
                #if should reverse notches, do it now
                if reverse_notch:
                    Notch_Start, Notch_End = Notch_End, Notch_Start
                    AngleOrtho += math.pi
                if AngleOrtho > 2*math.pi:
                    AngleOrtho -= 2*math.pi
                ln = 2.0
                if index == 0:
                    Newpath.MoveTo(Notch_Start[0], Notch_Start[1])
                    first = (Notch_Start[0], Notch_Start[1])
                    if not isClosed:       
                        ln = 1.0        # Actual, different Notch size for the first one when open path
                else:
                    Newpath.LineTo(Notch_Start[0], Notch_Start[1])
                    if not isClosed and index == notch_number - 1: 
                        ln = 1.0
                    self.DebugMsg("LineTo starting point from :"+str((x,y))+" to "+str((Notch_Start[0], Notch_Start[1]))+" Length ="+str(distance2points(x, y, Notch_Start[0], Notch_Start[1]))+'\n')
                Newpath.LineTo(Notch_End[0], Notch_End[1])
                NX0 = Notch_Start[0]
                NY0 = Notch_Start[1]
                NX1 = Notch_End[0]
                NY1 = Notch_End[1]
                self.DebugMsg("Draw notch_1 start from "+str((Notch_Start[0], Notch_Start[1]))+" to "+str((Notch_End[0], Notch_End[1]))+'Center is '+str(((Notch_Start[0]+Notch_End[0])/2, (Notch_Start[1]+Notch_End[1])/2))+'\n')
                #Now draw a line parallel to the path, which is notch_size*(2/(notchesInterval+2)) long. Internal part of the notch
                x = Notch_End[0] + (notch_size*ln)/(self.notchesInterval+ln)*math.cos(AngleSlope)
                y = Notch_End[1] + (notch_size*ln)/(self.notchesInterval+ln)*math.sin(AngleSlope)
                Newpath.LineTo(x, y)
                NX2 = x
                NY2 = y
                self.DebugMsg("Draw notch_2 to "+str((x, y))+'\n')
                #Then a line orthogonal, which is thickness long, reverse from first one
                x = x + self.thickness*math.cos(AngleOrtho)
                y = y + self.thickness*math.sin(AngleOrtho)
                Newpath.LineTo(x, y)
                NX3 = x
                NY3 = y
                self.DebugMsg("Draw notch_3 to "+str((x, y))+'\n')
                Notch_Pos.append((NX0, NY0, NX1, NY1, NX2, NY2, NX3, NY3, N_Angle))
                # No need to draw the last segment, it will be drawn when starting the next notch
                index += 1
            #And the last one if the path is closed
            if isClosed:
                self.DebugMsg("Path is closed, draw line to start point "+str((p[0][0], p[0][1]))+'\n')
                Newpath.LineTo(first[0], first[1])
            else:
                self.DebugMsg("Path is open\n") 
            Newpath.GenPath()
            # Analyze notches for debugging purpose
            for i in range(len(Notch_Pos)):
                self.DebugMsg("Notch "+str(i)+" Pos="+str(Notch_Pos[i])+" Angle="+str(round(Notch_Pos[i][8]*180/math.pi))+"\n")
                if (i > 0):
                    self.DebugMsg("  FromLast Notch N3-N0="+str(distance2points(Notch_Pos[i-1][6], Notch_Pos[i-1][7], Notch_Pos[i][0], Notch_Pos[i][1]))+"\n")
                self.DebugMsg("  Distances: N0-N3="+str(distance2points(Notch_Pos[i][0], Notch_Pos[i][1], Notch_Pos[i][6], Notch_Pos[i][7]))+" N1-N2="+str(distance2points(Notch_Pos[i][2], Notch_Pos[i][3], Notch_Pos[i][4], Notch_Pos[i][5]))+"\n")
            # For each notch determine if we need flex or not. Flex is only needed if there is some curves 
            #   So if notch[i]-1 notch[i] notch[i+1] are aligned, no need to generate flex in i-1 and i
            for index in range(notch_number):
                self.flexnotch.append(1)            # By default all notches need flex
            index = 1
            while index < notch_number-1:
                det =  (notch_points[index+1][0]- notch_points[index-1][0])*(notch_points[index][1] - notch_points[index-1][1]) - (notch_points[index+1][1] - notch_points[index-1][1])*(notch_points[index][0] - notch_points[index-1][0])
                self.DebugMsg("Notch "+str(index)+": det="+str(det))
                if abs(det) < 0.1:       #  My threhold to be adjusted
                    self.flexnotch[index-1] = 0        # No need for flex for this one and the following 
                    self.flexnotch[index] = 0
                    self.DebugMsg(" no flex in notch "+str(index-1)+" and "+str(index))
                index += 1
                self.DebugMsg("\n")
            # For the last one try notch_number - 2, notch_number - 1 and 0
            det =  (notch_points[0][0]- notch_points[notch_number - 2][0])*(notch_points[notch_number - 1][1] - notch_points[notch_number - 2][1]) - (notch_points[0][1] - notch_points[notch_number - 2][1])*(notch_points[notch_number - 1][0] - notch_points[notch_number - 2][0])
            if abs(det) < 0.1:       #  My threhold to be adjusted
                self.flexnotch[notch_number-2] = 0        # No need for flex for this one and the following 
                self.flexnotch[notch_number-1] = 0
            # and the first one with notch_number - 1, 0 and 1
            det =  (notch_points[1][0]- notch_points[notch_number-1][0])*(notch_points[0][1] - notch_points[notch_number-1][1]) - (notch_points[1][1] - notch_points[notch_number-1][1])*(notch_points[0][0] - notch_points[notch_number-1][0])
            if abs(det) < 0.1:       #  My threhold to be adjusted
                self.flexnotch[notch_number-1] = 0        # No need for flex for this one and the following 
                self.flexnotch[0] = 0
            self.DebugMsg("FlexNotch ="+str(self.flexnotch)+"\n")
            # Generate Associated flex
            self.GenFlex(parent, notch_number, notch_size, xFlexOffset, yFlexOffset)
            yFlexOffset -= self.height + 10
            index_path += 1
        

    def recursivelyTraverseSvg(self, aNodeList):

        '''
        [ This too is largely lifted from eggbot.py and path2openscad.py ]

        Recursively walk the SVG document, building polygon vertex lists
        for each graphical element we support.

        Rendered SVG elements:
            <circle>, <ellipse>, <line>, <path>, <polygon>, <polyline>, <rect>
            Except for path, all elements are first converted into a path the processed

        Supported SVG elements:
            <group>

        Ignored SVG elements:
            <defs>, <eggbot>, <metadata>, <namedview>, <pattern>,
            processing directives

        All other SVG elements trigger an error (including <text>)
        '''

        for node in aNodeList:

            self.DebugMsg("Node type :" + node.tag + '\n')
            if node.tag == inkex.addNS('g', 'svg') or node.tag == 'g':
                self.DebugMsg("Group detected, recursive call\n")
                self.recursivelyTraverseSvg(node)

            elif node.tag == inkex.addNS('path', 'svg'):
                self.DebugMsg("Path detected, ")
                path_data = node.get('d')
                if path_data:
                    self.getPathVertices(path_data, node)
                else:
                    self.DebugMsg("NO path data present\n")

            elif node.tag == inkex.addNS('rect', 'svg') or node.tag == 'rect':

                # Create a path with the outline of the rectangle
                x = float(node.get('x'))
                y = float(node.get('y'))
                if (not x) or (not y):
                    pass
                w = float(node.get('width', '0'))
                h = float(node.get('height', '0'))

                self.DebugMsg('Rectangle X='+ str(x)+',Y='+str(y)+', W='+str(w)+' H='+str(h)+'\n')

                a = []
                a.append(['M', [x, y]])
                a.append(['l', [w, 0]])
                a.append(['l', [0, h]])
                a.append(['l', [-w, 0]])
                a.append(['Z', []])
                self.getPathVertices(str(Path(a)), node)
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
                self.DebugMsg('Line X1='+ str(x1)+',Y1='+str(y1)+', X2='+str(x2)+' Y2='+str(y2)+'\n')

                if (not x1) or (not y1) or (not x2) or (not y2):
                    pass
                a = []
                a.append(['M', [x1, y1]])
                a.append(['L', [x2, y2]])
                self.getPathVertices(str(Path(a)), node)

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
                    pass

                pa = pl.split()
                d = "".join(["M " + pa[i] if i == 0 else " L " + pa[i] for i in range(0, len(pa))])
                self.DebugMsg('PolyLine :'+ d +'\n')

                
                self.getPathVertices(d, node)

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
                    pass

                pa = pl.split()
                d = "".join(["M " + pa[i] if i == 0 else " L " + pa[i] for i in range(0, len(pa))])
                d += " Z"
                self.DebugMsg('Polygon :'+ d +'\n')
                self.getPathVertices(d, node)

            elif node.tag == inkex.addNS('ellipse', 'svg') or \
                node.tag == 'ellipse' or \
                node.tag == inkex.addNS('circle', 'svg') or \
                node.tag == 'circle':

                    # Convert circles and ellipses to a path with two 180 degree arcs.
                    # In general (an ellipse), we convert
                    #
                    #   <ellipse rx="RX" ry="RY" cx="X" cy="Y"/>
                    #
                    # to
                    #
                    #   <path d="MX1,CY A RX,RY 0 1 0 X2,CY A RX,RY 0 1 0 X1,CY"/>
                    #
                    # where
                    #
                    #   X1 = CX - RX
                    #   X2 = CX + RX
                    #
                    # Note: ellipses or circles with a radius attribute of value 0 are ignored

                    if node.tag == inkex.addNS('ellipse', 'svg') or node.tag == 'ellipse':
                        rx = float(node.get('rx', '0'))
                        ry = float(node.get('ry', '0'))
                    else:
                        rx = float(node.get('r', '0'))
                        ry = rx
                    if rx == 0 or ry == 0:
                        pass

                    cx = float(node.get('cx', '0'))
                    cy = float(node.get('cy', '0'))
                    x1 = cx - rx
                    x2 = cx + rx
                    d = 'M %f,%f ' % (x1, cy) + \
                        'A %f,%f ' % (rx, ry) + \
                        '0 1 0 %f,%f ' % (x2, cy) + \
                        'A %f,%f ' % (rx, ry) + \
                        '0 1 0 %f,%f' % (x1, cy)
                    self.DebugMsg('Arc :'+ d +'\n')
                    self.getPathVertices(d, node)

            elif node.tag == inkex.addNS('pattern', 'svg') or node.tag == 'pattern':

                pass

            elif node.tag == inkex.addNS('metadata', 'svg') or node.tag == 'metadata':

                pass

            elif node.tag == inkex.addNS('defs', 'svg') or node.tag == 'defs':

                pass

            elif node.tag == inkex.addNS('desc', 'svg') or node.tag == 'desc':

                pass

            elif node.tag == inkex.addNS('namedview', 'sodipodi') or node.tag == 'namedview':

                pass

            elif node.tag == inkex.addNS('eggbot', 'svg') or node.tag == 'eggbot':

                pass

            elif node.tag == inkex.addNS('text', 'svg') or node.tag == 'text':

                inkex.errormsg('Warning: unable to draw text, please convert it to a path first.')

                pass

            elif node.tag == inkex.addNS('title', 'svg') or node.tag == 'title':

                pass

            elif node.tag == inkex.addNS('image', 'svg') or node.tag == 'image':

                if not self.warnings.has_key('image'):
                    inkex.errormsg(gettext.gettext('Warning: unable to draw bitmap images; ' +
                        'please convert them to line art first.  Consider using the "Trace bitmap..." ' +
                        'tool of the "Path" menu.  Mac users please note that some X11 settings may ' +
                        'cause cut-and-paste operations to paste in bitmap copies.'))
                    self.warnings['image'] = 1
                pass

            elif node.tag == inkex.addNS('pattern', 'svg') or node.tag == 'pattern':

                pass

            elif node.tag == inkex.addNS('radialGradient', 'svg') or node.tag == 'radialGradient':

                # Similar to pattern
                pass

            elif node.tag == inkex.addNS('linearGradient', 'svg') or node.tag == 'linearGradient':

                # Similar in pattern
                pass

            elif node.tag == inkex.addNS('style', 'svg') or node.tag == 'style':

                # This is a reference to an external style sheet and not the value
                # of a style attribute to be inherited by child elements
                pass

            elif node.tag == inkex.addNS('cursor', 'svg') or node.tag == 'cursor':

                pass

            elif node.tag == inkex.addNS('color-profile', 'svg') or node.tag == 'color-profile':

                # Gamma curves, color temp, etc. are not relevant to single color output
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


    def effect(self):

        # convert units
        unit = self.options.unit
        self.thickness = self.svg.unittouu(str(self.options.thickness) + unit)
        self.height = self.svg.unittouu(str(self.options.zc) + unit)
        self.max_flex_size = self.svg.unittouu(str(self.options.max_size_flex) + unit)
        self.notchesInterval = int(self.options.notch_interval)

        svg = self.document.getroot()
        docWidth = self.svg.unittouu(svg.get('width'))
        docHeigh = self.svg.unittouu(svg.attrib['height'])

        # Open Debug file if requested
        if self.options.Mode_Debug:
            try:
                self.fDebug = open('DebugPath2Flex.txt', 'w')
            except IOError:
                print ('cannot open debug output file')
            self.DebugMsg("Start processing\n")


        # First traverse the document (or selected items), reducing
        # everything to line segments.  If working on a selection,
        # then determine the selection's bounding box in the process.
        # (Actually, we just need to know it's extrema on the x-axis.)

        # Traverse the selected objects
        for id in self.options.ids:
            self.recursivelyTraverseSvg([self.svg.selected[id]])
        # Determine the center of the drawing's bounding box
        self.cx = self.xmin + (self.xmax - self.xmin) / 2.0
        self.cy = self.ymin + (self.ymax - self.ymin) / 2.0

        layer = etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), 'Flex_Path')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')

        # For each path, build a polygon with notches and the corresponding flex.
        for key in self.paths:
            self.writeModifiedPath(key, layer)

        if self.fDebug:
            self.fDebug.close()

if __name__ == '__main__':
    BoxMakerPathToFlex().run()
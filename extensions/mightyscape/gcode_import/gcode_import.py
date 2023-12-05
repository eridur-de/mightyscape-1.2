#!/usr/bin/env python3
"""
ImportGCode, and Inkscape extension by Nathaniel Klumb

This extension adds support for some GCode files to the File/Import...
dialog in Inkscape.  It loads the GCode file passed to it by Inkscape as a
command-line parameter and writes the resulting SVG to stdout (which is how
Inkscape input plugins work).

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""
import re
import inkex
import sys
import argparse
from io import StringIO
from math import sqrt ,pi, sin, cos, tan, acos, atan2, fabs
from lxml import etree

class ImportGCode:
    """ Import a GCode file and process it into an SVG. """
    current_id = 0
    geometry_error = False
    
    def __init__(self,gcode_filename,v_carve=False,laser_mode=False,
                 ignore_z=True,label_z=True,
                 tool_diameter=1.0,v_angle=90.0,v_top=0.0,v_step=1.0):
        """ Load a GCode file and process it into an SVG. """
        self.unit = 1.0
        self.ignore_z = ignore_z or v_carve
        self.label_z = label_z and not v_carve
        self.tool_diameter = tool_diameter
        self.v_carve = v_carve
        self.v_angle = v_angle * pi / 180.0
        self.v_top = v_top
        self.v_step = v_step
        self.laser_mode = laser_mode
        self.spindle = False
        self.speed = 0
        with open(gcode_filename) as file:
            self.loadGCode(file)
        self.createSVG()

    def getIJ(self,x1,y1,x2,y2,r):
        """ Calculate I and J from two arc endpoints and a radius. """
        theta = atan2(y2 - y1, x2 - x1)
        alpha = acos(sqrt((x2 - x1)**2 + (y2 - y1)**2)/(2 * abs(r)))
        return (r * cos(theta + alpha), r * sin(theta + alpha))

    def getTangentPoints(self,x1,y1,r1,x2,y2,r2):
        """ Compute the four outer tangent endpoints of two circles. """
        theta = atan2(y2 - y1, x2 - x1)
        try:
            alpha = acos((r1 - r2)/sqrt((x2 - x1)**2 + (y2 - y1)**2))
        except ValueError:
            # It's broken, but we'll just cap it off.
            # The SVG will be messed up, but that's better feedback
            # than just blankly saying, "Sorry, please try again."
            if not self.geometry_error: #Only show the error once.
                inkex.errormsg('Math error importing V-carve: '
                               'V-bit angle too large?')
                inkex.errormsg('    Check your included angle '
                               'setting and try again.')
                self.geometry_error = True
            if ((r1 - r2)/sqrt((x2 - x1)**2 + (y2 - y1)**2) < -1):
                alpha = pi
            else:
                alpha = 0
        return ((x1 + r1 * cos(theta - alpha), y1 + r1 * sin(theta - alpha)),
                (x1 + r1 * cos(theta + alpha), y1 + r1 * sin(theta + alpha)),
                (x2 + r2 * cos(theta + alpha), y2 + r2 * sin(theta + alpha)),
                (x2 + r2 * cos(theta - alpha), y2 + r2 * sin(theta - alpha)))

    def intersectLines(self, p1, p2, p3, p4): 
        """ Calculate the intersection of Line(p1,p2) and Line(p3,p4)
                
        returns a tuple: (x, y, valid, included)
            (x, y): the intersection
            valid: a unique solution exists
            included: the solution is within both the line segments
                                Segment(p1,p2) and Segment(p3,p4)
        """

        DET_TOLERANCE = 0.00000001
        T = 0.00000001
        
        # the first line is pt1 + r*(p2-p1)
        x1,y1 = p1
        x2,y2 = p2
        dx1 = x2 - x1
        dy1 = y2 - y1

        # the second line is p4 + s*(p4-p3)
        x3,y3 = p3
        x4,y4 = p4;
        dx2 = x4 - x3
        dy2 = y4 - y3

        # In matrix form:
        #        [ dx1  -dx2 ][ r ] = [ x3-x1 ]
        #        [ dy1  -dy2 ][ s ] = [ y3-y1 ]
        #
        # Which can be solved:
        #        [ r ] = _1_  [ -dy2  dx2 ] [ x3-x1 ]
        #        [ s ] = DET  [ -dy1  dx1 ] [ y3-y1 ]
        #
        # With the deteminant: DET = (-dx1 * dy2 + dy1 * dx2)
        DET = (-dx1 * dy2 + dy1 * dx2)

        # If DET is zero, they're parallel
        if fabs(DET) < DET_TOLERANCE:
            # If they overlap, either p3 or p4 must be
            # an included point, so check one, then check the
            # other.  If either falls inside the segment from
            # p1 to p2, return it as *a* valid intersection.
            # Otherwise, return the bad news -- no intersection.
            #
            # Also, when checking the limits, allow a tolerance, T,
            # since we're working in floating point.
            if ((((x3 >= x1 - T) and (x3 <= x2 + T)) or 
                 ((x3 <= x1 + T) and (x3 >= x2 - T))) and
                (((y3 >= y1 - T) and (y3 <= y2 + T)) or 
                ((y3 <= y1 + T) and (y3 >= y2 - T)))):
                return (x3,y3,False,True)
            elif ((((x4 >= x1 - T) and (x4 <= x2 + T)) or 
                   ((x4 <= x1 + T) and (x4 >= x2 - T))) and
                  (((y4 >= y1 - T) and (y4 <= y2 + T)) or 
                   ((y4 <= y1 + T) and (y4 >= y2 - T)))):
                return (x4,y4,False,True)
            # NO CONNECTION... *dialtone*
            else:
                return (None,None,False,False)
                
        # Since the determinant is non-zero, now take the reciprocal.
        invDET = 1.0/DET

        # We want to calculate the intersection for each line so we can
        # average the results together.  They should be identical, but
        # floating-point and rounding error, etc...       
        # Calculate the scalar distances along Line(p1,p2) and Line(p3,p4)
        r = invDET * (-dy2 * (x3-x1) + dx2 * (y3-y1))
        s = invDET * (-dy1 * (x3-x1) + dx1 * (y3-y1))

        # Average the intersection's coordinates from the two lines.
        x = (x1 + r*dx1 + x3 + s*dx2)/2.0
        y = (y1 + r*dy1 + y3 + s*dy2)/2.0
        
        # Now one last check to see if the intersection's coordinates are
        # included within both line segments.
        included = ((((x >= x1 - T) and (x <= x2 + T)) or 
                     ((x <= x1 + T) and (x >= x2 - T))) and
                    (((y >= y1 - T) and (y <= y2 + T)) or 
                     ((y <= y1 + T) and (y >= y2 - T))) and
                    (((x >= x3 - T) and (x <= x4 + T)) or 
                     ((x <= x3 + T) and (x >= x4 - T))) and
                    (((y >= y3 - T) and (y <= y4 + T)) or 
                     ((y <= y3 + T) and (y >= y4 - T))))
        return (x,y,True,included)
    
    def getRadius(self,Z):
        """ Compute the radius of a V-bit given a Z coordinate. 
        
        If the V-bit is above stock top, we just mirror it.
        Technically, the file's broken, but hey, may as well do something.
        """
        if (self.v_top <= Z):
            return (Z - self.v_top) * tan(self.v_angle / 2)
        else:
            return (self.v_top - Z) * tan(self.v_angle / 2)
    
    def getAngle(self,center,point):
        """ Calculate the angle from a center to a point. """
        a = atan2(point[1] - center[1], point[0] - center[0])
        return a + ((2*pi) if (a<0.0) else 0)
    
    def isLargeAngle(self,center,p1,p2):
        """ Determine whether the SVG large angle flag should be set. """
        a1 = self.getAngle(center,p1)
        a2 = self.getAngle(center,p2)
        angle = a1 - a2
        if angle < 0:
            angle += 2 * pi
        return 1 if (abs(angle) > pi) else 0

    def interpolatePoints(self,center,p1,p2):
        """ Interpolate a set of points along an arc. """
        a1 = self.getAngle(center,p1)
        a2 = self.getAngle(center,p2)
        angle = a2 - a1
        dz = 1.0 * (p2[2]-p1[2])
        r = sqrt((center[0] - p1[0])**2 + (center[1] - p1[1])**2)
        length = r * abs(angle) / pi
        steps = int(round(length/self.v_step))
        points = []
        for i in range(1,steps):
          point = (center[0] + r * cos(a1 + angle*i/steps),
                   center[1] + r * sin(a1 + angle*i/steps),
                   p1[2] + dz*i/steps)
          points += [point]
        points += [p2]
        return points
    
    def makeVcarve(self,v_segments):
        """ Connect multiple V-carve segments into one path. 
        
        Start on one V-carve segment and chain all the way to the
        opposite end, then add a switchback and chain all the way
        back to the beginning.
        """
        vs = v_segments
        # Move to the starting point.
        path = 'M {} {} '.format(vs[0][1][0][0],vs[0][1][0][1])
        # Initial arc, if it's not a point.
        if vs[0][0][0][2] > 0:
            path += ('A {} {} 0 {} {} {} {} '
                    ).format(vs[0][0][0][2],vs[0][0][0][2],
                                 1 if (vs[0][0][0][2] > vs[0][0][1][2]) else 0,
                                 0,vs[0][1][1][0],vs[0][1][1][1])
        # Step through all the segments on the way to the other end.
        for v in range(len(vs)-1):
            # Check whether an intersection exists between the two
            # line segments.  If so, use it, otherwise, connect with an arc.
            x,y,valid,included = self.intersectLines(vs[v][1][1],
                                                     vs[v][1][2],
                                                     vs[v+1][1][1],
                                                     vs[v+1][1][2])
            if included: #line segments
                path += 'L {} {} '.format(x,y)
            else:
                path += ('L {} {} A {} {} 0 {} {} {} {} '
                        ).format(vs[v][1][2][0],vs[v][1][2][1],
                                     vs[v][0][1][2],vs[v][0][1][2],
                                     self.isLargeAngle(vs[v][0][1],
                                                       vs[v][1][2],
                                                       vs[v+1][1][1]),
                                     0,vs[v+1][1][1][0],vs[v+1][1][1][1])
        # Connecting line.
        path += 'L {} {} '.format(vs[len(vs)-1][1][2][0],
                                  vs[len(vs)-1][1][2][1])
        # Switchback arc, if it's not a point.
        if vs[len(vs)-1][0][1][2] > 0:
            path += ('A {} {} 0 {} {} {} {} '
                    ).format(vs[len(vs)-1][0][1][2],vs[len(vs)-1][0][1][2],
                             1 if (vs[len(vs)-1][0][1][2] >
                                   vs[len(vs)-2][0][0][2]) else 0,
                             0,vs[len(vs)-1][1][3][0],vs[len(vs)-1][1][3][1])
        # Step through all the segments on the way back home.
        for v in range(len(vs)-1,0,-1):
            # Check whether an intersection exists between the two
            # line segments.  If so, use it, otherwise, connect with an arc.
            x,y,valid,included = self.intersectLines(vs[v][1][3],
                                                     vs[v][1][0],
                                                     vs[v-1][1][3],
                                                     vs[v-1][1][0])
            if included: #line segments
                path += 'L {} {} '.format(x,y)
            else:
                path += ('L {} {} A {} {} 0 {} {} {} {} '
                        ).format(vs[v][1][0][0],vs[v][1][0][1],
                                 vs[v-1][0][1][2],vs[v-1][0][1][2],
                                 self.isLargeAngle(vs[v-1][0][1],
                                                   vs[v][1][0],
                                                   vs[v-1][1][3]),
                                 0,vs[v-1][1][3][0],vs[v-1][1][3][1])
        # And finally, close the curve.
        path += 'Z'
        return path
            
    def getVsegment(self,x1,y1,z1,x2,y2,z2):
        """ Compute the required data to define a V-carve segment. """
        r1 = self.getRadius(z1)
        r2 = self.getRadius(z2)
        p = self.getTangentPoints(x1,y1,r1,x2,y2,r2)
        return (((x1,y1,r1),(x2,y2,r2)),p)
        
    def parseLine(self,command,X,Y,Z,line,no_path=False):
        """ Parse a line of G-code. 
        
        This takes the current coordinates and modal command, then processes
        the new line of G-code to yield a new ending set of coordinates
        plus values necessary for curve computations.  It also returns the
        resulting path data, unless otherwise indicated, e.g. for V-carves.
        """
        comments = re.compile('\([^\)]*\)')
        commands = re.compile('([MSGXYZIJKR])([-.0-9]+)')
        
        lastX = X
        lastY = Y
        lastZ = Z
        I = 0.0
        J = 0.0
        K = 0.0
        R = None
        results = commands.findall(comments.sub('',line))
        if not line.startswith(";"):

            for (code,val) in results:
                v = float(val)
                i = int(v)
                
                if code == 'M':
                    if i == 3:
                        self.spindle = True
                    elif i == 5:
                        self.spindle = False
                elif code == 'S':
                    self.speed = v
                elif code == 'G':
                    if i == 0:
                        command = 'G0'
                    elif i == 1:
                        command = 'G1'
                    elif i == 2:
                        command = 'G2'
                    elif i == 3:
                        command = 'G3'
                    elif i == 20:
                        self.unit = 25.4
                    elif i == 21:
                        self.unit = 1.0
                    elif val == "90":
                        self.absolute = True
                    elif val == "91":
                        self.absolute = False
                    elif val == "90.1":
                        self.absoluteIJK = True
                    elif val == "91.1":
                        self.absoluteIJK = False
                elif code == 'X':
                    if self.absolute:
                        X = v * self.unit
                    else:
                        X += v * self.unit
                elif code == 'Y':
                    if self.absolute:
                        Y = v * self.unit
                    else:
                        Y += v * self.unit
                elif code == 'Z':
                    if self.absolute:
                        Z = v * self.unit
                    else:
                        Z += v * self.unit
                elif code == 'I':
                    I = v * self.unit
                    if self.absoluteIJK:
                        I -= X
                elif code == 'J':
                    J = v * self.unit
                    if self.absoluteIJK:
                        J -= Y
                elif code == 'K':
                    # Sure, process it, but we don't *do* anything with K.
                    K = v * self.unit
                    if self.absoluteIJK:
                        K -= Z
                elif code == 'R':
                    R = v * self.unit

        if no_path: # V-carving doesn't need any path data.
            return ((command, X, Y, Z, I, J, K, R, ''))
            
        # The line's been parsed.  Now let's generate path data from it.
        path = ''
        if command == 'G1':
            # If there's any XY motion, make a line segment.
            if ((X != lastX) or (Y != lastY)):
                path = 'L {} {} '.format(round(X,5),round(Y,5))
        elif (command == 'G2') or (command == 'G3'):
            # Arcs! Oh, what glorious fun we'll have!  First, sweep direction.
            sweep = 0 if (command == 'G2') else 1
            # R overrules I and J if both are present, so we compute
            # new I and J values based on R.  We need those to determine
            # whether the Large Angle Flag needs to be set.
            if R is not None:
                I,J = self.getIJ(lastX,lastY,X,Y,R)
            if (I != 0.0) or (J != 0.0):
                if sweep == 0:
                    large_arc = self.isLargeAngle((lastX+I,lastY+J),
                                                  (lastX,lastY),(X,Y))
                else:
                    large_arc = self.isLargeAngle((lastX+I,lastY+J),
                                                  (X,Y),(lastX,lastY))
                radius = sqrt(I**2 + J**2)
                path = 'A {} {} 0 {} {} {} {} '.format(round(radius,5),
                                                       round(radius,5),
                                                       large_arc,sweep,
                                                       round(X,5),round(Y,5))
            # No R, and no I or J either?  Let's just call it a line segment.
            # (It may have had a K, but we don't believe in K for SVG imports.)
            else:
                path = 'L {} {} '.format(round(X,5),round(Y,5))

        # In laser mode, if the spindle isn't active or the speed is zero,
        # there's no lasing to be had.  Drop the path data.  (The Inkscape
        # extension from J Tech Photonics uses G1/G2/G3 moves throughout,
        # with nary a G0, so if we don't do this, we'll show unlasered paths.)
        if (self.laser_mode and ((not self.spindle) or (self.speed == 0))):
            path = ''
        return ((command, X, Y, Z, I, J, K, R, path))

    def savePath(self,path,Z):
        """ Save a set of path data, filing it by Z if appropriate. """
        if (path.find('A') == -1) and (path.find('L') == -1):
            return #empty path
        if self.ignore_z:
            if path not in self.paths:
                self.paths.add(path)
        else:
            try:
                if path not in self.paths_by_z[Z]:
                    self.paths_by_z[Z].add(path)
            except KeyError:
                self.paths_by_z[Z] = set([path])
        
    def loadGCode(self,gcode_file):
        """ Load a G-code file, handling the contents. """
        if self.ignore_z:
            self.paths = set([])
        else:
            self.paths_by_z = {}
        self.absolute = True
        self.absoluteIJK = False
        self.unit=1.0
        command = ''
        X = 0.0
        Y = 0.0
        Z = 0.0
        lastX = X
        lastY = Y
        lastZ = Z
        self.minX = 0.0
        self.minY = 0.0
        self.minZ = 0.0
        self.maxX = 0.0
        self.maxY = 0.0
        self.maxZ = 0.0
        
        path = ''
        line = gcode_file.readline()
        v_segments = []
        while line:
            command,X,Y,Z,I,J,K,R,path_data = self.parseLine(command, 
                                                             X, Y, Z, line,
                                                             self.v_carve)
            self.minX = X if X < self.minX else self.minX
            self.maxX = X if X > self.maxX else self.maxX
            self.minY = Y if Y < self.minY else self.minY
            self.maxY = Y if Y > self.maxY else self.maxY
            self.minZ = Z if Z < self.minZ else self.minZ
            self.maxZ = Z if Z > self.maxZ else self.maxZ

            # V-carve mode.
            if self.v_carve:
                if (lastX != X) or (lastY != Y):
                    if command == 'G1':
                        v_segments += [self.getVsegment(lastX, lastY, lastZ,
                                                        X, Y, Z)]
                    elif (command == 'G2') or (command == 'G3'):
                        # We don't attempt to handle the plethora of curves
                        # that can result from V-carving arcs.  Instead, we
                        # just interpolate them and process the subparts.
                        points = self.interpolatePoints((lastX+I,lastY+J),
                                                        (lastX,lastY,lastZ),
                                                        (X,Y,Z))
                        iX = lastX
                        iY = lastY
                        iZ = lastZ
                        for p in points:
                            v_segments += [self.getVsegment(iX, iY, iZ,
                                                            p[0], p[1], p[2])]
                            iX = p[0]
                            iY = p[1]
                            iZ = p[2]
                    else:
                        if len(v_segments):
                            self.savePath(self.makeVcarve(v_segments),'VCarve')
                        v_segments = []
            # Standard mode (non-V-carve).
            else:
                if ((command == 'G0') or 
                    (not self.ignore_z and (Z != lastZ)) or 
                    (self.laser_mode and ((not self.spindle) or 
                                          (self.speed == 0)))):
                    if (path != ''):
                        self.savePath(path,lastZ)
                        path = ''
                if (((command == 'G1') or 
                     (command == 'G2') or 
                     (command == 'G3')) and (path == '')):
                    path = 'M {} {} {}'.format(lastX,lastY,path_data)
                else:
                    path += path_data
            lastX = X
            lastY = Y
            lastZ = Z
            line = gcode_file.readline()
        # Always remember to save the tail end of your work.
        if self.v_carve:
            if len(v_segments):
                self.savePath(self.makeVcarve(v_segments),'VCarve')
        else:
            if (path != ''):
                self.savePath(path,lastZ)
            
    def filterPaths(self):
        """ Filter out duplicate paths, leaving only the deepest instance. """
        if self.ignore_z:
            return
        z_depths = sorted(self.paths_by_z,None,None,True)
        for i in range(0,len(z_depths)):
            for j in range(i+1, len(z_depths)):
                self.paths_by_z[z_depths[i]] -= self.paths_by_z[z_depths[j]]
    
    def next_id(self):
        """ Return an incrementing value. """
        self.current_id += 1
        return self.current_id
    
    def getStyle(self,color='#000000',width=None):
        """ Create a CSS-type style string. """
        if width is None:
            width = self.tool_diameter
        return ('opacity:1;vector-effect:none;fill:none;fill-opacity:1;'
                'stroke:{};stroke-width:{};stroke-opacity:1;'
                'stroke-linecap:round;stroke-linejoin:round;'
                'stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0'
               ).format(color,width)
    
    def createSVG(self):
        """ Create the output SVG. """
        base = ('<svg xmlns="http://www.w3.org/2000/svg"'
                ' width="{}mm" height="{}mm" viewBox="{} {} {} {}"/>'
               ).format(self.maxX-self.minX, self.maxY-self.minY,
                        self.minX, self.minY, self.maxX-self.minX, self.maxY-self.minY)
        self.doc = etree.parse(StringIO((base)))
        svg = self.doc.getroot()
        # Since G-code and SVG interpret Y in opposite directions,
        # we just group everything under a transform that mirrors Y.
        svg = etree.SubElement(svg,'g',{'id':'gcode',
                                              'transform':'scale(1,-1)'})
        # Add illustrative axes to the SVG to facilitate positioning.
        etree.SubElement(svg,'path',
                               {'d':'M 0 {} V {}'.format(self.minY, self.maxY),
                                'style':self.getStyle('#00ff00',0.5),
                                'id':'vertical'})
        etree.SubElement(svg,'path',
                               {'d':'M {} 0 H {}'.format(self.minX, self.maxX),
                                'style':self.getStyle('#ff0000',0.5),
                                'id':'horizontal'})
        # For V-carves, include the paths and use a narrow stroke width.
        if self.v_carve:
            for path in self.paths:
                etree.SubElement(svg,'path',
                                       {'d':path,
                                        'style':self.getStyle(width=0.1),
                                        'id':'path{}'.format(self.next_id())})
        # For standard mode with Z ignored, include the paths.
        elif self.ignore_z:
            for path in self.paths:
                etree.SubElement(svg,'path',
                                       {'d':path,
                                        'style':self.getStyle(),
                                         'id':'path{}'.format(self.next_id())})
        # For standard mode with Z grouping, filter the paths, 
        # then add each group of paths (and optionally, labels).
        else:
            self.filterPaths()
            z_depths = sorted(self.paths_by_z)
            depth_num = 0
            for i in range(0,len(z_depths)):
                if len(self.paths_by_z[z_depths[i]]):
                    params = {'id':('group{}-{}'
                                   ).format(self.next_id(),z_depths[i]),
                              'style':self.getStyle()}
                    group = etree.SubElement(svg,'g',params)
                    
                    # If labels are enabled, add the label to the group.
                    if self.label_z:
                        params = {'x':'{}'.format(self.maxX),
                                  'y':'{}'.format(depth_num*-5),
                                  'transform':'scale(1,-1)',
                                  'id':'text{}'.format(i),
                                  'style':('opacity:1;fill:#0000ff;'
                                           'fill-opacity:1;stroke:none;'
                                           'font-size:4.5')}
                        if self.unit == 1.0:
                          label = '{} mm'.format(z_depths[i])
                        else:
                          label = '{} in'.format(z_depths[i]/self.unit)
                        etree.SubElement(group,'text',params
                                              ).text = label
                                     
                        depth_num += 1

                    # Now add the paths to the group.
                    for path in self.paths_by_z[z_depths[i]]:
                        id = 'path{}'.format(self.next_id())
                        etree.SubElement(group,'path',
                                               {'d':path,
                                                'style':self.getStyle(),
                                                'id':id})
            # If labels are enabled, label the labels.
            if self.label_z:
                etree.SubElement(svg,'text',
                                       {'x':'{}'.format(self.maxX),
                                        'y':'{}'.format(depth_num*-5),
                                        'transform':'scale(1,-1)',
                                        'id':'text{}'.format(i),
                                        'style':('opacity:1;fill:#0000ff;'
                                                 'fill-opacity:1;stroke:none;'
                                                 'font-size:4.5')}
                                      ).text = 'Z Groups:'

# And now for the code to allow Inkscape to run our lovely extension.                                      
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=('usage: %prog [options] GCodeFile'))
    parser.add_argument('-m', '--mode', help='Mode: vcarve, standard, laser', default='standard')
    parser.add_argument('-a', '--v_angle',  help='Included (full) angle for V-bit, in degrees.', default=None)
    parser.add_argument('-t', '--v_top',  help='Stock top (usually zero)', default=None)
    parser.add_argument('-s', '--v_step', help='Step size for curve interpolation.', default=None)
    parser.add_argument('-d', '--tool_diameter', help='Tool diameter / path width.', default=None)
    parser.add_argument('-u', '--units',  help='Dialog units.', default='mm')
    parser.add_argument('-z', '--z_axis', help='Z-axis: ignore,group,label', default=False)
    parser.add_argument('--tab')
    parser.add_argument('--inputhelp')
    parser.add_argument('inputfile')
	 
    # Now, process, my lovelies!
    args = parser.parse_args()
    
    # First steps first, what mode?
    v_carve = False
    ignore_z = False
    laser_mode = False
    if (args.mode == 'vcarve'):
      v_carve = True
    elif (args.mode == 'laser'):
      laser_mode = True
    
    # V-carve parameters.    
    try:
        v_angle = round(float(args.v_angle),3)
    except ValueError:
        v_angle = 1.0
    try:
        v_top = round(float(args.v_top) * 
                      (25.4 if (args.units == 'in') else 1.0),5)
    except ValueError:
        v_top = 0.0
    try:
        v_step = round(float(args.v_step) * 
                       (25.4 if (args.units == 'in') else 1.0),5)
    except ValueError:
        v_step = 1.0
    
    # Standard parameters.    
    try:
        diameter = round(float(args.tool_diameter) * 
                         (25.4 if (args.units == 'in') else 1.0),3)
    except ValueError:
        diameter = 1.0
    
    # General args.
    ignore_z = (args.z_axis == 'ignore')
    label_z = (args.z_axis == 'label')
     
    gc = ImportGCode(args.inputfile, v_carve, laser_mode, ignore_z, label_z, diameter, v_angle, v_top, v_step)
    gc.doc.write(sys.stdout.buffer)
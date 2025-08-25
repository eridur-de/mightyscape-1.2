#!/usr/bin/env python3

# Copyright (c) 2017, Ben Connors
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
from math import sin, cos, acos, tan, radians, pi, sqrt, ceil, floor
import inkex
from lxml import etree

__author__ = 'Ben Connors'
__credits__ = ['Ben Connors', 'Veronika Irvine', 'Jo Pol', 'Mark Shafer']
__license__ = 'Simplified BSD'

class Vector:
    def __repr__(self):
        return 'Vector(%.4f, %.4f)' % (self.dx,self.dy)

    def __hash__(self):
        return hash((self.dx,self.dy))

    def rotate(self,theta):
        """ Rotate counterclockwise by theta."""
        return self.mag*Vector(cos(self.theta+theta),
                               sin(self.theta+theta),
                               _theta=self.theta+theta)

    def __mul__(self,other):
        return Vector(self.dx*other,self.dy*other,_theta=self.theta)

    def __rmul__(self,other):
        return self*other

    def __init__(self,dx,dy,_theta=None):
        """ Create a vector with the specified components.
        _theta should NOT be passed in normal use - this value is passed by
        vector functions where the angle of the new vector is known in order
        to eliminate that calculation.
        """
        self.dx = float(dx)
        self.dy = float(dy)
        self.mag = sqrt(dx**2 + dy**2)
        self.tuple = (dx,dy)
        
        ## Angle to positive X axis
        if _theta == None:
            _theta = acos(self.dx/self.mag)
            self.theta = 2*pi-_theta if self.dy < 0 else _theta
        else:
            self.theta = _theta


class CircularGroundFromTemplate(inkex.EffectExtension):

    def unitToUu(self,param):
        """ Convert units.
        Converts a number in some units into the units used internally by 
        Inkscape.
        
        param is a string representing a number with units attached. An 
            example would be '3.8mm'. Any units supported by Inkscape
            are supported by this function.
        
        This wrapper function catches changes made to the location
        of the function between Inkscape versions.
        """
        try:
            return self.svg.unittouu(param)
        except:
            return inkex.unittouu(param)

    def loadFile(self):
        """ Load the specification for the unit cell from the file given.
        Note that the specification should be in the following format:
        TYPE    ROWS    COLS
        [x1,y1,x2,y2,x3,y3] [x4,y4,x5 ...

        And so on. The TYPE is always CHECKER and is ignored by this program.
        ROWS specifies the height of the     unit cell (i.e. max_y - min_y) 
        and COLS specifies the same for the width (i.e. max_x - min_x). 
        Note that this is not enforced when drawing the unit cell - points 
        may be outside this range. These values are used to determine the 
        distance between unit cells (i.e. unit cells may overlap).
        """
        # Ensure that file exists and has the proper extension
        if not self.options.file:
            inkex.errormsg('You must specify a template file.')
            exit()
        self.options.file = self.options.file.strip()
        if self.options.file == '':
            inkex.errormsg('You must specify a template file.')
            exit()
        if not os.path.isfile(self.options.file):
            inkex.errormsg('You have not specified a valid path for the template file.\n\nYour entry: '+self.options.file)
            exit()
        extension = os.path.splitext(self.options.file)[1]
        if extension != '.txt':
            inkex.errormsg('The file name must end with .txt.\n\nYour entry: '+self.options.file)
            exit()
            
        data = []
        rows, cols = -1, -1
        with open(self.options.file,'r') as f:
            for line in f:
                line = line.strip()
                ## If rows is not a positive integer, we're on the first line
                if rows == -1:
                    tmp = line.split('\t')
                    _type,cols,rows = tmp[0],int(tmp[1]),int(tmp[2])
                else:
                    data.append([])
                    for cell in line[1:-1].split(']\t['):
                        cell = cell.strip()
                        ## The pattern must be rotated 90 degrees clockwise. It's
                        ## simplest to just do that here
                        tmp = [float(n) for n in cell.split(',')]
                        data[-1].append([a for b in zip([rows-i for i in tmp[1::2]],[cols-i for i in tmp[::2]]) for a in b])
        return {'type': _type, 'rows': rows, 'cols': cols, 'data' : data}

    def line(self,points):
        """
        Draw a line from point at (x1, y1) to point at (x2, y2).
        Style of line is hard coded and specified by 's'.
        """
        # define the motions
        path = ('M%.4f,%.4fL' % tuple(points[0][:2])) + 'L'.join([('%f,%f' % tuple(a[:2])) for a in points[1:]])

        # define the stroke style
        s = {'stroke-linejoin': 'miter', 
            'stroke-width': self.options.linewidth,
            'stroke-opacity': '1.0', 
            'fill-opacity': '1.0',
            'stroke': self.options.linecolor, 
            'stroke-linecap': 'butt',
            'stroke-linejoin': 'miter',
            'fill': 'none'
        }


        ## Attributes for new element
        attribs = {'style':str(inkex.Style(s)),
                   'd' : path}

        ## Add new element
        etree.SubElement(self.svg.get_current_layer(), inkex.addNS('path', 'svg'), attribs)

    def baseVectors(self,segments):
        """ Create vectors for all vertices on the specified polygon."""
        ## Start at 12 o'clock
        theta = pi/2
        ## Move clockwise
        dtheta = -2*pi/segments

        vector = Vector(0,self.options.diameter/2)
        vectors = [vector]
        for i in range(1,segments):
            vector = vector.rotate(dtheta)
            vectors.append(vector)
        return vectors

    def fuzzyEquality(self,a,b):
        return (a-b <= 1e-8)

    def circleWrap(self,points,segments):
        """ Wrap a grid around the origin.
        <<points>> is a list of 2- or 3-tuples.
            In the case of 3-tuples, they should be laid out like: (x,y,name)
            Whereas 2-tuples should eliminate the name portion.
                Only one format may be passed; they may not be mixed.
            x- and y- values are rounded to the nearest integer.
                If more precision is desired, scale up the points before calling this function.
            x-values should be within [0,segments)
                Values not within range will be moved within range.
            y-values must be greater than 0
                An error will be raised if a y-value is less than 0.
            The 'name' portion is not touched by this function; it is merely
            passed along. This may be used to identify points or groups of points.
        <<radius>> is the inside radius (i.e. distance to origin from a point with
            a y-value of 0).
        <<segments>> is the number of segments (sides) of the polygon.
        <<angle>> is the angle of the diagonal of the square approximation. It must be
            somewhere on (0,pi/2).
        """
        angle = self.options.angle
        if angle <= 0 or angle >= pi/2:
            raise ValueError('Angle must be in (0,pi/2)')

        vectors = self.baseVectors(segments)
        theta = 2*pi/segments
        
        """
        Determine the coefficient to multiply the vectors by in order to deal
        with a higher x-value.
        With R being the large radius (radius to next y-value) and r being the
        small radius (radius to current y-value):
        
        a^2 = r^2 (1 - cos(theta)) ## Cosine law
        b^2 = R^2 (1 - cos(theta))

        To get the most square-like trapezoid:
        R - r = 0.5(a+b)

        Subbing in the equations for b^2 and a^2 yields the following lines.
        """
        C = sqrt(2*(1-cos(theta)))
        val = 2*tan(pi/2-angle)
        coeff = (val+C)/(val-C)
        diff = coeff-1

        ## Sort points in order of increasing y-value.
        named = False
        if len(points[0]) == 3:
            named = True
            points = [(x,y,name) for x,y,name in sorted(points,key=lambda a: a[1])]
        else:
            points = [(x,y,None) for x,y in sorted(points,key=lambda a: a[1])]

        done = []
        cur_y = 0
        for point in points:
            x,y,name = point

            ## Check constraints
            if y < cur_y:
                raise ValueError('Invalid point (%d,%d)' % (x,y))
            elif y >= cur_y+1:
                ## Multiply vectors accordingly
                delta = floor(y-cur_y)
                vectors = [(coeff**delta)*v for v in vectors]
                cur_y = floor(y)

            ## Wrap x-value to lie in the proper place
            ## lazy
            while x < 0:
                x += segments
            while x >= segments:
                x -= segments

            if self.fuzzyEquality(y,int(y)) and self.fuzzyEquality(x,int(x)):
                x = int(x)
                ## Can do it the quick way
                wx,wy = vectors[x].tuple
            else:
                ## Use vector rotation
                ## Determine nearest vector (counterclockwise)
                pointer = vectors[floor(x)]
                ## Scale x and y to be within (0,1)
                x -= int(x)
                y -= int(y)
                c = C*x ## This value is used a lot, cache it
                ## Now the angle of rotation must be determined using cosine law
                factor = 1
                if not self.fuzzyEquality(x,0):
                    ## x isn't equal to 0, must rotate vector
                    n2 = 1+c**2-2*c*cos((pi-theta)/2)
                    factor = sqrt(n2)
                    phi = acos((n2+1-c**2)/(2*factor))
                    pointer = pointer.rotate(-phi)
                ## Correct vector magnitude
                pointer = (1+y*diff)*factor*pointer
                wx,wy = pointer.tuple
            if named:
                done.append((wx,wy,name))
            else:
                done.append((wx,wy))
        return done

    def createGround(self,unit,rows,cols,scale=1):
        """ Return a lace ground.

        This function returns a list of points and corresponding lines that may
        be transformed or passed to a drawing function (such as draw_image) in
        order to draw a lace ground.

        unit is the pattern for the lace ground, in the format returned by
            loadFile.

        rows and cols are integers and represent the number of horizontal repeats
            and vertical repeats of the pattern, respectively.

        scale is an optional value that can be used to scale the pattern before it
            is repeated. Note that this comes with some constraints - the
            template's rows and cols after scaling (i.e. unit['rows']*scale) must
            be an integer. For example, a template with 4 rows and 4 cols before
            scaling may be scaled by any integer value above 1 and select values
            between 1 and 0 (namely 0.25,0.5,0.75). A scale value of 'True' may be
            passed if each repeat of the template should fit within a 1x1 square.
        """
        data = unit['data']
        unit_rows = unit['rows']
        unit_cols = unit['cols']
        if scale <= 0:
            raise ValueError('Scale must be greater than zero')
        elif scale != 1:
            ## The user wants to scale the template
            _data = []
            for row in data:
                _row = []
                for c in row:
                    if scale == True:
                        _row.append([i for n in zip([a/unit_cols for a in c[::2]],[a/unit_rows for a in c[1::2]]) for i in n])
                    else:
                        _row.append([a*scale for a in c])
                _data.append(_row)
            data = _data
            unit_rows *= scale
            unit_cols *= scale
            ## Catching invalid input
            if not self.fuzzyEquality(unit_rows,int(unit_rows)):
                raise ValueError('Scale factor must result in an integer value for template rows')
            if not self.fuzzyEquality(unit_cols,int(unit_cols)):
                raise ValueError('Scale factor must result in an integer value for template cols')
            unit_rows = int(unit_rows)
            unit_cols = int(unit_cols)
        line_num = 0
        points = []
        for c in range(cols):
            ## Do each column first
            x = c*unit_cols
            for r in range(rows):
                y = r*unit_rows
                for row in data:
                    for x1,y1,x2,y2,x3,y3 in row:
                        ## In order to draw lines in the correct order, an extra
                        ## point must be added
                        p1 = (x+x1,y+y1,'%09da,1'%line_num)
                        p2 = (x+x2,y+y2,'%09da,2'%line_num)
                        p1a = (x+x1,y+y1,'%09db,1'%line_num)
                        p3 = (x+x3,y+y3,'%09db,3'%line_num)
                        points.extend([p1,p2,p1a,p3])
                        line_num += 1
        return points

    def draw(self, points,line=lambda a: None):
        """ Draw the image.
        points - a list of points, as returned by createGround.
        line - a function that draws a line connecting all points in the passed list in order.
        """
        groups = {}
        ## This loop scales points, sorts them into groups, and gets image parameters
        xs = []
        ys = []
        for x,y,n in points:
            xs.append(x)
            ys.append(y)
            sn = n.split(',',1)
            ident = 0
            if len(sn) == 2:
                ident = int(sn[1])
                n = sn[0]
            if n not in groups:
                groups[n] = []
            groups[n].append((x,y,ident))
        max_x = max(xs)
        min_x = min(xs)
        max_y = max(ys)
        min_y = min(ys)
        ## Sort all groups to draw lines in order
        for group in groups:
            groups[group].sort(key=lambda a:a[2])
        ## Sort all groups to draw groups in order
        groups = sorted([(name,pts) for name,pts in groups.items()],key=lambda a:a[0])
        ## Draw lines
        for name,pts in groups:
            _pts = []
            for p in pts:
                _pts.append([p[0]-min_x,p[1]-min_y])
            self.line(_pts)

    def add_arguments(self, pars):
        pars.add_argument('--file')
        pars.add_argument('--angle', type=float)
        pars.add_argument('--cols', type=int)
        pars.add_argument('--diameter', type=float)
        pars.add_argument('--diamunits')
        pars.add_argument('--rows', type=int)
        pars.add_argument('--linewidth', type=float)
        pars.add_argument('--lineunits')
        pars.add_argument('--linecolor', type=inkex.Color)

    def effect(self):
        ## Load the file
        unit = self.loadFile()
        self.options.linecolor = self.options.linecolor.to_rgb()

        ## Change the input to universal units
        self.options.diameter = self.unitToUu(str(self.options.diameter)+self.options.diamunits)
        self.options.linewidth = self.unitToUu(str(self.options.linewidth)+self.options.lineunits)
        
        ## Convert the angle
        self.options.angle = radians(self.options.angle)

        ## Ensure no y-values are below 0
        min_y = min([b for a in [i[1::2] for row in unit['data'] for i in row] for b in a]) 
        if min_y < 0:
            data = []
            for row in unit['data']:
                _row = []
                for c in row:
                    _row.append([a for b in zip(c[::2],[i-min_y for i in c[1::2]]) for a in b])
                data.append(_row)
            unit['data'] = data

        ## Create the ground coordinates
        points = self.createGround(unit,self.options.rows,self.options.cols)

        ## Wrap it around a polygon
        points = self.circleWrap(points,self.options.cols*unit['cols'])

        ## Draw everything
        self.draw(points,line=lambda a: self.line(a))

if __name__ == '__main__':
    CircularGroundFromTemplate().run()
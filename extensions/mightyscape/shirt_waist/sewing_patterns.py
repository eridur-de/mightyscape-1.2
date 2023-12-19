#!/usr/bin/env python3
#
# sewing_patterns.py
# Inkscape extension-Effects-Sewing Patterns
# Copyright (C) 2010, 2011, 2012 Susan Spencer, Steve Conklin  < www.taumeta.org >
#
# This program is free software:you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version. Attribution must be given in
# all derived works.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see < http://www.gnu.org/licenses/ >

import subprocess, math, inkex, gettext
from lxml import etree

def debug(errmsg, file = 'bell'):
    #audio files directory: /usr/share/sounds/ubuntu/stereo
    sounds(file)
    inkex.errormsg(gettext.gettext(errmsg))

def sounds(file):
    subprocess.call(['/usr/bin/canberra-gtk-play', '--id', file ])

#---
class Point():
    '''Python object class to create variables that represent a named Cartesian point.
    Accepts id, x, y. Returns object with .id, .x, .y attributes.
    Example: a5 = Point('a5', 10.0, 15.32) returns variable a5 where a5.id = 'a5', a5.x = 10.0, a5.y = 15.32xt
    If called with no parameters the defaults are id = '', x = 0, y = 0
    The python object's id attribute enables it to be represented on the canvas as an svg object with the same id.
    '''
    def __init__(self, id = '', x = 0.0, y = 0.0): #if no parameters are passed in then the default values id = '', x = 0, y = 0 are used
        self.id = id
        self.x = x
        self.y = y
        self.y = y

def patternPointXY(parent, id, x, y):
    '''Accepts parent, id, x, y. Returns object of class Point. Calls addPoint() & addText() to create a pattern point on canvas.'''
    # create python variable
    pnt = Point(id, x, y)
    # create svg circle red 5px radius
    addCircle(parent, id, x, y, radius = 5, fill = 'red', stroke = 'red', stroke_width = '1', reference = 'true')
    #draw label 8px right and 8px above circle
    addText(parent, id + '_text', x + 8, y-8, id, fontsize = '30', textalign = 'left', textanchor = 'start', reference = 'true') #the id is used for two things here: the text object's id and the text object's content.
    return pnt # return python variable for use in remainder of pattern

def patternPoint(parent, id, pnt):
    """Wrapper for patternPointXY. Accepts a Point object instead of X & Y values."""
    return patternPointXY(parent, id, pnt.x, pnt.y)

def controlPointXY(parent, id, x, y):
    '''Accepts parent, id, x, y. Returns object of class Point. Calls addPoint() & addText() to create a pattern point with label on canvas.'''
    # create python variable
    pnt = Point(id, x, y)
    # create unfilled grey circle 5px radius
    addCircle(parent, id, x, y, radius = 5, fill = 'none', stroke = 'gray', stroke_width = '1', reference = 'true')
    #draw label 8px right and 8px above circle
    addText(parent, id + '_text', x + 8, y-8, id, fontsize = '30', textalign = 'left', textanchor = 'start', reference = 'true') #the id is used twice: the text object id and the text object content.
    return pnt # return python variable for use in remainder of pattern

def controlPoint(parent, id, pnt):
    """Wrapper for controlPointXY. Accepts a Point object instead of X & Y values."""
    return controlPointXY(parent, id, pnt.x, pnt.y)

def pointList( * args):
    """Accepts list of args. Returns array of args."""
    list = []
    for arg in args:
        list.append(arg)
    return list

#---tests for position---
def isRight(pnt1, pnt2):
    '''returns 1 if pnt2 is to the right of pnt1'''
    right = 0
    if pnt2.x > pnt1.x:
        right = 1
    return right

def isLeft(pnt1, pnt2):
    '''returns 1 if pnt2 is to the left of pnt1'''
    left = 0
    if pnt2.x < pnt1.x:
        left = 1
    return left

def isAbove(pnt1, pnt2):
    '''returns 1 if pnt2 is above pnt1'''
    up = 0
    if pnt2.y < pnt1.y:
        up = 1
    return up

def isBelow(pnt1, pnt2):
    '''returns 1 if pnt2 is below pnt1'''
    down = 0
    if pnt2.y > pnt1.y:
        down = 1
    return down

def lowest(pnts):
    """Accepts array pnts[]. Returns lowest point in array."""
    low = Point('', pnts[0].x, pnts[0].y)
    for item in pnts:
        if isBelow(low, item): #if item is below current low
            updatePoint('', low, item)
    return low

def highest(pnts):
    """Accepts array pnts[]. Returns highest point in array."""
    high = Point('', pnts[0].x, pnts[0].y)
    for item in pnts:
        if isAbove(high, item): #if item is above current high
            updatePoint(high, item)
    return high

def leftmost(pnts):
    """Accepts array pnts[]. Returns leftmost point in array."""
    left = Point('', pnts[0].x, pnts[0].y)
    for item in pnts:
        if isLeft(left, item):
            updatePoint(left, item)
    return left

def rightmost(pnts):
    """Accepts array pnts[]. Returns rightmost point in array."""
    right = Point('', pnts[0].x, pnts[0].y)
    for item in pnts:
        if isRight(right, item):
            updatePoint(right, item)
    return right

#---functions to calculate points. These functions do not create SVG objects---

def updatePoint(p1, p2):
    '''Accepts p1 and p2 of class Point. Updates p1 with x & y values from p2'''
    p1.x = p2.x
    p1.y = p2.y
    return

def right(p1, n):
    '''Accepts point p1 and float n. Returns (x,y) to the right of p1 at (p1.x + n, p1.y)'''
    return Point('', p1.x + n, p1.y)

def left(p1, n):
    '''Accepts point p1 and float n. Returns p2 to the left of p1 at (p1.x-n, p1.y)'''
    return Point('', p1.x-n, p1.y)

def up(p1, n):
    '''Accepts point p1 and float n. Returns p2 above p1 at (p1.x, p1.y-n)'''
    return Point('', p1.x, p1.y-n)

def down(p1, n):
    '''Accepts point p1 and float n. Returns p2 below p1 at (p1.x, p1.y + n)'''
    return Point('', p1.x, p1.y + n)

def symmetric(p1, p2, type = 'vertical'):
    """
    Accepts p1 and p2 of class Point, and optional type is either 'vertical' or 'horizontal with default 'vertical'.
    Returns p3 of class Point as "mirror image" of p1 relative to p2
    If type == 'vertical': pnt is on opposite side of vertical line x = p2.x from p1
    If type == 'horizontal': pnt is on opposite side of horizontal line y = p2.y from p1
    """
    p3 = Point()
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    if (type == 'vertical'):
        p3.x = p2.x + dx
        p3.y = p1.y
    elif (type == 'horizontal'):
        p3.x = p1.x
        p3.y = p2.y + dy
    return p3

def polar(p1, length, angle):
    '''
    Adapted from http://www.teacherschoice.com.au/maths_library/coordinates/polar_-_rectangular_conversion.htm
    Accepts p1 as type Point, length as float, angle as float. angle is in radians
    Returns p2 as type Point, calculated at length and angle from p1,
    Angles start at position 3:00 and move clockwise due to y increasing downwards on Cairo Canvas
    '''
    id = ''
    r = length
    x = p1.x + (r * math.cos(angle))
    y = p1.y + (r * math.sin(angle))
    p2 = Point(id, x, y)
    return p2

def midPoint(p1, p2, n = 0.5):
    '''Accepts points p1 & p2, and n where 0 < n < 1. Returns point p3 as midpoint b/w p1 & p2'''
    p3 = Point('', (p1.x + p2.x) * n, (p1.y + p2.y) * n)
    return p3


#---measurements
def distance(p1, p2):
    '''Accepts two points p1 & p2. Returns the distance between p1 & p2.'''
    return ( ((p2.x-p1.x) ** 2) + ((p2.y-p1.y) ** 2) ) ** 0.5

def angleOfDegree(degree):
    '''Accepts degree. Returns radians.'''
    return degree  *  math.pi/180.0

def angleOfLine(p1, p2):
    """ Accepts points p1 & p2. Returns the angle of the vector between them. Uses atan2."""
    return math.atan2(p2.y-p1.y, p2.x-p1.x)

def angleOfVector(p1, v, p2):
    '''Accepts three points o1, v, and p2. Returns radians of the angle formed between the three points.'''
    return abs(angleOfLine(v, p1)-angleOfLine(v, p2))

def slopeOfLine(p1, p2):
    """ Accepts two point objects and returns the slope """
    if ((p2.x-p1.x) != 0):
        m = (p2.y-p1.y)/(p2.x-p1.x)
    else:
        #TODO: better error handling here
        debug('Vertical Line in slopeOfLine')
        m = None
    return m

def slopeOfAngle(radians):
    '''
    Accepts angle (radians)
    Returns the slope as tangent radians
    '''
    #get tangent of radians
    return math.tan(radians)

#---intersections & extensions

def extendLine(p1, p2, length, rotation=0):
    """
    Accepts two directed points of a line, and a length to extend the line
    Finds point along line at length from p2 in direction p1->p2
    """
    return onLineAtLength(p2, p1, -length)

def onLineAtLength(p1, p2, length, rotation=0):
    """
    Accepts points p1 and p2, distance,  and an optional rotation angle.
    Returns coordinate pair on the line at length measured from p1 towards p2
    If length is negative,  will return a coordinate pair at length measured
    from p1 in opposite direction from p2.
    The result is optionally rotated about the first point by the rotation angle in degrees
    """
    lineangle = angleOfLine(p1, p2)
    angle = lineangle + rotation * (math.pi/180)
    x = (length * math.cos(angle)) + p1.x
    y = (length * math.sin(angle)) + p1.y
    return Point('', x, y)

def onLineAtX(p1, p2, x):
    #on line p1-p2, given x find y
    if (p1.x == p2.x):# vertical line
        raise ValueError('Points form a vertical line, infinite answers possible')
        return None
    else:
        m = (p2.y - p1.y)/(p2.x - p1.x)
        b = p2.y - (m * p2.x)
        return Point('', x, (m * x) + b)

def onLineAtY(p1, p2, y):
    #on line p1-p2, find x given y
    if (p1.y == p2.y): #if horizontal line
        raise ValueError('Points form a horizontal line, infinite answers possible')
        return None
    elif (p1.x == p2.x): # if vertical line
        return Point('', p1.x, y)
    else:
        m = (p1.y - p2.y)/(p1.x - p2.x)
        b = p2.y - (m * p2.x)
        return Point('', (y - b)/m, y)

def intersectLines(p1, p2, p3, p4):
    """
    Find intersection between two lines. Accepts p1, p2, p3, p4 as class Point. Returns p5 as class Point
    Intersection does not have to be within the supplied line segments
    """
    x, y = 0.0, 0.0
    if (p1.x == p2.x): #if 1st line vertical, use slope of 2nd line
        x = p1.x
        m2 = slopeOfLine(p3, p4)
        b2 = p3.y-m2 * p3.x
        y = m2 * x + b2
    elif (p3.x == p4.x): #if 2nd line vertical, use slope of 1st line
        x = p3.x
        m1 = slopeOfLine(p1, p2)
        b1 = p1.y-m1 * p1.x
        y = m1 * x + b1
    else: #otherwise use ratio of difference between points
        m1 = (p2.y-p1.y)/(p2.x-p1.x)
        m2 = (p4.y-p3.y)/(p4.x-p3.x)
        b1 = p1.y-m1 * p1.x
        b2 = p3.y-m2 * p3.x
        #if (abs(b1-b2) < 0.01) and (m1 == m2):
            #x = p1.x
        #else:
            #x = (b2-b1)/(m1-m2)
        if (m1 == m2):
            #TODO: better error handling here
            debug(' **  **  *  Parallel lines in intersectLines  **  **  * ')
        else:
            x = (b2-b1)/(m1-m2)
            y = (m1 * x) + b1 # arbitrary choice, could have used m2 & b2
    p5 = Point("", x, y)
    return p5

def intersectLineRay(P1, P2, R1, angle):
    '''
    Accepts two points defining a line, and a point and angle defining a ray.
    Returns point where they intersect.
    '''
    #define a line R1-R2 by finding point R2 along ray 25 pixels (arbitary) from R1
    R2 = polar(R1, 1  *  25,  angle)
    pnt = intersectLines(P1, P2, R1, R2)
    return pnt

def onRayAtX(P, angle, x):
    '''
    Accepts point P and angle of line.
    Returns point along ray at x
    '''
    #convert degrees to slope
    m = slopeOfAngle(angle)
    #solve for y
    #(P.y - y)/(P.x - x) = m
    y = P.y - m * (P.x - x)
    return Point('', x, y)

def onRayAtY(P, angle, y):
    '''
    Accepts point P and angle of line.
    Returns point along ray at y
    '''
    #convert degrees to slope
    m = slopeOfAngle(angle)
    #solve for x
    #(P.y - y)/(P.x - x) = m
    x = P.x - (P.y - y)/m
    return Point('', x, y)

def intersectCircles(C1, r1, C2, r2):
    """
    Accepts C1, r1, C2, r2 where C1 & C2 are center points of each circle, and r1 & r2 are the radius of each circle.
    Returns an array of points of intersection.
    """
    x0, y0 = C1.x, C1.y
    x1, y1 = C2.x, C2.y
    d = distance(C1, C2) # distance b/w circle centers
    dx, dy = (x1-x0), (y1-y0) # negate y b/c canvas increases top to bottom
    pnts = []
    if (d == 0):
        #intersections = 0
        #TODO: better error handling here
        debug('center of both circles are the same in intersectCircles()')
        debug('C1 = ', C1.x, C1.y, 'radius1 = ', r1)
        debug('C2 = ', C2.x, C2.y, 'radius1 = ', r2)
        return
    elif (d < abs(r1-r2)):
        #intersections = 0
        #TODO: better error handling here
        debug('one circle is within the other in intersectCircles()')
        debug('d = ', d)
        debug('r1 - r2 = ', (r1-r2))
        debug('d <  abs(r1 - r2) ?', (d < abs(r1-r2)))
        debug('C1 = ', C1.x, C1.y, 'radius1 = ', r1)
        debug('C2 = ', C2.x, C2.y, 'radius1 = ', r2)
        return
    elif (d > (r1 + r2)):
        #intersections = 0
        #TODO: better error handling here
        debug('circles do not intersect in intersectCircles()')
        debug('d = ', d)
        debug('r1 + r2 = ', (r1 + r2))
        debug('d  >  abs(r1 + r2) ?', (d > abs(r1 + r2)))
        debug('C1 = ', C1.x, C1.y, 'radius1 = ', r1)
        debug('C2 = ', C2.x, C2.y, 'radius1 = ', r2)
        # TODO:possible kluge -check if this is acceptable using a small margin of error between r1 & r2 (0.5 * CM)?:
        #r2 = d-r1
        return
    else:
        #intersections = 2 or intersections = 1
        a = ((r1 * r1)-(r2 * r2) + (d * d))/(2.0 * d)
        x2 = x0 + (dx * a/d)
        y2 = y0 + (dy * a/d)
        h = math.sqrt((r1 * r1)-(a * a))
        rx = -dy * (h/d)
        ry = dx * (h/d)
        X1 = x2 + rx
        Y1 = y2 + ry
        X2 = x2-rx
        Y2 = y2-ry
        pnts.append(Point("", X1, Y1))
        pnts.append(Point("", X2, Y2))
        return pnts

def onCircleAtX(C, r, x):
    """
    Finds points on circle where p.x=x
    Accepts C as an object of class Point or xy coords for the center of the circle,
    r as the radius,  and x to find the points on the circle
    Returns an array P
    Based on paulbourke.net/geometry/sphereline/sphere_line_intersection.py
    """
    #print 'C =', C.x, C.y
    #print 'r =', r
    #print 'x =', x
    P = []
    if abs(x - C.x) > r:
        print('abs(x - C.x) > r ...', abs(x - C.x), ' > ', r)
        print('x is outside radius of circle in intersections.onCircleAtX()')
    else:
        translated_x = x - C.x # center of translated circle is (0, 0) as translated_x is the difference b/w C.x & x
        translated_y1 = abs(math.sqrt(r**2 - translated_x**2))
        translated_y2 = -(translated_y1)
        y1 = translated_y1 + C.y # translate back to C.y
        y2 = translated_y2 + C.y # translate back to C.y
        P.append(Point('', x, y1))
        P.append(Point('', x, y2))
    return P

def onCircleAtY(C, r, y):
    """
    Finds points one or two points on circle where P.y=y
    Accepts C of class Point or coords as circle center,  r of type float as radius,  and y of type float)
    Returns an array P
    Based on paulbourke.net/geometry/sphereline/sphere_line_intersection.py
    """
    #print('C =', C.x, C.y)
    #print('r =', r)
    #print('x = ', y))
    P = []
    if abs(y - C.y) > r:
        print('abs(y - C.y) > r ...', abs(y - C.y), ' > ', r)
        print('y is outside radius in onCircleAtY() -- no intersection')
    else:
        translated_y = y - C.y
        translated_x1 = abs(math.sqrt(r**2 - translated_y**2))
        translated_x2 = -translated_x1
        x1 = translated_x1 + C.x
        x2 = translated_x2 + C.x
        P.append(Point('', x1, y))
        P.append(Point('', x2, y))
    return P

def intersectLineCircle(P1, P2, C, r):
    """
    Finds intersection of a line segment and a circle.
    Accepts circle center point object C, radius r, and two line point objects P1 & P2
    Returns an array P with up to two coordinate pairs as P.intersections P[0] & P[1]
    Based on paulbourke.net/geometry/sphereline/sphere_line_intersection.py
    """

    #print('C =', C.x, C.y)
    #print('P1 =', P1.x, P1.y)
    #print('P2 =', P2.x, P2.y)
    #print('r =', r, 'pts', ', ', r / CM, 'cm')

    p1, p2 = Point('', '', ''), Point('', '', '')
    P = []

    if P1.x == P2.x: #vertical line
        if abs(P1.x - C.x) > r:
            print('no intersections for vertical line P1', P1.name, P1.x, P1.y, ',  P2', P2.name, P2.x, P2.y, ', and Circle', C.name, C.x, C.y, ',  radius', r)
            return None
        else:
            #print('Vertical line')
            p1.x = P1.x
            p2.x = P1.x
            p1.y = C.y + sqrt(r**2 - (P1.x - C.x)**2)
            p2.y = C.y - sqrt(r**2 - (P1.x - C.x)**2)
    elif P1.y == P2.y: #horizontal line
        if abs(P1.y-C.y) > r:
            print('no intersections for horizontal line P1', P1.name, P1.x, P1.y, ',  P2', P2.name, P2.x, P2.y, ', and Circle', C.name, C.x, C.y, ',  radius', r)
            return None
        else:
            #print('Horizontal line')
            p1.y = P1.y
            p2.y = P1.y
            p1.x = C.x + sqrt(r**2 - (P1.y - C.y)**2)
            p2.x = C.x - sqrt(r**2 - (P1.y - C.y)**2)
    else:
        a = (P2.x - P1.x)**2 + (P2.y - P1.y)**2
        b = 2.0 * ((P2.x - P1.x) * (P1.x - C.x)) + ((P2.y - P1.y) * (P1.y - C.y))
        c = C.x**2 + C.y**2 + P1.x**2 + P1.y**2 - (2.0 * (C.x * P1.x + C.y * P1.y)) - r**2
        i = b**2 - 4.0 * a * c
        if i < 0.0:
            print('no intersections b/w line', P1.name, P1.x, P1.y, '--', P2.name, P2.x, P2.y, 'and Circle', C.name, C.x, C.y, 'with radius', r)
            return None
        elif i == 0.0:
            # one intersection
            #print('one intersection')
            mu = -b/(2.0 * a)
            p1.x, p1.y = P1.x + mu * (P2.x - P1.x), P1.y + mu * (P2.y - P1.y)
        elif i > 0.0:
            # two intersections
            #print('two intersections')
            # first intersection
            mu1 = (-b + math.sqrt(i)) / (2.0*a)
            p1.x, p1.y = P1.x + mu1 * (P2.x - P1.x), P1.y + mu1 * (P2.y - P1.y)
            # second intersection
            mu2 = (-b - math.sqrt(i)) / (2.0*a)
            p2.x, p2.y = P1.x + mu2 * (P2.x - P1.x), P1.y + mu2 * (P2.y - P1.y)
    P.append(p1)
    P.append(p2)
    return P

def intersectChordCircle(C, r, P, chord_length):
    ''' Accepts center of circle, radius of circle, a point on the circle, and chord length.
    Returns an array of two points on the circle at chord_length distance away from original point'''
    d = chord_length
    # point on circle given chordlength & starting point = 2 * asin(d/2r)
    d_div_2r = d/(2.0 * r)
    angle = 2 * asin(d_div_2r)
    pnts = []
    pnts.append(polar(C, r, angle))
    pnts.append(polar(C, r, - angle))
    return pnts

def intersectLineCurve(P1, P2, curve, n = 100):
    '''
    Accepts two points of a line P1 & P2, and an array of connected bezier curves [P11, C11, C12, P12, C21, C22, P22, C31, C32, P32, ...]
    Returns an array points_found[] of point objects where line intersected with the curve, and tangents_found[] of tangent angle at that point
    '''
    # get polar equation for line for P1-P2
    # point furthest away from 1st point in curve[] is the fixed point & sets the direction of the angle towards the curve
    #if distance(P1, curve[0])  >  = distance(P2, curve[0] ):
    #   fixed_pnt = P1
    #   angle = angleOfLine(P1, P2)
    #else:
    #   fixed_pnt = P2
    #  angle = angleOfLine(P2, P1)
    #debug('intersectLineCurve...')
    #debug('....P1 = ' + P1.id + ' ' + str(P1.x) + ', ' + str(P1.y))
    #debug('....P2 = ' + P2.id + ' ' + str(P2.x) + ', ' + str(P2.y))
    #for pnt in curve:
        #debug( '....curve = ' + pnt.id + ' ' + str(pnt.x) + ', ' + str(pnt.y))
    fixed_pnt = P1
    angle = angleOfLine(P1, P2)
    intersections = 0
    points_found = []
    tangents_found = []
    pnt = Point()
    j = 0
    while j <= len(curve) -4: # for each bezier curve in curveArray
        intersection_estimate = intersectLines(P1, P2, curve[j], curve[j + 3]) # is there an intersection?
        if intersection_estimate != None or intersection_estimate != '':
            interpolatedPoints = interpolateCurve(curve[j], curve[j + 1], curve[j + 2], curve[j + 3], n)  #interpolate this bezier curve, n = 100
            k = 0
            while k < len(interpolatedPoints)-1:
                length = distance(fixed_pnt, interpolatedPoints[k])
                pnt_on_line = polar(fixed_pnt, length, angle)
                range = distance(interpolatedPoints[k], interpolatedPoints[k + 1]) # TODO:improve margin of error
                length = distance(pnt_on_line, interpolatedPoints[k])
                #debug(str(k) + 'pntOnCurve = ' + \
                #       str(interpolatedPoints[k].x) + ', ' + str(interpolatedPoints[k].y) + \
                #       'intersectLineAtLength = ' + str(pnt_on_line.x) + ', ' + str( pnt_on_line.y)\
                 #      + 'length = ' + str(length) + 'range = ' + str(range))
                if ( length <= range):
                    #debug('its close enough!')
                    if k > 1:
                        if (interpolatedPoints[k-1] not in points_found) and (interpolatedPoints[k-2] not in points_found):
                            points_found.append(interpolatedPoints[k])
                            tangents_found.append(angleOfLine(interpolatedPoints[k-1], interpolatedPoints[k + 1]))
                            intersections += 1
                    elif k == 1:
                        if (curve[0] not in intersections):
                            points_found.append(interpolatedPoints[1])
                            tangents_found.append(angleOfLine(curve[0], interpolatedPoints[2]))
                            intersections += 1
                    else:
                        intersections.append(curve[0])
                        tangents_found.append(angleOfLine(curve[0], curve[1]))
                k += 1
        j += 3 # skip j up to P3 of the current curve to be used as P0 start of next curve
        if intersections == 0:
            #TODO: better error handling here
            debug('no intersections found in intersectLineCurve(' + P1.id + ', ' + P2.id + ' and curve')
    #return points_found, tangents_found
    return points_found

def interpolateCurve(P0, C1, C2, P1, t = 100):
    '''
    Accepts curve points P0, C1, C2, P1 & number of interpolations t
    Returns array of interpolated points of class Point
    Adapted from http://www.planetclegg.com/projects/WarpingTextToSplines.htm
    '''
    # calculate coefficients for two knot points P0 & P1 ;     C1 & C2 are the controlpoints.
    # x coefficients
    A = P1.x-(3 * C2.x) + (3 * C1.x)-P0.x
    B = (3 * C2.x)-(6 * C1.x) + (3 * P0.x)
    C = (3 * C1.x)-(3 * P0.x)
    D = P0.x
    # y coefficients
    E = P1.y-(3 * C2.y) + (3 * C1.y)-P0.y
    F = (3 * C2.y)-(6 * C1.y) + (3 * P0.y)
    G = (3 * C1.y)-(3 * P0.y)
    H = P0.y
    # calculate interpolated points
    interpolatedPoints = []
    maxPoint = float(t)
    i = 0
    while ( i <= t):
            j = i/maxPoint # j can't be an integer, i/t is an integer..always 0.
            x = A * (j ** 3) + B * (j ** 2) + C * j + D
            y = E * (j ** 3) + F * (j ** 2) + G * j + H
            interpolatedPoints.append(Point('', x, y))
            i += 1
    return interpolatedPoints

#---rotations
def slashAndSpread(pivot, angle, *args):
        """
        Accepts pivot point, angle of rotation, and the points to be rotated.
        Accepts positive & negative angles.
        """
        if (angle == 0.0):
            print('Angle = 0 -- Slash and Spread not possible')
        else:
            list = []
            for arg in args:
                list.append(arg)
            i = 0
            for pnt in list:
                length = distance(pivot, pnt)
                rotated_pnt = polar(pivot, length, angleOfLine(pivot, pnt) + angle) # if angle > 0 spread clockwise. if angle < 0 spread counterclockwise
                updatePoint(pnt, rotated_pnt)
        return

#---darts
def foldDart(dart, inside_pnt, seam_allowance):
    '''
    Accepts dart, and the nearest point in the direction dart will be folded
    Returns dart.m, dart.oc, dart.ic, dart.angle
    dart.m = middle dart leg at seamline (to be included in seamline path)
    dart.oc = inside dart leg at cuttingline (to be included in dartline path)
    dart.oc = outside dart leg at cuttingline (to be included in dartline path)
    '''
    mid_pnt = midPoint(dart.i, dart.o)
    dart_length = distance(dart, dart.i)
    i_angle = angleOfLine(dart, dart.i)
    c_angle = angleOfLine(dart, inside_pnt)
    dart_angle = abs(angleOfVector(dart.i, dart, dart.o))
    dart_half_angle = dart_angle/2.0

    #determine which direction the dart will be folded
    #if ((dart.i.x > dart.x) and (dart.i.y > dart.y)) or ((dart.i.x < dart.x) and (dart.i.y > dart.y)):
        #x & y vectors not the same sign
        #dart_half_angle = -dart_half_angle
    if i_angle > c_angle:
        dart_half_angle = -dart_half_angle
    elif dart_angle < c_angle:
        #dart straddles 0 angle
        dart_half_angle = -dart_half_angle

    fold_angle = i_angle + dart_half_angle
    fold_pnt = intersectLineRay(dart.i, inside_pnt, dart, fold_angle)
    dart.m = onLineAtLength(dart, mid_pnt, distance(dart, fold_pnt)) #dart midpoint at seamline
    dart.oc = polar(dart, distance(dart, dart.o) + seam_allowance, angleOfLine(dart, dart.o)) #dart outside leg at cuttingline
    dart.ic = extendLine(dart, dart.i, seam_allowance) #dart inside leg at cuttingline
    #create or update dart.angles
    dart.angle = angleOfVector(dart.i, dart, dart.o)
    return

#---base, pattern & patternpiece groups
def base(parent, id):
    '''Create a base group to contain all patterns, parent should be the document'''
    newBase = addGroup(parent, id)
    newBase.set(inkex.addNS('label', 'inkscape'), id)
    newBase.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
    return newBase

def pattern(parent, id):
    '''Create a pattern group to hold a single pattern, parent should be the base group'''
    newPattern = addGroup(parent, id)
    newPattern.set(inkex.addNS('label', 'inkscape'), id)
    newPattern.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
    return newPattern

def patternPiece(parent, id, name, fabric = 2, interfacing = 0, lining = 0):
    '''Create a pattern piece group to hold a single pattern piece, parent should be a pattern group'''
    newPatternPiece = addGroup(parent, id)
    newPatternPiece.set(inkex.addNS('label', 'inkscape'), name)
    newPatternPiece.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
    return newPatternPiece

#---svg

def addCircle(parent, id, x, y, radius = 5, fill = 'red', stroke = 'red', stroke_width = '1', reference = 'false'):
    '''create & write a circle to canvas & set it's attributes'''
    circ = etree.SubElement(parent, inkex.addNS('circle', 'svg'))
    circ.set('id', id)
    circ.set('cx', str(x))
    circ.set('cy', str(y))
    circ.set('r', str(radius))
    circ.set('fill', fill)
    circ.set('stroke', stroke)
    circ.set('stroke-width', stroke_width)
    if reference == 'true':
        circ.attrib['reference'] = 'true'
    return

def addSquare(parent, id, w, h, x, y, reference='false'):
    # create & write a square element, set its attributes
    square = etree.SubElement(parent, inkex.addNS('rect', 'svg'))
    square.set('id', id)
    square.set('width', str(w))
    square.set('height', str(h))
    square.set('x', str(x))
    square.set('y', str(y))
    square.set('stroke', 'none')
    square.set('fill', '#000000')
    square.set('stroke-width', '1')
    if (reference == 'true'):
        square.attrib['reference'] = 'true'
    return

def addText(parent, id, x, y, text, fontsize = '12', textalign = 'left', textanchor = 'start', reference = 'false'):
    '''Create a text element, set its attributes, then write to canvas.
    The text element is different than other elements -- >  Set attributes first then write to canvas using append method.
    There is no etree.SubElement() method for creating a text element & placing it into the document in one step.
    Use inkex's etree.Element() method to create an unattached text svg object,
    then use a document object's append() method to place it on the document canvas'''
    #create a text element with inkex's Element()
    txt = etree.Element(inkex.addNS('text', 'svg'))
    #set attributes of the text element
    txt.set('id', id)
    txt.set('x', str(x))
    txt.set('y', str(y))
    txt.text = text
    style = {'text-align':textalign, 'text-anchor':textanchor, 'font-size':fontsize}
    txt.set('style', str(inkex.Style(style)))
    if reference == 'true':
        txt.attrib['reference'] = 'true'
        #txt.setAttribute('reference', 'true') #alternative syntax
    #add to canvas in the parent group
    parent.append(txt)
    return

def addLayer(parent, id):
    '''Create & write an inkscape group-layer to canvas'''
    new_layer = etree.SubElement(parent, 'g')
    new_layer.set('id', id)
    new_layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
    new_layer.set(inkex.addNS('label', 'inkscape'), '%s layer' % (id))
    return new_layer

def addGroup(parent, id):
    '''Create & write an svg group to canvas'''
    new_layer = etree.SubElement(parent, 'g')
    new_layer.set('id', id)
    return new_layer

def addPath(parent, id, path_str, path_type):
    '''Accepts parent, id, path string, path type. Creates attribute dictionary. Creates & writes path.'''
    reference = 'false'
    if path_type == 'seamline':
        path_style = {'stroke':'green', 'stroke-width':'4', 'fill':'none', 'opacity':'1', 'stroke-dasharray':'15, 5', 'stroke-dashoffset':'0'}
    elif path_type == 'cuttingline':
        path_style = {'stroke':'green', 'stroke-width':'4', 'fill':'none', 'opacity':'1'}
    elif path_type == 'gridline':
        path_style = {'stroke':'gray', 'stroke-width':'4', 'fill':'none', 'opacity':'1', 'stroke-dasharray':'6, 6', 'stroke-dashoffset':'0'}
        reference = 'true'
    elif path_type == 'dartline':
        path_style = {'stroke':'gray', 'stroke-width':'4', 'fill':'none', 'opacity':'1'}
    elif path_type == 'grainline':
        path_style = {'stroke':'DimGray', 'stroke-width':'3', 'fill':'none', 'opacity':'1', \
                    'marker-start':'url(#ArrowStart)', 'marker-end':'url(#ArrowEnd)'}
    elif path_type == 'slashline':
        path_style = {'stroke':'green', 'stroke-width':'4', 'fill':'none', 'opacity':'1'}
    svg_path = etree.SubElement(parent, inkex.addNS('path', 'svg'))
    svg_path.set('id', id)
    svg_path.set('d', path_str)
    svg_path.set('style', str(inkex.Style(path_style)))
    if reference == 'true':
        svg_path.attrib['reference'] = 'true'
    return svg_path

def formatPath( * args):
    """
    Accepts a series of pseudo svg path arguments  'M', 'L', 'C' , and point objects.
    Returns path_string which is a string formatted for use as the 'd' path attribute in an svg object.
    """
    tokens = [] # initialize an empty array
    # put all the parameters in  * args into the array
    for arg in args:
        tokens.append(arg)
    com = ', '
    path_string = ''
    i = 0
    while (i  <  len(tokens)):
        cmd = tokens[i]
        if (cmd == 'M') or (cmd == 'L'):
            path_string += " %s %g %g" % (cmd, tokens[i + 1].x, tokens[i + 1].y)
            i = i + 2
        elif (cmd == 'C'):
            path_string += " %s %g %g %g %g %g %g" % (cmd, tokens[i + 1].x, \
                            tokens[i + 1].y, tokens[i + 2].x, tokens[i + 2].y, tokens[i + 3].x, tokens[i + 3].y)
            i = i + 4
    return path_string

def addDefs(doc):
    '''Add defs group with markers to the document'''
    defs = etree.SubElement(doc, inkex.addNS('defs', 'svg'))
    #add start arrow
    marker = etree.SubElement(defs, 'marker', {'id':'ArrowStart', 'orient':'auto', 'refX':'0.0', 'refY':'0.0', 'style':'overflow:visible'})
    etree.SubElement(marker, 'path', {'d':'M 0, 0 L 0, 5 L -20, 0 L 0, -5 z', 'style':'fill:DimGray; stroke:DimGray; stroke-width:0.5'})
    #add end arrow
    marker = etree.SubElement(defs, 'marker', {'id':'ArrowEnd', 'orient':'auto', 'refX':'0.0', 'refY':'0.0', 'style':'overflow:visible'})
    etree.SubElement(marker, 'path', {'d':'M 0, 0 L 0, 5 L 20, 0 L 0, -5 z', 'style':'fill:DimGray; stroke:DimGray; stroke-width:0.5'})
#!/usr/bin/env python3

# We will use the inkex module with the predefined Effect base class.
import inkex
# The simplestyle module provides functions for style parsing.

import simplestyle
import math
from lxml import etree


objStyle = str(inkex.Style({'stroke': '#000000',
    'stroke-width': 0.1,
    'fill': 'none'
    }))

class th_inkscape_path:
    def __init__(self, Offset, group, Label=None, Style = None):
        self.offsetX = Offset[0]
        self.offsetY = Offset[1]
        self.Path = ''
        self.group = group
        self.Label = Label
        if Style:
            self.Style = Style
        else:
            self.Style = objStyle
        self.xmin = -self.offsetX
        self.xmax = -self.offsetX
        self.ymin = -self.offsetY
        self.ymax = -self.offsetY
        self.x = 0
        self.y = 0
        self.x_noff = 0
        self.y_noff = 0
    
    def MoveTo(self, x, y):
    #Return string 'M X Y' where X and Y are updated values from parameters
        self.Path += ' M ' + str(round(x-self.offsetX, 3)) + ',' + str(round(y-self.offsetY, 3))
        self.x = x - self.offsetX
        self.y = y - self.offsetY
        self.x_noff = x
        self.y_noff = y
        self.xmin= min(self.x, self.xmin)
        self.xmax= max(self.x, self.xmax)
        self.ymin= min(self.y, self.ymin)
        self.ymax= max(self.y, self.ymax)
        
    def LineTo(self, x, y):
    #Return string 'L X Y' where X and Y are updated values from parameters
        self.Path += ' L ' + str(round(x-self.offsetX, 3)) + ',' + str(round(y-self.offsetY, 3))
        self.x = x - self.offsetX
        self.y = y - self.offsetY
        self.x_noff = x
        self.y_noff = y
        self.xmin= min(self.x, self.xmin)
        self.xmax= max(self.x, self.xmax)
        self.ymin= min(self.y, self.ymin)
        self.ymax= max(self.y, self.ymax)


    def LineToRel(self, x, y):
    #Return string 'L X Y' where X and Y are updated values from parameters
        self.Path += ' l ' + str(round(x, 3)) + ',' + str(round(y, 3))
        self.x += x
        self.y += y
        self.x_noff += x
        self.y_noff += y
        self.xmin= min(self.x, self.xmin)
        self.xmax= max(self.x, self.xmax)
        self.ymin= min(self.y, self.ymin)
        self.ymax= max(self.y, self.ymax)

    def LineToHRel(self, x):
    #Return string 'h X' where X are updated values from parameters
        self.Path += ' h ' + str(round(x, 3)) 
        self.x += x
        self.x_noff += x
        self.xmin= min(self.x, self.xmin)
        self.xmax= max(self.x, self.xmax)


    def LineToVRel(self, y):
    #Return string 'v Y' where X and Y are updated values from parameters
        self.Path += ' v ' + str(round(y, 3)) 
        self.y += y
        self.y_noff += y
        self.ymin= min(self.y, self.ymin)
        self.ymax= max(self.y, self.ymax)

    def Line(self, x1, y1, x2, y2):
        self.x = x1 - self.offsetX
        self.y = y1 - self.offsetY        
        self.xmin= min(self.x, self.xmin)
        self.xmax= max(self.x, self.xmax)
        self.ymin= min(self.y, self.ymin)
        self.ymax= max(self.y, self.ymax)
    #Return string M X1 Y1 L X2 Y2
        self.Path += ' M ' + str(round(x1-self.offsetX, 3)) + ',' + str(round(y1-self.offsetY, 3)) + ' L ' + str(round(x2-self.offsetX, 3)) + ',' + str(round(y2-self.offsetY, 3))
        self.x = x2 - self.offsetX
        self.y = y2 - self.offsetY        
        self.x_noff = x2
        self.y_noff = y2
        self.xmin= min(self.x, self.xmin)
        self.xmax= max(self.x, self.xmax)
        self.ymin= min(self.y, self.ymin)
        self.ymax= max(self.y, self.ymax)

    def LineRel(self, x1, y1, x2, y2):
        self.x += x1
        self.y += y1
        self.x_noff += x1
        self.y_noff += y1
        self.xmin= min(self.x, self.xmin)
        self.xmax= max(self.x, self.xmax)
        self.ymin= min(self.y, self.ymin)
        self.ymax= max(self.y, self.ymax)

    #Return string m X1 Y1 l X2 Y2
        self.Path += ' m ' + str(round(x1, 3)) + ',' + str(round(y1, 3)) + ' l ' + str(round(x2, 3)) + ',' + str(round(y2, 3))
        self.x += x2
        self.y += y2
        self.x_noff += x2
        self.y_noff += y2
        self.xmin= min(self.x, self.xmin)
        self.xmax= max(self.x, self.xmax)
        self.ymin= min(self.y, self.ymin)
        self.ymax= max(self.y, self.ymax)

    def Bezier(self, xc1, yc1, xc2, yc2, x, y):
    #Return string C XC1 YC1 XC2 YC2 X Y
        self.Path += ' C ' + str(round(xc1-self.offsetX, 3)) + ',' + str(round(yc1-self.offsetY, 3)) + ' ' + str(round(xc2-self.offsetX, 3)) + ',' + str(round(yc2-self.offsetY, 3))+ ' ' + str(round(x-self.offsetX, 3)) + ',' + str(round(y-self.offsetY, 3))
        self.x = x - self.offsetX
        self.y = y - self.offsetY
        self.x_noff = x
        self.y_noff = y
        self.xmin= min(self.x, self.xmin)
        self.xmax= max(self.x, self.xmax)
        self.ymin= min(self.y, self.ymin)
        self.ymax= max(self.y, self.ymax)

    def BezierRel(self, xc1, yc1, xc2, yc2, x, y):
    #Return string c XC1 YC1 XC2 YC2 X Y
        self.Path += ' c ' + str(round(xc1, 3)) + ',' + str(round(yc1, 3)) + ' ' + str(round(xc2, 3)) + ',' + str(round(yc2, 3))+ ' ' + str(round(x, 3)) + ',' + str(round(y, 3))
        self.x += x
        self.y += y
        self.x_noff += x
        self.y_noff += y
        self.xmin= min(self.x, self.xmin)
        self.xmax= max(self.x, self.xmax)
        self.ymin= min(self.y, self.ymin)
        self.ymax= max(self.y, self.ymax)


    def drawQuarterCircle(self, xc, yc, radius, quarter):
        '''
        Draw a quarter of circle with a single bezier path
        xc, yc give the center of the circle, radius its radius
        quarter = 0 : upper left, 1: upper right, 2: lower right, 3: lower left
        Starting point is the last point of the path
        '''
        if quarter == 0:
            self.Bezier(xc-radius, yc - radius*0.551916, xc - radius*0.551916, yc-radius, xc, yc-radius)  # upper left quarter
        elif quarter == 1:
            self.Bezier(xc+radius*0.551916, yc - radius, xc + radius, yc-radius*0.551916, xc+radius, yc)  # upper right quarter
        elif quarter == 2:
            self.Bezier(xc+radius, yc + radius*0.551916, xc + radius*0.551916, yc+radius, xc, yc+radius)  # lower right quarter
        elif quarter == 3:
            self.Bezier(xc+radius*-0.551916, yc + radius, xc - radius, yc+radius*0.551916, xc-radius, yc)  # lower left quarter


    def drawCircle(self, xc, yc, radius):
    #Draw a circle, with 4 Bezier paths
        self.MoveTo(xc+radius, yc)    #R, 0
        self.Bezier(xc+radius, yc + radius*0.551916, xc + radius*0.551916, yc+radius, xc, yc+radius)  #1er quarter, lower right
        self.Bezier(xc+radius*-0.551916, yc + radius, xc - radius, yc+radius*0.551916, xc-radius, yc)  #2nd quarter, lower left
        self.Bezier(xc-radius, yc - radius*0.551916, xc - radius*0.551916, yc-radius, xc, yc-radius)  #3rd quarter, upper left
        self.Bezier(xc+radius*0.551916, yc - radius, xc + radius, yc-radius*0.551916, xc+radius, yc)  #4th quarter, upper right

    def Close(self):
        self.Path += ' z'

    def GenPath(self):
        if self.Label:
            line_attribs = {'style': self.Style, 'id' : self.Label, 'd': self.Path}
        else:            
            line_attribs = {'style': self.Style, 'd': self.Path}
        etree.SubElement(self.group, inkex.addNS('path', 'svg'), line_attribs)
    
    def GetBoundingBox(self):
        '''
        return a tuple giving MinPos, MaxPos and Size (6 elements)
        '''
        return(self.xmin, self.ymin, self.xmax, self.ymax, self.xmax - self.xmin, self.ymax - self.ymin)

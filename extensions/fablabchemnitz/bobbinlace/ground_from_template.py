#!/usr/bin/env python3

# Copyright (c) 2017, Veronika Irvine
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,#    this list of conditions and the following disclaimer in the documentation
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
from math import sin, cos, radians, ceil
from lxml import etree
import inkex

__author__ = 'Veronika Irvine'
__credits__ = ['Ben Connors', 'Veronika Irvine', 'Mark Shafer']
__license__ = 'Simplified BSD'

class GroundFromTemplate(inkex.EffectExtension):
    
    def loadFile(self):
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
        rowCount = 0
        colCount = 0
        with open(self.options.file,'r') as f:
            first = True
            for line in f:
                if first:
                    # first line of file gives row count and column count
                    first = False
                    line = line.strip()
                    temp = line.split('\t')
                    type = temp[0]
                    rowCount = int(temp[1])
                    colCount = int(temp[-1])
                    
                else:
                    line = line.strip()
                    line = line.lstrip('[')
                    line = line.rstrip(']')
                    rowData = line.split(']\t[')
                    data.append([])
                    for cell in rowData:
                        cell = cell.strip()
                        data[-1].append([float(num) for num in cell.split(',')])
                        
        return {'type':type, 'rowCount':rowCount, 'colCount':colCount, 'data':data}

    def line(self, x1, y1, x2, y2):
        """
        Draw a line from point at (x1, y1) to point at (x2, y2).
        Style of line is hard coded and specified by 's'.
        """
        # define the motions
        path = 'M %s,%s L %s,%s' %(x1,y1,x2,y2)
        
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
        
        # create attributes from style and path
        attribs = {'style':str(inkex.Style(s)), 'd':path}
        
        # insert path object into current layer
        etree.SubElement(self.svg.get_current_layer(), inkex.addNS('path', 'svg'), attribs)

    def draw(self, data, rowCount, colCount):
        a = self.options.distance
        theta = self.options.angle
        deltaX = a*sin(theta) 
        deltaY = a*cos(theta)
        maxRows = ceil(self.options.height / deltaY)
        maxCols = ceil(self.options.width  / deltaX)
        
        x = 0.0
        y = 0.0
        repeatY = 0
        repeatX = 0

        while repeatY * rowCount < maxRows:
            x = 0.0
            repeatX = 0
            
            while repeatX * colCount < maxCols:
                
                for row in data:
                    for coords in row:
                        x1 = x + coords[0]*deltaX
                        y1 = y + coords[1]*deltaY
                        x2 = x + coords[2]*deltaX
                        y2 = y + coords[3]*deltaY
                        x3 = x + coords[4]*deltaX
                        y3 = y + coords[5]*deltaY
                
                        self.line(x1,y1,x2,y2)
                        self.line(x1,y1,x3,y3)
                    
                repeatX += 1
                x += deltaX * colCount

            repeatY += 1
            y += deltaY * rowCount
        
    def add_arguments(self, pars):
        pars.add_argument('-f', '--file', help='File containing lace ground description')
        pars.add_argument('--angle', type=float)
        pars.add_argument('--distance', type=float)
        pars.add_argument('--pinunits')
        pars.add_argument('--width',  type=float)
        pars.add_argument('--patchunits')
        pars.add_argument('--height', type=float)
        pars.add_argument('--linewidth', type=float)
        pars.add_argument('--lineunits')
        pars.add_argument('--linecolor', type=inkex.Color)

    def effect(self):
        result = self.loadFile()
        
        # Convert input to universal units
        self.options.width = self.svg.unittouu(str(self.options.width)+self.options.patchunits)
        self.options.height = self.svg.unittouu(str(self.options.height)+self.options.patchunits)
        self.options.linewidth = self.svg.unittouu(str(self.options.linewidth)+self.options.lineunits)
        self.options.distance = self.svg.unittouu(str(self.options.distance)+self.options.pinunits)
        
        # Users expect distance to be the vertical distance between footside pins 
        # (vertical distance between every other row) but in the script we use it 
        # as the diagonal distance between grid points
        # therefore convert distance based on the angle chosen
        self.options.angle = radians(self.options.angle)
        self.options.distance = self.options.distance/(2.0*cos(self.options.angle))
        
        # Draw a ground based on file description and user inputs
        self.options.linecolor = self.options.linecolor.to_rgb()
        # For now, assume style is Checker but could change in future
        self.draw(result['data'],result['rowCount'],result['colCount'])

if __name__ == '__main__':
    GroundFromTemplate().run()
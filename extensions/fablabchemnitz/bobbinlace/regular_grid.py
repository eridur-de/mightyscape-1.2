#!/usr/bin/env python3

# Copyright (c) 2017, Veronika Irvine
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

from math import sin, cos, radians, ceil
import inkex
from lxml import etree

__author__ = 'Veronika Irvine'
__credits__ = ['Ben Connors', 'Veronika Irvine', 'Mark Shafer']
__license__ = 'Simplified BSD'

class RegularGrid(inkex.EffectExtension):        
    def circle(self, x, y, r, fill):
        # define the stroke style
        s = {'fill': fill}
     
        # create attributes from style and define path
        attribs = {'style':str(inkex.Style(s)), 
                    'cx':str(x),
                    'cy':str(y),
                    'r':str(r)}
        
        # insert path object into current layer
        etree.SubElement(self.svg.get_current_layer(), inkex.addNS('circle', 'svg'), attribs)

    def drawDot(self, x, y):
        self.circle(x, y, self.options.dotwidth, self.options.dotcolor)

    def draw(self):
        
        a = self.options.distance
        theta = self.options.angle
        
        hgrid = a*sin(theta);
        vgrid = a*cos(theta)
        rows = int(ceil(self.options.height / vgrid))
        cols = int(ceil(self.options.width  / hgrid))
        y = 0.0
        
        for r in range(rows):
            x = 0.0
            if (r % 2 == 1):
                x += hgrid
            
            for c in range(ceil(cols/2)):
                self.drawDot(x, y)
                x += 2.0*hgrid;
                
            y += vgrid;

    def add_arguments(self, pars):
        pars.add_argument('--angle', type=float)
        pars.add_argument('--distance', type=float)
        pars.add_argument('--pinunits')
        pars.add_argument('--width', type=float)
        pars.add_argument('--patchunits')
        pars.add_argument('--height', type=float)
        pars.add_argument('--dotwidth', type=float)
        pars.add_argument('--dotunits')
        pars.add_argument('--dotcolor', type=inkex.Color)

    def effect(self):
        """
        Effect behaviour.
        Overrides base class' method and draws something.
        """
        # Convert user input to universal units
        self.options.width = self.svg.unittouu(str(self.options.width)+self.options.patchunits)
        self.options.height = self.svg.unittouu(str(self.options.height)+self.options.patchunits)
        self.options.distance = self.svg.unittouu(str(self.options.distance)+self.options.pinunits)
        # Convert from diameter to radius
        self.options.dotwidth = self.svg.unittouu(str(self.options.dotwidth)+self.options.dotunits)/2
        # Users expect distance to be the vertical distance between footside pins 
        # (vertical distance between every other row) but in the script we use it 
        # as as diagonal distance between grid points
        # therefore convert distance based on the angle chosen
        self.options.angle = radians(self.options.angle)
        self.options.distance = self.options.distance/(2.0*cos(self.options.angle))
        
        # Draw a grid of dots based on user inputs
        self.options.dotcolor = self.options.dotcolor.to_rgb()
        self.draw()

if __name__ == '__main__':
    RegularGrid().run()
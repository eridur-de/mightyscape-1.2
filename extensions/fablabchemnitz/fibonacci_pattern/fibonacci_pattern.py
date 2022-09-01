#!/usr/bin/env python3
'''
Copyright (C) 2015-2015 Carlos Mostek carlosmostek@gmail.com

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
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''
import math
import inkex
from lxml import etree

# This is basically the draw method from the help guides for inkscape
def draw_SVG_ellipse(rx, ry, cx, cy, parent, start_end=(0,2*math.pi),transform='' ):

    style = {   'stroke'        : '#000000',
                'stroke-width'  : '1',
                'fill'          : 'none'            }
    ell_attribs = {'style':str(inkex.Style(style)),
        inkex.addNS('cx','sodipodi')        :str(cx),
        inkex.addNS('cy','sodipodi')        :str(cy),
        inkex.addNS('rx','sodipodi')        :str(rx),
        inkex.addNS('ry','sodipodi')        :str(ry),
        inkex.addNS('start','sodipodi')     :str(start_end[0]),
        inkex.addNS('end','sodipodi')       :str(start_end[1]),
        inkex.addNS('open','sodipodi')      :'true',    #all ellipse sectors we will draw are open
        inkex.addNS('type','sodipodi')      :'arc',
        'transform'                         :transform
            }
    ell = etree.SubElement(parent, inkex.addNS('path','svg'), ell_attribs )

# This is the workhorse, it draws the circle based on which node number
def drawKthCircle(k,firstRadius,lastRadius,numNodes,spreadFactor,parent):
    # Use golden circle phi
    phi = (math.sqrt(5) - 1)/2
    
    # Calculate the node radius
    growth = lastRadius - firstRadius
    nodeRadius = firstRadius + growth*float(k - 1)/float(numNodes)
    
    # Calculate X and Y from theta = 2 pi phi k and radius = sqrt(k)
    r = spreadFactor * math.sqrt(k)
    theta = 2*math.pi*phi*k

    # use simple trig to get cx and cy
    x = r * math.cos(theta)
    y = r * math.sin(theta)

    # Add the px to the size
    nodeRadiusTxt = "%spx"%nodeRadius
    
    # Draw the node
    draw_SVG_ellipse(nodeRadiusTxt,nodeRadiusTxt,x,y,parent)


class FibonacciPattern(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("-f", "--FirstRadius", type=int, default="5", help="The radius of the first layer of circles in pixels.")
        pars.add_argument("-l", "--LastRadius", type=int, default="10", help="The radius of the last layer of circles in pixels.")
        pars.add_argument("-n", "--NumberOfNodes", type=int, default="5", help="The number of layers in the fibonacci spiral")
        pars.add_argument("-s", "--SpreadFactor",type=int, default="10", help="This will create a larger spread between the nodes from the center.")

    def effect(self):
        # Foreach Node
        for k in range(1,self.options.NumberOfNodes):
            # Draw the circle
            drawKthCircle(k,
                self.options.FirstRadius,
                self.options.LastRadius,
                self.options.NumberOfNodes,
                self.options.SpreadFactor,
                self.svg.get_current_layer())
            
if __name__ == '__main__':
    FibonacciPattern().run()
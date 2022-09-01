#!/usr/bin/env python 3
'''
Copyright (C) 2013 Carl Sorensen carl.d.sorensen@gmail.com
Derived from grid_cartesion.py copyright (C) 2007 John Beard john.j.beard@gmail.com


##This extension allows you to draw a Triangular grid in Inkscape.
##There is a wide range of options including subdivision, subsubdivions
##and angles of the triangular axes.
##Custom line widths are also possible.
##All elements are grouped with similar elements (eg all x-subdivs)

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

import inkex
from lxml import etree
from math import *

def draw_SVG_line(x1, y1, x2, y2, width, stroke, name, parent):
    style = { 'stroke': stroke, 'stroke-width':str(width), 'fill': 'none' }
    line_attribs = {'style':str(inkex.Style(style)),
                    inkex.addNS('label','inkscape'):name,
                    'd':'M '+str(x1)+','+ str(y1) +' L '+ str(x2) + ',' + str(y2)}
    etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )
    
def draw_SVG_rect(x,y,w,h, width, stroke, fill, name, parent):
    style = { 'stroke': stroke, 'stroke-width':str(width), 'fill':fill}
    rect_attribs = {'style':str(inkex.Style(style)),
                    inkex.addNS('label','inkscape'):name,
                    'x':str(x), 'y':str(y), 'width':str(w), 'height':str(h)}
    etree.SubElement(parent, inkex.addNS('rect','svg'), rect_attribs )

def colorString(pickerColor):
    longcolor = int(pickerColor) & 0xFFFFFF00
    return '#' + format(longcolor >> 8, '06X')


class TriangularGrid(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--tabs")
        pars.add_argument("--size_unit", default="mm", help="Unit for grid size")
        pars.add_argument("--y_divs", type=int, default=3, help="Major vertical divisions")
        pars.add_argument("--x_divs", type=int, default=3, help="Major horizontal divisions")
        pars.add_argument("--grid_angle", type=float, default=30.0, help="Angle between X axis and triangular grid lines")
        pars.add_argument("--dm", type=float, default=100.0, help="Major grid division spacing")
        pars.add_argument("--subdivs", type=int, default=5, help="Subdivisions per major grid division")
        pars.add_argument("--subsubdivs", type=int, default=2, help="Subsubdivisions per minor grid subdivision")
        pars.add_argument("--border_th", type=float, default=3.0, help="Border Line thickness")
        pars.add_argument("--border_color", type=int, help="Border line color")
        pars.add_argument("--major_th", type=float, default=2.0, help="Major grid division line thickness")
        pars.add_argument("--major_color", type=int, help="Major grid division line color")
        pars.add_argument("--subdiv_th", type=float, default=1.0, help="Minor grid subdivision line thickness")
        pars.add_argument("--subdiv_color", type=int, help="Minor grid subdivision line color")
        pars.add_argument("--subsubdiv_th", type=float, default=1.0, help="Subminor grid division line thickness")
        pars.add_argument("--subsubdiv_color", type=int, help="Subminor grid division line color")

    def EdgePoints(self,x0, y0, theta):
        #  find the intersection points of the line with the extended
        #  grid bounding box.
        #  Note that y is positive DOWN, not up
        theta_r = radians(theta)
        r_bot = (self.ymax-y0)/sin(theta_r)
        r_top = -y0/sin(theta_r)
        r_left = -x0/cos(theta_r)
        r_right = (self.xmax-x0)/cos(theta_r)
        return [[x0+r_left*cos(theta_r),y0+r_left*sin(theta_r)],
               [x0+r_right*cos(theta_r), y0+r_right*sin(theta_r)],
               [x0+r_bot*cos(theta_r), y0+r_bot*sin(theta_r)],
               [x0+r_top*cos(theta_r), y0+r_top*sin(theta_r)]]

    def trimmed_coords(self, x1, y1, theta):
    #find the start and end coordinates for a grid line
    #starting at (x1, y1) with an angle of theta
        border_points = self.EdgePoints(x1, y1, theta)
        left = 0
        right = 1
        top = 3
        bottom = 2
        x=0
        y=1
        if theta > 0:
            if border_points[left][y] < 0:
                start_x = border_points[top][x]
                start_y = border_points[top][y]
            else:
                start_x = border_points[left][x]
                start_y = border_points[left][y]
            if border_points[right][y] > self.ymax:
                end_x = border_points[bottom][x]
                end_y = border_points[bottom][y]
            else:
                end_x = border_points[right][x]
                end_y = border_points[right][y]
        else:
            if border_points[left][y] > self.ymax:
                start_x = border_points[bottom][x]
                start_y = border_points[bottom][y]
            else:
                start_x = border_points[left][x]
                start_y = border_points[left][y]
            if border_points[right][y] < 0:
                end_x = border_points[top][x]
                end_y = border_points[top][y]
            else:
                end_x = border_points[right][x]
                end_y = border_points[right][y]
        return [[start_x,start_y],[end_x, end_y]]

    def drawAngledGridLine (self, x1, y1, theta, thickness, color, 
                            label, groupName):
        end_points = self.trimmed_coords(x1, y1, theta)
        x_start = end_points[0][0]
        y_start = end_points[0][1]
        x_end = end_points[1][0]
        y_end = end_points[1][1]

        if (x_end >= 0 and x_end <= self.xmax and
            y_end >= 0 and y_end <= self.ymax and
            (y_start != y_end and x_start != x_end)):
            draw_SVG_line(x_start, y_start,
                          x_end, y_end,
                          thickness, colorString(color), label, groupName)

    def effect(self):
        
        #find the pixel dimensions of the overall grid
        dm = self.svg.unittouu(str(self.options.dm) + self.options.size_unit)
        self.ymax = dm * self.options.y_divs #grid spacing defined along vertical
        dx = dm / (2.0 * tan(radians(self.options.grid_angle)))
        self.xmax = dx * self.options.x_divs
        dy = dm

        # Embed grid in group
        #Put in in the centre of the current view
        t = 'translate(' + str( self.svg.namedview.center[0]- self.xmax/2.0) + ',' + \
                           str( self.svg.namedview.center[1]- self.ymax/2.0) +  ')'
        g_attribs = {inkex.addNS('label','inkscape'):'Grid_Triangular:Size' + \
                     str( self.options.x_divs)+'x'+str(self.options.y_divs) +
             ':Angle'+str( self.options.grid_angle ),
                     'transform':t }
        grid = etree.SubElement(self.svg.get_current_layer(), 'g', g_attribs)
        
        #Group for major x gridlines
        g_attribs = {inkex.addNS('label','inkscape'):'MajorXGridlines'}
        majglx = etree.SubElement(grid, 'g', g_attribs)

        #Group for major positive theta gridlines
        g_attribs = {inkex.addNS('label','inkscape'):'MajorPosGridlines'}
        majglp = etree.SubElement(grid, 'g', g_attribs)
        
        #Group for major negative theta gridlines
        g_attribs = {inkex.addNS('label','inkscape'):'MajorNegGridLines'}
        majgln = etree.SubElement(grid, 'g', g_attribs)
        
        #Groups for minor gridlines
        if self.options.subdivs > 1:#if there are any minor gridlines
            g_attribs = {inkex.addNS('label','inkscape'):'MinorXGridlines'}
            minglx = etree.SubElement(grid, 'g', g_attribs)
            g_attribs = {inkex.addNS('label','inkscape'):'MinorPosGridlines'}
            minglp = etree.SubElement(grid, 'g', g_attribs)
            g_attribs = {inkex.addNS('label','inkscape'):'MinorNegGridlines'}
            mingln = etree.SubElement(grid, 'g', g_attribs)
        
        #Groups for subminor gridlines
        if self.options.subsubdivs > 1:#if there are any minor minor gridlines
            g_attribs = {inkex.addNS('label','inkscape'):'SubMinorXGridlines'}
            mminglx = etree.SubElement(grid, 'g', g_attribs)
            g_attribs = {inkex.addNS('label','inkscape'):'SubMinorPosGridlines'}
            mminglp = etree.SubElement(grid, 'g', g_attribs)
            g_attribs = {inkex.addNS('label','inkscape'):'SubMinorNegGridlines'}
            mmingln = etree.SubElement(grid, 'g', g_attribs)
        
        draw_SVG_rect(0, 0, self.xmax, self.ymax, 
                      self.options.border_th,
                      colorString(self.options.border_color), 'none',
                      'Border', grid) #border rectangle
        
        sd  = self.options.subdivs #sub divs per div
        ssd = self.options.subsubdivs #subsubdivs per subdiv
      
 
    #DO THE HORIZONTAL DIVISONS======================================
        
        for i in range(0, self.options.x_divs): #Major x divisons
            if i>0: #dont draw first line (we made a proper border)
        # Draw the vertical line
                draw_SVG_line(dx*i, 0,
                              dx*i,self.ymax,
                              self.options.major_th,
                  colorString(self.options.major_color),
                              'MajorDiv'+str(i), majglx)

            for j in range (0, sd):
                if j>0: #not for the first loop (this loop is for the subsubdivs before the first subdiv)
                   draw_SVG_line(dx*(i+j/float(sd)), 0,
                                 dx*(i+j/float(sd)), self.ymax,
                                 self.options.subdiv_th,
                     colorString(self.options.subdiv_color),
                                 'MinorDiv'+str(i)+':'+str(j), minglx)
                    
                for k in range (1, ssd): #subsub divs
                   draw_SVG_line(dx*(i+(j*ssd+k)/((float(sd)*ssd))) , 0,
                                 dx*(i+(j*ssd+k)/((float(sd)*ssd))) , self.ymax,
                                 self.options.subsubdiv_th,
                     colorString(self.options.subsubdiv_color),
                                 'SubminorDiv'+str(i)+':'+str(j)+':'+str(k), mminglx)
         
        #DO THE VERTICAL DIVISONS========================================
        for i in range(-self.options.x_divs-self.options.y_divs, 
                         self.options.x_divs+self.options.y_divs): #Major y divisons
            self.drawAngledGridLine(0, dy*i, self.options.grid_angle,
                               self.options.major_th,
                               self.options.major_color,
                               'MajorYDivP'+str(i),
                               majglp)
            self.drawAngledGridLine(0, dy*i, -self.options.grid_angle,
                               self.options.major_th,
                               self.options.major_color,
                               'MajorYDivN'+str(i),
                               majgln)
             
            for j in range (0, sd):  #subdivs
                if j>0:#not for the first loop (this loop is for the subsubdivs before the first subdiv)
                    self.drawAngledGridLine(0, dy*(i+j/float(sd)),
                               self.options.grid_angle,
                               self.options.subdiv_th,
                               self.options.subdiv_color,
                               'MinorYDivP'+str(i),
                               minglp)
                    self.drawAngledGridLine(0, dy*(i+j/float(sd)),
                               -self.options.grid_angle,
                               self.options.subdiv_th,
                               self.options.subdiv_color,
                               'MinorYDivN'+str(i),
                               mingln)
                for k in range (1, ssd): #subsub divs
                    self.drawAngledGridLine(0, dy*(i+(j*ssd+k)/((float(sd)*ssd))), 
                               self.options.grid_angle,
                               self.options.subsubdiv_th,
                               self.options.subsubdiv_color,
                               'SubMinorYDivP'+str(i),
                               mminglp)
                    self.drawAngledGridLine(0, dy*(i+(j*ssd+k)/((float(sd)*ssd))), 
                               -self.options.grid_angle,
                               self.options.subsubdiv_th,
                               self.options.subsubdiv_color,
                               'SubMinorYDivN'+str(i),
                               mmingln)


if __name__ == '__main__':
    TriangularGrid().run()
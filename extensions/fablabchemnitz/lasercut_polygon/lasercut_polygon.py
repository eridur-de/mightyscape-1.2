#! /usr/bin/env python
'''
Generates Inkscape SVG file containing up to two polygons or circle taking kerf and clearance into account

Copyright (C) 2016 Thore Mehr thore.mehr@gmail.com
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
__version__ = "0.8" ### please report bugs, suggestions etc to bugs@twot.eu ###

import inkex
import math
from lxml import etree
from inkex import Color


def drawS(s, XYstring, color):         # Draw lines from a list
    name='part'
    style = { 'stroke': color, 'stroke-width': s.svg.unittouu("1px"), 'fill': 'none' }
    drw = {'style':str(inkex.Style(style)),inkex.addNS('label','inkscape'):name,'d':XYstring}
    etree.SubElement(parent, inkex.addNS('path','svg'), drw )
    return
  
def groupdraw(s, XYstrings, colors)  :
    if len(XYstrings) == 1:
        drawS(s, XYstrings[0], colors[0])
        return
    grp_name = 'Group'
    grp_attribs = {inkex.addNS('label','inkscape'):grp_name}
    grp = etree.SubElement(parent, 'g', grp_attribs)#the group to put everything in
    name='part'
    for i in range(len(XYstrings)):
        style = { 'stroke': colors[i], 'fill': 'none' }
        drw = {'style':str(inkex.Style(style)),inkex.addNS('label','inkscape'):name+str(i),'d':XYstrings[i]}
        etree.SubElement(grp, inkex.addNS('path','svg'), drw )
    return

def svg_from_points(points,offset):
    s='M'+str(points[0][0]+offset[0])+','+str(points[0][1]+offset[1])
    for i in range(1,len(points)):
        s+='L'+str(points[i][0]+offset[0])+','+str(points[i][1]+offset[1])
    s+='Z'
    return s
  
class LasercutPolygon(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument('--page')
        pars.add_argument('--unit', default='mm', help='Measure Units')
        pars.add_argument('--o_type', type=int, default=1, help='Outer type')
        pars.add_argument('--o_radius',type=float, default=100, help='Outer Radius')
        pars.add_argument('--o_edges', type=int, default=1, help='Outer edges')
        pars.add_argument('--o_r_type', type=int, default=1, help='Outer radius type')
        pars.add_argument('--o_offset',type=float, default=100, help='Outer Radius')
        pars.add_argument('--i_type', type=int, default=1, help='Inner type')
        pars.add_argument('--i_radius',type=float, default=100, help='Inner Radius')
        pars.add_argument('--i_edges', type=int, default=1, help='Inner edges')
        pars.add_argument('--i_r_type', type=int, default=1, help='Inner radius type')
        pars.add_argument('--i_offset',type=float, default=100, help='Outer Radius')
        pars.add_argument('--kerf',type=float, default=0.5, help='Kerf (width) of cut')
        pars.add_argument('--spacing',type=float, default=0.5)
        pars.add_argument('--color1', type=Color, default='1923076095')
        pars.add_argument('--color2', type=Color, default='4012452351')
        pars.add_argument('--intensity', type=int, default=1)
        pars.add_argument('--speed', type=int, default=1)
        pars.add_argument('--pass_offset', type=int, default=1)
        pars.add_argument('--displaylasertag', type=inkex.Boolean, default=False) 
        pars.add_argument('--lasertag', default="=pass%n:%s:%i:%c=") 
      
    def effect(self):
        global parent,nomTab,equalTabs,thickness,kerf,correction
        
        # Get access to main SVG document element and get its dimensions.
        svg = self.document.getroot()
        
        # Get the attibutes:
        widthDoc  = self.svg.unittouu(svg.get('width'))
        heightDoc = self.svg.unittouu(svg.get('height'))
        
        parent=self.svg.get_current_layer()
        
        # Get script's option values.
        unit=self.options.unit
        kerf = self.svg.unittouu( str(self.options.kerf)  + unit )
        spacing = self.svg.unittouu( str(self.options.spacing)  + unit )
        
        o_type=self.options.o_type
        o_edges=self.options.o_edges
        o_r_type=self.options.o_r_type
        o_radius=self.svg.unittouu(str(self.options.o_radius)+unit)+kerf
        o_offset=math.radians(-self.options.o_offset)+math.pi
        
        i_type=self.options.i_type
        i_edges=self.options.i_edges
        i_r_type=self.options.i_r_type
        i_radius=self.svg.unittouu(str(self.options.i_radius)+unit)+kerf
        i_offset=math.radians(-self.options.i_offset)+math.pi
        
        color1=self.options.color1
        color2=self.options.color2
        intensity=self.options.intensity
        speed=self.options.speed
        pass_offset=self.options.pass_offset
        lasertag=self.options.lasertag
        
        if (o_r_type==2 and o_type==2):
        #a/sin(alpa)=b/sin(beta)=c/sin(gamma)
        #b=o_radius, alpha=(2*math.pi/o_edges), gamma=pi/2 , alpha+beta+gamma=pi->beta=pi-alpha+gamma
        #search for c
        #c=b*(sin(gamma)/sin(betta))
            beta=math.pi/2-(math.pi/o_edges)
            o_radius/=math.sin(beta)
        if (o_r_type==3 and o_type==2):
            beta=math.pi/2-(math.pi/o_edges)
            o_radius*=math.sin(beta)/math.sin(math.pi/o_edges)
        if (i_r_type==2 and i_type==3):
        #a/sin(alpa)=b/sin(beta)=c/sin(gamma)
        #b=o_radius, alpha=(2*math.pi/o_edges), gamma=pi/2 , alpha+beta+gamma=pi->beta=pi-alpha+gamma
        #search for c
        #c=b*(sin(gamma)/sin(betta))
            beta=math.pi/2-(math.pi/i_edges)
            i_radius/=math.sin(beta)
        if (i_r_type==3 and i_type==3):
            beta=math.pi/2-(math.pi/i_edges)
            i_radius*=math.sin(beta)/math.sin(math.pi/o_edges)
        
        
        #text = etree.Element(inkex.addNS('text','svg'))
        #text.text = "Outside:"+str(self.uutounit(cabinet_width,unit))+"x"+str(self.uutounit(cabinet_depth,unit))+"x"+str(self.uutounit(cabinet_height,unit))+"  "
        #layer.append(text)
        
        
        if(o_type==1):
            s=['M '+str(spacing)+','+str(o_radius+spacing)+'a'+str(o_radius)+','+str(o_radius)+' 0 1,0 '+str(2*o_radius)+',0'+'a'+str(o_radius)+','+str(o_radius)+' 0 1,0 '+str(-2*o_radius)+',0']
        if(o_type==2):
            stepsize=2*math.pi/o_edges
            points=[]
          
            for i in range(o_edges):
              points+=[(math.sin(o_offset+stepsize*i)*(o_radius+kerf),math.cos(o_offset+stepsize*i)*(o_radius+kerf))]
            s=[svg_from_points(points,(o_radius+spacing,o_radius+spacing))]
        if(i_type==2):
            s+=['M '+str(spacing+o_radius-i_radius)+','+str(o_radius+spacing)+'a'+str(i_radius)+','+str(i_radius)+' 0 1,0 '+str(2*i_radius)+',0'+'a'+str(i_radius)+','+str(i_radius)+' 0 1,0 '+str(-2*i_radius)+',0']
        if(i_type==3):
            stepsize=2*math.pi/i_edges
            points=[]
          
            for i in range(i_edges):
                points+=[(math.sin(i_offset+stepsize*i)*(i_radius+kerf),math.cos(i_offset+stepsize*i)*(i_radius+kerf))]
            s+=[svg_from_points(points,(o_radius+spacing,o_radius+spacing))]
        groupdraw(self, s,[color1,color2])
        
        if self.options.displaylasertag:
            # Create a new layer.
            layer = etree.SubElement(svg, 'g')
            layer.set(inkex.addNS('label', 'inkscape'), 'lasertag')
            layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        
            tag_1=lasertag
            tag_1=tag_1.replace("%n",str(pass_offset+1)).replace("%s",str(speed)).replace("%i",str(intensity)).replace("%c",str(color2))
            tag_2=lasertag
            tag_2=tag_2.replace("%n",str(pass_offset+2)).replace("%s",str(speed)).replace("%i",str(intensity)).replace("%c",str(color1))
            text = etree.Element(inkex.addNS('text','svg'))
            text.text = tag_1
            if (len(s)>1):
                text.text+="  "+tag_2
            layer.append(text) 

if __name__ == '__main__':
    LasercutPolygon().run()
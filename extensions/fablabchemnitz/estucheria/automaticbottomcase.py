#! /usr/bin/env python3
#
# 
# This script draws the outer profile of the box cut in a single 
# closed path and then add the other necessary strips with colours
# different to identify them.
# red > for cuts and outer profile
# blue > for crevices
# green > for drills
# yellow > half-cut
#
# EVERYTHING:
# add cm/in drawing option
# move drawing to the center of the document
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

__version__ = "0.2"

import inkex

class AutomaticBottomCase(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--width", type=float, default=25.0, help="Width of the box")
        pars.add_argument("--height", type=float, default=25.0, help="Height of the box")
        pars.add_argument("--depth", type=float, default=25.0, help="Length of the box")
        pars.add_argument("--glue_tab", type=float, default=5.0, help="Tab width")
        pars.add_argument("--close_tab", type=float, default=5.0, help="Height sealing flange")
        pars.add_argument("--side_tabs", type=float, default=5.0, help="Height side sealing flanges")
        pars.add_argument("--unit", default="mm", help="Type of units")

    def effect(self):
        width_center_document = self.svg.unittouu(self.document.getroot().get('width'))/2
        height_center_document = self.svg.unittouu(self.document.getroot().get('height'))/2

        eyelash_measure1=5
        eyelash_measure2=1
        eyelash_measure3=4
        eyelash_measure4=3

        box_width = self.svg.unittouu(str(self.options.width) + self.options.unit)
        box_height = self.svg.unittouu(str(self.options.height) + self.options.unit)
        box_length = self.svg.unittouu(str(self.options.depth) + self.options.unit)
        glue_width = self.svg.unittouu(str(self.options.glue_tab) + self.options.unit)
        top_flap_closure = self.svg.unittouu(str(self.options.close_tab) + self.options.unit)
        top_flap = self.svg.unittouu(str(self.options.side_tabs) + self.options.unit)

        if self.options.unit=="cm":
            eyelash_measure1=0.5
            eyelash_measure2=0.1
            eyelash_measure3=0.4
            eyelash_measure3=0.3
			
        if self.options.unit=='in':
            eyelash_measure1=0.196
            eyelash_measure2=0.039
            eyelash_measure3=0.157
            eyelash_measure3=0.118

        measure1_side_blind=self.svg.unittouu(str(eyelash_measure1) + self.options.unit)
        measure2_side_blind=self.svg.unittouu(str(eyelash_measure2) + self.options.unit)
        measure3_side_blind=self.svg.unittouu(str(eyelash_measure3) + self.options.unit)
        measure4_side_blind=self.svg.unittouu(str(eyelash_measure4) + self.options.unit)

        box_id = self.svg.get_unique_id('automaticbottomcase')
        group = self.svg.get_current_layer().add(inkex.Group(id=box_id))
        line_style_cuts = {'stroke': '#FF0000', 'fill': 'none', 'stroke-width': str(self.svg.unittouu('1px'))}
        cleft_line_style = {'stroke': '#0000FF', 'fill': 'none', 'stroke-width': str(self.svg.unittouu('1px'))}
        line_style_drills = {'stroke': '#00FF00', 'fill': 'none', 'stroke-width': str(self.svg.unittouu('1px'))}
        media_line_style = {'stroke': '#00FFFF', 'fill': 'none', 'stroke-width': str(self.svg.unittouu('1px'))}

        # line.path --> M = absolute coordinates
        # line.path --> l = draws a line from the current point to the specified coordinates
        # line.path --> c = draws a beizer curve from the current point to the specified coordinates
        # line.path --> q = draws an arc from the current point to the specified coordinates using a point as reference
        # line.path --> Z = close path
        
        #Outside profile of the box
        line = group.add(inkex.PathElement(id=box_id + '-profile-outside'))
        line.path = [
			['M', [0, 0]],
			['l', [0, 0-box_length]],
			['l', [0, 0]],
			['q', [0,0-top_flap_closure,top_flap_closure, 0-top_flap_closure]],
			['l', [box_width-(top_flap_closure*2), 0]],
			['q', [top_flap_closure,0,top_flap_closure,top_flap_closure]],
			['l', [0, 0]],
			['l', [0, (box_length)]],
			['l', [measure4_side_blind, 0-measure4_side_blind]],
			['l', [0,0-(top_flap-measure4_side_blind)]],
			['l', [(box_length-measure2_side_blind-measure3_side_blind-measure4_side_blind), 0]],
			['l', [measure3_side_blind, (top_flap-measure2_side_blind-measure1_side_blind)]],
			['l', [measure2_side_blind, measure2_side_blind]],
			['l', [0, measure1_side_blind]],
			['l', [0,0]],
			['l', [box_width, 0]],
			['l', [0,0]],
			['l', [0, 0]],
			['l', [0, 0-measure1_side_blind]],
			['l', [measure2_side_blind, 0-measure2_side_blind]],
			['l', [measure3_side_blind, 0-(top_flap-measure2_side_blind-measure1_side_blind)]], 
			['l', [(box_length-measure2_side_blind-measure3_side_blind-measure4_side_blind), 0]],
			['l', [0,top_flap-measure4_side_blind]],
			['l', [measure4_side_blind, measure4_side_blind]],
			['l', [0, box_height]],
			['l', [0-((box_length/2)),box_length/2]],
			['l', [0-((box_length/2)-(measure2_side_blind)*2),0]],
			['l', [0-(measure2_side_blind),0-((box_length/2)-measure2_side_blind)]],
			['l', [0-measure2_side_blind,0-measure2_side_blind]],
			['l', [0-measure2_side_blind,measure2_side_blind]],
			['l', [0,box_length*0.7]],
			['l', [0-(((box_length*0.5)-measure2_side_blind)/2),0]],
			['l', [0-(((box_length*0.5)-measure2_side_blind)/2),0-((box_length*0.7)-(box_length*0.5))]],
			['l', [0-((box_width/2)-((box_length*0.5)-measure2_side_blind)),0]],
			['l', [measure3_side_blind,measure3_side_blind]],
			['l', [0-((box_length*0.7)-(box_length*0.5))-measure3_side_blind,((box_length*0.7)-(box_length*0.5))-measure3_side_blind]],
			['l', [0-(((box_width/2)-((box_length*0.5)))+((box_length*0.7)-(box_length*0.5))),0]],
			['l', [0-measure4_side_blind/2,0-((box_length*0.7))-measure2_side_blind]],
			['l', [0-(box_length/2),box_length/2]],
			['l', [0-((box_length/2)-(measure2_side_blind)*2),0]],
			['l', [0-measure2_side_blind,0-((box_length/2)-measure2_side_blind)]],
			['l', [0-measure2_side_blind,0-measure2_side_blind]],
			['l', [0-measure2_side_blind,measure2_side_blind]],
			['l', [0,box_length*0.7]],
			['l', [0-(((box_length*0.5)-measure2_side_blind)/2),0]],
			['l', [0-(((box_length*0.5)-measure2_side_blind)/2),0-((box_length*0.7)-(box_length*0.5))]],
			['l', [0-((box_width/2)-((box_length*0.5)-measure2_side_blind)),0]],
			['l', [measure3_side_blind,measure3_side_blind]],
			['l', [0-((box_length*0.7)-(box_length*0.5))-measure3_side_blind,((box_length*0.7)-(box_length*0.5))-measure3_side_blind]],
			['l', [0-(((box_width/2)-((box_length*0.5)))+((box_length*0.7)-(box_length*0.5))),0]],
			['l', [0-measure4_side_blind/2,0-((box_length*0.7))-measure2_side_blind]],
			['l', [0, 0-measure2_side_blind]],
			['l', [0-glue_width, 0-(glue_width/2)]],
			['l', [0, 0-(box_height-glue_width-(measure2_side_blind*2))]],
			['l', [glue_width, 0-(glue_width/2)]],
			['Z', []]
        ]
        line.style = line_style_cuts
        
        #Hendidos
        line = group.add(inkex.PathElement(id=box_id + '-profile-splits-1'))
        line.path = [
			['M', [0,0]],
			['l', [0,box_height]]
		]
        line.style = cleft_line_style

        line = group.add(inkex.PathElement(id=box_id + '-profile-splits-2'))
        line.path = [
			['M', [box_width,0]],
			['l', [0,box_height]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=box_id + '-profile-splits-3'))
        line.path = [
			['M', [box_width+box_length,0]],
			['l', [0,box_height]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=box_id + '-profile-splits-4'))
        line.path = [
			['M', [box_width+box_width+box_length,0]],
			['l', [0,box_height]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=box_id + '-profile-splits-5'))
        line.path = [
			['M', [0,0]],
			['l', [box_width,0]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=box_id + '-profile-splits-6'))
        line.path = [
			['M', [0,box_height]],
			['l', [((box_length+box_width)*2),0]]
		]
        line.style = cleft_line_style
 
        line = group.add(inkex.PathElement(id=box_id + '-profile-splits-7'))
        line.path = [
			['M', [box_width,0]],
			['l', [box_length,0]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=box_id + '-profile-splits-8'))
        line.path = [
			['M', [box_length+box_width*2,0]],
			['l', [box_length,0]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=box_id + '-profile-splits-9'))
        line.path = [
			['M', [0,0-(box_length)]],
			['l', [box_width,0]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=box_id + '-profile-drill-1'))
        line.path = [
			['M', [box_width-measure2_side_blind,box_height+measure2_side_blind]],
			['l', [0-((box_length*0.5)),(box_length*0.5)]]
		]
        line.style = line_style_drills
        
        line = group.add(inkex.PathElement(id=box_id + '-profile-drill-2'))
        line.path = [
			['M', [((box_width*2)+box_length)-measure2_side_blind,box_height+measure2_side_blind]],
			['l', [0-((box_length*0.5)),(box_length*0.5)]]
		]
        line.style = line_style_drills

if __name__ == '__main__':
    AutomaticBottomCase().run()
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
# TODO:
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

class DoubeRailingCase(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--width", type=float, default=25.0, help="Width of the box")
        pars.add_argument("--height", type=float, default=25.0, help="Height of the box")
        pars.add_argument("--depth", type=float, default=25.0, help="Length of the box")
        pars.add_argument("--glue_tab", type=float, default=5.0, help="Tab width")
        pars.add_argument("--unit", default="mm", help="Type of units")

    def effect(self):
        center_width_document = self.svg.unittouu(self.document.getroot().get('width'))/2
        center_height_document = self.svg.unittouu(self.document.getroot().get('height'))/2

        box_width = self.svg.unittouu(str(self.options.width) + self.options.unit)
        box_height = self.svg.unittouu(str(self.options.height) + self.options.unit)
        box_length = self.svg.unittouu(str(self.options.depth) + self.options.unit)
        eyelash_width = self.svg.unittouu(str(self.options.glue_tab) + self.options.unit)
        
        eyelash_measure1=2
        eyelash_measure2=1
        eyelash_measure3=5
        eyelash_measure4=3
		
        id_box = self.svg.get_unique_id('double-railing-case')
        group = self.svg.get_current_layer().add(inkex.Group(id=id_box))
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
        line = group.add(inkex.PathElement(id=id_box + '-profile-outside'))
        line.path = [
			['M', [0, 0]],
			['l', [box_width,0]],
			['l', [0,0]],
			['l', [0,eyelash_width]],
			['l', [eyelash_width,0]],
			['l', [0-(eyelash_width-eyelash_measure1),box_height-eyelash_measure4]],
			['l', [0-eyelash_measure1,eyelash_measure2]],
			['l', [0,eyelash_measure1]],
			['l', [box_height-eyelash_measure3,eyelash_measure3]],
			['l', [eyelash_measure3,box_height-eyelash_measure3]],
			['l', [eyelash_measure1,0]],
			['l', [eyelash_measure2,eyelash_measure1]],
			['l', [box_height-eyelash_measure4,eyelash_width-eyelash_measure1]],
			['l', [0,box_length-(eyelash_width*2)]],
			['l', [0-(box_height-eyelash_measure4),eyelash_width-eyelash_measure1]],
			['l', [0-eyelash_measure2,eyelash_measure1]],
			['l', [0-eyelash_measure1,0]],
			['l', [0-eyelash_measure3,box_height-eyelash_measure3]],
			['l', [0-(box_height-eyelash_measure3),eyelash_measure3]],
			['l', [0,eyelash_measure1]],
			['l', [eyelash_measure1,eyelash_measure2]],
			['l', [eyelash_width-eyelash_measure1,box_height-eyelash_measure4]],
			['l', [0-eyelash_width,0]],
			['l', [0,0]],
			['l', [0,eyelash_width]],
			['l', [0-box_width,0]],
			['l', [0,0-eyelash_width]],
			['l', [0,0]],
			['l', [0-eyelash_width,0]],
			['l', [eyelash_width-eyelash_measure1,0-(box_height-eyelash_measure4)]],
			['l', [eyelash_measure1,0-eyelash_measure2]],
			['l', [0,0-eyelash_measure1]],
			['l', [0-(box_height-eyelash_measure3),0-eyelash_measure3]],
			['l', [0-eyelash_measure3,0-(box_height-eyelash_measure3)]],
			['l', [0-eyelash_measure1,0]],
			['l', [0-eyelash_measure2,0-eyelash_measure1]],
			['l', [0-(box_height-eyelash_measure4),0-(eyelash_width-eyelash_measure1)]],
			['l', [0,0-(box_length-(eyelash_width*2))]],
			['l', [box_height-eyelash_measure4,0-(eyelash_width-eyelash_measure1),]],
			['l', [eyelash_measure2,0-eyelash_measure1]],
			['l', [eyelash_measure1,0]],
			['l', [eyelash_measure3,0-(box_height-eyelash_measure3)]],
			['l', [(box_height-eyelash_measure3),0-eyelash_measure3]],
			['l', [0,0-eyelash_measure1]],
			['l', [0-eyelash_measure1,0-eyelash_measure2]],
			['l', [0-(eyelash_width-eyelash_measure1),0-(box_height-eyelash_measure4)]],
			['l', [eyelash_width,0]],
			['Z', []]
        ]
        line.style = line_style_cuts
        
        #profile splits
        line = group.add(inkex.PathElement(id=id_box + '-profile-splits-1'))
        line.path = [
			['M', [0,eyelash_width]],
			['l', [box_width,0]]
		]
        line.style = cleft_line_style

        line = group.add(inkex.PathElement(id=id_box + '-profile-splits-2'))
        line.path = [
			['M', [0,(box_height+eyelash_width)]],
			['l', [box_width,0]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=id_box + '-profile-splits-3'))
        line.path = [
			['M', [0-box_height,((box_height*2)+eyelash_width)]],
			['l', [box_width+(box_height*2),0]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=id_box + '-profile-splits-4'))
        line.path = [
			['M', [0-box_height,(((box_height*2)+eyelash_width)+box_length)]],
			['l', [box_width+(box_height*2),0]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=id_box + '-profile-splits-5'))
        line.path = [
			['M', [0,(box_height*3)+box_length+eyelash_width]],
			['l', [box_width,0]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=id_box + '-profile-splits-6'))
        line.path = [
			['M', [0,(box_height*4)+box_length+eyelash_width]],
			['l', [box_width,0]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=id_box + '-profile-splits-7'))
        line.path = [
			['M', [0,eyelash_width]],
			['l', [0,box_length+(box_height*4)]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=id_box + '-profile-splits-8'))
        line.path = [
			['M', [box_width,eyelash_width]],
			['l', [0,box_length+(box_height*4)]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=id_box + '-profile-splits-9'))
        line.path = [
			['M', [0-box_height,eyelash_width+(box_height*2)]],
			['l', [0,box_length]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=id_box + '-profile-splits-10'))
        line.path = [
			['M', [box_width+box_height,eyelash_width+(box_height*2)]],
			['l', [0,box_length]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=id_box + '-profile-splits-11'))
        line.path = [
			['M', [0,eyelash_width+(box_height*2)]],
			['l', [0-(box_height-eyelash_measure3),0-(box_height-eyelash_measure3)]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=id_box + '-profile-splits-12'))
        line.path = [
			['M', [box_width,eyelash_width+(box_height*2)]],
			['l', [box_height-eyelash_measure3,0-(box_height-eyelash_measure3)]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=id_box + '-profile-splits-13'))
        line.path = [
			['M', [box_width,eyelash_width+(box_height*2)+box_length]],
			['l', [box_height-eyelash_measure3,box_height-eyelash_measure3]]
		]
        line.style = cleft_line_style
        
        line = group.add(inkex.PathElement(id=id_box + '-profile-splits-14'))
        line.path = [
			['M', [0,eyelash_width+(box_height*2)+box_length]],
			['l', [0-(box_height-eyelash_measure3),box_height-eyelash_measure3]]
		]
        line.style = cleft_line_style

if __name__ == '__main__':
    DoubeRailingCase().run()
#! /usr/bin/env python3
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

__version__ = "0.1"

import inkex
import math

class GenerateFrame(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--width", type=float, default=100.0, help="Inner width")
        pars.add_argument("--height", type=float, default=150.0, help="Inner height")
        pars.add_argument("--depth", type=float, default=10.0, help="Frame depth")
        pars.add_argument("--border", type=float, default=20.0, help="Frame border width")
        pars.add_argument("--unit", default="mm", help="Unit of measure")

    def effect(self):
        center_x = self.svg.unittouu(self.document.getroot().get('width'))/2
        center_y = self.svg.unittouu(self.document.getroot().get('height'))/2

        _width = self.svg.unittouu(str(self.options.width) + self.options.unit)
        _height = self.svg.unittouu(str(self.options.height) + self.options.unit)
        _depth = self.svg.unittouu(str(self.options.depth) + self.options.unit)

        _border = self.svg.unittouu(str(self.options.border) + self.options.unit)
        _border_hyp = math.sqrt(2 * _border * _border)

        id_frame = self.svg.get_unique_id('papercraft-frame')
        group = self.svg.get_current_layer().add(inkex.Group(id=id_frame))
        id_score = self.svg.get_unique_id('papercraft-scores')
        score_group = group.add(inkex.Group(id=id_score))
        cut_line = {'stroke': '#FF0000', 'fill': 'none', 'stroke-width': str(self.svg.unittouu('1px'))}
        safe_line = {'stroke': '#0000FF', 'fill': 'none', 'stroke-width': str(self.svg.unittouu('1px'))}
        valley_score_line = {'stroke': '#00FF00', 'fill': 'none', 'stroke-width': str(self.svg.unittouu('1px')), 'stroke-dasharray': '1.05999995,0.52999997,0.26499999,0.52999997'}
        mountain_score_line = {'stroke': '#00FF00', 'fill': 'none', 'stroke-width': str(self.svg.unittouu('1px')), 'stroke-dasharray': '5,5'}

        # line.path --> M = absolute coordinates
        # line.path --> l = draws a line from the current point to the specified relative coordinates
        # line.path --> c = draws a beizer curve from the current point to the specified coordinates
        # line.path --> q = draw an arc from the current point to the specified coordinates using a point as reference
        # line.path --> Z = close path
        
        # outer profile (cut)
        line = group.add(inkex.PathElement(id=id_frame + '-outer-profile'))
        line.path = [
            # top-left
			['M', [0, 2 * (_border+_depth)]],
			['l', [_border+_depth+_border,0]],
			['l', [0,-_depth]],
			['l', [_depth,0]],
			['l', [_border,-_border]],
			['l', [0,-_depth]],
			['l', [-_border,-_border]],
			['l', [_width+2*_border,0]],

            # top-right
            ['l', [-_border,_border]],
            ['l', [0,_depth]],
			['l', [_border,_border]],  
			['l', [_depth,0]], 
			['l', [0,_depth]],  
			['l', [_border+_depth+_border,0]],             
            ['l', [0,_height+2*_border]],                              

            # bottom-right
			['l', [-(_border+_depth+_border),0]],
			['l', [0,_depth]],              
			['l', [-_depth,0]], 
			['l', [-_border,_border]],
            ['l', [0,_depth]],  
			['l', [_border,_border]],
			['l', [-(_width+2*_border),0]],            

            # bottom-left
			['l', [_border,-_border]],
            ['l', [0,-_depth]],              
			['l', [-_border,-_border]],
			['l', [-_depth,0]],              
			['l', [0,-_depth]],               
			['l', [-(_border+_depth+_border),0]],
          
			['Z', []]            
        ]
        line.style = cut_line

        line = group.add(inkex.PathElement(id=id_frame + '-inner-profile'))
        line.path = [
            ['M', [2*_depth+3*_border, 2*_depth+3*_border]],
            ['l', [_width,0]],
            ['l', [0,_height]],
            ['l', [-_width,0]],
            ['Z', []]            
        ]
        line.style = safe_line

        # score lines -- vertical
        _top_edge = 2 *_border+2*_depth
        line = score_group.add(inkex.PathElement(id=id_score + '-score-1'))
        line.path = [
			['M', [_border, _top_edge]],
			['l', [0, _height+2*_border]],
        ]
        line.style = valley_score_line

        line = score_group.add(inkex.PathElement(id=id_score + '-score-2'))
        line.path = [
			['M', [_border+_depth, _top_edge]],
			['l', [0, _height+2*_border]],
        ]
        line.style = valley_score_line

        line = score_group.add(inkex.PathElement(id=id_score + '-score-3'))
        line.path = [
			['M', [_border+_depth+_border, _top_edge]],
			['l', [0, _height+2*_border]],
        ]
        line.style = valley_score_line  

        line = score_group.add(inkex.PathElement(id=id_score + '-score-4'))
        line.path = [
			['M', [2*(_border+_depth), _top_edge-_depth]],
			['l', [0, _height+2*_border+2*_depth]],
        ]
        line.style = valley_score_line 

        _right_side = _width+4*_border+2*_depth

        line = score_group.add(inkex.PathElement(id=id_score + '-score-5'))
        line.path = [
			['M', [_right_side, _top_edge-_depth]],
			['l', [0, _height+2*_border+2*_depth]],
        ]
        line.style = valley_score_line

        line = score_group.add(inkex.PathElement(id=id_score + '-score-6'))
        line.path = [
			['M', [_right_side+_depth, _top_edge]],
			['l', [0, _height+2*_border]],
        ]
        line.style = valley_score_line

        line = score_group.add(inkex.PathElement(id=id_score + '-score-7'))
        line.path = [
			['M', [_right_side+_border+_depth, _top_edge]],
			['l', [0, _height+2*_border]],
        ]
        line.style = valley_score_line

        line = score_group.add(inkex.PathElement(id=id_score + '-score-8'))
        line.path = [
			['M', [_right_side+_border+_depth+_depth, _top_edge]],
			['l', [0, _height+2*_border]],
        ]
        line.style = valley_score_line         

        # corners
        _o1_x = 2*_border + _depth
        _o1_y = _o1_x + _depth             

        line = score_group.add(inkex.PathElement(id=id_score + '-score-22'))
        line.path = [
			['M', [_o1_x+_depth, _o1_y]],
            ['l', [-_depth,-_depth]],
        ]
        line.style = mountain_score_line

        _o2_x = _o1_x + _width + 2*_border + 2*_depth
        _o2_y = _o1_y           

        line = score_group.add(inkex.PathElement(id=id_score + '-score-24'))
        line.path = [
			['M', [_o2_x-_depth, _o2_y]],
            ['l', [_depth,-_depth]],
        ]
        line.style = mountain_score_line

        _o3_x = _o1_x
        _o3_y = _o1_y + _height + 2*_border            

        line = score_group.add(inkex.PathElement(id=id_score + '-score-26'))
        line.path = [
			['M', [_o3_x + _depth, _o3_y]],
            ['l', [-_depth,_depth]],
        ]
        line.style = mountain_score_line

        _o4_x = _o2_x
        _o4_y = _o3_y             

        line = score_group.add(inkex.PathElement(id=id_score + '-score-28'))
        line.path = [
			['M', [_o4_x - _depth, _o4_y]],
            ['l', [_depth,_depth]],
        ]
        line.style = mountain_score_line

        # horizontals
        line = score_group.add(inkex.PathElement(id=id_score + '-score-31'))
        line.path = [
			['M', [2*_border+_depth, 2*_border+2*_depth]],
            ['l', [_width+2*_border+2*_depth,0]],
        ]
        line.style = valley_score_line

        line = score_group.add(inkex.PathElement(id=id_score + '-score-32'))
        line.path = [
			['M', [2*_border+2*_depth, 2*_border+_depth]],
            ['l', [_width+2*_border,0]],
        ]
        line.style = valley_score_line

        line = score_group.add(inkex.PathElement(id=id_score + '-score-33'))
        line.path = [
			['M', [3*_border+2*_depth, _border+_depth]],
            ['l', [_width,0]],
        ]
        line.style = valley_score_line   

        line = score_group.add(inkex.PathElement(id=id_score + '-score-34'))
        line.path = [
			['M', [3*_border+2*_depth, _border]],
            ['l', [_width,0]],
        ]
        line.style = valley_score_line  

        _bottom = _height + 4*_border+2*_depth  

        line = score_group.add(inkex.PathElement(id=id_score + '-score-35'))
        line.path = [
			['M', [2*_border+_depth, _bottom]],
            ['l', [_width+2*_border+2*_depth,0]],
        ]
        line.style = valley_score_line

        line = score_group.add(inkex.PathElement(id=id_score + '-score-36'))
        line.path = [
			['M', [2*_border+2*_depth, _bottom+_depth]],
            ['l', [_width+2*_border,0]],
        ]
        line.style = valley_score_line

        line = score_group.add(inkex.PathElement(id=id_score + '-score-37'))
        line.path = [
			['M', [3*_border+2*_depth, _bottom+_border+_depth]],
            ['l', [_width,0]],
        ]
        line.style = valley_score_line   

        line = score_group.add(inkex.PathElement(id=id_score + '-score-38'))
        line.path = [
			['M', [3*_border+2*_depth, _bottom+_border+2*_depth]],
            ['l', [_width,0]],
        ]
        line.style = valley_score_line         

if __name__ == '__main__':
    GenerateFrame().run()
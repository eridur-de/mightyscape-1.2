#!/usr/bin/env python3

"""
Inkscape extension to create checkerboard patterns


Copyright (C) 2011 Jeff Kayser

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
"""

import inkex
from lxml import etree
import re
from inkex import Color

def rgbToHex(pickerColor):
    longcolor = int(pickerColor)
    if longcolor < 0:
        longcolor = longcolor & 0xFFFFFFFF
    return '#' + format(longcolor >> 8, '06X')

def draw_square(x, y, w, h, color, parent, id_=None):
    """Draw a w*h square at (x, y) having color color
    """
    if len(color) == 4:
        opacity=color[3]
    else:
        opacity=1.0   
    
    style = {'stroke': 'none', 'stroke-width': '1', 'fill': rgbToHex(color), 'fill-opacity': opacity}
    attribs = {'style': str(inkex.Style(style)), 'height': str(h), 'width': str(w), 'x': str(x), 'y': str(y)}
    if id_ is not None:
        attribs.update({'id': id_})
    obj = etree.SubElement(parent, inkex.addNS('rect', 'svg'), attribs)

def draw_grid(x, y, rows, cols, size, color1, color2, parent):
    """Draw a rows*cols checkboard grid at (x, y) with square size of size*size,
    with squares having alternating colors color1 and color2
    """
    # Group like-colors
    group1 = etree.SubElement(parent, 'g', {'id': 'diagonal1'})
    group2 = etree.SubElement(parent, 'g', {'id': 'diagonal2'})
    for row in range(int(rows)):
        for col in range(int(cols)):
            alternate = (col + row) % 2 == 0
            color = color1 if alternate else color2
            group = group1 if alternate else group2
            id_ = 'cell{0}x{1}'.format(col, row)
            draw_square(x + col * size, y + row * size, size, size, color, group, id_)
	
class Checkerboard(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--color1", type=Color, default=4286282751)
        pars.add_argument("--color2", type=Color, default=8092671)
        pars.add_argument("--size")
        pars.add_argument("--rows", type=int)
        pars.add_argument("--cols", type=int)
        pars.add_argument("--layer", type=inkex.Boolean)

    def effect(self):
        if self.svg.get_current_layer() is not None:
            group = etree.SubElement(self.svg.get_current_layer(), 'g', {'id': 'checkerboard'})
        else:
            parent = self.document.getroot()
            group = etree.SubElement(parent, 'g', {'id': 'checkerboard'})
		  
        rows = self.options.rows
        cols = self.options.cols
        # Convert to pixels
        size = self.svg.unittouu(self.options.size)
        color1 = self.options.color1
        color2 = self.options.color2
        # Center checkerboard within visible viewport
        x, y = self.svg.namedview.center[0] - cols * size / 2, self.svg.namedview.center[1] - rows * size / 2
        draw_grid(x, y, rows, cols, size, color1, color2, group)

if __name__ == '__main__':
    Checkerboard().run()
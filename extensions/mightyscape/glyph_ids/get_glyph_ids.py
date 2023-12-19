#!/usr/bin/env python3
#
# Copyright (C) 2020 Ellen Wasboe, ellen@wasbo.net
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
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
"""
Get path ids of all selected paths should be of all paths in "Glyphs" layer
Put all ids into a continueous string (no separation character) and paste as text element in layer Ids at position x 0 y 0. 
Paths are sorted by left bounding box.
Intention: 
to quickly retrieve all path-ids of the glyph-paths when using the Custom Stroke Font extension to edit a existing svg font  https://github.com/Shriinivas/inkscapestrokefont
this string of ids can then be used to set ids using setIds.py as ids might be lost in different path operations. https://gitlab.com/EllenWasbo/inkscape-extension-setIds
"""

import inkex
from inkex import Group, TextElement

class getGlyphIDs(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--tab", default="getGlyphIDs")

    def effect(self):
        
        if self.svg.getElementById('glyph') == None:
            raise inkex.AbortExtension("Could not find layer Glyphs (id=glyphs)")
        
        else:         
            txtElem=TextElement()
                
            if self.svg.getElementById('glyphIds') == None:
                txtLayer=self.svg.add(Group.new('glyphIds'))#, is_layer=True))
                txtLayer.set('id','glyphIds')
                txtLayer.set('inkscape:groupmode','layer')
                txtLayer.style={'display':'inline'}
            else:
                txtLayer=self.svg.getElementById('glyphIds')
                    
            if self.svg.getElementById('txtGlyphIds') == None:
                txt=txtLayer.add(txtElem)
                txt.style={'font-size': '20px','letter-spacing': '2px','fill': '#000000','fill-opacity': 1,'stroke': 'none'}
                txt.set('id','txtGlyphIds')
            else:
                txt=self.svg.getElementById('txtGlyphIds')
                
            idArr=''
                
            for elem in self.svg.getElementById('glyph'):
                idArr=idArr+elem.get('id')
                
            txt.text = idArr
                
if __name__ == '__main__':
    getGlyphIDs().run()
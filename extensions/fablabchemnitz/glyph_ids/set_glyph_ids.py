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
Set ids of selected paths to a character in the specified string. 
Paths a sorted by left bounding box. Id for the path to the left is set to the first character in the string.
Intention: to quickly set the correct id of the glyph-paths when using the Custom Stroke Font extension  https://github.com/Shriinivas/inkscapestrokefont
"""

import inkex, re

class setGlyphIDs(inkex.EffectExtension):
    """Set ids of selected paths to a character in the specified string. """
    def add_arguments(self, pars):
        pars.add_argument("--tab", default="setGlyphIDs")
        pars.add_argument("--characters", default="")

    def effect(self):

        if not self.svg.selected:
            raise inkex.AbortExtension("Please select the glyph paths.")
        
        else:
            if self.options.characters == "":
                raise inkex.AbortExtension("No characters specified.")
            else:
                chars=self.options.characters
                listChar=list(chars)
                leftVal=[]
            
                i = 0
                for id, elem in self.svg.selection.id_dict().items():
                    leftVal.append(elem.bounding_box().left)
                    elem.set('id','reset'+str(i))#reset all ids to prevent duplicate id problems
                    i+=1
                    
                leftVal.sort(key=float)

                i = 0
                for id, elem in self.svg.selection.id_dict().items():
                    thisLeft=elem.bounding_box().left
                    charNo=leftVal.index(thisLeft)
                    
                    if i < len(listChar):
                        elem.set('id',listChar[charNo])
                        i+=1
                    else:
                        break
                
if __name__ == '__main__':
    setGlyphIDs().run()
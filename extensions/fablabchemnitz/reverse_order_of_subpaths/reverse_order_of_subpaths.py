#!/usr/bin/env python3
#
# Copyright (C) Ellen Wasbo, cutlings.wasbo.net 2021
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
#
import inkex
from inkex import PathElement, CubicSuperPath

class ReverseOrderOfSubpaths(inkex.EffectExtension):
    
    def reverse(self, element):
        if element.tag == inkex.addNS('path','svg'):
            new = []
            sub = element.path.to_superpath()
            i = 0
            while i < len(sub):
                new.append(sub[-1-i])
                i += 1    
            element.path = CubicSuperPath(new).to_path(curves_only=True)
        elif element.tag == inkex.addNS('g','svg'):
            for child in element.getchildren():
                self.reverse(child)
    
    def effect(self):
        """Reverse order of subpaths (combined paths) without reversing node-order or order of paths"""
        if not self.svg.selected:
            raise inkex.AbortExtension("Please select an object.")
        for element in self.svg.selection.values():
            self.reverse(element)

if __name__ == '__main__':
    ReverseOrderOfSubpaths().run()
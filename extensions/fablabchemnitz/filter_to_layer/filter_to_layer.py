#!/usr/bin/env python3
'''
This extension adds filters to current layer or removes filters from current layer

Copyright (C) 2012 Jabiertxo Arraiza, jabier.arraiza@marker.es

Version 0.3

TODO:
Comment Better!!!

CHANGE LOG 
0.1 Start  30/07/2012

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
import sys
import re

class FilterToLayer(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument('--type', default = 'Add', help = 'Add or remove filters to current layer')
    
    def selectTop(self):
        selectedSorted = None
        if self.svg.selected is not None:
            for element in self.document.getroot().iter():
                if element.get("id") in self.svg.selection:
                    selectedSorted = element
        return selectedSorted

    def effect(self):
        svg = self.document.getroot()
        typeOperation = self.options.type
        xpathStr = '//sodipodi:namedview'
        namedview = svg.xpath(xpathStr, namespaces=inkex.NSS)
        idLayer = namedview[0].get('{http://www.inkscape.org/namespaces/inkscape}current-layer');
        xpathStr = '//svg:g[@id="'+idLayer+'"]'
        layer = svg.xpath(xpathStr, namespaces=inkex.NSS)
        
        if typeOperation == "Add": #Add action
            element = self.selectTop()
            if element is not None:
                if element.get('style'):
                    matchObj = re.search( r'filter:url\(#.*?[^\)]\)', element.get('style'), re.M|re.I)
                    if matchObj:
                        filter = matchObj.group()
                        element.set('style',element.get('style').replace(filter,"").replace(";;",";"))
                        if layer[0].get('style'):
                            matchObj = re.search( r'filter:url\(#.*?[^\)]\)', layer[0].get('style'), re.M|re.I)
                            if matchObj:
                                element.set('style',element.get('style').replace(matchObj.group(),"").replace(";;",";"))
                            style = layer[0].get('style')+ ";" + filter;
                            layer[0].set('style',style.replace(";;",";"))
                        else:
                            layer[0].set('style',filter)
            else:
                inkex.utils.debug("Nothing selected")
                
        else: #Remove action
            if layer[0].get('style'):
                matchObj = re.search( r'filter:url\(#.*?[^\)]\)', layer[0].get('style'), re.M|re.I)
                if matchObj:
                    layer[0].set('style',layer[0].get('style').replace(matchObj.group(),"").replace(";;",";"))

if __name__ == '__main__':    
    FilterToLayer().run()
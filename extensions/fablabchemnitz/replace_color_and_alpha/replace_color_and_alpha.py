#!/usr/bin/env python3
'''
This extension replace color and alpha from full inkscape document.

Copyright (C) 2012 Jabiertxo Arraiza, jabier.arraiza@marker.es

Version 0.2

TODO:
Comment Better!!!

CHANGE LOG 
0.1 Start  16/08/2012

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
from lxml import etree

class ReplaceColorAndAlpha(inkex.EffectExtension):
    
  def add_arguments(self, pars):
    pars.add_argument("--from_color", default="000000", help="Replace color")
    pars.add_argument("--to_color", default="000000", help="By color + Alpha")
    
  def effect(self):
    saveout = sys.stdout
    sys.stdout = sys.stderr
    fr = self.options.from_color.strip('"').strip('#').lower()
    try:
        alphaFr = str(float(int(self.options.from_color.strip('"').strip('#').lower()[-2:], 16))/255.0)
    except:
        pass
    to = self.options.to_color.strip('"').strip('#').lower()
    try:
        alphaTo = str(float(int(self.options.to_color.strip('"').strip('#').lower()[-2:], 16))/255.0)
    except Exception as e:
        inkex.utils.debug(e)
        pass
    
    elements = []
    if self.svg.selected:
        for id, node in self.svg.selected.items():
            elements.append(node)
    else:
        svg = self.document.getroot()
        for svg_element in svg.iter("*"):
            elements.append(svg_element)
            
    for element in elements:
        style = element.get('style')
        if style:
            if (style.lower().find('fill:#'+fr[:6]) != -1 and len(fr) == 6) or (style.lower().find('fill-opacity:'+alphaFr[:4]) != -1 and len(fr)==8 and style.lower().find('fill:#'+fr[:6]) != -1):
                style = re.sub('fill-opacity:.*?(;|$)',
                '\\1',
                style)
                style = re.sub('fill:#.*?(;|$)',
                'fill:#' + to[:6] + '\\1',
                style) 
                
                style = style + ";fill-opacity:" + alphaTo
                element.set('style',style)
            if (style.lower().find('stroke:#'+fr[:6]) != -1 and len(fr) == 6) or (style.lower().find('stroke:#'+fr[:6]) != -1 and style.lower().find('stroke-opacity:'+alphaFr[:4]) != -1 and len(fr)==8):
                style = re.sub('stroke-opacity:.*?(;|$)',
                '\\1',
                style)
                style = re.sub(r'stroke:#.*?(;|$)',
                'stroke:#' + to[:6] + '\\1',
                style) 
                style = style + ";stroke-opacity:" + alphaTo
                element.set('style',style)
        sys.stdout = saveout
    
if __name__ == '__main__':
    ReplaceColorAndAlpha().run()
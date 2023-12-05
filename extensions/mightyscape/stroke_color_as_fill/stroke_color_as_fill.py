#!/usr/bin/env python3
'''
This extension set the stroke of selected elements as fill color and fill opacity (and optional inversed)

Copyright (C) 2016 Jabiertxo Arraiza, jabier.arraiza@marker.es

Version 0.2


CHANGE LOG 
0.2 Added features done by suv in his swamp color extension https://gitlab.com/su-v/inx-modifycolor/
0.1 Start  25/11/2016

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

class StrokeColorAsFill(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--tab", help="The selected UI-tab")
        pars.add_argument("--fill_stroke_mode", default="fillstroke", help="Exchange mode fill, stroke")
        pars.add_argument("--fill_stroke_copy_alpha", type=inkex.Boolean, default=True, help="Copy alpha")
        pars.add_argument("--fill_stroke_copy_none", type=inkex.Boolean, default=True, help="Copy 'None' property")
        pars.add_argument("--fill_stroke_copy_unset", type=inkex.Boolean, default=True, help="Copy 'Unset' property")
        pars.add_argument("--fill_stroke_convert_unset",  type=inkex.Boolean, default=True, help="Convert 'Unset' property")
        pars.add_argument("--nodash", type=inkex.Boolean, default="false", help="Fix dash-stroke to alow no line only markers")

    def color_swapper(self, element):
        if element.tag == inkex.addNS('g', 'svg'):
            for e in element:
                self.color_swaper(e)
        else:
            style = element.get('style')
            if style:
                fill = re.search('fill:(.*?)(;|$)', style)
                if fill is not None:
                    style = style.replace(fill.group(),'')
                    fill = fill.group(1)
                stroke = re.search('stroke:(.*?)(;|$)', style)
                if stroke is not None:
                    style = style.replace(stroke.group(),'')
                    stroke = stroke.group(1)
                fill_opacity = re.search('fill-opacity:(.*?)(;|$)', style)
                if fill_opacity is not None:
                    style = style.replace(fill_opacity.group(),'')
                    fill_opacity = fill_opacity.group()
                stroke_opacity = re.search('stroke-opacity:(.*?)(;|$)', style)
                if stroke_opacity is not None:
                    style = style.replace(stroke_opacity.group(),'')
                    stroke_opacity = stroke_opacity.group()
                if 'fill' in self.options.fill_stroke_mode:
                    if self.options.fill_stroke_copy_none or fill != 'none':
                        if fill is None:
                            if self.options.fill_stroke_convert_unset:
                                style += ';stroke:black'
                        else:
                            style += ';stroke:' + fill
                    if self.options.fill_stroke_copy_alpha and fill_opacity is not None:
                        style += ';stroke-opacity:' + fill_opacity
                if 'stroke' in self.options.fill_stroke_mode:
                    if self.options.fill_stroke_copy_none or stroke != 'none':
                        if stroke is None:
                            if self.options.fill_stroke_convert_unset:
                                style += ';fill:none'
                        else:
                            style += ';fill:' + stroke
                    if self.options.fill_stroke_copy_alpha and stroke_opacity is not None:
                        style += ';fill-opacity:' + stroke_opacity
                if self.options.fill_stroke_mode == 'fill':
                    if fill is not None:
                        style += ';fill:' + fill
                    if fill_opacity is not None:
                        style += ';fill-opacity:' + fill_opacity
                if self.options.fill_stroke_mode == 'stroke':
                    if stroke is not None:
                        style += ';stroke:' + stroke
                    if stroke_opacity is not None:
                        style += ';stroke-opacity:' + stroke_opacity
                if self.options.nodash:
                    style = re.sub('stroke-dasharray:.*?(;|$)', '', style)
                    style = re.sub('stroke-dashoffset:.*?(;|$)', '', style)
                    style = re.sub('$', ';stroke-dasharray:0, 11;stroke-dashoffset:10$', style)
                element.set('style',style)

    def effect(self):
        saveout = sys.stdout
        sys.stdout = sys.stderr
        svg = self.document.getroot()
        for id, element in self.svg.selected.items():
            self.color_swapper(element)
        sys.stdout = saveout

if __name__ == '__main__':
    StrokeColorAsFill().run()
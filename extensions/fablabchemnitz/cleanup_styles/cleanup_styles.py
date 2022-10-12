#!/usr/bin/env python3
'''
Copyright (C) 2013 Matthew Dockrey  (gfish @ cyphertext.net)

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

Based on 
- coloreffect.py by Jos Hirth and Aaron C. Spike
- cleanup.py (https://github.com/attoparsec/inkscape-extensions) by attoparsec

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Last Patch: 12.04.2021
License: GNU GPL v3

Notes: 
 - This extension does not check if attributes contain duplicates properties like "opacity:1;fill:#393834;fill-opacity:1;opacity:1;fill:#393834;fill-opacity:1". We assume the SVG syntax is correct
'''

import inkex
import re
import numpy as np

class CleanupStyles(inkex.EffectExtension):

    groups = []
    roundUpColors = []
    roundUpColors = [
            [  0,   0,   0], #black       | eri1
            [  0,   0, 255], #blue        | eri2
            [  0, 255,   0], #green       | eri3
            [255,   0,   0], #red         | eri4
            [255,   0, 255], #magenta     | eri5
            [  0, 255, 255], #cyan        | eri6
            [255, 255,   0], #yellow      | eri7
            #half tones
            [128,   0, 255], #violet      | eri8
            [0  , 128, 255], #light blue  | eri9
            [255, 128,   0], #orange      | eri10
            [255,   0, 128], #pink        | eri11
            [128, 255,   0], #light green | eri12
            [0  , 255, 128], #mint        | eri13 
        ]
    
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--mode", default="Lines", help="Join paths with lines or polygons")
        pars.add_argument("--dedicated_style_attributes", default="ignore", help="Handling of dedicated style attributes")
        pars.add_argument("--stroke_width_override", type=inkex.Boolean, default=False, help="Override stroke width")
        pars.add_argument("--stroke_width", type=float, default=0.100, help="Stroke width")
        pars.add_argument("--stroke_width_units", default="mm", help="Stroke width unit")
        pars.add_argument("--stroke_opacity_override", type=inkex.Boolean, default=False, help="Override stroke opacity")
        pars.add_argument("--stroke_opacity", type=float, default="100.0", help="Stroke opacity (%)")
        pars.add_argument("--reset_opacity", type=inkex.Boolean, default=True, help="Reset stroke style attribute 'opacity'. Do not mix up with 'fill-opacity' and 'stroke-opacity'")
        pars.add_argument("--reset_stroke_attributes", type=inkex.Boolean, default=True, help="Remove 'stroke-dasharray', 'stroke-dashoffset', 'stroke-linejoin', 'stroke-linecap', 'stroke-miterlimit' from style attribute")
        pars.add_argument("--reset_fill_attributes", type=inkex.Boolean, default=True, help="Sets 'fill:none;fill-opacity:1;' to style attribute")
        pars.add_argument("--apply_hairlines", type=inkex.Boolean, default=True, help="Adds 'vector-effect:non-scaling-stroke;' and '-inkscape-stroke:hairline;' Hint: stroke-width is kept in background. All hairlines still have a valued width.")
        pars.add_argument("--apply_black_strokes", type=inkex.Boolean, default=True, help="Adds 'stroke:#000000;' to style attribute")
        pars.add_argument("--remove_group_styles", type=inkex.Boolean, default=False, help="Remove styles from groups")
        pars.add_argument("--harmonize_colors", type=inkex.Boolean, default=False, help="Round up colors to the next 'full color'. Example: make rgb(253,0,0) to rgb(255,0,0) to receive clear red color.")
        pars.add_argument("--allow_half_tones", type=inkex.Boolean, default=False, help="Allow rounding up to half-tone colors")
 
    
    def closestColor(self, colors, color):
        colors = np.array(colors)
        color = np.array(color)
        distances = np.sqrt(np.sum((colors-color)**2, axis=1))
        index_of_smallest = np.where(distances==np.amin(distances))
        smallest_distance = colors[index_of_smallest]
        return smallest_distance
    
    def effect(self):
        self.roundUpColors = [
                [  0,   0,   0], #black       | eri1
                [  0,   0, 255], #blue        | eri2
                [  0, 255,   0], #green       | eri3
                [255,   0,   0], #red         | eri4
                [255,   0, 255], #magenta     | eri5
                [  0, 255, 255], #cyan        | eri6
                [255, 255,   0], #yellow      | eri7
                [255, 255,  255], #white      | eri8 - useful for engravings, not for line cuttings
            ]
        if self.options.allow_half_tones is True:
            self.roundUpColors.extend([
            [128,   0, 255], #violet      | eri9
            [0  , 128, 255], #light blue  | eri10
            [255, 128,   0], #orange      | eri11
            [255,   0, 128], #pink        | eri12
            [128, 255,   0], #light green | eri13
            [128, 255, 255], #lighter blue| eri14
            [0  , 255, 128], #mint        | eri15 
            [128, 128, 128], #grey        | eri16
        ])
        
        if len(self.svg.selected) == 0:
            self.getAttribs(self.document.getroot())
        else:
            for element in self.svg.selected.values():
                self.getAttribs(element)
        #finally remove the styles from collected groups (if enabled)
        if self.options.remove_group_styles is True:
            for group in self.groups:
                if group.attrib.has_key('style') is True:
                    group.attrib.pop('style')

    def getAttribs(self, node):
        self.changeStyle(node)
        for child in node:
            self.getAttribs(child)

    #stroke and fill styles can be included in style attribute or they can exist separately (can occure in older SVG files). We do not parse other attributes than style
    def changeStyle(self, node):
        #we check/modify the style of all shapes (not groups)
        if isinstance(node, inkex.ShapeElement) and not isinstance(node, inkex.Group):
            # the final styles applied to this element (with influence from top level elements like groups)
            specified_style = node.specified_style()
            specifiedStyleAttributes = str(specified_style).split(';') #array
            specifiedStyleAttributesDict = {}
            if len(specified_style) > 0: #Style "specified_style" might contain just empty '' string which will lead to failing dict update
                for specifiedStyleAttribute in specifiedStyleAttributes:
                    specifiedStyleAttributesDict.update({'{}'.format(specifiedStyleAttribute.split(':')[0]): specifiedStyleAttribute.split(':')[1]})
           
            #three options to handle dedicated attributes (attributes not in the "style" attribute, but separate):
            # - just delete all dedicated properties
            # - merge dedicated properties, and prefer them over those from specified style
            # - merge dedicated properties, but prefer properties from specified style
            dedicatedStyleAttributesDict = {}
            popDict = []
            # there are opacity (of group/parent), fill-opacity and stroke-opacity
            popDict.extend(['opacity', 'stroke', 'stroke-opacity', 'stroke-width', 'stroke-dasharray', 'stroke-dashoffset', 'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit', 'fill', 'fill-opacity'])
            for popItem in popDict:
                if node.attrib.has_key(str(popItem)):
                    dedicatedStyleAttributesDict.update({'{}'.format(popItem): node.get(popItem)})
                    node.attrib.pop(popItem)
 
            #inkex.utils.debug("specifiedStyleAttributesDict = " + str(specifiedStyleAttributesDict))
            #inkex.utils.debug("dedicatedStyleAttributesDict = " + str(dedicatedStyleAttributesDict))
 
            if self.options.dedicated_style_attributes == 'prefer_dedicated':
                specifiedStyleAttributesDict.update(dedicatedStyleAttributesDict)
                node.set('style', specifiedStyleAttributesDict)
            elif self.options.dedicated_style_attributes == 'prefer_specified':
                dedicatedStyleAttributesDict.update(specifiedStyleAttributesDict)
                node.set('style', dedicatedStyleAttributesDict)
            elif self.options.dedicated_style_attributes == 'ignore':
                pass

            # now parse the style with possibly merged dedicated attributes modded style attribute (dedicatedStyleAttributes)
            if node.attrib.has_key('style') is False:
                node.set('style', 'stroke:#000000;') #we add basic stroke color black. We cannot set to empty value or just ";" because it will not update properly
            style = node.get('style')
            
            #add missing style attributes if required
            if style.endswith(';') is False:
                style += ';'
            if re.search('(;|^)stroke:(.*?)(;|$)', style) is None: #if "stroke" is None, add one. We need to distinguish because there's also attribute "-inkscape-stroke" that's why we check starting with ^ or ;
                style += 'stroke:none;'
            if self.options.stroke_width_override is True and "stroke-width:" not in style:
                style += 'stroke-width:{:1.4f};'.format(self.svg.unittouu(str(self.options.stroke_width) + self.options.stroke_width_units))
            if self.options.stroke_opacity_override is True and "stroke-opacity:" not in style:
                style += 'stroke-opacity:{:1.1f};'.format(self.options.stroke_opacity / 100)

            if self.options.apply_hairlines is True:
                if "vector-effect:non-scaling-stroke" not in style:
                    style += 'vector-effect:non-scaling-stroke;'
                if "-inkscape-stroke:hairline" not in style:
                    style += '-inkscape-stroke:hairline;'
               
            if re.search('fill:(.*?)(;|$)', style) is None: #if "fill" is None, add one.
                style += 'fill:none;'
                                   
            #then parse the content and check what we need to adjust   
            declarations = style.split(';')
            for i, decl in enumerate(declarations):
                parts = decl.split(':', 2)
                if len(parts) == 2:
                    (prop, val) = parts
                    prop = prop.strip().lower()
                    if prop == 'stroke-width' and self.options.stroke_width_override is True:
                        new_val = self.svg.unittouu(str(self.options.stroke_width) + self.options.stroke_width_units)
                        declarations[i] = prop + ':{:1.4f}'.format(new_val)
                    if prop == 'stroke-opacity' and self.options.stroke_opacity_override is True:
                        new_val = self.options.stroke_opacity / 100
                        declarations[i] = prop + ':{:1.1f}'.format(new_val)
                    if self.options.reset_opacity is True:
                        if prop == 'opacity':
                            declarations[i] = ''             
                    if self.options.reset_stroke_attributes is True:
                        if prop == 'stroke-dasharray':
                            declarations[i] = ''
                        if prop == 'stroke-dashoffset':
                            declarations[i] = ''
                        if prop == 'stroke-linejoin':
                            declarations[i] = ''
                        if prop == 'stroke-linecap':
                            declarations[i] = ''
                        if prop == 'stroke-miterlimit':
                            declarations[i] = ''
                    if self.options.apply_black_strokes is True:
                        if prop == 'stroke':
                            if val == 'none':
                                new_val = '#000000'
                                declarations[i] = prop + ':' + new_val
                    if self.options.harmonize_colors is True:
                        if prop == 'fill':
                            if re.search('fill:none(.*?)(;|$)', style) is None:
                                rgb = inkex.Color(val).to_rgb()    
                                closest_color = self.closestColor(self.roundUpColors, [rgb[0], rgb[1], rgb[2]])
                                rgbNew = inkex.Color((
                                    int(closest_color[0][0]), 
                                    int(closest_color[0][1]), 
                                    int(closest_color[0][2])
                                    ), space='rgb')
                                declarations[i] = prop + ':' + str(inkex.Color(rgbNew).to_named())
                        if prop == 'stroke':
                            if re.search('stroke:none(.*?)(;|$)', style) is None:
                                rgb = inkex.Color(val).to_rgb()    
                                closest_color = self.closestColor(self.roundUpColors, [rgb[0], rgb[1], rgb[2]])
                                rgbNew = inkex.Color((
                                    int(closest_color[0][0]), 
                                    int(closest_color[0][1]), 
                                    int(closest_color[0][2])
                                    ), space='rgb')
                                declarations[i] = prop + ':' + str(inkex.Color(rgbNew).to_named())  
                    if self.options.reset_fill_attributes is True:
                        if prop == 'fill':
                                new_val = 'none'
                                declarations[i] = prop + ':' + new_val
                        if prop == 'fill-opacity':
                                new_val = '1'
                                declarations[i] = prop + ':' + new_val
                    if self.options.apply_hairlines is False:
                        if prop == '-inkscape-stroke':
                            if val == 'hairline':
                                del declarations[i]
                        if prop == 'vector-effect':
                            if val == 'non-scaling-stroke':
                                del declarations[i]
            node.set('style', ';'.join(declarations))
            
        # if element is group we add it to collection to remove it's style after parsing all selected items
        elif isinstance(node, inkex.ShapeElement) and isinstance(node, inkex.Group):
            self.groups.append(node)

if __name__ == '__main__':
    CleanupStyles().run()
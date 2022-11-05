#!/usr/bin/env python3
#
# Copyright (C) 2005,2007 Aaron Spike, aaron@ekips.org
# Copyright (C) 2009 Alvin Penner, penner@vaxxine.com
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
"""
This extension converts a path into a dashed line using 'stroke-dasharray'
It is a modification of the file addelements.py
It is a modification of the file convert2dash.py
Extension to convert paths into dash-array line

Extension for InkScape 1.X
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 09.04.2021
Last patch: 28.10.2021
License: GNU GPL v3
"""

import copy
import re

import inkex
from inkex import bezier, CubicSuperPath, Group, PathElement
from inkex.bezier import csplength


class LinksCreator(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--path_types", default="closed_paths", help="Apply for closed paths, open paths or both")
        pars.add_argument("--creationunit", default="mm", help="Creation Units")
        pars.add_argument("--creationtype", default="entered_values", help="Creation")
        pars.add_argument("--link_count", type=int, default=1, help="Link count")
        pars.add_argument("--link_multiplicator", type=int, default=1, help="If set, we create a set of multiple gaps of same size next to the main gap")
        pars.add_argument("--length_link", type=float, default=1.000, help="Link length")
        pars.add_argument("--link_offset", type=float, default=0.000, help="Link offset (+/-)")
        pars.add_argument("--switch_pattern", type=inkex.Boolean, default=False, help="If enabled, we use gap length as dash length (switches the dasharray pattern")
        pars.add_argument("--weakening_mode", type=inkex.Boolean, default=False, help="If enabled, we colorize the swap links in #0000ff (blue) and disable the option 'Keep selected elements'")
        pars.add_argument("--custom_dasharray_value", default="", help="A list of separated lengths that specify the lengths of alternating dashes and gaps. Input only accepts numbers. It ignores percentages or other characters.")
        pars.add_argument("--custom_dashoffset_value", type=float, default=0.000, help="Link offset (+/-)")       
        pars.add_argument("--length_filter", type=inkex.Boolean, default=False, help="Enable path length filtering")
        pars.add_argument("--length_filter_value", type=float, default=0.000, help="Paths with length more than")
        pars.add_argument("--length_filter_unit", default="mm", help="Length filter unit")
        pars.add_argument("--keep_selected", type=inkex.Boolean, default=False, help="Keep selected elements")
        pars.add_argument("--no_convert", type=inkex.Boolean, default=False, help="Do not create segments (cosmetic gaps only)")
        pars.add_argument("--breakapart", type=inkex.Boolean, default=True, help="Performs CTRL + SHIFT + K to break the new output path into it's parts. Recommended to enable because default break apart of Inkscape might produce pointy paths.")
        pars.add_argument("--show_info", type=inkex.Boolean, default=False, help="Print some length and pattern information")
        pars.add_argument("--skip_errors", type=inkex.Boolean, default=False, help="Skip errors")

    def breakContours(self, element, breakelements = None): #this does the same as "CTRL + SHIFT + K"
        if breakelements == None:
            breakelements = []
        if element.tag == inkex.addNS('path','svg'):
            parent = element.getparent()
            idx = parent.index(element)
            idSuffix = 0  
            raw = element.path.to_arrays()
            subPaths, prev = [], 0
            for i in range(len(raw)): # Breaks compound paths into simple paths
                if raw[i][0] == 'M' and i != 0:
                    subPaths.append(raw[prev:i])
                    prev = i
            subPaths.append(raw[prev:])
            for subpath in subPaths:
                replacedelement = copy.copy(element)
                oldId = replacedelement.get('id')
                csp = CubicSuperPath(subpath)
                if len(subpath) > 1 and csp[0][0] != csp[0][1]: #avoids pointy paths like M "31.4794 57.6024 Z"
                    replacedelement.set('d', csp)
                    if len(subPaths) == 1:
                        replacedelement.set('id', oldId)
                    else:
                        replacedelement.set('id', oldId + str(idSuffix))
                        idSuffix += 1
                    parent.insert(idx, replacedelement)
                    breakelements.append(replacedelement)
            parent.remove(element)
        for child in element.getchildren():
            self.breakContours(child, breakelements)
        return breakelements

    def effect(self):
        def createLinks(element):   
            elementParent = element.getparent()
            path = element.path.to_arrays() #to_arrays() is deprecated. How to make more modern?
            pathIsClosed = False
            if path[-1][0] == 'Z' or \
                (path[-1][0] == 'L' and path[0][1] == path[-1][1]) or \
                (path[-1][0] == 'C' and path[0][1] == [path[-1][1][-2], path[-1][1][-1]]) \
                :  #if first is last point the path is also closed. The "Z" command is not required
                pathIsClosed = True
                
            if self.options.path_types == 'open_paths' and pathIsClosed is True:
                return #skip this loop iteration
            elif self.options.path_types == 'closed_paths' and pathIsClosed is False:
                return #skip this loop iteration
            elif self.options.path_types == 'both':
                pass
                         
            # if keeping is enabled we make of copy of the current element and insert it while modifying the original ones. We could also delete the original and modify a copy...
            if self.options.keep_selected is True and self.options.weakening_mode is False:
                parent = element.getparent()
                idx = parent.index(element)
                copyelement = copy.copy(element)
                parent.insert(idx, copyelement)

            # we measure the length of the path to calculate the required dash configuration
            csp = element.path.transform(element.composed_transform()).to_superpath()
            slengths, stotal = csplength(csp) #get segment lengths and total length of path in document's internal unit
           
            if self.options.length_filter is True:
                if stotal < self.svg.unittouu(str(self.options.length_filter_value) + self.options.length_filter_unit):
                    if self.options.show_info is True: self.msg("element " + element.get('id') + " is shorter than minimum allowed length of {:1.3f} {}. Path length is {:1.3f} {}".format(self.options.length_filter_value, self.options.length_filter_unit, stotal, self.options.creationunit))
                    return #skip this loop iteration

            if self.options.creationunit == "percent":
                length_link = (self.options.length_link / 100.0) * stotal
            else:
                length_link = self.svg.unittouu(str(self.options.length_link) + self.options.creationunit)

            dashes = [] #central dashes array
            
            if self.options.creationtype == "entered_values":
                dash_length = ((stotal - length_link * self.options.link_count) / self.options.link_count) - 2 * length_link * self.options.link_multiplicator
                dashes.append(dash_length)
                dashes.append(length_link)                  
                for i in range(0, self.options.link_multiplicator):
                    dashes.append(length_link) #stroke (=gap)
                    dashes.append(length_link) #gap
                    
                if self.options.switch_pattern is True:
                    dashes = dashes[::-1] #reverse the array
                    
                #validate dashes. May not be negative (dash or gap cannot be longer than the path itself). Otherwise Inkscape will freeze forever. Reason: rendering issue
                if any(dash <= 0.0 for dash in dashes) == True: 
                    if self.options.show_info is True: self.msg("element " + element.get('id') + ": Error! Dash array may not contain negative numbers: " + ' '.join(format(dash, "1.3f") for dash in dashes) + ". Path skipped. Maybe it's too short. Adjust your link count, multiplicator and length accordingly, or set to unit '%'")
                    return False if self.options.skip_errors is True else exit(1)
               
                if self.options.creationunit == "percent":
                    stroke_dashoffset = (self.options.link_offset / 100.0 * stotal) - length_link/2
                else:         
                    stroke_dashoffset = self.svg.unittouu(str(self.options.link_offset) + self.options.creationunit)
                    
                if self.options.switch_pattern is True:
                    stroke_dashoffset = stroke_dashoffset + ((self.options.link_multiplicator * 2) + 1)  * length_link

            if self.options.creationtype == "use_existing":
                if self.options.no_convert is True:
                    if self.options.show_info is True: self.msg("element " + element.get('id') + ": Nothing to do. Please select another creation method or disable cosmetic style output paths.")
                    return False if self.options.skip_errors is True else exit(1)
                stroke_dashoffset = 0
                style = element.style
                if 'stroke-dashoffset' in style:
                    stroke_dashoffset = style['stroke-dashoffset']
                try:
                    floats = [float(dash) for dash in re.findall(r"[+]?\d*\.\d+|\d+", style['stroke-dasharray'])] #allow only positive values
                    if len(floats) > 0:
                        dashes = floats #overwrite previously calculated values with custom input
                    else:
                        raise ValueError
                except:
                    if self.options.show_info is True: self.msg("element " + element.get('id') + ": No dash style to continue with.")
                    return False if self.options.skip_errors is True else exit(1)
                           
            if self.options.creationtype == "custom_dashpattern":
                stroke_dashoffset = self.options.custom_dashoffset_value
                try:
                    floats = [float(dash) for dash in re.findall(r"[+]?\d*\.\d+|\d+", self.options.custom_dasharray_value)] #allow only positive values
                    if len(floats) > 0:
                        dashes = floats #overwrite previously calculated values with custom input
                    else:
                        raise ValueError
                except:
                    if self.options.show_info is True: self.msg("element " + element.get('id') + ": Error in custom dasharray string (might be empty or does not contain any numbers).")
                    return False if self.options.skip_errors is True else exit(1)

            #assign stroke dasharray from entered values, existing style or custom dashpattern
            stroke_dasharray = ' '.join(format(dash, "1.3f") for dash in dashes)

            # check if the element has a style attribute. If not we create a blank one with a black stroke and without fill
            style = None
            default_fill = 'none'
            default_stroke = '#000000'
            default_stroke_width = str(self.svg.unittouu('1px'))
            if element.attrib.has_key('style'):
                element.style['stroke-dasharray'] = stroke_dasharray
                element.style['stroke-dashoffset'] = stroke_dashoffset
                #if has style attribute but the style attribute does not contain fill, stroke, stroke-width, stroke-dasharray or stroke-dashoffset yet
                if element.style.get('fill') is None: element.style['fill'] = default_fill
                if element.style.get('stroke') is None: element.style['stroke'] = default_stroke
                if element.style.get('stroke-width') is None: element.style['stroke-width'] = default_stroke_width
            else:
                element.style = 'fill:{};stroke:{};stroke-width:{};stroke-dasharray:{};stroke-dashoffset:{};'.format(
                    default_fill, default_stroke, default_stroke_width, stroke_dasharray, stroke_dashoffset)

            #if enabled, we override stroke color with blue (now, as the element definitely has a style)
            if self.options.weakening_mode is True and self.options.switch_pattern is True:
                element.style['stroke'] = "#0000ff"

            # Print some info about values
            if self.options.show_info is True:
                self.msg("element " + element.get('id') + ":")
                if self.options.creationunit == "percent":
                    self.msg(" * total path length = {:1.3f} {}".format(stotal, self.svg.unit)) #show length, converted in selected unit
                    self.msg(" * (calculated) offset: {:1.3f} %".format(stroke_dashoffset))
                    if self.options.creationtype == "entered_values":
                        self.msg(" * (calculated) gap length: {:1.3f} %".format(length_link))
                else:
                    self.msg(" * total path length = {:1.3f} {} ({:1.3f} {})".format(self.svg.uutounit(stotal, self.options.creationunit), self.options.creationunit, stotal, self.svg.unit)) #show length, converted in selected unit
                    self.msg(" * (calculated) offset: {:1.3f} {}".format(self.svg.uutounit(stroke_dashoffset, self.options.creationunit), self.options.creationunit))
                    if self.options.creationtype == "entered_values":
                        self.msg(" * (calculated) gap length: {:1.3f} {}".format(length_link, self.options.creationunit))
                if self.options.creationtype == "entered_values":        
                    self.msg(" * total gaps = {}".format(self.options.link_count))
                self.msg(" * (calculated) dash/gap pattern: {} ({})".format(stroke_dasharray, self.svg.unit))
     
            # Conversion step (split cosmetic path into real segments)    
            if self.options.no_convert is False:
                style = element.style #get the style again, but this time as style class    
                    
                gaps = []    
                new = []
                for sub in element.path.to_superpath():
                    idash = 0
                    dash = dashes[0]
                    length = float(stroke_dashoffset)
                    while dash < length:
                        length = length - dash
                        idash = (idash + 1) % len(dashes)
                        dash = dashes[idash]
                    new.append([sub[0][:]])
                    i = 1
                    while i < len(sub):
                        dash = dash - length
                        length = bezier.cspseglength(new[-1][-1], sub[i])
                        while dash < length:
                            new[-1][-1], nxt, sub[i] = bezier.cspbezsplitatlength(new[-1][-1], sub[i], dash/length)
                            if idash % 2: # create a gap
                                new.append([nxt[:]])
                            else:  # splice the curve
                                new[-1].append(nxt[:])
                            length = length - dash
                            idash = (idash + 1) % len(dashes)
                            dash = dashes[idash]
                        if idash % 2:
                            new.append([sub[i]])
                        else:
                            new[-1].append(sub[i])
                        i += 1  
                     
                #filter pointy subpaths
                final_new = []
                for sub in new:
                    if len(sub) > 1:
                        final_new.append(sub)
                        
                style.pop('stroke-dasharray')
                element.pop('sodipodi:type')
                element.path = CubicSuperPath(final_new)
                element.style = style
                
                # break apart the combined path to have multiple elements
                if self.options.breakapart is True:
                    breakOutputelements = None
                    breakOutputelements = self.breakContours(element, breakOutputelements)
                    breakApartGroup = elementParent.add(inkex.Group())
                    for breakOutputelement in breakOutputelements:
                        breakApartGroup.append(breakOutputelement)
                        #self.msg(replacedelement.get('id'))
                        #self.svg.selection.set(replacedelement.get('id')) #update selection to split paths segments (does not work, so commented out)
                        
        if len(self.svg.selected) > 0:
            for element in self.svg.selection.values():
                #at first we need to break down combined elements to single path, otherwise dasharray cannot properly be applied
                breakInputelements = None
                breakInputelements = self.breakContours(element, breakInputelements)
                for breakInputelement in breakInputelements:
                    createLinks(breakInputelement)
        else:
            self.msg('Please select some paths first.')
            return
        
if __name__ == '__main__':
    LinksCreator().run()
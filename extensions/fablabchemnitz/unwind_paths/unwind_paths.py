#!/usr/bin/env python3

"""
Extension for InkScape 1.0+

Paperfold is another flattener for triangle mesh files, heavily based on paperfoldmodels by Felix Scholz aka felixfeliz.

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 17.05.2021
Last patch: 18.05.2021
License: GNU GPL v3

For each selected path element, this extension creates an additional path element
consisting of horizontal line segments which are the same size as the original
path segments. Has options to extrude as a band (adds height; adds vertical lines and another horizontal path as bottom enclosure)

ToDos:
- option to render separate rectangle shapes
- option to duplicate vertical lines and then to group each 4 lines into one rect-shape like group
- option to colorize vertical line start + end
- option to add glue tabs/flaps
- option to add length text to each segment
- option to add segment/surface numbers
"""
import copy
import inkex
from inkex import Color, bezier, Path, CubicSuperPath, TextElement, Tspan
from inkex.bezier import csplength
from lxml import etree
import math
import random

class UnwindPaths(inkex.EffectExtension):
    
    #draw an SVG line segment between the given (raw) points
    def drawline(self, pathData, name, parent, line_style):
        line_attribs = {'style' : str(inkex.Style(line_style)),  inkex.addNS('label','inkscape') : name,  'd' : pathData}
        line = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )
        
    def add_arguments(self, pars):
        pars.add_argument('--tab')
        pars.add_argument('--keep_original', type=inkex.Boolean, default=False, help="If not selected, the original paths get deleted")
        pars.add_argument('--break_apart', type=inkex.Boolean, default=False, help="Split each path into single curve segments")
        pars.add_argument('--break_only', type=inkex.Boolean, default=False, help="Only splits root paths into segments (no unwinding)")
        pars.add_argument('--colorize', type=inkex.Boolean, default=False, help="Colorize original paths and glue pairs")
        pars.add_argument('--color_increment', type=int, default=10000, help="For each segment we count up n colors. Does not apply if 'Randomize colors' is enabled.")
        pars.add_argument('--randomize_colors', type=inkex.Boolean, default=False, help="Randomize colors")
        pars.add_argument('--number', type=inkex.Boolean, default=False, help="Number segments")
        pars.add_argument('--unit', default="mm")
        pars.add_argument('--thickness_offset', type=float, default=0.000, help="Allows to add/subtract extra offset length for each curve segment.")
        pars.add_argument('--extrude', type=inkex.Boolean, default=False)
        pars.add_argument('--extrude_height', type=float, default=10.000)
        pars.add_argument('--render_vertical_dividers', type=inkex.Boolean, default=False)
        pars.add_argument('--render_with_dashes', type=inkex.Boolean, default=False)
        
    #if multiple curves are inside the path we split (break apart)
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
            if len(subPaths) > 1:
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
            else:
                breakelements.append(element)
            for child in element.getchildren():
                self.breakContours(child, breakelements)
        return breakelements

    def rgb(self, minimum, maximum, value):
        minimum, maximum = float(minimum), float(maximum)
        ratio = 2 * (value-minimum) / (maximum - minimum)
        b = int(max(0, 255 * (1 - ratio)))
        r = int(max(0, 255 * (ratio - 1)))
        g = 255 - b - r
        return r, g, b

    def effect(self):
        shifting = self.svg.unittouu(str(self.options.extrude_height) + self.options.unit)
        to = self.svg.unittouu(str(self.options.thickness_offset) + self.options.unit)

        #some mode handling
        if self.options.colorize is True or self.options.number:
            self.options.break_apart = True #required to make it work

        if len(self.svg.selected) > 0:
            #we break apart combined paths to get distinct contours
            breakApartPaths = []
            for element in self.svg.selection.filter(inkex.PathElement).values():
                breakApartPaths.append(self.breakContours(element))
                
            for breakApartPath in breakApartPaths:
                for element in breakApartPath:
                    elemGroup = self.svg.get_current_layer().add(inkex.Group(id="unwinding-" + element.get('id')))
        
                    #beginning point of the unwind band:
                    bbox = element.bounding_box() #shift the element to the bottom of the element
                    xmin = bbox.left
                    ymax = bbox.bottom + bbox.height * 0.1 #10% additional spacing
           
                    csp = element.path.to_superpath()
                    subCount = len(element.path)
                    
                    #generate random colors; used to identify glue tab pairs
                    if self.options.colorize is True:
                        colorSet = []
                        if self.options.randomize_colors is True:
                            while len(colorSet) < subCount - 1:
                                    r = lambda: random.randint(0,255)
                                    newColor = '#%02X%02X%02X' % (r(),r(),r())
                                    if newColor not in colorSet:
                                        colorSet.append(newColor)
                        else:
                            for i in range(subCount):
                                colorSet.append(Color(self.rgb(0, i+self.options.color_increment, 1*i)))        
                    
                    slengths, stotal = csplength(csp) #get segment lengths and total length of path in document's internal unit
                    #self.msg(stotal) #total length of the path
                    
                    for sub in csp:
                        #generate new horizontal line data by measuring each segment
                        new = []
                        new.append([sub[0]])
                        i = 1
                        topPathData = "m {:0.6f},{:0.6f} ".format(xmin, ymax)
                        bottomPathData = "m {:0.6f},{:0.6f} ".format(xmin, ymax + shifting)
                        lengths = []
    
                        if self.options.break_apart is True:
                            topLineGroup = self.svg.get_current_layer().add(inkex.Group(id="hline-top-" + element.get('id')))
                            bottomLineGroup = self.svg.get_current_layer().add(inkex.Group(id="hline-bottom-" + element.get('id')))
                            elemGroup.append(topLineGroup)      
                            elemGroup.append(bottomLineGroup)
                            
                            newOriginalPathGroup = self.svg.get_current_layer().add(inkex.Group(id="new-original-" + element.get('id')))
                            self.svg.get_current_layer().append(newOriginalPathGroup) #we want this to be one level above unwound stuff
                    
                        if self.options.extrude is True:
                            vlinesGroup = self.svg.get_current_layer().add(inkex.Group(id="vlines-" + element.get('id')))
                            elemGroup.append(vlinesGroup)
                                               
                        if self.options.break_only is False:
                            while i <= len(sub) - 1:
                                stroke_color = '#000000'
                                if self.options.colorize is True and self.options.break_apart is True:
                                    stroke_color =colorSet[i-1]
        
                                horizontal_line_style = {'stroke':stroke_color,'stroke-width':self.svg.unittouu('1px'),'fill':'none'}
        
                                length = bezier.cspseglength(new[-1][-1], sub[i]) + to #sub path length
                                #if length <= 0:
                                #   inkex.utils.debug("Warning: path id={}, segment={} might overlap with previous and/or next segment. Maybe check for negative thickness offset.".format(element.get('id'), i))
                                segment = "h {:0.6f} ".format(length)
                                topPathData += segment
                                bottomPathData += segment
                                new[-1].append(sub[i]) #important line!
                                          
                                mid_coord_x = xmin + sum([length for length in lengths]) + length/2
                                font_size = 5
                                font_y_offset = font_size + 1
                                
                                if self.options.number is True:
                                    text = topLineGroup.add(TextElement(id=element.get('id') + "_TextNr{}".format(i)))
                                    text.set("x", "{:0.6f}".format(mid_coord_x))
                                    text.set("y", "{:0.6f}".format(ymax - font_y_offset))
                                    text.set("font-size", "{:0.6f}".format(font_size))
                                    text.set("style", "text-anchor:middle;text-align:center;fill:{}".format(stroke_color))
                              
                                    tspan = text.add(Tspan(id=element.get('id') + "_TSpanNr{}".format(i)))
                                    tspan.set("x", "{:0.6f}".format(mid_coord_x))
                                    if length <= 0:
                                        tspan.set("y", "{:0.6f}".format(ymax - font_y_offset - i))
                                    else:
                                        tspan.set("y", "{:0.6f}".format(ymax - font_y_offset))        
                                    tspan.text = str(i)
                                
                                if self.options.break_apart is True:
                                    self.drawline("m {:0.6f},{:0.6f} ".format(xmin + sum([length for length in lengths]), ymax) + segment, 
                                                  "segmented-top-{}-{}".format(element.get('id'), i), topLineGroup, horizontal_line_style)
                                    if length <= 0:
                                        self.drawline("m {:0.6f},{:0.6f} ".format(mid_coord_x, ymax) + "v {} ".format(-5-i), 
                                                      "segmented-top-overlap-{}-{}".format(element.get('id'), i), topLineGroup, horizontal_line_style)        
                                    if self.options.extrude is True:
                                        self.drawline("m {:0.6f},{:0.6f} ".format(xmin + sum([length for length in lengths]), ymax + shifting) + segment, 
                                                      "segmented-bottom-{}-{}".format(element.get('id'), i), bottomLineGroup, horizontal_line_style) 
                                lengths.append(length) 
                                i += 1
                         
                            if self.options.break_apart is False:  
                                self.drawline(topPathData, "combined-top-{0}".format(element.get('id')), elemGroup, horizontal_line_style)
                                if self.options.extrude is True:
                                    self.drawline(bottomPathData, "combined-bottom-{0}".format(element.get('id')), elemGroup, horizontal_line_style)
        
                            #draw as much vertical lines as segments in bezier + start + end vertical line
                            vertical_end_lines_style = {'stroke':'#000000','stroke-width':self.svg.unittouu('1px'),'fill':'none'}
                            if self.options.extrude is True:
                                #render start line
                                self.drawline("m {:0.6f},{:0.6f} v {:0.6f}".format(xmin, ymax, shifting),"vline-{}-start".format(element.get('id')), vlinesGroup, vertical_end_lines_style)
                                #render divider lines
                                if self.options.render_vertical_dividers is True:
                                    vertical_mid_lines_style = {'stroke':'#000000','stroke-width':self.svg.unittouu('1px'),'fill':'none'}
                                    if self.options.render_with_dashes is True:
                                        vertical_mid_lines_style = {'stroke':'#000000','stroke-width':self.svg.unittouu('1px'),"stroke-dasharray":"2 2", 'fill':'none'}
                                    x = 0
                                    for n in range(0, i-2):           
                                        x += lengths[n]
                                        self.drawline("m {:0.6f},{:0.6f} v {:0.6f}".format(xmin + x, ymax, shifting),"vline-{}-{}".format(element.get('id'), n + 1), vlinesGroup, vertical_mid_lines_style)
                                #render end line
                                self.drawline("m {:0.6f},{:0.6f} v {:0.6f}".format(xmin + sum([length for length in lengths]), ymax, shifting),"vline-{}-end".format(element.get('id')), vlinesGroup, vertical_end_lines_style)
    
                    if self.options.break_apart is True:
                        # Split (already broken apart) paths into detached segments
                        raw = Path(element.get("d")).to_arrays() #returns Uppercase Command Letters; does not include H, V
                        for i in range(len(raw)):
                            if i > 0:
                                                 
                                if raw[i-1][0] in ("M", "L"):
                                    startPoint = "M {},{}".format(raw[i-1][1][0], raw[i-1][1][1])
                                elif raw[i-1][0] == 'C':
                                    startPoint = "M {},{}".format(raw[i-1][1][-2], raw[i-1][1][-1])
                                else:
                                    inkex.utils.debug("Start point error. Unknown command!")
                                    
                                if raw[i][0] in ("M", "L"):
                                    segment = " {},{}".format(raw[i][1][0], raw[i][1][1])
                                elif raw[i][0] == 'C':
                                    segment = "{} {}".format(raw[i][0], ''.join(str(raw[i][1]))[1:-1])
                                elif raw[i][0] == 'Z':
                                    segment = "{},{}".format(raw[0][1][0], raw[0][1][1])
                                else:
                                    inkex.utils.debug("Segment error. Unknown command!")
            
                                d = str(Path("{} {}".format(startPoint, segment)))
                       
                                stroke_color = '#000000'
                                if self.options.colorize is True:
                                    stroke_color =colorSet[i-1]
                                new_original_line_style = {'stroke':stroke_color,'stroke-width':self.svg.unittouu('1px'),'fill':'none'}
                                self.drawline(d, "segmented-" + element.get('id'), newOriginalPathGroup, new_original_line_style)
    
                    if self.options.keep_original is False:
                        element.delete()

        else:
            self.msg('Please select some paths first.')
            return

if __name__ == '__main__':
    UnwindPaths().run()

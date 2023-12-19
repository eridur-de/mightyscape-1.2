#!/usr/bin/env python3
'''
This extension allows you to draw crop, registration and other
printing marks in Inkscape.

Authors:
  Nicolas Dufour - Association Inkscape-fr
  Aurelio A. Heckert <aurium(a)gmail.com>

Copyright (C) 2008 Authors

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

from subprocess import Popen, PIPE, STDOUT
import math
import inkex
from lxml import etree

class PrintingMarksDotted(inkex.EffectExtension):

    # Default parameters
    stroke_width = 0.25

    def add_arguments(self, pars):
        pars.add_argument("--where_to_crop", default=True, help="Apply crop marks to...")
        pars.add_argument("--crop_marks",  type=inkex.Boolean, default=True, help="Draw crop Marks?")          
        pars.add_argument("--dotted_crop_marks", type=inkex.Boolean, default=True, help="Draw dotted crop Marks?")   
        pars.add_argument("--bleed_marks", type=inkex.Boolean, default=False, help="Draw Bleed Marks?")         
        pars.add_argument("--registration_marks", type=inkex.Boolean, default=False, help="Draw Registration Marks?")  
        pars.add_argument("--star_target", type=inkex.Boolean, default=False, help="Draw Star Target?")         
        pars.add_argument("--colour_bars",  type=inkex.Boolean, default=False, help="Draw Colour Bars?")         
        pars.add_argument("--page_info", type=inkex.Boolean, default=False, help="Draw Page Information?")    
        pars.add_argument("--unit",default="px", help="Draw measurment")
        pars.add_argument("--crop_offset", type=float, default=0, help="Offset")
        pars.add_argument("--bleed_top", type=float, default=0, help="Bleed Top Size")
        pars.add_argument("--bleed_bottom", type=float, default=0, help="Bleed Bottom Size")
        pars.add_argument("--bleed_left", type=float, default=0, help="Bleed Left Size")
        pars.add_argument("--bleed_right",type=float, default=0, help="Bleed Right Size")
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def addMarker(self):
        svg = self.document.getroot()
        xpathStr = '//marker[@id="scissorsCroper"]'
        maskElement = svg.xpath(xpathStr, namespaces=inkex.NSS)
        if maskElement == []:
            xpathStr = '//svg:defs'
            defs = svg.xpath(xpathStr, namespaces=inkex.NSS)
            line_attribs = {'markerWidth': "8.2212915",
                            'markerHeight': "4.8983894",
                            'orient': "auto",
                            'id':"scissorsCroper"}
            markerElement = etree.SubElement(defs[0],inkex.addNS('marker','svg'), line_attribs)
            line_attribs = {'style': "fill:#000000;stroke:#ffffff;stroke-width:0.2;stroke-miterlimit:4;stroke-opacity:1",
                            'id': "scissorsCroperPath",
                            'd': "m -3.09375,-2.59375 c -0.2875213,-0.019086 -0.5530997,0.080418 -0.78125,0.25 -0.2281503,0.1695818 -0.4212781,0.4427198 -0.4375,0.75 -0.014236,0.2696628 0.032949,0.4281517 0.09375,0.53125 0.011692,0.019827 0.022314,0.017924 0.03125,0.03125 -0.074992,0.019409 -0.1886388,0.0360237 -0.34375,0.0625 -0.3217609,0.0549221 -0.7596575,0.13825127 -1.21875,0.375 l -3.03125,-1.125 c -0.2710413,-0.1042898 -0.5662791,-0.1829987 -0.875,-0.15625 -0.3087209,0.026749 -0.621076,0.1687088 -0.84375,0.4375 a 0.20792008,0.20792008 0 0 0 -0.03125,0.03125 0.20792008,0.20792008 0 0 0 -0.03125,0.0625 0.20792008,0.20792008 0 0 0 0,0.0625 0.20792008,0.20792008 0 0 0 0.03125,0.0625 0.20792008,0.20792008 0 0 0 0.03125,0.03125 0.20792008,0.20792008 0 0 0 0.09375,0.0625 l 2.9375,1.15625 -2.96875,1.125 a 0.20792008,0.20792008 0 0 0 -0.09375,0.0625 0.20792008,0.20792008 0 0 0 -0.03125,0.03125 0.20792008,0.20792008 0 0 0 -0.03125,0.0625 0.20792008,0.20792008 0 0 0 0,0.0625 0.20792008,0.20792008 0 0 0 0.03125,0.0625 0.20792008,0.20792008 0 0 0 0.03125,0.03125 C -10.094168,1.9539272 -9.4699318,1.9749423 -9,1.84375 L -5.71875,0.6875 c 0.481754,0.20541523 0.912658,0.3186677 1.1875,0.375 0.1483249,0.030401 0.2392409,0.045912 0.3125,0.0625 0.03663,0.00829 0.024599,-0.00324 0.03125,0 -0.0079,0.02335 -0.010635,0.041757 -0.03125,0.09375 -0.053917,0.1359822 -0.1506131,0.3500538 -0.09375,0.625 0.074929,0.3622982 0.3561361,0.6217769 0.65625,0.75 0.3001139,0.1282231 0.6300895,0.1440646 0.9375,0.03125 0.6444683,-0.175589 0.9014775,-0.9349259 0.625,-1.5 C -2.2324842,0.83910622 -2.4880622,0.66240891 -2.75,0.5625 -3.0119378,0.46259109 -3.2717529,0.42256233 -3.53125,0.4375 c -0.2805605,0.0161501 -0.5796777,0.0351178 -0.8125,-0.03125 -0.1944918,-0.0554414 -0.3308104,-0.18103045 -0.46875,-0.375 0.1925418,-0.25215792 0.4169804,-0.350782 0.71875,-0.375 0.3394341,-0.0272407 0.7247815,0.0434012 1.0625,0 0.010025,-6.5986e-4 0.021283,9.2632e-4 0.03125,0 0.5937358,-0.0551819 1.1050788,-0.57908524 1.0625,-1.1875 -0.00523,-0.6217326 -0.5853909,-1.0659264 -1.15625,-1.0625 z M -2.9375,-1.875 c 0.1401777,0.04894 0.2268596,0.139783 0.25,0.25 a 0.20792008,0.20792008 0 0 0 0.03125,0.03125 c 0.046997,0.1597651 -0.018243,0.2935457 -0.15625,0.40625 -0.1380068,0.1127043 -0.3531142,0.176154 -0.5,0.125 -0.1652738,-0.046651 -0.2408416,-0.1796945 -0.25,-0.34375 -0.00916,-0.1640555 0.046643,-0.3414062 0.21875,-0.4375 0.104863,-0.058549 0.2664752,-0.08005 0.40625,-0.03125 z m -0.21875,3.03125 c 0.2392165,0.047351 0.4697735,0.2941069 0.4375,0.53125 -0.010405,0.1211995 -0.066062,0.2235316 -0.1875,0.28125 C -3.0276883,2.0264684 -3.2009829,2.0387215 -3.3125,2 A 0.20792008,0.20792008 0 0 0 -3.34375,2 C -3.6474031,1.9320987 -3.710744,1.2999504 -3.40625,1.1875 a 0.20792008,0.20792008 0 0 0 0.03125,0 c 0.072689,-0.036572 0.1390112,-0.047034 0.21875,-0.03125 z"}
            pathElement = etree.SubElement(markerElement, inkex.addNS('path','svg'), line_attribs)

    def draw_crop_line(self, x1, y1, x2, y2, name, parent):
        if self.options.dotted_crop_marks == True:
            self.addMarker()
            style = { 'stroke': '#FFFFFF', 'stroke-width': str(self.stroke_width),
                      'fill': 'none'}
        else:
            style = { 'stroke': '#000000', 'stroke-width': str(self.stroke_width),
                  'fill': 'none'}
        line_attribs = {'style': str(inkex.Style(style)),
                        'id': name,
                        'd': 'M '+str(x1)+','+str(y1)+' L '+str(x2)+','+str(y2)}
        etree.SubElement(parent, 'path', line_attribs)
        if self.options.dotted_crop_marks == True:
            style = { 'stroke': '#000000', 'stroke-width': str(self.stroke_width),
                      'fill': 'none' , 'marker-end':'url(#scissorsCroper)',
                      'stroke-dasharray' :'0.5,0.25', 'stroke-miterlimit':"4"}
            
            line_attribs = {'style': str(inkex.Style(style)),
                            'id': name + "_dotted",
                            'd': 'M '+str(x1)+','+str(y1)+' L '+str(x2)+','+str(y2)}
            etree.SubElement(parent, 'path', line_attribs)

    def draw_bleed_line(self, x1, y1, x2, y2, name, parent):
        style = { 'stroke': '#000000', 'stroke-width': str(self.stroke_width),
                  'fill': 'none',
                  'stroke-miterlimit': '4', 'stroke-dasharray': '4, 2, 1, 2',
                  'stroke-dashoffset': '0' }
        line_attribs = {'style': str(inkex.Style(style)),
                        'id': name,
                        'd': 'M '+str(x1)+','+str(y1)+' L '+str(x2)+','+str(y2)}
        etree.SubElement(parent, 'path', line_attribs)

    def draw_reg_circles(self, cx, cy, r, name, colours, parent):
        for i in range(len(colours)):
            style = {'stroke':colours[i], 'stroke-width':str(r / len(colours)),
                     'fill':'none'}
            circle_attribs = {'style':str(inkex.Style(style)),
                              inkex.addNS('label','inkscape'):name,
                              'cx':str(cx), 'cy':str(cy),
                              'r':str((r / len(colours)) * (i + 0.5))}
            etree.SubElement(parent, inkex.addNS('circle','svg'),
                                   circle_attribs)

    def draw_registration_marks(self, cx, cy, rotate, name, parent):
        colours = ['#000000','#00ffff','#ff00ff','#ffff00','#000000']
        g = etree.SubElement(parent, 'g', { 'id': name })
        for i in range(len(colours)):
            style = {'fill':colours[i], 'fill-opacity':'1', 'stroke':'none'}
            r = (self.mark_size/2)
            step = r
            stroke = r / len(colours)
            regoffset = stroke * i
            regmark_attribs = {'style': str(inkex.Style(style)),
                               'd': 'm' +\
                               ' '+str(-regoffset)+','+str(r)  +\
                               ' '+str(-stroke)   +',0'        +\
                               ' '+str(step)      +','+str(-r) +\
                               ' '+str(-step)     +','+str(-r) +\
                               ' '+str(stroke)    +',0'        +\
                               ' '+str(step)      +','+str(r)  +\
                               ' '+str(-step)     +','+str(r)  +\
                               ' z',
                               'transform': 'translate('+str(cx)+','+str(cy)+ \
                                            ') rotate('+str(rotate)+')'}
            etree.SubElement(g, 'path', regmark_attribs)

    def draw_star_target(self, cx, cy, name, parent):
        r = (self.mark_size/2)
        style = {'fill':'#000 device-cmyk(1,1,1,1)', 'fill-opacity':'1', 'stroke':'none'}
        d = ' M 0,0'
        i = 0
        while i < ( 2 * math.pi ):
            i += math.pi / 16
            d += ' L 0,0 ' +\
                 ' L '+ str(math.sin(i)*r) +','+ str(math.cos(i)*r) +\
                 ' L '+ str(math.sin(i+0.09)*r) +','+ str(math.cos(i+0.09)*r)
        regmark_attribs = {'style':str(inkex.Style(style)),
                          inkex.addNS('label','inkscape'):name,
                          'transform':'translate('+str(cx)+','+str(cy)+')',
                          'd':d}
        etree.SubElement(parent, inkex.addNS('path','svg'),
                               regmark_attribs)

    def draw_coluor_bars(self, cx, cy, rotate, name, parent):
        g = etree.SubElement(parent, 'g', {
                'id':name,
                'transform':'translate('+str(cx)+','+str(cy)+\
                            ') rotate('+str(rotate)+')' })
        l = min( self.mark_size / 3, max(self.area_w,self.area_h) / 45 )
        for bar in [{'c':'*', 'stroke':'#000', 'x':0,        'y':-(l+1)},
                    {'c':'r', 'stroke':'#0FF', 'x':0,        'y':0},
                    {'c':'g', 'stroke':'#F0F', 'x':(l*11)+1, 'y':-(l+1)},
                    {'c':'b', 'stroke':'#FF0', 'x':(l*11)+1, 'y':0}
                   ]:
            i = 0
            while i <= 1:
                cr = '255'
                cg = '255'
                cb = '255'
                if bar['c'] == 'r' or bar['c'] == '*' : cr = str(255*i)
                if bar['c'] == 'g' or bar['c'] == '*' : cg = str(255*i)
                if bar['c'] == 'b' or bar['c'] == '*' : cb = str(255*i)
                r_att = {'fill':'rgb('+cr+','+cg+','+cb+')',
                         'stroke':bar['stroke'],
                         'stroke-width':'0.5',
                         'x':str((l*i*10)+bar['x']), 'y':str(bar['y']),
                         'width':str(l), 'height':str(l)}
                r = etree.SubElement(g, 'rect', r_att)
                i += 0.1

    def get_selection_area(self):
        scale = self.svg.unittouu('1px')    # convert to document units
        sel_area = {}
        min_x, min_y, max_x, max_y = False, False, False, False
        for id in self.options.ids:
            sel_area[id] = {}
            for att in [ "x", "y", "width", "height" ]:
                args = [ "inkscape", "-I", id, "--query-"+att, self.options.input_file ]
                sel_area[id][att] = scale* \
                    float(Popen(args, stdout=PIPE, stderr=PIPE).communicate()[0])
            current_min_x = sel_area[id]["x"]
            current_min_y = sel_area[id]["y"]
            current_max_x = sel_area[id]["x"] + \
                            sel_area[id]["width"]
            current_max_y = sel_area[id]["y"] + \
                            sel_area[id]["height"]
            if not min_x: min_x = current_min_x
            if not min_y: min_y = current_min_y
            if not max_x: max_x = current_max_x
            if not max_y: max_y = current_max_y
            if current_min_x < min_x: min_x = current_min_x
            if current_min_y < min_y: min_y = current_min_y
            if current_max_x > max_x: max_x = current_max_x
            if current_max_y > max_y: max_y = current_max_y
            #inkex.errormsg( '>> '+ id +
            #                ' min_x:'+ str(min_x) +
            #                ' min_y:'+ str(min_y) +
            #                ' max_x:'+ str(max_x) +
            #                ' max_y:'+ str(max_y) )
        self.area_x1 = min_x
        self.area_y1 = min_y
        self.area_x2 = max_x
        self.area_y2 = max_y
        self.area_w = max_x - min_x
        self.area_h = max_y - min_y

    def effect(self):
        self.mark_size = self.svg.unittouu('1cm')
        self.min_mark_margin = self.svg.unittouu('3mm')

        if self.options.where_to_crop == 'selection' :
            self.get_selection_area()
            #inkex.errormsg('Sory, the crop to selection is a TODO feature')
            #exit(1)
        else :
            svg = self.document.getroot()
            self.area_w  = self.svg.unittouu(svg.get('width'))
            self.area_h  = self.svg.unittouu(svg.attrib['height'])
            self.area_x1 = 0
            self.area_y1 = 0
            self.area_x2 = self.area_w
            self.area_y2 = self.area_h

        # Get SVG document dimensions
        # self.width must be replaced by self.area_x2. same to others.
        svg = self.document.getroot()
        #self.width  = width  = self.svg.unittouu(svg.get('width'))
        #self.height = height = self.svg.unittouu(svg.attrib['height'])

        # Convert parameters to user unit
        offset = self.svg.unittouu(str(self.options.crop_offset) + \
                                self.options.unit)
        bt = self.svg.unittouu(str(self.options.bleed_top)    + self.options.unit)
        bb = self.svg.unittouu(str(self.options.bleed_bottom) + self.options.unit)
        bl = self.svg.unittouu(str(self.options.bleed_left)   + self.options.unit)
        br = self.svg.unittouu(str(self.options.bleed_right)  + self.options.unit)
        # Bleed margin
        if bt < offset : bmt = 0
        else :           bmt = bt - offset
        if bb < offset : bmb = 0
        else :           bmb = bb - offset
        if bl < offset : bml = 0
        else :           bml = bl - offset
        if br < offset : bmr = 0
        else :           bmr = br - offset

        # Define the new document limits
        offset_left   = self.area_x1 - offset
        offset_right  = self.area_x2 + offset
        offset_top    = self.area_y1 - offset
        offset_bottom = self.area_y2 + offset

        # Get middle positions
        middle_vertical   = self.area_y1 + ( self.area_h / 2 )
        middle_horizontal = self.area_x1 + ( self.area_w / 2 )

        # Test if printing-marks layer existis
        layer = self.document.xpath(
                     '//*[@id="printing-marks" and @inkscape:groupmode="layer"]',
                     namespaces=inkex.NSS)
        if layer: svg.remove(layer[0]) # remove if it existis
        # Create a new layer
        layer = etree.SubElement(svg, 'g')
        layer.set('id', 'printing-marks')
        layer.set(inkex.addNS('label', 'inkscape'), 'Printing Marks')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        layer.set(inkex.addNS('insensitive', 'sodipodi'), 'true')

        # Crop Mark
        if self.options.crop_marks == True:
            # Create a group for Crop Mark
            g_attribs = {inkex.addNS('label','inkscape'):'CropMarks',
                                                    'id':'CropMarks'}
            g_crops = etree.SubElement(layer, 'g', g_attribs)

            # Top left Mark
            self.draw_crop_line(self.area_x1, offset_top,
                                self.area_x1, offset_top - self.mark_size,
                                'cropTL1', g_crops)
            self.draw_crop_line(offset_left, self.area_y1,
                                offset_left - self.mark_size, self.area_y1,
                                'cropTL2', g_crops)

            # Top right Mark
            self.draw_crop_line(self.area_x2, offset_top,
                                self.area_x2, offset_top - self.mark_size,
                                'cropTR1', g_crops)
            self.draw_crop_line(offset_right, self.area_y1,
                                offset_right + self.mark_size, self.area_y1,
                                'cropTR2', g_crops)

            # Bottom left Mark
            self.draw_crop_line(self.area_x1, offset_bottom,
                                self.area_x1, offset_bottom + self.mark_size,
                                'cropBL1', g_crops)
            self.draw_crop_line(offset_left, self.area_y2,
                                offset_left - self.mark_size, self.area_y2,
                                'cropBL2', g_crops)

            # Bottom right Mark
            self.draw_crop_line(self.area_x2, offset_bottom,
                                self.area_x2, offset_bottom + self.mark_size,
                                'cropBR1', g_crops)
            self.draw_crop_line(offset_right, self.area_y2,
                                offset_right + self.mark_size, self.area_y2,
                                'cropBR2', g_crops)

        # Bleed Mark
        if self.options.bleed_marks == True:
            # Create a group for Bleed Mark
            g_attribs = {inkex.addNS('label','inkscape'):'BleedMarks',
                                                    'id':'BleedMarks'}
            g_bleed = etree.SubElement(layer, 'g', g_attribs)

            # Top left Mark
            self.draw_bleed_line(self.area_x1 - bl, offset_top - bmt,
                                 self.area_x1 - bl, offset_top - bmt - self.mark_size,
                                 'bleedTL1', g_bleed)
            self.draw_bleed_line(offset_left - bml, self.area_y1 - bt,
                                 offset_left - bml - self.mark_size, self.area_y1 - bt,
                                 'bleedTL2', g_bleed)

            # Top right Mark
            self.draw_bleed_line(self.area_x2 + br, offset_top - bmt,
                                 self.area_x2 + br, offset_top - bmt - self.mark_size,
                                 'bleedTR1', g_bleed)
            self.draw_bleed_line(offset_right + bmr, self.area_y1 - bt,
                                 offset_right + bmr + self.mark_size, self.area_y1 - bt,
                                 'bleedTR2', g_bleed)

            # Bottom left Mark
            self.draw_bleed_line(self.area_x1 - bl, offset_bottom + bmb,
                                 self.area_x1 - bl, offset_bottom + bmb + self.mark_size,
                                 'bleedBL1', g_bleed)
            self.draw_bleed_line(offset_left - bml, self.area_y2 + bb,
                                 offset_left - bml - self.mark_size, self.area_y2 + bb,
                                 'bleedBL2', g_bleed)

            # Bottom right Mark
            self.draw_bleed_line(self.area_x2 + br, offset_bottom + bmb,
                                 self.area_x2 + br, offset_bottom + bmb + self.mark_size,
                                 'bleedBR1', g_bleed)
            self.draw_bleed_line(offset_right + bmr, self.area_y2 + bb,
                                 offset_right + bmr + self.mark_size, self.area_y2 + bb,
                                 'bleedBR2', g_bleed)

        # Registration Mark
        if self.options.registration_marks == True:
            # Create a group for Registration Mark
            g_attribs = {inkex.addNS('label','inkscape'):'RegistrationMarks',
                                                    'id':'RegistrationMarks'}
            g_center = etree.SubElement(layer, 'g', g_attribs)

            # Left Mark
            cx = max( bml + offset, self.min_mark_margin )
            self.draw_registration_marks(self.area_x1 - cx - (self.mark_size/2),
                                middle_vertical - self.mark_size*1.5,
                                '0', 'regMarkL', g_center)

            # Right Mark
            cx = max( bmr + offset, self.min_mark_margin )
            self.draw_registration_marks(self.area_x2 + cx + (self.mark_size/2),
                                middle_vertical - self.mark_size*1.5,
                                '180', 'regMarkR', g_center)

            # Top Mark
            cy = max( bmt + offset, self.min_mark_margin )
            self.draw_registration_marks(middle_horizontal,
                                self.area_y1 - cy - (self.mark_size/2),
                                '90', 'regMarkT', g_center)

            # Bottom Mark
            cy = max( bmb + offset, self.min_mark_margin )
            self.draw_registration_marks(middle_horizontal,
                                self.area_y2 + cy + (self.mark_size/2),
                                '-90', 'regMarkB', g_center)

        # Star Target
        if self.options.star_target == True:
            # Create a group for Star Target
            g_attribs = {inkex.addNS('label','inkscape'):'StarTarget',
                                                    'id':'StarTarget'}
            g_center = etree.SubElement(layer, 'g', g_attribs)

            if self.area_h < self.area_w :
                # Left Star
                cx = max( bml + offset, self.min_mark_margin )
                self.draw_star_target(self.area_x1 - cx - (self.mark_size/2),
                                      middle_vertical,
                                      'starTargetL', g_center)
                # Right Star
                cx = max( bmr + offset, self.min_mark_margin )
                self.draw_star_target(self.area_x2 + cx + (self.mark_size/2),
                                      middle_vertical,
                                      'starTargetR', g_center)
            else :
                # Top Star
                cy = max( bmt + offset, self.min_mark_margin )
                self.draw_star_target(middle_horizontal - self.mark_size*1.5,
                                      self.area_y1 - cy - (self.mark_size/2),
                                      'starTargetT', g_center)
                # Bottom Star
                cy = max( bmb + offset, self.min_mark_margin )
                self.draw_star_target(middle_horizontal - self.mark_size*1.5,
                                      self.area_y2 + cy + (self.mark_size/2),
                                      'starTargetB', g_center)


        # Colour Bars
        if self.options.colour_bars == True:
            # Create a group for Colour Bars
            g_attribs = {inkex.addNS('label','inkscape'):'ColourBars',
                                                    'id':'PrintingColourBars'}
            g_center = etree.SubElement(layer, 'g', g_attribs)

            if self.area_h > self.area_w :
                # Left Bars
                cx = max( bml + offset, self.min_mark_margin )
                self.draw_coluor_bars(self.area_x1 - cx - (self.mark_size/2),
                                      middle_vertical + self.mark_size,
                                      90,
                                      'PrintingColourBarsL', g_center)
                # Right Bars
                cx = max( bmr + offset, self.min_mark_margin )
                self.draw_coluor_bars(self.area_x2 + cx + (self.mark_size/2),
                                      middle_vertical + self.mark_size,
                                      90,
                                      'PrintingColourBarsR', g_center)
            else :
                # Top Bars
                cy = max( bmt + offset, self.min_mark_margin )
                self.draw_coluor_bars(middle_horizontal + self.mark_size,
                                      self.area_y1 - cy - (self.mark_size/2),
                                      0,
                                      'PrintingColourBarsT', g_center)
                # Bottom Bars
                cy = max( bmb + offset, self.min_mark_margin )
                self.draw_coluor_bars(middle_horizontal + self.mark_size,
                                      self.area_y2 + cy + (self.mark_size/2),
                                      0,
                                      'PrintingColourBarsB', g_center)


        # Page Information
        if self.options.page_info == True:
            # Create a group for Page Information
            g_attribs = {inkex.addNS('label','inkscape'):'PageInformation',
                                                    'id':'PageInformation'}
            g_pag_info = etree.SubElement(layer, 'g', g_attribs)
            y_margin = max( bmb + offset, self.min_mark_margin )
            txt_attribs = {
                    'style': 'font-size:12px;font-style:normal;font-weight:normal;fill:#000000;font-family:Bitstream Vera Sans,sans-serif;text-anchor:middle;text-align:center',
                    'x': str(middle_horizontal),
                    'y': str(self.area_y2+y_margin+self.mark_size+20)
                }
            txt = etree.SubElement(g_pag_info, 'text', txt_attribs)
            txt.text = 'Page size: ' +\
                       str(round(self.svg.uutounit(self.area_w,self.options.unit),2)) +\
                       'x' +\
                       str(round(self.svg.uutounit(self.area_h,self.options.unit),2)) +\
                       ' ' + self.options.unit


if __name__ == '__main__':
    PrintingMarksDotted().run()
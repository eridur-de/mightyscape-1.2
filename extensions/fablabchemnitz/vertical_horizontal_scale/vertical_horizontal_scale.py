#!/usr/bin/env python3
'''
Copyright (C)
2009 Sascha Poczihoski, sascha@junktech.de
Original author.

2013 Roger Jeurissen, roger@acfd-consultancy.nl
Added dangling labels and inside/outside scale features.

2015 Paul Rogalinski, pulsar@codewut.de
Adapted Inkscape 0.91 API changes.

2015 Bit Barrel Media, bitbarrelmedia -at- gmail dot com
-Changed UI and added the following features:
    Label offset. This will move the labels side to side and up/down.
    Option to use the center of a bounding box as the drawing reference.
    Ability to set line stroke width.
    Option to add a perpendicular line.
    Mathematical expression for the number format. For example, to divide the label number by 2, use "n/2".
    "Draw all labels" checkbox.
    Option to flip the label orientation.
    Support for "Draw every x lines" = 0 in order to remove lines.


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

TODO
    - fix bug: special chars in suffix

#for debugging:
message = "Debug: " + str(i) + "\n"
inkex.utils.debug(message)
'''

import math
import inkex
from lxml import etree

class VerticalHorizontalScale(inkex.EffectExtension):


    def add_arguments(self, pars):
        # Define string option "--what" with "-w" shortcut and default value "World".
        pars.add_argument('-f', '--scalefrom', type = int, default = '0', help = 'Number from...')
        pars.add_argument('-t', '--scaleto', type = int,default = '20', help = 'Number to...')
        pars.add_argument('--mathexpression', default = '', help = 'Math expression')
        pars.add_argument('-c', '--reverse', default = 'false', help = 'Reverse order:')
        pars.add_argument('-p', '--type', default = 'false', help = 'Type:')
        pars.add_argument('--radius', type = float, default = '100', help = 'Radius')
        pars.add_argument('--scaleradcount', type = float, default = '90', help = 'Circular count')
        pars.add_argument('--scaleradbegin', type = float, default = '0', help = 'Circular begin')
        pars.add_argument('--radmark', default = 'True', help = 'Mark origin')
        pars.add_argument('--insidetf', type = inkex.Boolean, default = 'False', help = 'Swap inside out')
        pars.add_argument('--ishorizontal',  default = 'False', help = 'Horizontal labels')
        pars.add_argument('--rotate', default = '0', help = 'Rotate:')
        pars.add_argument('-b', '--units_per_line', type = float, default = '100', help = 'Units per line')
        pars.add_argument('-g', '--labellinelength', type = float, default = '100', help = 'Label line - Length')
        pars.add_argument('-s', '--fontsize', type = float, default = '3', help = 'Font Size:')
        pars.add_argument('-i', '--suffix', default = '', help = 'Suffix:')
        pars.add_argument('--drawalllabels', type = inkex.Boolean, default = 'True', help = 'Draw all labels')
        pars.add_argument('--fliplabel', type = inkex.Boolean, default = 'False', help = 'Flip orientation')
        pars.add_argument('--labellinestrokewidth', type = float, default = '0.4', help = 'Label line - Stroke width')
        pars.add_argument('--longlinestrokewidth', type = float, default = '0.2', help = 'Long line - Stroke width')
        pars.add_argument('--shortlinestrokewidth', type = float, default = '0.2', help = 'Short line - Stroke width')
        pars.add_argument('--perplinestrokewidth', type = float, default = '0.2', help = 'Perpendicular line - Stroke width')
        
        # label offset
        pars.add_argument('-x', '--labeloffseth', type = float, default = '0', help = 'Label offset h:')
        pars.add_argument('-y', '--labeloffsetv', type = float, default = '-3.5', help = 'Label offset v:')
        
        # line spacing
        pars.add_argument('-m', '--mark0', type = int, default = '10', help = 'Label line - Draw every x lines:')
        pars.add_argument('-n', '--mark1', type = int, default = '5', help = 'Long line - Draw every x lines')
        pars.add_argument('-o', '--mark2', type = int, default = '1', help = 'Short line - Draw every x lines')
        
        # line length
        pars.add_argument('-w', '--mark1wid', type = int, default = '75', help = 'Long line: - Length (units): (\%):')
        pars.add_argument('-v', '--mark2wid', type = int, help = 'Short line: - Length (units): (\%):')
        pars.add_argument('-u', '--unit', default = 'mm', help = 'Unit:')
        pars.add_argument('--useref', type = inkex.Boolean, default = False, help = 'Reference is bounding box center')
        pars.add_argument('--tab', default = 'global', help = '')
        pars.add_argument("--perpline", type=inkex.Boolean, default=True, help="Perpendicular line")
        pars.add_argument('--perplineoffset', type = float, default = '0', help = 'Offset')


    def addLabel(self, n, x, y, group, fontsize, phi = 0.0):
        mathexpression = self.options.mathexpression
        fliplabel = self.options.fliplabel
        drawalllabels = self.options.drawalllabels
        labeloffseth = self.options.labeloffseth
        labeloffsetv = self.options.labeloffsetv
        scaletype = self.options.type
        insidetf = self.options.insidetf
        rotate = self.options.rotate
        unit = self.options.unit

        fontsize = self.svg.unittouu(str(fontsize)+unit)
        labeloffseth = self.svg.unittouu(str(labeloffseth)+unit)
        labeloffsetv = self.svg.unittouu(str(labeloffsetv)+unit)

        #swapped and horizontal
        if scaletype == 'straight' and insidetf and rotate=='90':
            labeloffsetv *= -1

        #swapped and vertical
        if scaletype == 'straight' and insidetf and rotate=='0':
            labeloffseth *= -1

        if drawalllabels==True:
            if fliplabel==True:
                phi += 180

            if scaletype == 'straight':
                x = float(x) + labeloffseth
                y = float(y) - labeloffsetv

            res = self.options.units_per_line
            pos = n*res + fontsize/2
            suffix = self.options.suffix
            text = etree.SubElement(group, inkex.addNS('text','svg'))

            number = n;
            try:
                number = eval(mathexpression)
            except (ValueError, SyntaxError, NameError):
                pass

            text.text = str(number)+suffix
            cosphi=math.cos(math.radians(phi))
            sinphi=math.sin(math.radians(phi))
            a1 = str(cosphi)
            a2 = str(-sinphi)
            a3 = str(sinphi)
            a4 = str(cosphi)
            a5 = str((1-cosphi)*x-sinphi*y)
            a6 = str(sinphi*x+(1-cosphi)*y)
            fs = str(fontsize)
            style = {'text-align' : 'center', 'text-anchor': 'middle', 'font-size': fs}
            text.set('style', str(inkex.Style(style)))
            text.set('transform', 'matrix({0},{1},{2},{3},{4},{5})'.format(a1,a2,a3,a4,a5,a6))
            text.set('x', str(float(x)))
            text.set('y', str(float(y)))
            group.append(text)


    def addLine(self, i, scalefrom, scaleto, group, grpLabel, type=2):
        reverse = self.options.reverse
        rotate = self.options.rotate
        unit = self.options.unit
        fontsize = self.options.fontsize
        res = self.options.units_per_line
        labellinestrokewidth = self.options.labellinestrokewidth
        longlinestrokewidth = self.options.longlinestrokewidth
        shortlinestrokewidth = self.options.shortlinestrokewidth
        insidetf = self.options.insidetf

        perplinestrokewidth = self.options.perplinestrokewidth
        perplineoffset = self.options.perplineoffset

        factor = 1
        if insidetf==True:
            factor = -1

        #vertical
        if rotate=='0':
            res *= -1

        label = False
        if reverse=='true':
            # Count absolute i for labeling
            counter = 0
            for n in range(scalefrom, i):
                counter += 1
            n = scaleto-counter-1
        else:
            n = i

        #label line
        if type==0:
            name = 'label line'
            stroke = self.svg.unittouu(str(labellinestrokewidth)+unit)
            line_style = { 'stroke': 'black',    'stroke-width': stroke }
            x1 = 0
            y1 = i*res
            x2 = self.options.labellinelength*factor
            y2 = i*res

            label = True

        #long line
        if type==1:
            name = 'long line'
            stroke = self.svg.unittouu(str(longlinestrokewidth)+unit)
            line_style = { 'stroke': 'black', 'stroke-width': stroke }
            x1 = 0
            y1 = i*res
            x2 = self.options.labellinelength*0.01*self.options.mark1wid*factor
            y2 = i*res

        #short line
        name = 'short line'
        if type==2:
            stroke = self.svg.unittouu(str(shortlinestrokewidth)+unit)
            line_style = { 'stroke': 'black', 'stroke-width': stroke }
            x1 = 0
            y1 = i*res
            x2 = self.options.labellinelength*0.01*self.options.mark2wid*factor
            y2 = i*res

        #perpendicular line
        if type==3:
            name = 'perpendicular line'
            stroke = self.svg.unittouu(str(perplinestrokewidth)+unit)
            line_style = { 'stroke': 'black', 'stroke-width': stroke }

            #if stroke is in px, use this logic:
        #    unitfactor = self.svg.unittouu(str(1)+unit)
        #    strokeoffset = (labellinestrokewidth / 2) / unitfactor

            #if stroke is in units, use this logic:
            strokeoffset = (labellinestrokewidth / 2)

            x1 = perplineoffset
            x2 = perplineoffset

            #horizontal
            if rotate=='90':
                y2 = ((scaleto-1)*res) + strokeoffset
                y1 = -strokeoffset

            #vertical
            else:
                y2 = ((scaleto-1)*res) - strokeoffset
                y1 = strokeoffset


        x1 = str(self.svg.unittouu(str(x1)+unit) )
        y1 = str(self.svg.unittouu(str(y1)+unit) )
        x2 = str(self.svg.unittouu(str(x2)+unit) )
        y2 = str(self.svg.unittouu(str(y2)+unit) )

        #horizontal
        if rotate=='90':
            tx = x1
            x1 = y1
            y1 = tx

            tx = x2
            x2 = y2
            y2 = tx

        if label==True:
            self.addLabel(n , x2, y2, grpLabel, fontsize)

        line_attribs = {'style' : str(inkex.Style(line_style)), inkex.addNS('label','inkscape') : name, 'd' : 'M '+x1+','+y1+' L '+x2+','+y2}
        line = etree.SubElement(group, inkex.addNS('path','svg'), line_attribs )


    def addLineRad(self, i, scalefrom, scaleto, group, grpLabel, type=2, ishorizontal=True):
        height = self.options.labellinelength
        reverse = self.options.reverse
        radbegin = self.options.scaleradbegin
        radcount = self.options.scaleradcount
        unit = self.options.unit
        fontsize = self.options.fontsize
        radius = self.options.radius
        labeloffseth = self.options.labeloffseth
        labeloffsetv = self.options.labeloffsetv
        insidetf = self.options.insidetf
        labellinestrokewidth = self.options.labellinestrokewidth
        longlinestrokewidth = self.options.longlinestrokewidth
        shortlinestrokewidth = self.options.shortlinestrokewidth
        perplinestrokewidth = self.options.perplinestrokewidth
        perplineoffset = self.options.perplineoffset

        label = False

        labeloffsetv *= -1

        # Count absolute count for evaluation of increment
        count = 0
        for n in range(scalefrom, scaleto):
            count += 1
        countstatus = 0
        for n in range(scalefrom, i):
            countstatus += 1

        if reverse=='true':
            counter = 0
            for n in range(scalefrom, i):
                counter += 1
            n = scaleto-counter-1
        else:
            n = i
        inc = radcount / (count-1)
        irad = countstatus*inc
        irad = -1 * (radbegin+irad+180)

        dangle = 0
        if ishorizontal=='false':
            dangle = 1

        inside = -1
        if insidetf==True:
            inside = 1

        #label line
        if type==0:
            name = 'label line'
            stroke = self.svg.unittouu(str(labellinestrokewidth)+unit)
            line_style = { 'stroke': 'black',    'stroke-width': stroke }
            x1 = math.sin(math.radians(irad))*radius
            y1 = math.cos(math.radians(irad))*radius
            x2 = math.sin(math.radians(irad))*(radius-inside*height)
            y2 = math.cos(math.radians(irad))*(radius-inside*height)

            label = True

        #long line
        if type==1:
            name = 'long line'
            stroke = self.svg.unittouu(str(longlinestrokewidth)+unit)
            line_style = { 'stroke': 'black', 'stroke-width': stroke }
            x1 = math.sin(math.radians(irad))*radius
            y1 = math.cos(math.radians(irad))*radius
            x2 = math.sin(math.radians(irad))*(radius-inside*height*self.options.mark1wid*0.01)
            y2 = math.cos(math.radians(irad))*(radius-inside*height*self.options.mark1wid*0.01)

        #short line
        if type==2:
            name = 'short line'
            stroke = self.svg.unittouu(str(shortlinestrokewidth)+unit)
            line_style = { 'stroke': 'black', 'stroke-width': stroke }
            x1 = math.sin(math.radians(irad))*radius
            y1 = math.cos(math.radians(irad))*radius
            x2 = math.sin(math.radians(irad))*(radius-inside*height*self.options.mark2wid*0.01)
            y2 = math.cos(math.radians(irad))*(radius-inside*height*self.options.mark2wid*0.01)

        #perpendicular line
        if type==3:
            name = 'perpendicular line'
            stroke = self.svg.unittouu(str(perplinestrokewidth)+unit)
            line_style = {'stroke': 'black', 'stroke-width' : stroke, 'fill': 'none'}

            rx = self.svg.unittouu(str(radius+perplineoffset)+unit)
            ry = rx

            #if stroke is in px, use this logic:
            #unitfactor = self.svg.unittouu(str(1)+unit)
            #strokeoffset = math.atan(((labellinestrokewidth / 2) / unitfactor) / radius)

            #if stroke is in units, use this logic:
            strokeoffset = math.atan((labellinestrokewidth / 2) / radius)

            start = math.radians(radbegin + 270) - strokeoffset
            end = math.radians(radbegin+radcount + 270) + strokeoffset

            if radcount != 360:
                line_attribs = {'style':str(inkex.Style(line_style)),
                    inkex.addNS('label','inkscape')        :name,
                    inkex.addNS('cx','sodipodi')           :str(0),
                    inkex.addNS('cy','sodipodi')           :str(0),
                    inkex.addNS('rx','sodipodi')           :str(rx),
                    inkex.addNS('ry','sodipodi')           :str(ry),
                    inkex.addNS('start','sodipodi')        :str(start),
                    inkex.addNS('end','sodipodi')          :str(end),
                    inkex.addNS('open','sodipodi')         :'true',    #all ellipse sectors we will draw are open
                    inkex.addNS('type','sodipodi')         :'arc',}
            else:
                line_attribs = {'style':str(inkex.Style(line_style)),
                    inkex.addNS('label','inkscape')        :name,
                    inkex.addNS('cx','sodipodi')           :str(0),
                    inkex.addNS('cy','sodipodi')           :str(0),
                    inkex.addNS('rx','sodipodi')           :str(rx),
                    inkex.addNS('ry','sodipodi')           :str(ry),
                    inkex.addNS('open','sodipodi')         :'true',    #all ellipse sectors we will draw are open
                    inkex.addNS('type','sodipodi')         :'arc',}

        if type!=3:
            # use user unit
            x1 = self.svg.unittouu(str(x1)+unit)
            y1 = self.svg.unittouu(str(y1)+unit)
            x2 = self.svg.unittouu(str(x2)+unit)
            y2 = self.svg.unittouu(str(y2)+unit)

            if label==True :

                #if the circle count is 360 degrees, do not draw the last label because it will overwrite the first.
                if not (radcount==360 and n==360):
                    x2label = math.sin(math.radians(irad + labeloffseth))*(radius-inside*(-labeloffsetv+height*self.options.mark2wid*0.01))
                    y2label = math.cos(math.radians(irad + labeloffseth))*(radius-inside*(-labeloffsetv+height*self.options.mark2wid*0.01))
                    x2label = self.svg.unittouu(str(x2label)+unit)
                    y2label = self.svg.unittouu(str(y2label)+unit)
                    self.addLabel(n , x2label, y2label, grpLabel, fontsize,dangle*(irad+labeloffseth))

            line_attribs = {'style' : str(inkex.Style(line_style)),    inkex.addNS('label','inkscape') : name, 'd' : 'M '+str(x1)+','+str(y1)+' L '+str(x2)+','+str(y2)}

        line = etree.SubElement(group, inkex.addNS('path','svg'), line_attribs )


    def skipfunc(self, i, markArray, groups):

        skip = True
        group = groups[0]
        type = 0

        if markArray[0] != 0:
            if (i % markArray[0])==0:
                type = 0        # the labeled line
                group = groups[0]
                skip = False

        if markArray[1] != 0 and skip==1:
            if (i % markArray[1])==0:
                type = 1     # the long line
                group = groups[1]
                skip = False

        if markArray[2] != 0 and skip==1:
            if (i % markArray[2])==0:
                type = 2     # the short line
                group = groups[2]
                skip = False

        return (skip, group, type)



    def effect(self):
        scalefrom = self.options.scalefrom
        scaleto = self.options.scaleto

        scaleGroup = self.svg.get_current_layer().add(inkex.Group())
        groups = [None, None, None, None]
        markArray = [self.options.mark0, self.options.mark1, self.options.mark2]

        # Get access to main SVG document element and get its dimensions.
        svg = self.document.getroot()

        # Again, there are two ways to get the attributes:
        width  = self.svg.unittouu(svg.get('width'))
        height = self.svg.unittouu(svg.get('height'))

        centre = self.svg.namedview.center   #Put in in the centre of the current view

        if self.options.useref is True:
            self.bbox = sum([node.bounding_box() for node in self.svg.selected.values() ])
            try:
                test = self.bbox[0]
            except TypeError:
                pass
            else:
                half = (self.bbox[1] - self.bbox[0]) / 2
                x = self.bbox[0] + half

                half = (self.bbox[3] - self.bbox[2]) / 2
                y = self.bbox[2] + half
                centre = (x, y)

        grp_transform = 'translate(' + str(centre) + ')'

        grp_name = 'Label line'
        grp_attribs = {inkex.addNS('label','inkscape'):grp_name, 'transform':grp_transform }
        groups[0] = etree.SubElement(self.svg.get_current_layer(), 'g', grp_attribs)

        if self.options.mark1 > 0:
            grp_name = 'Long line'
            grp_attribs = {inkex.addNS('label','inkscape'):grp_name, 'transform':grp_transform }
            groups[1] = etree.SubElement(self.svg.get_current_layer(), 'g', grp_attribs)

        if self.options.mark2 > 0:
            grp_name = 'Short line'
            grp_attribs = {inkex.addNS('label','inkscape'):grp_name, 'transform':grp_transform }
            groups[2] = etree.SubElement(self.svg.get_current_layer(), 'g', grp_attribs)

        if self.options.drawalllabels is True:
            grp_name = 'Labels'
            grp_attribs = {inkex.addNS('label','inkscape'):grp_name, 'transform':grp_transform }
            groups[3] = etree.SubElement(self.svg.get_current_layer(), 'g', grp_attribs)

        # to allow positive to negative counts
        if scalefrom < scaleto:
            scaleto += 1
        else:
            temp = scaleto
            scaleto = scalefrom+1
            scalefrom = temp

        if self.options.type == 'straight':

            for i in range(scalefrom, scaleto):
                skip, group, type = self.skipfunc(i, markArray, groups)
                if skip==False:
                    self.addLine(i, scalefrom, scaleto, group, groups[3], type) # addLabel is called from inside

            #add the perpendicular line
            if self.options.perpline is True:
                self.addLine(0, scalefrom, scaleto, groups[0], groups[3], 3)

        elif self.options.type == 'circular':

            for i in range(scalefrom, scaleto):
                skip, group, type = self.skipfunc(i, markArray, groups)
                if skip==False:
                    self.addLineRad(i, scalefrom, scaleto, group, groups[3], type, self.options.ishorizontal) # addLabel is called from inside

            #add the perpendicular (circular) line
            if self.options.perpline is True:
                self.addLineRad(0, scalefrom, scaleto, groups[0], groups[3], 3, self.options.ishorizontal)

            if self.options.radmark=='true':

                grp_name = 'Radial center'
                grp_attribs = {inkex.addNS('label','inkscape'):grp_name, 'transform':grp_transform }
                grpRadMark = etree.SubElement(self.svg.get_current_layer(), 'g', grp_attribs)

                line_style   = { 'stroke': 'black',    'stroke-width': '1' }
                line_attribs = {'style' : str(inkex.Style(line_style)),    inkex.addNS('label','inkscape') : 'name', 'd' : 'M '+str(-10)+','+str(-10)+' L '+str(10)+','+str(10)}
                line = etree.SubElement(grpRadMark, inkex.addNS('path','svg'), line_attribs )

                line_attribs = {'style' : str(inkex.Style(line_style)), inkex.addNS('label','inkscape') : 'name', 'd' : 'M '+str(-10)+','+str(10)+' L '+str(10)+','+str(-10)}
                line = etree.SubElement(grpRadMark, inkex.addNS('path','svg'), line_attribs )

        #add all sub groups into a top one
        for group in groups:
            if group is not None:
                scaleGroup.append(group)

if __name__ == '__main__':
    VerticalHorizontalScale().run()
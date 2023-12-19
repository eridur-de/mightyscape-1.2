#! /usr/bin/python
'''
Rounder 0.4
Based in deprecated "Path Rounder 0.2"
Based in  radiusrand script from Aaron Spike and make it by Jabier Arraiza, 
jabier.arraiza@marker.es
Copyright (C) 2005 Aaron Spike, aaron@ekips.org

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
import random
import math
import inkex
from inkex.paths import Path, CubicSuperPath
import re

class Rounder(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--precision", type=int, default=3, help="Precision")
        pars.add_argument("--ctrl", type=inkex.Boolean, default = False, help="Round element handles")
        pars.add_argument("--along", type=inkex.Boolean, default = True, help="Move handles following element movement")
        pars.add_argument("--half", type=inkex.Boolean, default = False, help="Allow round to half if nearest")
        pars.add_argument("--paths", type=inkex.Boolean, default = True, help="Affect to paths")
        pars.add_argument("--widthheight", type=inkex.Boolean, default = False, help="Affect to width and height of objects")
        pars.add_argument("--position", type=inkex.Boolean,  default = False, help="Affect to position of objects")
        pars.add_argument("--strokewidth", type=inkex.Boolean,  default = False, help="Affect to stroke width of objects")
        pars.add_argument("--opacity", type=inkex.Boolean, default = False, help="Affect to global opacity of objects")
        pars.add_argument("--strokeopacity", type=inkex.Boolean,  default = False, help="Affect to stroke opcacity of objects")
        pars.add_argument("--fillopacity", type=inkex.Boolean, default = False, help="Affect to fill opcacity of objects")

    def roundFloat(self, n):
        if self.options.half:
            if self.options.precision == 0:
                return str(round(n * 2) / 2)
            else:
                return str(round(n * (self.options.precision) * 10 * 2) / ((self.options.precision) * 10 * 2))
        else:
            return str(round(n,  self.options.precision))
 
    def roundit(self, p):
        x = self.roundFloat(p[0])
        y = self.roundFloat(p[1])
        return [float(x) - p[0], float(y) - p[1]]
    
    def path_round_it(self,element):
        if element.tag == inkex.addNS('path','svg'):
            d = element.get('d')
            p = CubicSuperPath(d)
            for subpath in p:
                for csp in subpath:
                    delta = self.roundit(csp[1])
                    if self.options.along:
                        csp[0][0]+=delta[0] 
                        csp[0][1]+=delta[1] 
                    csp[1][0]+=delta[0] 
                    csp[1][1]+=delta[1] 
                    if self.options.along:
                        csp[2][0]+=delta[0] 
                        csp[2][1]+=delta[1] 
                    if self.options.ctrl:
                        delta = self.roundit(csp[0])
                        csp[0][0]+=delta[0] 
                        csp[0][1]+=delta[1] 
                        delta = self.roundit(csp[2])
                        csp[2][0]+=delta[0] 
                        csp[2][1]+=delta[1] 
            element.set('d',str(Path(p)))
        elif element.tag == inkex.addNS('g','svg'):
            for e in element:
                self.path_round_it(e)

    def roundStroke(self,matchobj):
        return 'stroke-width:' + self.roundFloat(float( re.sub(r'[a-zA-Z]', "", matchobj.group(1)))) +  matchobj.group(2);

    def roundOpacity(self,matchobj):
        return matchobj.group(1) + matchobj.group(2) + self.roundFloat(float( matchobj.group(3))) +  matchobj.group(4);

    def roundWHXY(self,matchobj):
        return matchobj.group(1) + self.roundFloat(float( matchobj.group(2))) +  matchobj.group(3);


    def stroke_round_it(self, element):
        if element.tag == inkex.addNS('g','svg'):
            for e in element:
                self.stroke_round_it(e)
        else:
            style = element.get('style')
            if style:
                style = re.sub('stroke-width:(.*?)(;|$)',self.roundStroke, style)
                element.set('style',style)
    def opacity_round_it(self, element, typeOpacity):
        if element.tag == inkex.addNS('g','svg'):
            for e in element:
                self.opacity_round_it(e, typeOpacity)
        else:
            style = element.get('style')
            if style:
                style = re.sub('(^|;)(' + typeOpacity + ':)(.*?)(;|$)',self.roundOpacity, style)
                element.set('style',style)

    def widthheight_round_it(self, element):
        if element.tag == inkex.addNS('g','svg'):
            for e in element:
                self.widthheight_round_it(e)
        else:
            width = element.get('width')
            if width:
                width = re.sub('^(\-|)([0-9]+\.[0-9]+)(.*?)$',self.roundWHXY, width)
                element.set('width',width)
            height = element.get('height')
            if height:
                height = re.sub('^(\-|)([0-9]+\.[0-9]+)(.*?)$',self.roundWHXY, height)
                element.set('height',height)
    
    def position_round_it(self, element):
        if element.tag == inkex.addNS('g','svg'):
            for e in element:
                self.position_round_it(e)
        else:
            x = element.get('x')
            if x:
                x = re.sub('^(\-|)([0-9]+\.[0-9]+)(.*?)$',self.roundWHXY, x)
                element.set('x', x)
            y = element.get('y')
            if y:
                y = re.sub('^(\-|)([0-9]+\.[0-9]+)(.*?)$',self.roundWHXY, y)
                element.set('y', y)
    
    def effect(self):
        
        if len(self.svg.selected) > 0:
            for element in self.svg.selection.values():
                if self.options.paths:
                    self.path_round_it(element)
                if self.options.strokewidth:
                    self.stroke_round_it(element)
                if self.options.widthheight:
                    self.widthheight_round_it(element)
                if self.options.position:
                    self.position_round_it(element)
                if self.options.opacity:
                    self.opacity_round_it(element, "opacity")
                if self.options.strokeopacity:
                    self.opacity_round_it(element, "stroke-opacity")
                if self.options.fillopacity:
                    self.opacity_round_it(element, "fill-opacity")
        else:
            self.msg('Please select some paths first.')
            return 

if __name__ == '__main__':
    Rounder().run()
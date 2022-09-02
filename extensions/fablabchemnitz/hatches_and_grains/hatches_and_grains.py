#!/bin/env python3
#
# Copyright (C) 2020 Marc Jeanmougin, Laurent Porcheret
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
# Thanks to Bénédicte Cuperly for reminding me to do this and for her feedback


""" Geography patterns """

import math
import inkex
from inkex import Pattern, PathElement, Circle, Rectangle, AbortExtension

GRAIN_V="m 0 0 10 20 10 -20"
GRAIN_VI="m 0 20 10 -20 10 20"
GRAIN_PLUS="M 10 0 10 20 M 0 10 20 10"
GRAIN_X="M 0 0 20 20 M 0 20 20 0"


class Geography(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--tab', default='grains_page', help='grains_page or hatches_page')
        pars.add_argument('--type', default='h', help='h|d')
        pars.add_argument('--angle', default='0', help='angle')
        pars.add_argument('--thickness', default='1', help='width')
        pars.add_argument('--spacing', default='8', help='spacing between hatches')
        pars.add_argument('--type_grain', default='grain_v', help='Shape of patterns (v^+xoO)')
        pars.add_argument('--size', default='1', help='size of grain')
        pars.add_argument('--hcolor', default=inkex.Color(255), type=inkex.Color, help='color of hatches')
        pars.add_argument('--gcolor', default=inkex.Color(255), type=inkex.Color, help='color of grains')

    def effect(self):
        #step 0: find desired id
        i=self.get_id()
        #step 1: add stuff in defs if not present
        if self.svg.getElementById(i) is None:
            #construct it
            newNode = self.svg.defs.add(Pattern())
            self.construct(newNode)
        
        #step 2: assign
        for node in self.svg.selection.values():
            node.style['fill'] = "url(#"+i+")"
            node.set('fill', "url(#"+i+")")

    def construct(self, node):
        if(self.options.tab == "grains_page"):
            self.construct_grain(node)
        else:
            self.construct_hatch(node)
        node.set('patternUnits', "userSpaceOnUse")
        node.set('id', self.get_id())
    
    def get_id(self):
        if(self.options.tab=="grains_page"):
            return "inkgeo_"+self.options.type_grain+"_"+self.options.size+"_"+str(int(self.options.gcolor))
        else:
            return "inkgeo_"+self.options.type+"_"+self.options.angle+"_"+self.options.thickness+"_"+self.options.spacing+"_"+str(int(self.options.hcolor))


    def construct_grain(self, node):
        size=str(math.sqrt(float(self.options.size)))
        node.set('width', "100")
        node.set('height', "100")
        n1=0
        n2=0
        node.style="stroke-width:4;"
        if self.options.type_grain == "grain_c" or self.options.type_grain == "grain_r":
            n1 = node.add(Circle())
            n2 = node.add(Circle())
            n1.set('cx',10)
            n1.set('cy',10)
            n1.set('r',10)
            n2.set('cx',10)
            n2.set('cy',10)
            n2.set('r',10)
            if self.options.type_grain == "grain_c":
                node.style.set_color(self.options.gcolor, 'stroke')
                node.set('fill', "none")
            else:
                node.style.set_color(self.options.gcolor, 'stroke')
                node.style.set_color(self.options.gcolor, 'fill')
        else:
            node.style.set_color(self.options.gcolor, 'stroke')
            node.set('fill', "none")
            #paths
            n1 = node.add(PathElement())
            n2 = node.add(PathElement())
            if self.options.type_grain == "grain_v":
                n1.set('d', GRAIN_V)
                n2.set('d', GRAIN_V)
            elif self.options.type_grain == "grain_m":
                n1.set('d', GRAIN_VI)
                n2.set('d', GRAIN_VI)
            elif self.options.type_grain == "grain_p":
                n1.set('d', GRAIN_PLUS)
                n2.set('d', GRAIN_PLUS)
            elif self.options.type_grain == "grain_x":
                n1.set('d', GRAIN_X)
                n2.set('d', GRAIN_X)
        n1.set('transform', "translate(5,5)scale("+size+")")
        n2.set('transform', "translate(55,55)scale("+size+")")
        node.set('patternTransform', "scale(0.1)")

    def construct_hatch(self,node):
        h = int(self.options.spacing)+int(self.options.thickness)
        node.set('width', str(h))
        node.set('patternTransform', "rotate("+self.options.angle+")")
        r = node.add(Rectangle())
        r.set('x', "0")
        r.set('y', "0")
        r.set('height', self.options.thickness)
        r.style.set_color(self.options.hcolor, 'fill')
        if self.options.type=="h":
            node.set('height',str(h))
            r.set('width', str(h))
        else:
            node.set('height',str(2*h))
            r.set('width', str(h/2))
            r2 = node.add(Rectangle())
            r2.set('x', str(h/2))
            r2.set('y', str(h))
            r2.set('width', str(h/2))
            r2.set('height', self.options.thickness)
            r2.style.set_color(self.options.hcolor, 'fill')


if __name__ == '__main__':
    Geography().run()

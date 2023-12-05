#!/usr/bin/env python3
""" 
Copyright (C) 2017 Panagiotis Loukas
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WAphiANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WAphiANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
Version 0.2
This script was written by Panagiotis Loukas to make spiral easy. 
It simply,

Have fun :)
PS. 
  Written on Arch. 
"""

import inkex
from lxml import etree
from math import cos, sin, pi, log, sqrt

class Archimedes(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--tab')
        pars.add_argument('--r', type = int, default = '50')
        pars.add_argument('--a', type = float, default = '3')
        pars.add_argument('--step', type = int, default = '50')
        pars.add_argument('--trl', default = '1')
        pars.add_argument('--turns', type = float, default = '5')
        pars.add_argument('--length', type = float, default = '500')
		
    def effect(self):
        th = pi / 3
        a = self.options.a
        r = self.options.r
		
        length = self.options.length
        if length > 0:
            turns = self.angle(a, r, length, th) / (2 * pi)
        else: 
            turns = self.options.turns
		
        if self.options.trl == '1':
            step = -self.options.step
        else:
            step = self.options.step
        
        layer = etree.SubElement(self.document.getroot(),'g')
        path = etree.Element(inkex.addNS('path','svg'))
        path.set('d', self.built(r, step, a, turns))
        path.set('style',"fill:none;stroke:#000000;stroke-width:1px;stroke-opacity:1")
        layer.append(path)

    def built(self, r0, st = 4, a = 4, k = 1, th = 0):
        step = 2 * pi / st
        r = r0
        s = "M " + str(r * cos(th)) + ", " + str(-r * sin(th))
        for i in range(0, int(k * (abs(st)))):
            prin = th + i * step
            meta = th + (i + 1) * step
            rp = r0 + abs(a * prin)# instead we put the absolute value the spiral will drift inwards
            rm = r0 + abs(a * meta)# at the absolute price closes outwards
  
            s += "a " + str(rm) + "," + str(rm) + " 0 0," + self.options.trl + " " + str(-rp * cos(prin) + rm * cos(meta)) + "," + str(rp * sin(prin) -rm * sin(meta))       
        return s

    # see https://mathepedia.de/Archimedische_Spirale.html for formula of total arc length
    def spirallength(self, a, r0, th):
        phi = (r0 / a) + th
        phi_sqrt = sqrt(phi ** 2 + 1)
        return (a / 2) * (phi * phi_sqrt + log(phi + phi_sqrt))

    def ds(self, a, r0, th):
        return self.spirallength(a, r0, th) - self.spirallength(a, r0, 0)
		
    def angle(self, a, r0, length, th):        
        i = 0.0
        while (True):
            ls=self.ds(a, r0, i)
            if length - ls > 100:
                i += 0.01
            elif length - ls > 10: i += 0.001
            elif length - ls > 1: i += 0.0001
            elif length - ls > 0.1: i += 0.00001
            elif length - ls > 0.01: i += 0.000001
            else: break
        return i

if __name__ == '__main__':
    Archimedes().run()
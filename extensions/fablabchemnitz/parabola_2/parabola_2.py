#!/usr/bin/env python3
#
# 7/9/2021  - v.2.0
#
# Copyright (C) 2021 Reginald Waters opensourcebear@nthebare.com
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
This extension renders a wireframe shape and then draws lines to form a parabola 
shape.

The height and width are independently variable. The number of lines will change 
the density of the end product.

# Triangle has 3 sides and the sum of the 3 angles is 180 degrees 
# (sides - 2) * 180
# This can be 60/60/60   or 90/45/45

# Square has 4 sides and the sum of 4 angles is 360 degrees
# (sides - 2) * 180
# 90/90/90/90

# Pentagon has 5 sides and the sum of 5 angels is 540 degrees
# (sides - 2) * 180
# 108/108/108/108/108
...
"""
import inkex

from inkex import turtle as pturtle

class Parabola2(inkex.GenerateExtension):
    container_label = 'Parabola 2'
    def add_arguments(self, pars):
        pars.add_argument("--length", type=int, default=300, help="Side Length")
        pars.add_argument("--segments", type=int, default=10, help="Number of line segments")
        pars.add_argument("--shape", default="square")

        sideopts = [
        (1,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),
        (2,3),(2,4),(2,5),(2,6),(2,7),(2,8),
        (3,4),(3,5),(3,6),(3,7),(3,8),
        (4,5),(4,6),(4,7),(4,8),
        (5,6),(5,7),(5,8),
        (6,7),(6,8),
        (7,8)]

    def generate(self):
        sl = self.options.length
        sc = self.options.segments
        shape = self.options.shape

        cp = self.svg.namedview.center # Center Point
        sp = (cp[0] + (sl / 2), cp[1] + (sl / 2)) # Start Point
        cords = []

        def mapshape(sides, sl, sc, sp):
            exteriorAngle = 360/sides
            movement = sl / sc
            tur.setpos(sp)
            for i in range(sides):
                sidecords = []
                tl = 0 # total length
                while tl < sl:
                    sidecords.append(tur.getpos())
                    tur.forward(movement)
                    tl += movement
#                sidecords.append(tur.getpos())
                tur.right(exteriorAngle)
                cords.append(sidecords)
            return cords
        
        def mapcross(sl, sc, sp):
            movement = sl / sc
            tur.setpos(sp)
            sidecords = []
            tl = 0 
            tur.forward(sl)
            while tl < sl:
                tur.backward(movement)
                sidecords.append(tur.getpos())
                tur.right(90)

        def drawshape(cords):
            tur.setpos(cords[0][0])
            for i in range(len(cords)):
#                tur.pd()
#                tur.setpos(cords[i][-1])
#                tur.pu()
                for side in range(len(cords)):
                    for cord in range(len(cords[0])):
                        if side == (len(cords) - 1):
                            tur.setpos(cords[side][cord])
                            tur.pd()
                            if cord != (len(cords[0])):
                                tur.setpos(cords[0][cord])
                                tur.pu()
                        else:
                            tur.setpos(cords[side][cord])
                            tur.pd()
                            tur.setpos(cords[side + 1][cord])
                            tur.pu()
                tur.pu()
            
        tur = pturtle.pTurtle()
        tur.pu()

        if shape == "triangle":
            sides = 3
            mapshape(sides, sl, sc, sp)
            drawshape(cords)
        elif shape == "square":
            sides = 4
            mapshape(sides, sl, sc, sp)
            drawshape(cords)
        elif shape == "pentagon":
            sides = 5
            mapshape(sides, sl, sc, sp)
            drawshape(cords)
        elif shape == "hexagon":
            sides = 6
            mapshape(sides, sl, sc, sp)
            drawshape(cords)
        elif shape == "septagon":
            sides = 7
            mapshape(sides, sl, sc, sp)
            drawshape(cords)
        elif shape == "octagon":
            sides = 8
            mapshape(sides, sl, sc, sp)
            drawshape(cords)

        style = inkex.Style({
                'stroke-linejoin': 'miter', 'stroke-width': str(self.svg.unittouu('1px')),
                'stroke-opacity': '1.0', 'fill-opacity': '1.0',
                'stroke': '#000000', 'stroke-linecap': 'butt',
                'fill': 'none'
        })      
        return inkex.PathElement(d=tur.getPath(), style=str(style))   

if __name__ == "__main__":
    Parabola2().run()
#!/usr/bin/env python3
# coding=utf-8
#
# 2/27/2021 - v.1.1.0
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
"""
import inkex

from inkex import turtle as pturtle

class Parabola(inkex.GenerateExtension):
    
    container_label = 'Parabola'
    def add_arguments(self, pars):
        pars.add_argument("--height", type=int, default=300, help="Shape Height")
        pars.add_argument("--width", type=int, default=300, help="Shape Width")
        pars.add_argument("--seg_count", type=int, default=10, help="Number of line segments")
        pars.add_argument("--shape", default="square")
        pars.add_argument("--tab", default="common")
        pars.add_argument("--c1", default="true")
        pars.add_argument("--c2", default="false")
        pars.add_argument("--c3", default="false")
        pars.add_argument("--c4", default="false")

    def generate(self):
        # Let's simplify the variable names
        ht = int(self.options.height)
        wt = int(self.options.width)
        sc = int(self.options.seg_count)
        shape = self.options.shape
        c1 = self.options.c1
        c2 = self.options.c2
        c3 = self.options.c3
        c4 = self.options.c4

        point = self.svg.namedview.center
        style = inkex.Style({
                'stroke-linejoin': 'miter', 'stroke-width': str(self.svg.unittouu('1px')),
                'stroke-opacity': '1.0', 'fill-opacity': '1.0',
                'stroke': '#000000', 'stroke-linecap': 'butt',
                'fill': 'none'
        })
        
        # Setting the amount to move across the horizontal and vertical
        increaseht = (ht / sc)
        increasewt = (wt / sc)

        tur = pturtle.pTurtle()

        tur.pu()  # Pen up
        tur.setpos(point) # start in the center
        
        if shape == "cross":
            # We draw the cross shape and store the 4 points
            # Can this be looped?
            # Should I store the coordinates in an array/list?
            tur.forward((ht / 2)) 
            toppoint = tur.getpos() 
            if c3 == 'true' or c4 == 'true':
                tur.pd()
            tur.backward((ht / 2)) 
            tur.pu()
            if c1 == 'true' or c2 == 'true':
                tur.pd()
            tur.backward((ht / 2))
            bottompoint = tur.getpos()
            tur.pu()
            tur.setpos(point)
            tur.left(90)
            tur.forward((wt / 2))
            rightpoint = tur.getpos()
            if c3 == 'true' or c2 == 'true':
                tur.pd()
            tur.backward((wt / 2))
            tur.pu()
            if c1 == 'true' or c4 == 'true':
                tur.pd()
            tur.backward((wt / 2))
            leftpoint = tur.getpos()

            while sc > 0:
                if c1 == 'true':
                # Drawing the SE Corner based on SW coordinates
                # We always draw this corner
                    tur.pu()
                    tur.setpos((bottompoint[0], bottompoint[1] - ( (increaseht / 2) * sc ) ))
                    tur.pd()    
                    tur.setpos((bottompoint[0] + ( (increasewt / 2) * sc ), bottompoint[1] - (ht / 2) ))
                
                if c2 == 'true': # Drawing the SW Corner based on SE Coordinates
                    tur.pu()
                    tur.setpos((bottompoint[0], bottompoint[1] - ( (increaseht / 2) * sc ) ))
                    tur.pd()    
                    tur.setpos((bottompoint[0] - ( (increasewt / 2) * sc ), bottompoint[1] - (ht / 2) ))
                
                if c3 == 'true': # Drawing the NW Corner based on NE Coordinates
                    tur.pu()
                    tur.setpos((toppoint[0], toppoint[1] + ( (increaseht / 2) * sc ) ))
                    tur.pd()    
                    tur.setpos((toppoint[0] - ( (increasewt / 2) * sc ), toppoint[1] + (ht / 2) ))
                
                if c4 == 'true': # Drawing the NE Corner based on NW Coordinates
                    tur.pu()
                    tur.setpos((toppoint[0], toppoint[1] + ( (increaseht / 2) * sc ) ))
                    tur.pd()    
                    tur.setpos((toppoint[0] + ( (increasewt / 2) * sc ), toppoint[1] + (ht / 2) ))

                sc = sc - 1

        if shape == "triangle":
            # We draw the triangle and store the 3 corner points
            # Loopable?
            tur.backward((ht / 2))
            tur.left(90)
            tur.forward((wt /2))
            cornera = tur.getpos()
            if c3 == 'true' or c2 == 'true':
                tur.pd()
            tur.backward((wt))
            cornerb = tur.getpos()
            tur.pu()
            if c2 == 'true' or c1 == 'true':
                tur.pd()
            tur.setpos((point[0], (cornera[1] - ht) ))
            cornerc = tur.getpos()
            tur.pu()
            if c1 == 'true' or c3 == 'true':
                tur.pd()            
            tur.setpos(cornera)

# So..  The math below took a lot of trial and error to figure out...
# I probably need to take some geography classes...

            while sc > 0:
                if c1 == 'true':
                    tur.pu()
                    tur.setpos(( (cornerb[0] + ((increasewt / 2) * (sc)) - (wt / 2)), cornerb[1] + (increaseht * sc) - ht ))
                    tur.pd()    
                    tur.setpos(( (cornera[0] + (increasewt / 2) * (sc)), cornera[1] - (increaseht * sc) ))

                if c2 == 'true':
                    tur.pu()
                    tur.setpos((cornerb[0] - (increasewt * sc ) , cornerb[1] ))
                    tur.pd()    
                    tur.setpos(( (cornerb[0] + ((increasewt / 2) * sc) - (wt / 2)), cornerb[1] + (increaseht * sc) - ht ))

                if c3 == 'true':
                    tur.pu()
                    tur.setpos((cornera[0] + (increasewt * sc ) , cornera[1] ))
                    tur.pd()    
                    tur.setpos(( (cornera[0] - ((increasewt / 2) * sc) + (wt / 2)), cornera[1] + (increaseht * sc) - ht ))

                sc = sc - 1


        if shape == "square":
            # We draw out the square shape and store the coordinates for each corner
            # Can this be looped?
            tur.left(90)
            tur.forward((wt / 2))
            tur.left(90)
            tur.forward((ht / 2))
            swcorner = tur.getpos()
            if c4 == 'true' or c3 == 'true': # We only draw the 2 lines that are part of these corners
                tur.pd()  # Pen Down
            tur.left(90)
            tur.forward(wt)
            secorner = tur.getpos()
            tur.pu()
            if c3 == 'true' or c2 == 'true': # We only draw the 2 lines that are part of these corners
                tur.pd()
            tur.left(90)
            tur.forward(ht)
            necorner = tur.getpos()
            tur.pu()
            if c1 == 'true' or c2 == 'true': # We only draw the 2 lines that are part of these corners
                tur.pd()
            tur.left(90)
            tur.forward(wt)
            nwcorner = tur.getpos()
            tur.left(90)
            tur.pu()
            if c4 == 'true' or c1 == 'true': # We only draw the 2 lines that are part of these corners
                tur.pd()
            tur.forward(ht)

            while sc > 0:
                if c1 == 'true':
                # Drawing the NW Corner based on SW coordinates
                # We always draw this corner
                    tur.pu()
                    tur.setpos((swcorner[0], swcorner[1] - ( increaseht * sc ) ))
                    tur.pd()    
                    tur.setpos((swcorner[0] + ( increasewt * sc ), swcorner[1] - ht))
                
                if c2 == 'true': # Drawing the NE Corner based on SE Coordinates
                    tur.pu()
                    tur.setpos((secorner[0], secorner[1] - ( increaseht * sc ) ))
                    tur.pd()    
                    tur.setpos((secorner[0] - ( increasewt * sc ), secorner[1] - ht))
                
                if c3 == 'true': # Drawing the SE Corner based on NE Coordinates
                    tur.pu()
                    tur.setpos((necorner[0], necorner[1] + ( increaseht * sc ) ))
                    tur.pd()    
                    tur.setpos((necorner[0] - ( increasewt * sc ), necorner[1] + ht))
                
                if c4 == 'true': # Drawing the SW Corner based on NW Coordinates
                    tur.pu()
                    tur.setpos((nwcorner[0], nwcorner[1] + ( increaseht * sc ) ))
                    tur.pd()    
                    tur.setpos((nwcorner[0] + ( increasewt * sc ), nwcorner[1] + ht))

                sc = sc - 1
    
        return inkex.PathElement(d=tur.getPath(), style=str(style))

if __name__ == "__main__":
    Parabola().run()
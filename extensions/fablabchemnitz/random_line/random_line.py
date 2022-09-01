#!/usr/bin/env python3
##
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
# 
# 5/19/2021 - v.01
# Ideas: 
# 1. If we move randist out of next nextmove(), can we re-used that code?
# 2. Should we allow users to specify the max line length drawn?
# 3. Should we provide an option to draw past the height/width boundry?

import inkex
import random

from inkex import turtle as pturtle

class RandomLine(inkex.GenerateExtension):
    
    container_label = 'Random Line'
    
    def add_arguments(self, pars):
        pars.add_argument("--height", type=int, default=300, help="Shape Height")
        pars.add_argument("--width", type=int, default=300, help="Shape Width")        
        pars.add_argument("--seg_count", type=int, default=10, help="Number of line segments")
        
    def generate(self):
        # Let's simplify the variable names
        ht = int(self.options.height)
        wt = int(self.options.width)
        sc = int(self.options.seg_count)
        cp = self.svg.namedview.center # center point
        maxx = cp[0] + (wt / 2)
        maxy = cp[0] + (ht / 2)
        minx = cp[1] - (wt / 2)
        miny = cp[1] - (ht / 2)

        # We need to decide what the maximum length we can draw a line
        # maxlen is used to seed the random length of the line
        # It may still be too long, but we'll check on that later! 
        if ht > wt:
            maxlen = ht
        else:
            maxlen = wt
        
        style = inkex.Style({
                'stroke-linejoin': 'miter', 'stroke-width': str(self.svg.unittouu('1px')),
                'stroke-opacity': '1.0', 'fill-opacity': '1.0',
                'stroke': '#000000', 'stroke-linecap': 'butt',
                'fill': 'none'
        })

        tur = pturtle.pTurtle()
        tur.pu()  # Pen up
        tur.setpos(cp) # position to center of window

        def nextmove(maxlen):
            randdist = random.randint(0, maxlen) # how far should we draw?
            tur.forward(randdist) # Let's move the new distance
            newpos = tur.getpos() # Did we go to far?
            return newpos, randdist

        while sc > 0:
            turpos = tur.getpos() # where are we?

            randangle = random.randint(1, 360) # Let's Pick a new direction
            tur.rt(randangle) # Let's turn to face that new direction

            tur.pu() # We don't want to draw just yet, so pick up the pen/pencil

            newpos, randdist = nextmove(maxlen) # If we make this move will we go out of bounds?

            while newpos[0] > maxx or newpos[0] < minx or newpos[1] < miny or newpos[1] > maxy:
                tur.setpos(turpos)
                newpos, randdist = nextmove(maxlen)

            # If it all tests ok, we reset the position 
            # and draw the line for real!
            tur.setpos(turpos)
            tur.pd()
            tur.forward(randdist)
            

            sc = sc - 1

        return inkex.PathElement(d=tur.getPath(), style=str(style))

if __name__ == "__main__":
    RandomLine().run()

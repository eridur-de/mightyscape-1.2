#!/usr/bin/env python3

# Copyright (c) 2012 Stuart Pernsteiner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import inkex
from inkex import Transform

class SetViewBox(inkex.EffectExtension):

    def effect(self):
        if len(self.svg.selected) != 1:
            sys.exit("Error: You must select exactly one rectangle")
        if list(self.svg.selected.items())[0][1].tag != inkex.addNS('rect','svg'):
            sys.exit("Error: You must select exactly one rectangle")
            
        sel = None
        for pathId in self.svg.selected:
            sel = self.svg.selected[pathId]

        mat = [[1,0,0],[0,1,0]]
        cur = sel
        while cur is not None:
            curMat = Transform(cur.get('transform'))
            mat = Transform(curMat) @ Transform(mat)
            cur = cur.getparent()

        [x,y,w,h] = map(lambda attr: float(sel.get(attr)),
                ['x','y','width','height'])
    
        (x1,y1) = transformPoint(mat, (x,y))
        (x2,y2) = transformPoint(mat, (x+w,y+h))

        ww = x2-x1
        hh = y2-y1

        format_units = inkex.units.parse_unit(self.svg.get('width'))[1] #get the "Format:" unit at "Display tab"

        root = self.svg.getElement('//svg:svg');
        root.set('viewBox', '%f %f %f %f' % (x1,y1,ww,hh))
        root.set('width', str(ww) + format_units)
        root.set('height', str(hh) + format_units)

def transformPoint(mat, pt):
    pt2 = [pt[0], pt[1]]
    Transform(mat).apply_to_point(pt2)
    return (pt2[0], pt2[1])

if __name__ == '__main__':
    SetViewBox().run()

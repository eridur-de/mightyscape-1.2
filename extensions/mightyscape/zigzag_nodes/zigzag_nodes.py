#!/usr/bin/env python3
'''
zigzag.py
Sunabe kazumichi 2009/9/29
http://dp48069596.lolipop.jp/


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

this program shifts the nodes zigzags.
'''
import random
import math
import inkex
from inkex import CubicSuperPath

def pointdistance(x1, y1, x2, y2):
    dist=math.sqrt(((x2 - x1) ** 2) + ((y2 - y1) ** 2))
    if dist==0:
        dx=0
        dy=0
    else:
        dx=(x2 - x1)/dist
        dy=(y2 - y1)/dist    
    return dx,dy

def randomize(x,y, r):    
    if y == 0:
        a = math.pi
    elif x == 0 and y != 0:
        a = math.pi/2
    else:
        a = math.atan2(y,x)
    x = math.cos(a-math.pi/2)*r
    y = math.sin(a-math.pi/2)*r       
    return [x, y]

class ZigzagNodes(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--title")
        pars.add_argument("--radius", type=float, default=10.0, help="Randomly move control and end points in this radius")
        
    def effect(self):
        for id, node in self.svg.selected.items():
            if node.tag == inkex.addNS('path','svg'):
                d = node.get('d')
                p = CubicSuperPath(d)
                for subpath in p:
                    for i, csp in enumerate(subpath):
                        if i % 2 != 0:
                            dx,dy=pointdistance(csp[0][0], csp[0][1], csp[1][0], csp[1][1])
                            delta=randomize(dx, dy, self.options.radius)
                            csp[0][0]+=delta[0] 
                            csp[0][1]+=delta[1] 
                            csp[1][0]+=delta[0] 
                            csp[1][1]+=delta[1] 
                            csp[2][0]+=delta[0] 
                            csp[2][1]+=delta[1]                                
                        else:
                            dx,dy=pointdistance(csp[0][0], csp[0][1], csp[1][0], csp[1][1])
                            delta=randomize(dx, dy, self.options.radius)
                            csp[0][0]-=delta[0] 
                            csp[0][1]-=delta[1] 
                            csp[1][0]-=delta[0] 
                            csp[1][1]-=delta[1] 
                            csp[2][0]-=delta[0] 
                            csp[2][1]-=delta[1]

                node.set('d', CubicSuperPath(p))

if __name__ == '__main__':       
    ZigzagNodes().run()
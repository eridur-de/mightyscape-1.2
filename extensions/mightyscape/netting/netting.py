#!/usr/bin/env python3
'''
netting.py
Sunabe kazumichi 2010/3/4
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

this program nets in the line.
'''
import random
import math
import inkex
import cubicsuperpath
from lxml import etree
from inkex.paths import Path, CubicSuperPath

class Netting(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--netting_type", default="allwithall", help="Netting type")
        pars.add_argument("--node_shifting", type=int, default=0, help="Does not apply for 'all with all' type.")
        pars.add_argument("--stroke_width", type=float, default=1.0, help="stroke width")
        pars.add_argument("--allwithall_limit", type=int, default=100, help="This applies to 'all with all' option only. We limit the nettings loops because 100 path nodes will generate 100x100=10000 netted path nodes already. Might crash Inkscape at higher values easily!")

    def effect(self):
        #static
        style = {'stroke-width': "{:0.6f}".format(self.svg.unittouu(str(self.options.stroke_width) + "px")), 'stroke': '#000000', 'fill': 'none'}  
        old_segments = []
        new_segments = []
        
        #get complete path data from all selected paths
        for element in self.svg.selected.filter(inkex.PathElement).values():
            d = element.get('d')
            p = CubicSuperPath(Path(d))
            for subpath in p:
                for i, csp in enumerate(subpath):
                    old_segments.append("%f,%f" % (csp[1][0], csp[1][1]))
        
            if self.options.netting_type == "allwithall":
                count = 0
                allnet_group = inkex.Group(id="g" + element.get('id'))
                pathsCollection = []
                self.svg.get_current_layer().append(allnet_group)
                for segment1 in range(0, len(old_segments)):
                    count = count + 1
                    for segment2 in range(1, len(old_segments)):
                        if old_segments[segment1] != old_segments[segment2]:
                            pathVariant1 = Path('M' + old_segments[segment1] + ' L' + old_segments[segment2])
                            pathVariant2 = Path('M' + old_segments[segment2] + ' L' + old_segments[segment1]) #the reversed one  
                            if pathVariant1 not in pathsCollection and pathVariant2 not in pathsCollection:
                                pathsCollection.append(pathVariant1)
                    if count >= self.options.allwithall_limit:
                        break #skip
                        
                for p in pathsCollection:
                    allnet_path = inkex.PathElement()
                    allnet_path.style = style
                    allnet_path.path = p
                    allnet_group.append(allnet_path)
                    

            elif self.options.netting_type == "alternatingly":
                #build up the net path between the path points alternatingly
                first = True
                while len(old_segments) > 0:
                    if first is True:
                        new_segments.append('M')
                        first = False
                    else:
                        new_segments.append('L')
                    new_segments.append(old_segments.pop(0))
                    if len(old_segments) > 0:
                        new_segments.append('L')
                        new_segments.append(old_segments.pop())
            
                shift = self.options.node_shifting
                if shift < 0:
                    counter = -1
                else:
                    counter = +1     
                for i in range(0, self.options.node_shifting, counter):
                    for i in range(4):
                        shifting = new_segments[0]
                        if new_segments[0] == 'M':
                            shifting = 'L' #overwrite possible 'M' with 'L'
                        del new_segments[0]
                        new_segments.append(shifting)
                new_segments[0] = 'M' #let's begin the path with 'M' again

                #create the path and add it to the current layer 
                net_path = inkex.PathElement()
                net_path.style = style
                net_path.path = Path(" ".join(new_segments))
                self.svg.get_current_layer().append(net_path)
                       
if __name__ == '__main__':
    Netting().run()
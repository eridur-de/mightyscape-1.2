#! /usr/bin/env python3
'''
Copyright (C) 2020 Christian Hoffmann christian@lehrer-hoffmann.de

##This extension allows you to draw a Cartesian grid in Inkscape.
##There is a wide range of options including subdivision, subsubdivions
## and logarithmic scales. Custom line widths are also possible.
##All elements are grouped with similar elements (eg all x-subdivs)

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
Foundation, Inc., 51 Fraanklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''

import inkex 

class DotsToPathPoints(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--endpoints", type=inkex.Boolean, default=True)
        pars.add_argument("--controlpoints", type=inkex.Boolean, default=False)
    
    def effect(self):
        if len(self.svg.selected) != 2:
            inkex.errormsg("Please select exact two objects:\n1. object representing path,\n2. object representing dots.")
            return
    
        nodes = list(self.svg.selected.values())
        iddot  = nodes[0].get('id')
        idpath = nodes[1].get('id')
        dot    = self.svg.selected[iddot]
        path   = self.svg.selected[idpath]
        self.svg.selected.popitem()
        self.svg.selected.popitem()
        bb = dot.bounding_box()
        parent = path.find('..')
        group = inkex.Group()
        parent.add(group)

        end_points = list(path.path.end_points)
        control_points = []
        for cp in path.path.control_points:
            is_endpoint = False
            for ep in end_points:
                if cp.x == ep.x and cp.y == ep.y:
                    is_endpoint = True
                    break
            if not is_endpoint:
                control_points.append(cp)
        
        pointlist = []
        if self.options.endpoints:
            pointlist += end_points
        if self.options.controlpoints:
            pointlist += control_points
        for point in pointlist:
            clone = inkex.Use()
            clone.set('xlink:href','#'+iddot)
            clone.set('x',point.x-bb.center.x)
            clone.set('y',point.y-bb.center.y)
            group.add(clone)
        
if __name__ == '__main__':
    DotsToPathPoints().run()

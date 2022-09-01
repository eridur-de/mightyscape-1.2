#!/usr/bin/env python3

"""
Extension for InkScape 1.0

Converts curves to polylines - a quick and dirty helper for a lot of elements. Basically the same functionality can be done with default UI featureset but with a lot more mouse clicks

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 05.09.2020
Last patch: 05.09.2020
License: GNU GPL v3
"""

import inkex
from inkex.paths import Path

class ConvertToPolylines(inkex.EffectExtension):

    #convert a path (curve) to a polyline and remove dangling/duplicate/useless overlapping handles (points)
    def convertPath(self, node):
        if node.tag == inkex.addNS('path','svg'):
            polypath = []
            i = 0
            for x, y in node.path.end_points:
                if i == 0:
                    polypath.append(['M', [x,y]])
                else:
                    polypath.append(['L', [x,y]])
                    if i == 1 and polypath[len(polypath)-2][1] == polypath[len(polypath)-1][1]:
                        polypath.pop(len(polypath)-1) #special handling for the seconds point after M command
                    elif polypath[len(polypath)-2] == polypath[len(polypath)-1]: #get the previous point
                        polypath.pop(len(polypath)-1)
                i += 1
                node.set('d', str(Path(polypath)))
        children = node.getchildren()
        if children is not None: 
            for child in children:
                self.convertPath(child) 
 
    def effect(self):
        if len(self.svg.selected) == 0:
             self.convertPath(self.document.getroot())
        else:
            for id, item in self.svg.selected.items():
                self.convertPath(item)
      
if __name__ == '__main__':
    ConvertToPolylines().run()
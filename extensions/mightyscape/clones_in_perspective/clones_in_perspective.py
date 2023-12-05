#!/usr/bin/env python3
import sys
import math
import inkex
from lxml import etree

class clonesInPerspective(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--num', type = int, default = 5, help = 'Drag out center of rotation before calling')
        pars.add_argument('--ratio', type = float, default = 0.9, help = 'Ratio of size of nearest neighbor to first.  Must be < 1')

    def effect(self):
        if len(self.svg.selected) != 1:
            inkex.errormsg("Select exactly 1 thing. If necessary, group your items before.")
            sys.exit(1)
        xpath = list(self.svg.selected.items())[0][0]
        sel = self.svg.selected[xpath]
        id = sel.get('id')

        try :
            tx = sel.attrib[inkex.addNS('transform-center-x','inkscape')]
        except KeyError:
            tx = '0.'
        try :
            ty = sel.attrib[inkex.addNS('transform-center-y','inkscape')]
        except KeyError: 
            ty = '0.'

        if float(tx) == 0. and float(ty) == 0. :
            inkex.errormsg("Center of rotation ist at the center of object. Please move the center first.")
            sys.exit(1)
  
        bbox = sel.bounding_box()
        width =  bbox.height
        height = bbox.width
        cx = float(bbox.left) + 0.5 * width  #Find center of selected object
        cy = float(bbox.top) + 0.5 * height #Find center of selected object
        tx = float(tx)
        ty = float(ty)
        crat = 1.0
        otx = tx
        oty = ty

        parent = sel.getparent()
        j = parent.index(sel)
        for i in range(self.options.num) :
            crat *= self.options.ratio
            tx *= self.options.ratio
            ty *= self.options.ratio
            att = {
                "id" : self.svg.get_unique_id("clone" + id),
                inkex.addNS('href','xlink') : "#" + id,
                inkex.addNS('transform-center-x','inkscape') : str(tx),
                inkex.addNS('transform-center-y','inkscape') : str(ty),
                'transform' : ("matrix(%f,0,0,%f,%f,%f)" % (crat, crat,(1. - crat)*(cx + otx), (1. - crat)*(cy - oty))),
            "width" :  "100%",
            "height" : "100%",
            }
            parent.insert(j, etree.Element('use', att))

if __name__ == '__main__':
    clonesInPerspective().run()
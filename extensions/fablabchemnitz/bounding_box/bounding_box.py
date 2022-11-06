#!/usr/bin/env python3

import inkex
import math
from lxml import etree

class BoundingBox(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--offset', type=float, default=0.0, help='Offset from object (all directions)')
        pars.add_argument('--unit', default="mm")
        pars.add_argument('--box', type=inkex.Boolean, default=0.0, help='Draw boxes')
        pars.add_argument('--corner_radius', type=float, default=0.0, help='Corner radius')
        pars.add_argument('--circle', type=inkex.Boolean, default=0.0, help='Draw circles')
        pars.add_argument('--split', type = inkex.Boolean, default = True, help = 'Handle selection as group')
      
    def drawBBox(self, bbox):
        if bbox is not None: #bbox might be None in case of shape elements like pointy paths
            so = self.options
            offset = self.svg.unittouu(str(so.offset) + so.unit)
            if self.options.box:
                attribs = {
                    'style' : str(inkex.Style({'stroke':'#ff0000','stroke-width':str(self.svg.unittouu("1px")),'fill':'none'})),
                    'x'     : str(bbox.left - offset),
                    'y'     : str(bbox.top - offset),
                    'width' : str(bbox.width + 2 * offset),
                    'height': str(bbox.height + 2 * offset),
                    'ry'    : str(self.options.corner_radius),
                    'rx'    : str(self.options.corner_radius)
                }
                etree.SubElement(self.svg.get_current_layer(), inkex.addNS('rect','svg'), attribs)
    		    	
            if self.options.circle:			    	
                attribs = {
                    'style': str(inkex.Style({'stroke':'#ff0000','stroke-width':str(self.svg.unittouu("1px")),'fill':'none'})),
                    'cx'   : str(bbox.center_x),
                    'cy'   : str(bbox.center_y),
                    #'r'   : str(bbox.width / 2 + offset),
                    'r'    : str(math.sqrt((bbox.width + 2 * offset)* (bbox.width + 2 * offset) + (bbox.height + 2 * self.options.offset) * (bbox.height + 2 * self.options.offset)) / 2),
                }
                etree.SubElement(self.svg.get_current_layer(), inkex.addNS('circle','svg'), attribs)
     
      
    def effect(self):
        
        scale_factor = self.svg.unittouu("1px")
        
        if len(self.svg.selected) > 0:
            if self.options.split is False:
                for element in self.svg.selected.values():
                    self.drawBBox(element.bounding_box())
            else: #combined bbox
                #self.drawBBox(self.svg.get_selected_bbox()) #works for InkScape (1:1.0+devel+202008292235+eff2292935) @ Linux and for Windows (but with deprecation)
                #self.drawBBox(self.svg.selection.bounding_box()) #works for InkScape 1.1dev (9b1fc87, 2020-08-27)) @ Windows
                bbox = inkex.BoundingBox()
                for element in self.svg.selected.values():
                    if isinstance (element, inkex.ShapeElement) and element.tag != inkex.addNS('use','svg') and element.get('inkscape:groupmode') != 'layer': #bbox fails for svg:use elements and layers:
                        bbox += element.bounding_box()
                self.drawBBox(bbox)       
        else:
            inkex.errormsg('Please select some objects first.')
            return

if __name__ == '__main__':
    BoundingBox().run()
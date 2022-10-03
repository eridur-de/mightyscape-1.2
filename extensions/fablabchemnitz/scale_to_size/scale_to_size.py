#!/usr/bin/env python3

# Author: Mario Voigt / FabLab Chemnitz
# Mail: mario.voigt@stadtfabrikanten.org
# Date: 04.08.2020
# License: GNU GPL v3

import inkex
from inkex.paths import CubicSuperPath, Path
from inkex import Transform
from lxml import etree
from inkex.styles import Style
import copy

# This extension can scale any object or path on X, Y or both axes. This addon is kind of obsolete because you can do the same from transforms menu

class ScaleToSize(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--unit')
        pars.add_argument("--keep_aspect", type=inkex.Boolean, default=True, help="Does not apply for uniform scaling")
        pars.add_argument("--expected_size", type=float, default=100.000, help="The expected size of the object")
        pars.add_argument("--copies", type=int, default=1, help="Count of copies")
        pars.add_argument("--scale_increment", type=float, default=0.000, help="Scale increment")
        pars.add_argument("--scale_type", default="Horizontal", help="Scale type (Uniform, Horizontal, Vertical)")
        pars.add_argument("--description")

    def effect(self):
        unit_factor = 1.0 / self.svg.uutounit(1.0,self.options.unit)
        so = self.options
        scale_factor = self.svg.unittouu("1px")
        #get recent XY coordinates (top left corner of the bounding box)
        for element in self.svg.selected.values():
            allCopies = []
            allCopies.append(element)
            for aCopy in range(so.copies):
                newElem = copy.copy(element)
                oldId = element.get('id')
                newElem.set('id', "{}_scalecopy_{}".format(oldId, aCopy))
                parent = element.getparent()
                parent.insert(parent.index(element) + 1 + aCopy, newElem)
                allCopies.append(newElem)

            i = 1
            for element in allCopies:
                i += 1
                if isinstance (element, inkex.Rectangle) or \
                   isinstance (element, inkex.Circle) or \
                   isinstance (element, inkex.Ellipse):
                    bbox = element.bounding_box() * unit_factor
                    new_horiz_scale = (so.expected_size + so.scale_increment * i) * unit_factor / bbox.width / scale_factor
                    new_vert_scale = (so.expected_size + so.scale_increment * i) * unit_factor / bbox.height / scale_factor
                else:
                    bbox = element.bounding_box()
                    new_horiz_scale = (so.expected_size + so.scale_increment * i) * unit_factor / bbox.width
                    new_vert_scale = (so.expected_size + so.scale_increment * i) * unit_factor / bbox.height
                if self.options.scale_type == "Horizontal":
                    if self.options.keep_aspect is False:
                        translation_matrix = [[new_horiz_scale, 0.0, 0.0], [0.0, 1.0, 0.0]]
                    else:
                        translation_matrix = [[new_horiz_scale, 0.0, 0.0], [0.0, new_horiz_scale, 0.0]]
                elif self.options.scale_type == "Vertical":
                    if self.options.keep_aspect is False:
                        translation_matrix = [[1.0, 0.0, 0.0], [0.0, new_vert_scale, 0.0]]
                    else:
                        translation_matrix = [[new_vert_scale, 0.0, 0.0], [0.0, new_vert_scale, 0.0]]
                else: #Uniform
                    translation_matrix = [[new_horiz_scale, 0.0, 0.0], [0.0, new_vert_scale, 0.0]]			
                element.transform = Transform(translation_matrix) @ element.composed_transform()
    			
                # now that the element moved we need to get the elements XY coordinates again to fix them
                bbox_new = element.bounding_box()
    
                #inkex.utils.debug(cx)
                #inkex.utils.debug(cy)
                #inkex.utils.debug(cx_new)
                #inkex.utils.debug(cy_new)
    		
                # We remove the transformation attribute from SVG XML tree in case it's regular path. In case the element is an object like arc,circle, ellipse or star we have the attribute "sodipodi:type". Then we do not play with it's path because the size transformation will not apply (this code block is ugly)
                if element.get ('sodipodi:type') is None and 'd' in element.attrib:
                    #inkex.utils.debug("it's a path!")
                    d = element.get('d')
                    p = CubicSuperPath(d)
                    transf = Transform(element.get("transform", None))
                    if 'transform' in element.attrib:
                        del element.attrib['transform']
                    p = Path(p).to_absolute().transform(transf, True)
                    element.set('d', Path(CubicSuperPath(p).to_path()))
                #else:
                    #inkex.utils.debug("it's an object!")
    		
                #we perform second translation to reset the center of the path	
                if isinstance (element, inkex.Rectangle) or \
                   isinstance (element, inkex.Circle) or \
                   isinstance (element, inkex.Ellipse):
                    translation_matrix = [
                                    [1.0, 0.0, scale_factor * (bbox.left - bbox_new.left + (bbox.width - bbox_new.width)/2)], 
                                    [0.0, 1.0, scale_factor * (bbox.top - bbox_new.top + (bbox.height - bbox_new.height)/2)]
                                ]            
                else:	
                    translation_matrix = [
                                    [1.0, 0.0, bbox.left - bbox_new.left + (bbox.width - bbox_new.width)/2], 
                                    [0.0, 1.0, bbox.top - bbox_new.top + (bbox.height - bbox_new.height)/2]
                                ]			
                element.transform = Transform(translation_matrix) @ element.composed_transform()	
		
if __name__ == '__main__':
    ScaleToSize().run()
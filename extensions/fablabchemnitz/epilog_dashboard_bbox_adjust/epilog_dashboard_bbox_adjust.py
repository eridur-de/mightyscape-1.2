#!/usr/bin/env python3

'''
Extension for InkScape 1.3
Features
- This tool is a helper to adjust the document border including an offset value, which is added. 
Sending vector data to Epilog Dashboard often results in trimmed paths. This leads to wrong geometry where the laser misses to cut them.
So we add a default (small) amount of 1.0 doc units to expand the document's canvas

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 21.04.2021
Last patch: 21.08.2023
License: GNU GPL v3

#known bugs/todo:
- viewbox/width/height do not correctly apply if documents only contain an object (not a path). After converting it to path it works. Seems to be a bbox problem
- note from 07.05.2021: seems if the following order is viewBox/width/height, or width/height/viewBox, the units are not respected. So we mess around a little bit
- add some way to handle translations properly

'''

import math
import sys
import inkex
from inkex import Transform
sys.path.append("../apply_transformations")

class EpilogDashboardBboxAdjust(inkex.EffectExtension):

    def getElementChildren(self, element, elements = None):
        if elements == None:
            elements = []
        if element.tag != inkex.addNS('g','svg'):
                elements.append(element)
        for child in element.getchildren():
            self.getElementChildren(child, elements)
        return elements

    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--apply_transformations", type=inkex.Boolean, default=False, help="Run 'Apply Transformations' extension before running vpype. Helps avoiding geometry shifting")
        pars.add_argument("--offset", type=float, default="1.0", help="XY Offset (mm) from top left corner")
        pars.add_argument("--removal", default="none", help="Remove all elements outside the bounding box or selection")
        pars.add_argument("--use_machine_size", type=inkex.Boolean, default=False, help="Use machine size")
        pars.add_argument("--machine_size", default="812x508", help="Machine/Size (mm)")
        pars.add_argument("--debug", type=inkex.Boolean, default=False, help="Debug output")
        pars.add_argument("--skip_errors", type=inkex.Boolean, default=False, help="Skip on errors")
        
    def effect(self):
        
        applyTransformationsAvailable = False # at first we apply external extension
        try:
            import apply_transformations
            applyTransformationsAvailable = True
        except Exception as e:
            # self.msg(e)
            self.msg("Calling 'Apply Transformations' extension failed. Maybe the extension is not installed. You can download it from official InkScape Gallery. Skipping ...")
             
        if self.options.apply_transformations is True and applyTransformationsAvailable is True:
            apply_transformations.ApplyTransformations().recursiveFuseTransform(self.document.getroot()) 
        
        offset = self.options.offset
        units = self.svg.unit
        #https://wiki.inkscape.org/wiki/Units_In_Inkscape

        # create a new bounding box and get the bbox size of all elements of the document (we cannot use the page's bbox)
        bbox = inkex.BoundingBox()
        if len(self.svg.selected) > 0:
            #bbox = self.svg.selection.bounding_box() #it could be so easy! But ...
            for element in self.svg.selected.values():

                if isinstance (element, inkex.TextElement) or \
                     isinstance (element, inkex.Tspan):
                    if self.options.skip_errors is False:
                        self.msg("Text elements are not supported!")
                        return
                    else:
                        continue
                else:
                    bbox += element.bounding_box()
        else:
            #for element in self.svg.root.getchildren():
            for element in self.document.getroot().iter("*"):
                if isinstance (element, inkex.ShapeElement) and element.tag != inkex.addNS('use','svg') and element.get('inkscape:groupmode') != 'layer': #bbox fails for svg:use elements and layers:
                    if isinstance (element, inkex.TextElement) or \
                         isinstance (element, inkex.Tspan):
                        if self.options.skip_errors is False:
                            self.msg("Text elements are not supported!")
                            return
                        else:
                            continue
                    else:
                        bbox += element.bounding_box()         

        if abs(bbox.width) == math.inf or abs(bbox.height) == math.inf:
            inkex.utils.debug("Error while calculating overall bounding box! Check your element types. Things like svg:text or svg:use are not supported. Impossible to continue!")
            return

    # adjust the viewBox to the bbox size and add the desired offset
        if self.options.use_machine_size is True:
            machineWidth = self.svg.unittouu(self.options.machine_size.split('x')[0] + "mm")
            machineHeight = self.svg.unittouu(self.options.machine_size.split('x')[1] + "mm")
            width = f'{machineWidth}' + units
            height = f'{machineHeight}' + units
            viewBoxXmin = -offset
            viewBoxYmin = -offset
            viewBoxXmax = machineWidth
            viewBoxYmax = machineHeight
        else:
            width = f'{bbox.width + offset * 2}' + units
            height = f'{bbox.height + offset * 2}' + units
            viewBoxXmin = -offset
            viewBoxYmin = -offset
            viewBoxXmax = bbox.width + offset * 2
            viewBoxYmax = bbox.height + offset * 2
        self.document.getroot().attrib['width'] = width
        self.document.getroot().attrib['viewBox'] = f'{viewBoxXmin} {viewBoxYmin} {viewBoxXmax} {viewBoxYmax}'
        self.document.getroot().attrib['height'] = height
        
        if self.options.removal == "outside_canvas":
            for element in self.document.getroot().iter("*"):
                if isinstance (element, inkex.ShapeElement) and element.tag != inkex.addNS('g', 'svg'):
                    ebbox = element.bounding_box()
                    #inkex.utils.debug("{:02f} < {:02f} {}".format(ebbox.right, viewBoxXmin, ebbox.right < viewBoxXmin))
                    #inkex.utils.debug("{:02f} > {:02f} {}".format(ebbox.left, viewBoxXmax, ebbox.left > viewBoxXmax))
                    #inkex.utils.debug("{:02f} < {:02f} {}".format(ebbox.top, viewBoxYmin, ebbox.top < viewBoxYmin))
                    #inkex.utils.debug("{:02f} > {:02f} {}".format(ebbox.bottom, viewBoxYmax, ebbox.bottom > viewBoxYmax))
                    #self.msg("{} | bbox: left = {:0.3f} right = {:0.3f} top = {:0.3f} bottom = {:0.3f}".format(element.get('id'), ebbox.left, ebbox.right, ebbox.top, ebbox.bottom))
                    #check if the element's bbox is inside the view canvas. If not: delete it!
                    if ebbox.right  < viewBoxXmin or \
                       ebbox.left   > viewBoxXmax or \
                       ebbox.top    < viewBoxYmin or \
                       ebbox.bottom > viewBoxYmax:
                        if self.options.debug is True:
                            self.msg("Removing {} {}".format(element.get('id'), ebbox))
                        element.delete()
        if self.options.removal == "outside_selection":
            if len(self.svg.selected) == 0:
                inkex.utils.debug("Your selection is empty but you have chosen the option to remove all elements outside selection!")
                return
            allElements = []
            for selected in self.svg.selection:
                allElements = self.getElementChildren(selected, allElements)
            for element in self.document.getroot().iter("*"):
                if element not in allElements and isinstance (element, inkex.ShapeElement) and element.tag != inkex.addNS('g', 'svg'):
                    if self.options.debug is True:
                        self.msg("Removing {}".format(element.get('id')))
                    element.delete()
                    
        # translate all remaining elements to fit the adjusted viewBox
        mat = Transform("translate(%f, %f)" % (-bbox.left,-bbox.top))
        for element in self.document.getroot().iter("*"):
            if isinstance (element, inkex.ShapeElement) and element.tag != inkex.addNS('g', 'svg'):
                element.transform = Transform(mat) @ element.composed_transform()
   

if __name__ == '__main__':
    EpilogDashboardBboxAdjust().run()
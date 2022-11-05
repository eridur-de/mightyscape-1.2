#!/usr/bin/env python3

import logging
logger = logging.getLogger()
logger.setLevel(level=logging.ERROR) #we set this to error before importing vpype to ignore the nasty output "WARNING:root:!!! `vpype.Length` is deprecated, use `vpype.LengthType` instead."

import sys
import os
from lxml import etree

import inkex
from inkex import transforms, bezier, PathElement
from inkex.paths import CubicSuperPath, Path
from inkex.command import inkscape

import vpype
import vpype_viewer
from vpype_viewer import ViewMode
from vpype_cli import execute

logger = logging.getLogger()
logger.setLevel(level=logging.WARNING) #after importing vpype we enabled logging again

import warnings # we import this to suppress moderngl warnings from vpype_viewer

from shapely.geometry import LineString, Point

"""
Extension for InkScape 1.X
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 02.04.2021
Last patch: 06.06.2021
License: GNU GPL v3

This piece of spaghetti-code, called "vpypetools", is a wrapper to pass (pipe) line elements from InkScape selection (or complete canvas) to vpype. 
It allows to run basic commands on the geometry. The converted lines are getting pushed back into InkScape. 
vpypetools allows to enable some important adjusters and debugging settings to get the best out of it.

vpypetools is based on 
 - Aaron Spike's "Flatten Bezier" extension, licensed by GPL v2
 - a lot of other extensions to rip off the required code pieces ;-)
 - used (tested) version of vpype: commit id https://github.com/abey79/vpype/commit/0b0dc8dd7e32998dbef639f9db578c3bff02690b (29.03.2021)
 - used (tested) version of vpype occult: commit id https://github.com/LoicGoulefert/occult/commit/2d04ca57d69078755c340066c226fd6cd927d41e (04.02.2021)

CLI / API docs:
- https://vpype.readthedocs.io/en/stable/api/vpype_cli.html#module-vpype_cli
- https://vpype.readthedocs.io/en/stable/api/vpype.html#module-vpype

Todo's
- find some python code to auto-convert strokes and objects to paths (for input and for output again)
- remove fill property of converted lines (because there is no fill anymore) without crashing Inkscape ...
- as we use flatten() we modify the original path. rewrite to avoid modifications to original path
"""

class vpypetools (inkex.EffectExtension):

    def add_arguments(self, pars):
        
        # Line Sorting
        pars.add_argument("--linesort", type=inkex.Boolean, default=False)
        pars.add_argument("--linesort_no_flip", type=inkex.Boolean, default=False, help="Disable reversing stroke direction for optimization")
        
        # Line Merging
        pars.add_argument("--linemerge", type=inkex.Boolean, default=False)
        pars.add_argument("--linemerge_tolerance", type=float, default=0.500, help="Maximum distance between two line endings that should be merged (default 0.500 mm)")
        pars.add_argument("--linemerge_no_flip", type=inkex.Boolean, default=False, help="Disable reversing stroke direction for merging")
  
        # Trimming
        pars.add_argument("--trim", type=inkex.Boolean, default=False)
        pars.add_argument("--trim_x_margin", type=float, default=0.000, help="trim margin - x direction (mm)") # keep default at 0.000 to keep clean bbox
        pars.add_argument("--trim_y_margin", type=float, default=0.000, help="trim margin - y direction (mm)") # keep default at 0.000 to keep clean bbox
    
        # Relooping
        pars.add_argument("--reloop", type=inkex.Boolean, default=False)
        pars.add_argument("--reloop_tolerance", type=float, default=0.500, help="Controls how close the path beginning and end must be to consider it closed (default 0.500 mm)")
 
        # Multipass
        pars.add_argument("--multipass", type=inkex.Boolean, default=False)
        pars.add_argument("--multipass_count", type=int, default=2, help="How many passes for each line (default 2)")
 
        # Filter
        pars.add_argument("--filter", type=inkex.Boolean, default=False)
        pars.add_argument("--filter_tolerance", type=float, default=0.050, help="Tolerance used to determined if a line is closed or not (default 0.050 mm)")
        pars.add_argument("--filter_closed", type=inkex.Boolean, default=False, help="Keep closed lines")
        pars.add_argument("--filter_not_closed", type=inkex.Boolean, default=False, help="Keep open lines")
        pars.add_argument("--filter_min_length_enabled", type=inkex.Boolean, default=False, help="filter by min length")
        pars.add_argument("--filter_min_length", type=float, default=0.000, help="Keep lines whose length isn't shorter than value")
        pars.add_argument("--filter_max_length_enabled", type=inkex.Boolean, default=False, help="filter by max length") 
        pars.add_argument("--filter_max_length", type=float, default=0.000, help="Keep lines whose length isn't greater than value") 
 
        # Split All
        pars.add_argument("--splitall", type=inkex.Boolean, default=False)
 
        # Plugin Occult
        pars.add_argument("--plugin_occult", type=inkex.Boolean, default=False)
        pars.add_argument("--plugin_occult_tolerance", type=float, default=0.01, help="Max distance between start and end point to consider a path closed (default 0.01 mm)")
        pars.add_argument("--plugin_occult_keepseparatelayer", type=inkex.Boolean, default=False, help="Put occulted lines to separate layer")

        # Plugin Deduplicate
        pars.add_argument("--plugin_deduplicate", type=inkex.Boolean, default=False)
        pars.add_argument("--plugin_deduplicate_tolerance", type=float, default=0.01, help="Max distance between points to consider them equal (default 0.01 mm)")
        pars.add_argument("--plugin_deduplicate_keepseparatelayer", type=inkex.Boolean, default=False, help="Put duplicate lines to separate layer")

        # Free Mode
        pars.add_argument("--tab")
        pars.add_argument("--freemode", type=inkex.Boolean, default=False)
        pars.add_argument("--freemode_cmd1", default="")
        pars.add_argument("--freemode_cmd1_enabled", type=inkex.Boolean, default=True)
        pars.add_argument("--freemode_cmd2", default="")
        pars.add_argument("--freemode_cmd2_enabled", type=inkex.Boolean, default=False)
        pars.add_argument("--freemode_cmd3", default="")
        pars.add_argument("--freemode_cmd3_enabled", type=inkex.Boolean, default=False)
        pars.add_argument("--freemode_cmd4", default="")
        pars.add_argument("--freemode_cmd4_enabled", type=inkex.Boolean, default=False)
        pars.add_argument("--freemode_cmd5", default="")
        pars.add_argument("--freemode_cmd5_enabled", type=inkex.Boolean, default=False)
        pars.add_argument("--freemode_show_cmd", type=inkex.Boolean, default=False)
 
        # General Settings
        pars.add_argument("--input_handling", default="paths", help="Input handling")
        pars.add_argument("--flattenbezier", type=inkex.Boolean, default=False, help="Flatten bezier curves to polylines")
        pars.add_argument("--flatness", type=float, default=0.1, help="Minimum flatness = 0.1. The smaller the value the more fine segments you will get (quantization).")
        pars.add_argument("--decimals", type=int, default=3, help="Accuracy for imported lines' coordinates into vpype. Does not work for 'Multilayer/document'")
        pars.add_argument("--simplify", type=inkex.Boolean, default=False, help="Reduces significantly the number of segments used to approximate the curve while still guaranteeing an accurate conversion, but may increase the execution time. Does not work for 'Singlelayer/paths'")
        pars.add_argument("--parallel", type=inkex.Boolean, default=False, help="Enables multiprocessing for the SVG conversion. This is recommended ONLY when using 'Simplify geometry' on large SVG files with many curved elements. Does not work for 'Singlelayer/paths'")
        pars.add_argument("--output_show", type=inkex.Boolean, default=False, help="This will open a separate window showing the finished SVG data. If enabled, output is not applied to InkScape canvas (only for preview)!")
        pars.add_argument("--output_show_points", type=inkex.Boolean, default=False, help="Enable point display in viewer")
        pars.add_argument("--output_stats", type=inkex.Boolean, default=False, help="Show output statistics before/after conversion")
        pars.add_argument("--output_trajectories", type=inkex.Boolean, default=False, help="Add paths for the travel trajectories")
        pars.add_argument("--keep_objects", type=inkex.Boolean, default=False, help="If false, selected paths will be removed")
        pars.add_argument("--strokes_to_paths", type=inkex.Boolean, default=True, help="Recommended option. Performs 'Path' > 'Stroke to Path' (CTRL + ALT + C) to convert vpype converted lines back to regular path objects")
        pars.add_argument("--use_style_of_first_element", type=inkex.Boolean, default=True, help="If enabled the first element in selection is scanned and we apply it's style to all imported vpype lines (but not for trajectories). Does not work for 'Multilayer/document'")
        pars.add_argument("--lines_stroke_width", type=float, default=1.0, help="Stroke width of tooling lines (px). Gets overwritten if 'Use style of first selected element' is enabled")
        pars.add_argument("--trajectories_stroke_width", type=float, default=1.0, help="Stroke width of trajectory lines (px). Gets overwritten if 'Use style of first selected element' is enabled")
 
    def effect(self):
        lc = vpype.LineCollection() # create a new array of LineStrings consisting of Points. We convert selected paths to polylines and grab their points
        elementsToWork = [] # we make an array of all collected nodes to get the boundingbox of that array. We need it to place the vpype converted stuff to the correct XY coordinates
          
        def flatten(node):
            #path = node.path.to_superpath()
            path = node.path.transform(node.composed_transform()).to_superpath()
            bezier.cspsubdiv(path, self.options.flatness)
            newpath = []
            for subpath in path:
                first = True
                for csp in subpath:
                    cmd = 'L'
                    if first:
                        cmd = 'M'
                    first = False
                    newpath.append([cmd, [csp[1][0], csp[1][1]]])
            node.path = newpath

        # flatten the node's path to linearize, split up the path to it's subpaths (break apart) and add all points to the vpype lines collection
        def convertPath(node, nodes = None):
            if nodes is None:
                nodes = []
            if node.tag == inkex.addNS('path','svg'):
                nodes.append(node)
                if self.options.flattenbezier is True:
                    flatten(node)

                raw = node.path.to_arrays()
                subPaths, prev = [], 0
                for i in range(len(raw)): # Breaks compound paths into simple paths
                    if raw[i][0] == 'M' and i != 0:
                        subPaths.append(raw[prev:i])
                        prev = i
                subPaths.append(raw[prev:])
                for subPath in subPaths:
                    points = []
                    for csp in subPath:
                        if len(csp[1]) > 0: #we need exactly two points per straight line segment
                            points.append(Point(round(csp[1][0], self.options.decimals), round(csp[1][1], self.options.decimals)))
                    if  len(subPath) > 2 and (subPath[-1][0] == 'Z' or subPath[0][1] == subPath[-1][1]):  #check if path has more than 2 points and is closed by Z or first pont == last point
                        points.append(Point(round(subPath[0][1][0], self.options.decimals), round(subPath[0][1][1], self.options.decimals))) #if closed, we add the first point again
                    lc.append(LineString(points))
                      
            children = node.getchildren()
            if children is not None: 
                for child in children:
                    convertPath(child, nodes)
            return nodes

        doc = None #create a vpype document
        
        '''
        if 'paths' we process paths only. Objects like rectangles or strokes like polygon have to be converted before accessing them
        if 'layers' we can process all layers in the complete document
        '''
        if self.options.input_handling == "paths":
            # getting the bounding box of the current selection. We use to calculate the offset XY from top-left corner of the canvas. This helps us placing back the elements
            input_bbox = None
            if len(self.svg.selected) == 0:
                elementsToWork = convertPath(self.document.getroot())
                for element in elementsToWork:
                    input_bbox += element.bounding_box()      
            else:
                elementsToWork = None
                for element in self.svg.selected.values():
                    elementsToWork = convertPath(element, elementsToWork)
                #input_bbox = inkex.elements._selected.ElementList.bounding_box(self.svg.selected) # get BoundingBox for selection
                input_bbox = self.svg.selection.bounding_box() # get BoundingBox for selection
            if len(lc) == 0:
                self.msg('Selection appears to be empty or does not contain any valid svg:path nodes. Try to cast your objects to paths using CTRL + SHIFT + C or strokes to paths using CTRL + ALT+ C')
                return  
            # find the first object in selection which has a style attribute (skips groups and other things which have no style)
            firstElementStyle = None
            for element in elementsToWork:
                if element.attrib.has_key('style'):
                    firstElementStyle = element.get('style')
            doc = vpype.Document(page_size=(input_bbox.width + input_bbox.left, input_bbox.height + input_bbox.top)) #create new vpype document     
            doc.add(lc, layer_id=None) # we add the lineCollection (converted selection) to the vpype document
            
        elif self.options.input_handling == "layers":
            doc = vpype.read_multilayer_svg(self.options.input_file, quantization = self.options.flatness, crop = False, simplify = self.options.simplify, parallel = self.options.parallel, default_width = self.document.getroot().get('width'), default_height = self.document.getroot().get('height'))

            for element in self.document.getroot().xpath("//svg:g", namespaces=inkex.NSS): #all groups/layers
                elementsToWork.append(element)

        tooling_length_before = doc.length()
        traveling_length_before = doc.pen_up_length()
        
        # build and execute the conversion command
        # the following code block is not intended to sum up the commands to build a series (pipe) of commands!
        ##########################################
        
        # Line Sorting
        if self.options.linesort is True:
            command = "linesort "
            if self.options.linesort_no_flip is True:
                command += " --no-flip"

        # Line Merging
        if self.options.linemerge is True:     
            command = "linemerge --tolerance " + str(self.options.linemerge_tolerance)
            if self.options.linemerge_no_flip is True:
                command += " --no-flip"
 
        # Trimming
        if self.options.trim is True:     
            command = "trim " + str(self.options.trim_x_margin) + " " + str(self.options.trim_y_margin)
 
        # Relooping
        if self.options.reloop is True:     
            command = "reloop --tolerance " + str(self.options.reloop_tolerance)
 
        # Multipass
        if self.options.multipass is True:     
            command = "multipass --count " + str(self.options.multipass_count)
 
        # Filter
        if self.options.filter is True:     
            command = "filter --tolerance " + str(self.options.filter_tolerance)
            if self.options.filter_min_length_enabled is True:
                command += " --min-length " + str(self.options.filter_min_length)
            if self.options.filter_max_length_enabled is True:
                command += " --max-length " + str(self.options.filter_max_length)
            if self.options.filter_closed is True and self.options.filter_not_closed is False:
                command += " --closed"
            if self.options.filter_not_closed is True and self.options.filter_closed is False:
                command += " --not-closed"
            if self.options.filter_closed is False and \
                self.options.filter_not_closed is False and \
                self.options.filter_min_length_enabled is False and \
                self.options.filter_max_length_enabled is False:
                self.msg('No filters to apply. Please select at least one filter.')
                return

        # Plugin Occult
        if self.options.plugin_occult is True:     
            command = "occult --tolerance " + str(self.options.plugin_occult_tolerance)
            if self.options.plugin_occult_keepseparatelayer is True:
                command += " --keep-occulted"

        # Plugin Deduplicate
        if self.options.plugin_deduplicate is True:     
            command = "deduplicate --tolerance " + str(self.options.plugin_deduplicate_tolerance)
            if self.options.plugin_deduplicate_keepseparatelayer is True:
                command += " --keep-duplicates"

        # Split All
        if self.options.splitall is True:     
            command = " splitall"

        # Free Mode
        if self.options.freemode is True:
            command = ""
            if self.options.freemode_cmd1_enabled is True:
                command += " " + self.options.freemode_cmd1.strip()
            if self.options.freemode_cmd2_enabled is True:
                command += " " + self.options.freemode_cmd2.strip()
            if self.options.freemode_cmd3_enabled is True:
                command += " " + self.options.freemode_cmd3.strip()
            if self.options.freemode_cmd4_enabled is True:
                command += " " + self.options.freemode_cmd4.strip()
            if self.options.freemode_cmd5_enabled is True:
                command += " " + self.options.freemode_cmd5.strip()
            if self.options.freemode_cmd1_enabled is False and \
                self.options.freemode_cmd2_enabled is False and \
                self.options.freemode_cmd3_enabled is False and \
                self.options.freemode_cmd4_enabled is False and \
                self.options.freemode_cmd5_enabled is False:
                self.msg("Warning: empty vpype pipeline. With this you are just getting read-write layerset/lineset.")
            else:
                if self.options.freemode_show_cmd is True:
                    self.msg("Your command pipe will be the following:")
                    self.msg(command)

        # self.msg(command)
        try:
            warnings.filterwarnings('ignore', 'SelectableGroups dict interface')
            doc = execute(command, doc)
        except Exception as e:
            self.msg("Error in vpype:\n" + str(e))
            return

        ##########################################
        
        tooling_length_after = doc.length()
        traveling_length_after = doc.pen_up_length()        
        if tooling_length_before > 0:
            tooling_length_saving = (1.0 - tooling_length_after / tooling_length_before) * 100.0
        else:
            tooling_length_saving = 0.0            
        if traveling_length_before > 0:
            traveling_length_saving = (1.0 - traveling_length_after / traveling_length_before) * 100.0
        else:
            traveling_length_saving = 0.0  
        if self.options.output_stats is True:
            self.msg('Total tooling length before vpype conversion: '   + str('{:0.2f}'.format(tooling_length_before))   + ' mm')
            self.msg('Total traveling length before vpype conversion: ' + str('{:0.2f}'.format(traveling_length_before)) + ' mm')
            self.msg('Total tooling length after vpype conversion: '    + str('{:0.2f}'.format(tooling_length_after))    + ' mm')
            self.msg('Total traveling length after vpype conversion: '  + str('{:0.2f}'.format(traveling_length_after))  + ' mm')
            self.msg('Total tooling length optimized: '   + str('{:0.2f}'.format(tooling_length_saving))   + ' %')
            self.msg('Total traveling length optimized: ' + str('{:0.2f}'.format(traveling_length_saving)) + ' %')
         
        if tooling_length_after == 0:
            self.msg('No lines left after vpype conversion. Conversion result is empty. Cannot continue. Check your document about containing any svg:path elements. You will need to convert objects and strokes to paths first! Vpype command chain was:')
            self.msg(command)
            return
         
        # show the vpype document visually
        if self.options.output_show:
            warnings.filterwarnings("ignore") # workaround to suppress annoying DeprecationWarning
            # vpype_viewer.show(doc, view_mode=ViewMode.PREVIEW, show_pen_up=self.options.output_trajectories, show_points=self.options.output_show_points, pen_width=0.1, pen_opacity=1.0, argv=None)
            vpype_viewer.show(doc, view_mode=ViewMode.PREVIEW, show_pen_up=self.options.output_trajectories, show_points=self.options.output_show_points, argv=None) # https://vpype.readthedocs.io/en/stable/api/vpype_viewer.ViewMode.html
            warnings.filterwarnings("default") # reset warning filter
            exit(0) #we leave the code loop because we only want to preview. We don't want to import the geometry
          
        # save the vpype document to new svg file and close it afterwards
        output_file = self.options.input_file + ".vpype.svg"
        output_fileIO = open(output_file, "w", encoding="utf-8")
        #vpype.write_svg(output_fileIO, doc, page_size=None, center=False, source_string='', layer_label_format='%d', show_pen_up=self.options.output_trajectories, color_mode='layer', single_path = True)       
        vpype.write_svg(output_fileIO, doc, page_size=None, center=False, source_string='', layer_label_format='%d', show_pen_up=self.options.output_trajectories, color_mode='layer')       
        #vpype.write_svg(output_fileIO, doc, page_size=(self.svg.unittouu(self.document.getroot().get('width')), self.svg.unittouu(self.document.getroot().get('height'))), center=False, source_string='', layer_label_format='%d', show_pen_up=self.options.output_trajectories, color_mode='layer')       
        output_fileIO.close()
        
        # parse the SVG file
        try:
            stream = open(output_file, 'r')
        except FileNotFoundError as e:
            self.msg("There was no SVG output generated by vpype. Cannot continue")
            exit(1)
        p = etree.XMLParser(huge_tree=True)
        import_doc = etree.parse(stream, parser=etree.XMLParser(huge_tree=True))
        stream.close()
          
        # handle pen_up trajectories (travel lines)
        trajectoriesLayer = import_doc.getroot().xpath("//svg:g[@id='pen_up_trajectories']", namespaces=inkex.NSS)
        if self.options.output_trajectories is True:
            if len(trajectoriesLayer) > 0:
                trajectoriesLayer[0].set('style', 'stroke:#0000ff;stroke-width:{:0.2f}px;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1;fill:none'.format(self.options.trajectories_stroke_width))
                trajectoriesLayer[0].attrib.pop('stroke') # remove unneccesary stroke attribute
                trajectoriesLayer[0].attrib.pop('fill') # remove unneccesary fill attribute
        else:
            if len(trajectoriesLayer) > 0:
                trajectoriesLayer[0].delete()
   
        lineLayers = import_doc.getroot().xpath("//svg:g[not(@id='pen_up_trajectories')]", namespaces=inkex.NSS) #all layer except the pen_up trajectories layer
        if self.options.use_style_of_first_element is True and self.options.input_handling == "paths" and firstElementStyle is not None:
            
            # if we remove the fill property and use "Use style of first element in layer" the conversion will just crash with an unknown reason
            #declarations = firstElementStyle.split(';')
            #for i, decl in enumerate(declarations):
            #    parts = decl.split(':', 2)
            #    if len(parts) == 2:
            #        (prop, val) = parts
            #        prop = prop.strip().lower()
            #        #if prop == 'fill':
            #        #   declarations[i] = prop + ':none'   
            for lineLayer in lineLayers:
                #lineLayer.set('style', ';'.join(declarations))
                lineLayer.set('style', firstElementStyle)
                lineLayer.attrib.pop('stroke') # remove unneccesary stroke attribute
                lineLayer.attrib.pop('fill') # remove unneccesary fill attribute

        else:
            for lineLayer in lineLayers:          
                if lineLayer.attrib.has_key('stroke'):
                    color = lineLayer.get('stroke')
                    lineLayer.set('style', 'stroke:' + color + ';stroke-width:{:0.2f}px;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1;fill:none'.format(self.options.lines_stroke_width))
                    lineLayer.attrib.pop('stroke') # remove unneccesary stroke attribute
                    lineLayer.attrib.pop('fill') # remove unneccesary fill attribute
                 
        import_viewBox = import_doc.getroot().get('viewBox').split(" ")
        self_viewBox = self.document.getroot().get('viewBox')
        
        if self_viewBox is not None: #some SVG files do not have this attribute
            self_viewBoxValues = self_viewBox.split(" ")
            scaleX = self.svg.unittouu(self_viewBoxValues[2]) / self.svg.unittouu(import_viewBox[2])
            scaleY = self.svg.unittouu(self_viewBoxValues[3]) / self.svg.unittouu(import_viewBox[3])

        for element in import_doc.getroot().iter("{http://www.w3.org/2000/svg}g"):
            e = self.document.getroot().append(element)
            if self.options.input_handling == "layers":
                if self_viewBox is not None:
                    element.set('transform', 'scale(' + str(scaleX) + ',' + str(scaleY) + ')') #imported groups need to be transformed. Or they have wrong size. Reason: different viewBox sizes/units in namedview definitions
       
            # convert vpype polylines/lines/polygons to regular paths again (objects to paths)
            if self.options.strokes_to_paths is True:     
                for line in element.iter("{http://www.w3.org/2000/svg}line"):
                    newLine = PathElement()
                    newLine.path = Path("M {},{} L {},{}".format(line.attrib['x1'], line.attrib['y1'], line.attrib['x2'], line.attrib['y2']))
                    element.append(newLine)
                    line.delete()
            
                for polyline in element.iter("{http://www.w3.org/2000/svg}polyline"):
                    newPolyLine = PathElement()
                    newPolyLine.path = Path('M' + polyline.attrib['points'])
                    element.append(newPolyLine)
                    polyline.delete()
    
                for polygon in element.iter("{http://www.w3.org/2000/svg}polygon"):
                    newPolygon = PathElement()
                    #newPolygon.path = Path('M' + " ".join(polygon.attrib['points'].split(' ')[:-1]) + ' Z') #remove the last point of the points string by splitting at whitespace, converting to array and removing the last item. then converting back to string
                    newPolygon.path = Path('M' + " ".join(polygon.attrib['points'].split(' ')) + ' Z')
                    element.append(newPolygon)
                    polygon.delete()

        # Delete the temporary file again because we do not need it anymore
        if os.path.exists(output_file):
            os.remove(output_file)
            
        # Remove selection objects to do a real replace with new objects from vpype document
        if self.options.keep_objects is False:
            for element in elementsToWork:
                element.delete()
    
if __name__ == '__main__':
    vpypetools().run()
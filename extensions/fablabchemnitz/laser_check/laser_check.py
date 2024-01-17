#!/usr/bin/env python3

import inkex
from inkex.bezier import csplength, csparea
from lxml import etree
import re
import math
import sys
from math import log
import datetime
import os
from collections import Counter

class LaserCheck(inkex.EffectExtension):
    
    '''
    ToDos:
     - inx:
         - set speed manually or pick machine (epilog) - travel and cut speed are prefilled then
         - calculate cut estimation with linear or non-linear (epilog) speeds > select formula or like this
         - select material (parameters -> how to???)
         - add fields for additional costs like configuring the machine or grabbing parts out of the machine (weeding), etc.
         - add mode select: cut, engrave
     - Handlungsempfehlungen einbauen
        - verweisen auf diverse plugins, die man nutzen kann:
            - migrate ungrouper
            - pointy paths
            - cleaner
            - styles to layers
            - apply transforms
            - epilog bbox adjust
        - wege zum Pfade fixen:
            - cut slower ( > muss aber auch leistung reduzieren - inb welchem umfang?)
            - sort
            - chaining with touching neighbours
            - remove path
            - remove modes/simplify
    - find duplicate lines
    - visualize results as a nice SVG rendered check list page with 
        - red/green/grey icons (failed, done, skipped) and calculate some scores
        - preview image
        - statistics
        - export as PDF
    - run as script to generate quick results for users
    - check for old styles which should be upgraded (cleanup styles tool)
    - check for elements which have no style attribute (should be created) -> (cleanup styles tool)
    - self-intersecting paths
    - number of parts (isles) to weed in total - this is an indicator for manually picking work; if we add bridges we have less work
    - number of parts which are smaller than vector grid
    - add some inkex.Desc to all elements which were checked and which have some issue. use special syntax to remove old stuff each time the check is applied again
    - this code is horrible ugly stuff
    - output time/cost estimations per stroke color
    '''
    
    def add_arguments(self, pars):
        pars.add_argument('--tab')
        
        pars.add_argument('--machine_size', default="812x508")
        pars.add_argument('--max_cutting_speed', type=float, default=120.0)
        pars.add_argument('--max_travel_speed', type=float, default=450.0)
        pars.add_argument('--job_time_offset', type=float, default=0.0)
        pars.add_argument('--price_per_minute_gross', type=float, default=2.0)
        pars.add_argument('--vector_grid_xy', type=float, default=12.0) #TODO
        pars.add_argument('--co2_power', type=float, default=60.0) #TODO
        pars.add_argument('--round_times', type=inkex.Boolean, default=True)
        
        pars.add_argument('--show_issues_only', type=inkex.Boolean, default=False)  
        pars.add_argument('--checks', default="check_all")
        pars.add_argument('--statistics', type=inkex.Boolean, default=False)
        pars.add_argument('--filesize_max', type=float, default=2048.000)
        pars.add_argument('--bbox', type=inkex.Boolean, default=False)
        pars.add_argument('--bbox_offset', type=float, default=5.000)
        pars.add_argument('--cutting_estimation', type=inkex.Boolean, default=False)
        pars.add_argument('--cutting_speedfactors', default="100 90 80 70 60 50 40 30 20 10 9 8 7 6 5 4 3 2 1")
        pars.add_argument('--elements_outside_canvas', type=inkex.Boolean, default=False)
        pars.add_argument('--groups_and_layers', type=inkex.Boolean, default=False)
        pars.add_argument('--nest_depth_max', type=int, default=2)
        pars.add_argument('--clones', type=inkex.Boolean, default=False)
        pars.add_argument('--clippaths', type=inkex.Boolean, default=False)
        pars.add_argument('--images', type=inkex.Boolean, default=False)
        pars.add_argument('--texts', type=inkex.Boolean, default=False)
        pars.add_argument('--filters', type=inkex.Boolean, default=False)
        pars.add_argument('--lowlevelstrokes', type=inkex.Boolean, default=False)
        pars.add_argument('--style_types', type=inkex.Boolean, default=False)
        pars.add_argument('--stroke_colors', type=inkex.Boolean, default=False)
        pars.add_argument('--stroke_colors_max', type=int, default=3)
        pars.add_argument('--stroke_widths', type=inkex.Boolean, default=False)
        pars.add_argument('--stroke_widths_max', type=int, default=1)
        pars.add_argument('--opacities', type=inkex.Boolean, default=False)
        pars.add_argument('--cosmestic_dashes', type=inkex.Boolean, default=False)
        pars.add_argument('--invisible_shapes', type=inkex.Boolean, default=False)
        pars.add_argument('--pointy_paths', type=inkex.Boolean, default=False)
        pars.add_argument('--combined_paths', type=inkex.Boolean, default=False)
        pars.add_argument('--transformations', type=inkex.Boolean, default=False)
        pars.add_argument('--short_paths', type=inkex.Boolean, default=False)
        pars.add_argument('--short_paths_min', type=float, default=1.000)
        pars.add_argument('--non_path_shapes', type=inkex.Boolean, default=False)
        pars.add_argument('--nodes_per_path', type=inkex.Boolean, default=False)
        pars.add_argument('--nodes_per_path_max', type=int, default=2)
        pars.add_argument('--nodes_per_path_interval', type=float, default=10.000)
        
    def effect(self):
        
        so = self.options
        docroot = self.document.getroot()
        
        machineWidth = self.svg.unittouu(so.machine_size.split('x')[0] + "mm")
        machineHeight = self.svg.unittouu(so.machine_size.split('x')[1] + "mm")
        selected = [] #total list of elements to parse

        
        def parseChildren(element):
            if element not in selected:
                selected.append(element)
            children = element.getchildren()
            if children is not None:
                for child in children:
                    if child not in selected:
                        selected.append(child)
                    parseChildren(child) #go deeper and deeper
        
        #check if we have selected elements or if we should parse the whole document instead
        if len(self.svg.selected) == 0:
            for element in docroot.iter(tag=etree.Element):
                if element != docroot:

                    selected.append(element)
        else:
            for element in self.svg.selected.values():
                parseChildren(element)
                
        namedView = docroot.find(inkex.addNS('namedview', 'sodipodi'))
        doc_units = namedView.get(inkex.addNS('document-units', 'inkscape'))        
        user_units = namedView.get(inkex.addNS('units'))  
        pagecolor = namedView.get('pagecolor')
        inkex.utils.debug("---------- Default checks")
        inkex.utils.debug("Document units: {}".format(doc_units))
        inkex.utils.debug("User units: {}".format(user_units))
        
        '''
        Check for scalings
            > Page size is determined by SVG root 'width' and 'height'.
            > 'viewBox' defined in 'user units' with the values: (x offset, y-offset, width, height).
            > Document scale is determined by ratio of 'width'/'height' to 'viewBox'.
        '''
        
        inkscapeScale = self.svg.inkscape_scale #this is the "Scale:" value at "Display tab"
        #docScale = self.svg.scale
        #docWidth = self.svg.viewport_width
        #docHeight = self.svg.viewport_height
        #inkex.utils.debug("Document scale (x/y)={:0.3f}".format(docScale))
        #inkex.utils.debug("Document width={:0.3f}".format(docWidth))
        vxMin, vyMin, vxMax, vyMax = self.svg.get_viewbox()
        #vxTotal = vxMax - vxMin
        #vyTotal = vyMax - vyMin
        #vScaleX = self.svg.unittouu(str(vxTotal / docWidth) + doc_units)
        #vScaleXpx = self.svg.unittouu(str(vxTotal / docWidth) + "px")
        #vScaleY = vyTotal / docHeight #should/must be the same as vScaleX value
        #inkex.utils.debug(vxTotal)
        #inkex.utils.debug(vyTotal)
        #inkex.utils.debug(vScaleY)
        #inkex.utils.debug("Document scale (x/y): {:0.5f}{} ({:0.5f}px)".format(vScaleX, doc_units, vScaleXpx))
        #if round(vScaleX, 5) != 1.0:
        #    inkex.utils.debug("WARNING: Document scale not 100%!")
        inkex.utils.debug("Document scale (x/y): {:0.5f}".format(inkscapeScale))
        scaleOk = True
        if round(inkscapeScale, 5) != 1.0:
            scaleOk = False
            inkex.utils.debug("WARNING: Document scale not 100%!")
        scaleX = namedView.get('scale-x')
        if scaleX is not None:
            inkex.utils.debug("WARNING: Document has scale-x attribute with value={}".format(scaleX)) 
        
        inkex.utils.debug("Viewbox:\n  x.min = {:0.0f}\n  y.min = {:0.0f}\n  x.max = {:0.0f}\n  y.max = {:0.0f}".format( vxMin, vyMin, vxMax, vyMax))
        viewboxOk = True
        if vxMin < 0 or vyMin < 0 or vxMax < 0 or vyMax < 0:
            viewboxOk = False
            # values may be lower than 0, but it does not make sense. The viewbox defines the top-left corner, which is usually 0,0. In case we want to allow that, we need to convert all bounding boxes accordingly. See also https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/viewBox.
            inkex.utils.debug("WARNING: Viewbox does not start at 0,0. Visible results will differ from real coordinates.")
      
        '''
        The SVG format is highly complex and offers a lot of possibilities. Most things of SVG we do not
        need for a laser cutter. Usually we need svg:path and maybe svg:image; we can drop a lot of stuff
        like svg:defs, svg:desc, etc.
        '''
        nonShapes = []
        shapes = [] #this may contains paths, rectangles, circles, groups and more
        for element in selected:       
            if not isinstance(element, inkex.ShapeElement):
                if element.tag not in (
                        "{http://www.w3.org/2000/svg}defs", 
                        "{http://www.w3.org/2000/svg}metadata", 
                        "{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}namedview",
                        "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF",
                        "{http://creativecommons.org/ns#}Work"):
                    nonShapes.append(element)
            else:
                shapes.append(element)
        if so.show_issues_only is False:        
            inkex.utils.debug("{} shape elements in total".format(len(shapes)))
            inkex.utils.debug("{} non-shape elements in total".format(len(nonShapes)))
        for nonShape in nonShapes:
            inkex.utils.debug("non-shape id={}".format(nonShape.get('id')))
        
        
        #that size is actually not the stored one on file system
        #filesize = len(etree.tostring(self.document, pretty_print=True).decode('UTF-8')) / 1000
        filesize = 0
        if os.path.exists(self.document_path()) is False:
            inkex.utils.debug("WARNING: File was not saved yet!")
        else:
            filesize = os.path.getsize(self.document_path()) / 1000
        inkex.utils.debug("File size: {:0.1f} KB (That might be wrong. Check first for recently saved file)".format(filesize))
        if filesize > so.filesize_max:
            inkex.utils.debug("WARNING: file size is larger than allowed: {} KB > {} KB".format(filesize, so.filesize_max))
            
        inkex.utils.debug("Total overview of element types:")
        elementTypes = []
        for element in selected:
            if element not in elementTypes:
                elementTypes.append(element.tag
                    .replace("{http://www.w3.org/2000/svg}", "")
                    .replace("{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}", "")
                    .replace("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}", "")
                    .replace("{http://creativecommons.org/ns#}", "")
                    .replace("{http://www.inkscape.org/namespaces/inkscape}", "")
                )
        
        counter = Counter(elementTypes)
        uniqElementTypes = counter
        for key in counter.keys():
            inkex.utils.debug(" - {}: {}x".format(key, counter[key]))

        '''
        Nearly each laser job needs a bit of border to place the material inside the laser. Often
        we have to fixate on vector grid, pin grid or task plate. Thus we need tapes or pins. So we 
        leave some borders off the actual part geometries.
        '''
        if so.checks == "check_all" or so.bbox is True:
            inkex.utils.debug("\n---------- Borders around all elements - minimum offset {} mm from each side".format(so.bbox_offset))
            if scaleOk is False:
                inkex.utils.debug("WARNING: Document scale is not 100%. Calculating bounding boxes might create wrong results.")
            if viewboxOk is False:
                inkex.utils.debug("WARNING: Viewbox does not start at 0,0. Calculating bounding boxes might create wrong results.")
            bbox = inkex.BoundingBox()
            for element in selected:
            #for element in docroot.iter(tag=etree.Element):
                if element != docroot and isinstance(element, inkex.ShapeElement) and element.tag != inkex.addNS('use','svg') and element.get('inkscape:groupmode') != 'layer': #bbox fails for svg:use elements and layers
                    transform = inkex.Transform()
                    parent = element.getparent()
                    if parent is not None and isinstance(parent, inkex.ShapeElement):
                        transform = parent.composed_transform()
                    try:
                        if isinstance (element, inkex.TextElement) or isinstance (element, inkex.Tspan):
                            continue
                        else:  
                            bbox += element.bounding_box(transform)
                    except Exception:
                        transform = element.composed_transform()
                        x1, y1 = transform.apply_to_point([0, 0])
                        x2, y2 = transform.apply_to_point([1, 1])
                        bbox += inkex.BoundingBox((x1, x2), (y1, y2))
     
            if abs(bbox.width) == math.inf or abs(bbox.height) == math.inf:
                inkex.utils.debug("bounding box could not be calculated. SVG seems to be empty.")
            #else:
            #    inkex.utils.debug("bounding box is {}".format(bbox))
            inkex.utils.debug("bounding box is:\n  x.min = {}\n  y.min = {}\n  x.max = {}\n  y.max = {}".format(bbox.left, bbox.top, bbox.right, bbox.bottom))
            page_width = self.svg.unittouu(docroot.attrib['width'])
            width_height = self.svg.unittouu(docroot.attrib['height'])
            fmm = self.svg.unittouu(str(so.bbox_offset) + "mm")
            bb_left = round(bbox.left, 3)
            bb_right = round(bbox.right, 3)
            bb_top = round(bbox.top, 3)
            bb_bottom = round(bbox.bottom, 3)
            bb_width = round(bbox.width, 3)
            bb_height = round(bbox.height, 3)
    
            if bb_left >= fmm:
                if so.show_issues_only is False:
                    inkex.utils.debug("left border... ok")
            else:
                inkex.utils.debug("left border... fail: {:0.3f} mm".format(self.svg.uutounit(bb_left, "mm")))
                 
            if bb_top >= fmm:
                if so.show_issues_only is False:
                    inkex.utils.debug("top border... ok")
            else:
                inkex.utils.debug("top border... fail: {:0.3f} mm".format(self.svg.uutounit(bb_top, "mm")))
                
            if bb_right + fmm <= page_width:
                if so.show_issues_only is False:
                    inkex.utils.debug("right border... ok")
            else:
                inkex.utils.debug("right border... fail: {:0.3f} mm".format(self.svg.uutounit(bb_right, "mm")))
                
            if bb_bottom + fmm <= width_height:
                if so.show_issues_only is False:
                    inkex.utils.debug("bottom border... ok")
            else:
                inkex.utils.debug("bottom border... fail: {:0.3f} mm".format(self.svg.uutounit(bb_bottom, "mm")))
            if bb_width <= machineWidth:
                if so.show_issues_only is False:
                    inkex.utils.debug("page width... ok")
            else:
                inkex.utils.debug("page width... fail: {:0.3f} mm".format(bb_width))
            if bb_height <= machineHeight:
                if so.show_issues_only is False:
                    inkex.utils.debug("page height... ok")
            else:
                inkex.utils.debug("page height... fail: {:0.3f} mm".format(bb_height))
             
        
        '''
        We check for possible deep nested groups/layers, empty groups/layers or groups/layers with styles.
        '''
        if so.checks == "check_all" or so.groups_and_layers is True:
            inkex.utils.debug("\n---------- Groups and layers")
            global md
            md = 0
            def maxDepth(element, level): 
                global md
                if (level == md):
                    md += 1
                for child in element:
                    maxDepth(child, level + 1) 
            maxDepth(docroot, -1)
            if so.show_issues_only is False:        
               inkex.utils.debug("Maximum group depth={}".format(md - 1))
            if md - 1 > so.nest_depth_max:
                inkex.utils.debug("Warning: maximum allowed group depth reached: {}".format(so.nest_depth_max))
            groups = []
            layers = []
            for element in selected:
                if element.tag == inkex.addNS('g','svg'):
                    if element.get('inkscape:groupmode') == 'layer':
                        layers.append(element)
                    else:
                        groups.append(element)

            if so.show_issues_only is False:  
                inkex.utils.debug("{} groups in total".format(len(groups)))
                inkex.utils.debug("{} layers in total".format(len(layers)))
    
            #check for empty groups
            for group in groups:
                if len(group) == 0:
                    inkex.utils.debug("id={} is empty group".format(group.get('id')))
    
            #check for empty layers
            for layer in layers:
                if len(layer) == 0:
                    inkex.utils.debug("id={} is empty layer".format(layer.get('id')))

        '''
        Style scheme in svg. We can style elements by ...
        - "style" attribute for elements like svg:path
        - dedicated attributes for elements like svg:path
        - "style" attributes or dedicated attributes at group level
        - css class together with svg:style elements
        For a cleaner file we should avoid to mess up. Best is to define styles 
        at svg:path level or using properly defined css classes
        We can use "Cleanup Styles" and "Styles To Layers" extension to change this behaviour.
        '''
        if so.checks == "check_all" or so.style_types is True: 
            inkex.utils.debug("\n---------- Style types")
            groupStyles = []
            svgStyleElements = []
            styleInNonGroupLayerShapes = []
            dedicatedStylesInNonGroupLayerShapes = []
            dedicatedStyleDict = []
            dedicatedStyleDict.extend(['opacity', 'stroke', 'stroke-opacity', 'stroke-width', 'stroke-dasharray', 'stroke-dashoffset', 'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit', 'fill', 'fill-opacity'])

            for element in selected:
                if element.tag == inkex.addNS('g','svg'):
                    if element.style is not None and element.style != "": #style may also be just empty (weird, but was validated on 21.12.2021)
                        groupStyles.append(element)
                if element.tag == inkex.addNS('style', 'svg'):
                    svgStyleElements.append(element)
            for element in shapes:
                if element.tag != inkex.addNS('g','svg'):
                    if element.style is not None:
                        styleInNonGroupLayerShapes.append(element)
                    for dedicatedStyleItem in dedicatedStyleDict:
                        if element.attrib.has_key(str(dedicatedStyleItem)):
                            dedicatedStylesInNonGroupLayerShapes.append(element)           
            if so.show_issues_only is False:
                inkex.utils.debug("{} groups/layers with style in total".format(len(groupStyles)))
                inkex.utils.debug("{} svg:style elements in total".format(len(svgStyleElements)))
                inkex.utils.debug("{} shapes using style attribute in total".format(len(svgStyleElements)))
                inkex.utils.debug("{} shapes using dedicated style attributes in total".format(len(dedicatedStylesInNonGroupLayerShapes)))
            for groupStyle in groupStyles:
                inkex.utils.debug("group id={} has style".format(groupStyle.get('id')))
            for svgStyleElement in svgStyleElements:
                inkex.utils.debug("id={} is svg:style element".format(svgStyleElement.get('id')))
            for styleInNonGroupLayerShape in styleInNonGroupLayerShapes:
                inkex.utils.debug("id={} has style attribute".format(styleInNonGroupLayerShape.get('id')))
            for dedicatedStylesInNonGroupLayerShape in dedicatedStylesInNonGroupLayerShapes:
                inkex.utils.debug("id={} used dedicated style attribute(s)".format(dedicatedStylesInNonGroupLayerShape.get('id')))
                
                       
        '''
        Clones should be unlinked because they cause similar issues like transformations
        '''
        if so.checks == "check_all" or so.clones is True:
            inkex.utils.debug("\n---------- Clones (svg:use) - maybe unlink") 
            uses = []
            for element in selected:
                if element.tag == inkex.addNS('use','svg'):
                    uses.append(element)
            if so.show_issues_only is False:
                inkex.utils.debug("{} svg:use clones in total".format(len(uses)))
            for use in uses:
                inkex.utils.debug("id={}".format(use.get('id')))
   
   
        '''
        Clip paths are neat to visualize things, but they do not perform a real path cutting.
        Please perform real intersections to have an intact target geometry.
        '''
        if so.checks == "check_all" or so.clippaths is True:
            inkex.utils.debug("\n---------- Clippings (svg:clipPath) - please replace with real cut paths") 
            clipPaths = []
            for element in selected:
                if element.tag == inkex.addNS('clipPath','svg'):
                    clipPaths.append(element)
            if so.show_issues_only is False:
                inkex.utils.debug("{} svg:clipPath in total".format(len(clipPaths)))
            for clipPath in clipPaths:
                inkex.utils.debug("id={}".format(clipPath.get('id')))
   
   
        '''
        Sometimes images look like vector but they are'nt. In case you dont want to perform engraving, either
        check to drop or trace to vector paths
        '''
        if so.checks == "check_all" or so.images is True:
            inkex.utils.debug("\n---------- Images (svg:image) - maybe trace to svg") 
            images = []
            for element in selected:
                if element.tag == inkex.addNS('image','svg'):
                    images.append(element)
            if so.show_issues_only is False:
                inkex.utils.debug("{} svg:image in total".format(len(images)))
            for image in images:
                inkex.utils.debug("image id={}".format(image.get('id')))
    
    
        '''
        Low level strokes cannot be properly edited in Inkscape (no node handles). Converting helps
        '''
        if so.checks == "check_all" or so.lowlevelstrokes is True:
            inkex.utils.debug("\n---------- Low level strokes (svg:line/polyline/polygon) - maybe convert to path") 
            lowlevels = []
            for element in selected:
                if element.tag in (inkex.addNS('line','svg'), inkex.addNS('polyline','svg'), inkex.addNS('polygon','svg')):
                    lowlevels.append(element)
            if so.show_issues_only is False:
                inkex.utils.debug("{} low level strokes in total".format(len(lowlevels)))
            for lowlevel in lowlevels:
                inkex.utils.debug("id={}".format(lowlevel.get('id')))
    
    
        '''
        Texts cause problems when sharing with other people. You must ensure that everyone has the
        font files installed you used. Convert to paths avoids this issue and guarantees same result
        everywhere.
        '''
        if so.checks == "check_all" or so.texts is True:
            inkex.utils.debug("\n---------- Texts (should be converted to paths)") 
            texts = []
            for element in selected:
                if element.tag == inkex.addNS('text','svg'):
                    texts.append(element)
            if so.show_issues_only is False:
                inkex.utils.debug("{} svg:text in total".format(len(texts)))
            for text in texts:
                inkex.utils.debug("id={}".format(text.get('id')))
             

        '''
        Filters on elements let Epilog Software Suite always think vectors should get to raster image data. That might be good sometimes,
        but not in usual case.
        '''
        if so.checks == "check_all" or so.filters is True:
            inkex.utils.debug("\n---------- Filters (should be removed to keep vector characterism)") 

            filter_elements = []
            for element in selected:
                if element.tag == inkex.addNS('filter','svg'):
                    filter_elements.append(element)                    
            filter_styles = []
            if so.show_issues_only is False:
                inkex.utils.debug("{} filters (as svg:filter) in total".format(len(filter_elements)))
            for filter_element in filter_elements:
                inkex.utils.debug("id={}".format(filter_element.get('id')))
                
            for element in selected:
                filter_style = [element, element.style.get('filter')]
                if filter_style[1] is None or filter_style[1]  == "none":
                    filter_style[1] = "none"
                if filter_style[1] != "none" and filter_style not in filter_styles:
                    filter_styles.append(filter_style)
            if so.show_issues_only is False:
                inkex.utils.debug("{} filters (in styles) in total".format(len(filter_styles)))
            for filter_style in filter_styles:
                inkex.utils.debug("id={}, filter={}".format(filter_style[0].get('id'), filter_style[1]))
            
        
        '''
        The more stroke colors the more laser job configuration is required. Reduce the SVG file
        to a minimum of stroke colors to be quicker. Note that a None stroke might be same like #000000 but thats not guaranteed
        '''
        if so.checks == "check_all" or so.stroke_colors is True:
            inkex.utils.debug("\n---------- Stroke colors ({} are allowed)".format(so.stroke_colors_max))
            strokeColors = []
            for element in shapes:
                strokeColor = element.style.get('stroke')
                if  strokeColor not in strokeColors: #we also add None (default value is #000000 then) and "none" values. 
                    strokeColors.append(strokeColor)
            if so.show_issues_only is False:
                inkex.utils.debug("{} different stroke colors in total".format(len(strokeColors)))
            if len(strokeColors) > so.stroke_colors_max:
                for strokeColor in strokeColors:
                    inkex.utils.debug("stroke color {}".format(strokeColor))
                    
      
        '''
        Different stroke widths might behave the same like different stroke colors. Reduce to a minimum set.
        Ideally all stroke widths are set to 1 pixel.
        '''
        if so.checks == "check_all" or so.stroke_widths is True:              
            inkex.utils.debug("\n---------- Stroke widths ({} are allowed)".format(so.stroke_widths_max))
            strokeWidths = []
            for element in shapes:  
                strokeWidth = element.style.get('stroke-width')
                if strokeWidth not in strokeWidths: #we also add None and "none" values. Default width for None value seems to be 1px
                    strokeWidths.append(strokeWidth)
            if so.show_issues_only is False:
                inkex.utils.debug("{} different stroke widths in total".format(len(strokeWidths)))
            if len(strokeWidths) > so.stroke_widths_max:
                for strokeWidth in strokeWidths:
                    if strokeWidth is None:
                        inkex.utils.debug("stroke width: default (None, system standard value)")
                    elif strokeWidth == "none":
                        inkex.utils.debug("stroke width: none (invisible)")
                    else:
                        swConverted = self.svg.uutounit(float(self.svg.unittouu(strokeWidth))) #possibly w/o units. we unify to some internal float. The value "none" converts to 0.0
                        inkex.utils.debug("stroke width: {}px ({}mm)".format(
                            round(self.svg.uutounit(swConverted, "px"),4),
                            round(self.svg.uutounit(swConverted, "mm"),4),
                            ))
                
                
        '''
        Cosmetic dashes cause simulation issues and are no real cut paths. It's similar to the thing
        with clip paths. Please convert lines to real dash segments if you want to laser them.
        '''
        if so.checks == "check_all" or so.cosmestic_dashes is True:   
            inkex.utils.debug("\n---------- Cosmetic dashes - should be converted to paths")
            strokeDasharrays = []
            for element in shapes:  
                strokeDasharray = element.style.get('stroke-dasharray')
                if strokeDasharray is not None and strokeDasharray != 'none' and strokeDasharray not in strokeDasharrays:
                    strokeDasharrays.append(strokeDasharray)
            if so.show_issues_only is False:
                inkex.utils.debug("{} different stroke dash arrays in total".format(len(strokeDasharrays)))
            for strokeDasharray in strokeDasharrays:
                inkex.utils.debug("stroke dash array {}".format(strokeDasharray))
     
  
        '''
        Shapes/paths with the same color like the background, 0% opacity, etc. lead to strange
        laser cutting results, like duplicated edges, enlarged laser times and more. Please double
        check for such occurences.
        Please transfer styles from layers/groups level to element level! You can use "Cleanup Styles" extension to do that
        '''
        if so.checks == "check_all" or so.invisible_shapes is True:     
            inkex.utils.debug("\n---------- Invisible shapes")
            invisibles = []
            for element in shapes:
                if element.tag not in (inkex.addNS('tspan','svg')) and element.get('inkscape:groupmode') != 'layer' and not isinstance(element, inkex.Group):                             
                    strokeAttr = element.get('stroke') #same information could be in regular attribute instead nested in style attribute
                    if strokeAttr is None or strokeAttr == "none":
                        strokeVis = 0
                    elif strokeAttr in ('#ffffff', 'white', 'rgb(255,255,255)'):
                        strokeVis = 0
                    else:
                        strokeVis = 1
                    stroke = element.style.get('stroke')
                    if stroke is not None:
                        if stroke == "none":
                            strokeVis = 0
                        elif stroke in ('#ffffff', 'white', 'rgb(255,255,255)'):
                            strokeVis = 0
                        else:
                            strokeVis = 1
                    
                    
                    strokeWidthAttr = element.get('stroke-width') #same information could be in regular attribute instead nested in style attribute
                    if strokeWidthAttr == "none":
                        widthVis = 0
                    elif strokeWidthAttr is not None and self.svg.unittouu(strokeWidthAttr) < 0.005: #really thin (0,005pc = 0,080px)
                        widthVis = 0
                    else:
                        widthVis = 1
                    stroke_width = element.style.get('stroke-width')
                    if stroke_width is not None:
                        if stroke_width == "none":
                            widthVis = 0
                        elif stroke_width is not None and self.svg.unittouu(stroke_width) < 0.005: #really thin (0,005pc = 0,080px)
                            widthVis = 0
                        else:
                            widthVis = 1
  
  
                    strokeOpacityAttr = element.get('stroke-opacity') #same information could be in regular attribute instead nested in style attribute
                    if strokeOpacityAttr == "none":
                        strokeOpacityVis = 0
                    elif strokeOpacityAttr is not None and self.svg.unittouu(strokeOpacityAttr) < 0.05: #nearly invisible (<5% opacity)
                        strokeOpacityVis = 0
                    else:
                        strokeOpacityVis = 1
                    stroke_opacity = element.style.get('stroke-opacity')
                    if stroke_opacity is not None:
                        if stroke_opacity == "none": #none means visible!
                            strokeOpacityVis = 1
                        elif stroke_opacity is not None and self.svg.unittouu(stroke_opacity) < 0.05: #nearly invisible (<5% opacity)
                            strokeOpacityVis = 0
                        else:
                            strokeOpacityVis = 1
  
  
                    if pagecolor == '#ffffff':
                        invisColors = [pagecolor, 'white', 'rgb(255,255,255)']
                    else:
                        invisColors = [pagecolor] #we could add some parser to convert pagecolor to rgb/hsl/cmyk
                    fillAttr = element.get('fill') #same information could be in regular attribute instead nested in style attribute
                    if fillAttr is None or fillAttr == "none":
                        fillVis = 0
                    elif fillAttr in invisColors:
                        fillVis = 0
                    else:
                        fillVis = 1
                    fill = element.style.get('fill')
                    if fill is not None:
                        if fill == "none": #none means invisible! (opposite of stroke behaviour)
                            fillVis = 0
                        elif fill in invisColors:
                            fillVis = 0
                        else:
                            fillVis = 1
              

                    fillOpacityAttr = element.get('fill-opacity') #same information could be in regular attribute instead nested in style attribute
                    if fillOpacityAttr == "none":
                        fillOpacityVis = 0
                    elif strokeOpacityAttr is not None and self.svg.unittouu(fillOpacityAttr) < 0.05: #nearly invisible (<5% opacity)
                        fillOpacityVis = 0
                    else:
                        fillOpacityVis = 1
                    fill_opacity = element.style.get('fill-opacity')
                    if fill_opacity is not None:
                        if fill_opacity == "none":
                            fillOpacityVis = 0
                        elif fill_opacity is not None and self.svg.unittouu(fill_opacity) < 0.05: #nearly invisible (<5% opacity)
                            fillOpacityVis = 0
                        else:
                            fillOpacityVis = 1


                    display = element.style.get('display')
                    if display == "none":
                        displayVis = 0
                    else:
                        displayVis = 1
                    displayAttr = element.get('display') #same information could be in regular attribute instead nested in style attribute
                    if displayAttr == "none":
                        displayAttrVis = 0
                    else:
                        displayAttrVis = 1
                     
                 
                    #check for svg:path elements which have consistent slope (straight lines) and no a defined fill and no stroke. such (poly)lines are still not visible
                    pathVis = 1
                    if element.tag == inkex.addNS('path','svg') and fillVis == 1 and strokeVis == 0:
                        segments = element.path.to_arrays()
                        chars = set('aAcCqQtTsS')
                        if not any((c in chars) for c in str(element.path)): #skip beziers (we only check for polylines)
                            slopes = []
                            for i in range(0, len(segments)):
                                if i > 0:
                                    if segments[i][0].lower() == 'z' or segments[i-1][0].lower() == 'z':
                                        continue #skip closed contours in combined path
                                    x1, y1, x2, y2 = segments[i-1][1][0], segments[i-1][1][1], segments[i][1][0], segments[i][1][1]
                                    if x1 < x2:
                                        p0 = [x1, y1]
                                        p1 = [x2, y2]
                                    else:
                                        p0 = [x2, y2]
                                        p1 = [x1, y1]
                                    dx = p1[0] - p0[0]
                                    if dx == 0:
                                        slope = sys.float_info.max #vertical
                                    else:
                                        slope = (p1[1] - p0[1]) / dx
                                    slope = round(slope, 6)
                                    if slope not in slopes:
                                        slopes.append(slope)
                            if len(slopes) < 2:
                                pathVis = 0
                              
                    if element.style is not None: #f if the style attribute is not set at all, the element will be visible with default black color fill and w/o stroke
                        if (strokeVis == 0 or widthVis == 0 or strokeOpacityVis == 0):
                            strokeInvis = True
                        else:
                            strokeInvis = False
                        if (fillVis == 0 or fillOpacityVis == 0):
                            fillInvis = True
                        else:
                            fillInvis = False
                        flags = "id={},strokeVis={},widthVis={},strokeOpacityVis={}=>strokeInvisble:{}|fillVis={},fillOpacityVis={}=>fillInvisble:{}|displayVis={},displayAttrVis=, {}|pathVis={}"\
                        .format(element.get('id'), strokeVis, widthVis, strokeOpacityVis, strokeInvis, fillVis, fillOpacityVis, fillInvis, displayVis, displayAttrVis, pathVis)
                        if strokeInvis is True and fillInvis is True:
                            if element not in invisibles:
                                invisibles.append(flags)
                        if displayVis == 0 or displayAttrVis == 0:
                            if element not in invisibles:
                                invisibles.append(flags)
                        if pathVis == 0:
                            if element not in invisibles:
                                invisibles.append(flags) 
            if so.show_issues_only is False:
                inkex.utils.debug("{} invisible shapes in total".format(len(invisibles)))
            for invisible in invisibles:
                inkex.utils.debug(invisible)
          
                
        '''
        Additionally, opacities less than 1.0 cause problems in most laser softwares. Please
        adjust all strokes to use full opacity.
        '''
        if so.checks == "check_all" or so.opacities is True:
            inkex.utils.debug("\n---------- Objects with transparencies < 1.0 - should be set to 1.0")
            transparencies = []
            for element in shapes: 
                strokeOpacityAttr = element.get('stroke-opacity') #same information could be in regular attribute instead nested in style attribute
                if strokeOpacityAttr is not None and strokeOpacityAttr not in transparencies:
                    if float(strokeOpacityAttr) < 1.0:
                            transparencies.append([element, strokeOpacityAttr, "stroke-opacity"])
                stroke_opacity = element.style.get('stroke-opacity')
                if stroke_opacity is not None and stroke_opacity not in transparencies:
                    if stroke_opacity != "none":
                        if float(stroke_opacity) < 1.0:
                                transparencies.append([element, stroke_opacity, "stroke-opacity"])
                                
                fillOpacityAttr = element.get('fill-opacity') #same information could be in regular attribute instead nested in style attribute
                if fillOpacityAttr is not None and fillOpacityAttr not in transparencies:
                    if float(fillOpacityAttr) < 1.0:
                            transparencies.append([element, fillOpacityAttr, "fill-opacity"])
                fill_opacity = element.style.get('fill-opacity')
                if fill_opacity is not None and fill_opacity not in transparencies:
                    if fill_opacity != "none":
                        if float(fill_opacity) < 1.0:
                                transparencies.append([element, fill_opacity, "fill-opacity"])
                  
                opacityAttr = element.get('opacity') #same information could be in regular attribute instead nested in style attribute
                if opacityAttr is not None and opacityAttr not in transparencies:
                    if float(opacityAttr) < 1.0:
                            transparencies.append([element, opacityAttr, "opacity"])
                opacity = element.style.get('opacity')
                if opacity is not None and opacity not in transparencies:
                    if opacity != "none":
                        if float(opacity) < 1.0:
                                transparencies.append([element, opacity, "opacity"])
                                
            if so.show_issues_only is False:
                inkex.utils.debug("{} objects with transparencies < 1.0 in total".format(len(transparencies)))
            for transparency in transparencies:
                inkex.utils.debug("id={}, transparency={}, attribute={}".format(transparency[0].get('id'), transparency[1], transparency[2]))  
      
      
        '''
        We look for paths which are just points. Those are useless in case of lasercutting.
        Note: this scan only works for paths, not for subpaths. If so, you need to break apart before
        '''
        if so.checks == "check_all" or so.pointy_paths is True:          
            inkex.utils.debug("\n---------- Pointy paths - should be deleted")
            pointyPaths = []
            for element in shapes:
                if isinstance(element, inkex.PathElement):
                    p = element.path
                    commandsCoords = p.to_arrays()
                    if len(commandsCoords) == 1 or \
                        (len(commandsCoords) == 2 and commandsCoords[0][1] == commandsCoords[1][1]) or \
                        (len(commandsCoords) == 2 and commandsCoords[-1][0] == 'Z') or \
                        (len(commandsCoords) == 3 and commandsCoords[0][1] == commandsCoords[1][1] and commandsCoords[2][1] == 'Z'):
                        pointyPaths.append(element)
            if so.show_issues_only is False:
                inkex.utils.debug("{} pointy paths in total".format(len(pointyPaths)))
            for pointyPath in pointyPaths:
                inkex.utils.debug("id={}".format(pointyPath.get('id')))    
   
        '''
        Combined paths make trouble with vector sorting algorithm. Check which paths could be broken apart
        '''
        if so.checks == "check_all" or so.combined_paths is True:          
            inkex.utils.debug("\n---------- Combined paths - should be broken apart")
            combinedPaths = []
            for element in shapes:
                if isinstance(element, inkex.PathElement):
                    break_paths = element.path.break_apart()
                    if len(break_paths) > 2:
                        combinedPaths.append([element, len(break_paths)])
            if so.show_issues_only is False:
                inkex.utils.debug("{} combined paths in total".format(len(combinedPaths)))
            for combinedPath in combinedPaths:
                inkex.utils.debug("id={} has sub paths: {}".format(combinedPath[0].get('id'), combinedPath[1]))    
   
   
        '''
        Transformations often lead to wrong stroke widths or mis-rendering in end software. The best we
        can do with a final SVG is to remove all relative translations, rotations and scalings. We should
        apply absolute coordinates only.
        '''
        if so.checks == "check_all" or so.transformations is True:
            inkex.utils.debug("\n---------- Transformations - should be applied to absolute")
            transformations = []
            for element in shapes:
                if element.get('transform') is not None:
                    transformations.append(element)
            if so.show_issues_only is False:
                inkex.utils.debug("{} transformation in total".format(len(transformations)))
            for transformation in transformations:
                inkex.utils.debug("transformation in id={}".format(transformation.get('id')))    
          
        '''
        Really short paths can cause issues with laser cutter mechanics and should be avoided to 
        have healthier stepper motor belts, etc.
        '''
        if so.checks == "check_all" or so.short_paths is True:  
            inkex.utils.debug("\n---------- Short paths (< {} mm)".format(so.short_paths_min))
            shortPaths = []
            totalLength = 0
            totalDropLength = 0
            for element in shapes:
                if isinstance(element, inkex.PathElement):
                    slengths, stotal = csplength(element.path.transform(element.composed_transform()).to_superpath())
                    totalLength += stotal
                    if stotal < self.svg.unittouu(str(so.short_paths_min) + "mm"):
                        shortPaths.append([element, stotal])
                        totalDropLength += stotal
            if so.show_issues_only is False:
                inkex.utils.debug("{} short paths in total".format(len(shortPaths)))
            if totalDropLength > 0:
                inkex.utils.debug("{:0.2f}% of total ({:0.2f} mm /{:0.2f} mm)".format(totalDropLength / totalLength, self.svg.uutounit(str(totalDropLength), "mm"), self.svg.uutounit(str(totalLength), "mm")))
            for shortPath in shortPaths:
                inkex.utils.debug("id={}, length={}mm".format(shortPath[0].get('id'), round(self.svg.uutounit(str(shortPath[1]), "mm"), 3)))    
          
        '''
        Really short paths can cause issues with laser cutter mechanics and should be avoided to 
        have healthier stepper motor belts, etc.
        
        Peck Sidara from Epilog: 
         "Most of the acceleration of speed occurs from the 1-20% range, there is a difference between say 30% and 90%speed 
         but due to the many variables (length of nodes, shape and contour of nodes), you may not see a noticable difference in time. 
         Additional variables include acceleration, deceleration and how our laser handles/translates the vector data."
        '''
        if so.checks == "check_all" or so.cutting_estimation is True:
            inkex.utils.debug("\n---------- Cutting time estimation (Epilog Lasers)")
            totalCuttingLength = 0
            totalTravelLength = 0
            cuttingPathCount = 0
            travelPathCount = 0
            
            for element in shapes:
                if isinstance(element, inkex.PathElement):
                    slengths, stotal = csplength(element.path.transform(element.composed_transform()).to_superpath())
                    if "-travelLine" in element.get('id'): #we use that id scheme together with the extension "Draw Directions / Travel Moves"
                        totalTravelLength += stotal
                        travelPathCount += 1
                    elif "markerId-" in element.get('id'):
                        pass #we skip the path "markerId-<nr>", possibly generated by the extension "Draw Directions / Travel Moves
                    else:
                        totalCuttingLength += stotal
                        cuttingPathCount += 1
            totalLength = totalCuttingLength + totalTravelLength
            v_travel = so.max_travel_speed #this is always at maximum
            inkex.utils.debug("total cutting paths={}".format(cuttingPathCount))
            inkex.utils.debug("total travel paths={}".format(travelPathCount))
            inkex.utils.debug("(measured) cutting length (mm) = {:0.2f} mm".format(self.svg.uutounit(str(totalCuttingLength), "mm"), self.svg.uutounit(str(totalCuttingLength), "mm")))
            inkex.utils.debug("(measured) travel length (mm) = {:0.2f} mm".format(self.svg.uutounit(str(totalTravelLength), "mm"), self.svg.uutounit(str(totalTravelLength), "mm")))
            inkex.utils.debug("(measured) total length (mm) = {:0.2f} mm".format(self.svg.uutounit(str(totalLength), "mm"), self.svg.uutounit(str(totalLength), "mm")))
            inkex.utils.debug("travel speed={:06.2f}mm/s".format(v_travel))
            ''' from https://www.epiloglaser.com/assets/downloads/fusion-material-settings.pdf
            "Speed Settings: The speed setting scale of 1% to 100% is not linear – 
            i.e. 100% speed will not be twice as fast as 50% speed. This non-linear 
            scale is very useful in compensating for the different factors that affect engraving time."
            '''
            speedFactors = []
            try:
                for speed in re.findall(r"[+]?\d*\.\d+|\d+", self.options.cutting_speedfactors): #allow only positive values
                    if float(speed) > 0:
                        speedFactors.append(float(speed))
                speedFactors = sorted(speedFactors)[::-1]
            except:
                inkex.utils.debug("Error parsing cutting estimation speeds. Please try again!")
                exit(1)            
            for speedFactor in speedFactors:
                speedFactorR = speedFactor / 100.0
                adjusted_speed =  480.0 / so.max_cutting_speed #empiric - found out by trying for hours ...
                empiric_scale = 1 + (speedFactorR**2) / 15.25 #empiric - found out by trying for hours ...
                v_cut    = so.max_cutting_speed * speedFactorR
                tsec_cut    = (self.svg.uutounit(str(totalCuttingLength)) / (adjusted_speed * so.max_cutting_speed * speedFactorR)) * empiric_scale
                tsec_travel = self.svg.uutounit(str(totalTravelLength))  / v_travel
                tsec_total = so.job_time_offset + tsec_cut + tsec_travel
                minutes, seconds = divmod(tsec_total, 60)  # split the seconds to minutes and seconds
                seconds_for_price = seconds
                #round seconds up to 30 or 60
                if so.round_times is True:
                    if seconds_for_price < 30:
                        seconds_for_price = 30
                    if seconds_for_price > 30 and seconds_for_price != 60:
                        seconds_for_price = 60
                
                partial_minutes = round(seconds_for_price/60 * 2) / 2    
                costs = so.price_per_minute_gross * (minutes + partial_minutes)
                if "{:02.0f}".format(seconds) == "60": #for formatting reasons
                    seconds = 0
                    minutes += 1         
                inkex.utils.debug("@{:05.1f}% (cut={:06.2f}mm/s > {:03.0f}min {:02.0f}sec | cost={:02.0f}€".format(speedFactor, v_cut, minutes, seconds, costs))

        
        ''' Measurements from Epilog Software Suite
        We are using a huge SVG graphic with 100 meters (=100.000 mm) of lines.
        The following speeds are getting precalculated (travel moves = 0mm): 
            @ 100% = 13:45   = 825s   -> 121,21mm/s
            @ 090% = 15:12   = 912s   -> 109,65mm/s
            @ 080% = 17:01   = 1021s  ->  97,94mm/s
            @ 070% = 19:21   = 1161s  ->  86,13mm/s
            @ 060% = 22:28   = 1348s  ->  74,18mm/s
            @ 050% = 26:49   = 1609s  ->  62,15mm/s
            @ 040% = 33:21   = 2001s  ->  49,98mm/s
            @ 030% = 44:13   = 2653s  ->  37,69mm/s
            @ 020% = 65:51   = 3951s  ->  25,31mm/s
            @ 010% = 130:52  = 7852s  ->  12,74mm/s
            @ 009% = 145:21  = 8721s  ->  11,47mm/s
            @ 008% = 163:27  = 9807s  ->  10,20mm/s
            @ 007% = 186:44  = 11204s ->   8,93mm/s
            @ 006% = 217:48  = 13068s ->   7,65mm/s
            @ 005% = 261:18  = 15678s ->   6,38mm/s
            @ 004% = 326:34  = 19594s ->   5,10mm/s
            @ 003% = 435:21  = 26121s ->   3,83mm/s
            @ 002% = 652:57  = 39177s ->   2,55mm/s
            @ 001% = 1305:49 = 78349s ->   1,28mm/s
            
        It does not matter how slow we configure the laser, the job time estimation always has the same amount of travel time
        (if we have some travel moves to perform), so the travel speed is always constant. The max. travel speed of Fusion Pro 32 
        is between 425mm/s and 460mm/s (measured by Mario by hand at different laser jobs).
        If the laser is in X=0 Y=0 the jobs needs ~2 seconds to start moving and firing the laser. We use this as constant offset
        '''
        
        '''
        Paths with a high amount of nodes will cause issues because each node means slowing down/speeding up the laser mechanics
        '''
        if so.checks == "check_all" or so.nodes_per_path is True:  
            inkex.utils.debug("\n---------- Heavy node-loaded paths (allowed: {} node(s) per {} mm) - should be simplified".format(so.nodes_per_path_max, round(so.nodes_per_path_interval, 3)))
            heavyPaths = []
            totalNodesCount = 0
            for element in shapes:
                if isinstance(element, inkex.PathElement):
                    slengths, stotal = csplength(element.path.transform(element.composed_transform()).to_superpath())
                    nodes = len(element.path)
                    if stotal > 0: #ignore pointy paths, which might generate zero length paths. Use the pointy path check to find them!
                        if nodes /  stotal > so.nodes_per_path_max / self.svg.unittouu(str(so.nodes_per_path_interval) + "mm"):
                            heavyPaths.append([element, nodes, stotal])
            if so.show_issues_only is False:
                inkex.utils.debug("{} Heavy node-loaded paths in total".format(len(heavyPaths)))
            for heavyPath in heavyPaths:
                totalNodesCount += heavyPath[1]
                inkex.utils.debug("id={}, nodes={}, length={}mm, density={}nodes/mm".format(
                        heavyPath[0].get('id'), 
                        heavyPath[1], 
                        round(self.svg.uutounit(str(heavyPath[2]), "mm"), 3),
                        round(heavyPath[1] / self.svg.uutounit(str(heavyPath[2]), "mm"), 3)
                        )
                    )
            inkex.utils.debug("Total nodes on paths: {}".format(totalNodesCount))
            pathCount = 0
            for key in counter.keys():
                if key == "path":
                    pathCount = counter[key]
            if pathCount > 0:
                inkex.utils.debug("Average nodes per path: {:0.0f}".format(totalNodesCount/pathCount))


        '''
        Elements outside canvas or touching the border. These are critical because they won't be lasered or not correctly lasered
        '''
        if so.checks == "check_all" or so.elements_outside_canvas is True:  
            inkex.utils.debug("\n---------- Elements outside canvas or touching the border")
            elementsOutside = []
            for element in shapes:
                if element.tag != inkex.addNS('g', 'svg'):
                    ebbox = element.bounding_box(element.composed_transform())
                    if ebbox is not None: #pointy paths for example could generate non-bbox shapes. So we ignore them here
                        precision = 3
                        #inkex.utils.debug("{} | bbox: left = {:0.3f} right = {:0.3f} top = {:0.3f} bottom = {:0.3f}".format(element.get('id'), ebbox.left, ebbox.right, ebbox.top, ebbox.bottom))
                        #pagew = round(self.svg.unittouu(self.svg.get('width')), precision)
                        #pageh = round(self.svg.unittouu(self.svg.get('height')), precision)   
                        vxMin, vyMin, vxMax, vyMax = self.svg.get_viewbox()
                        pagew = round(vxMax - vxMin, precision)
                        pageh = round(vyMax - vyMin, precision)  
                        
                        if round(ebbox.right,  precision) == 0 or \
                           round(ebbox.left,   precision) == pagew or \
                           round(ebbox.top,    precision) == 0 or \
                           round(ebbox.bottom, precision) == pageh:
                            elementsOutside.append([element, "touching"])
                        elif \
                           round(ebbox.right,  precision) < 0 or \
                           round(ebbox.left,   precision) > pagew or \
                           round(ebbox.top,    precision) < 0 or \
                           round(ebbox.bottom, precision) > pageh:
                            elementsOutside.append([element, "fully outside"])
                        else: #fully inside or partially inside/outside. we check if one or more corners is outside the canvas
                            rightOutside = False
                            leftOutside = False
                            topOutside = False
                            bottomOutside = False
                            if round(ebbox.right,  precision) < 0 or round(ebbox.right,  precision) > pagew:
                               rightOutside = True
                            if round(ebbox.left,  precision) < 0 or round(ebbox.left,  precision) > pagew:
                               leftOutside = True  
                            if round(ebbox.top,  precision) < 0 or round(ebbox.top,  precision) > pageh:
                               topOutside = True
                            if round(ebbox.bottom,  precision) < 0 or round(ebbox.bottom,  precision) > pageh:
                               bottomOutside = True
                            if rightOutside is True or leftOutside is True or topOutside is True or bottomOutside is True:
                                elementsOutside.append([element, "partially outside"])
            if so.show_issues_only is False:
                inkex.utils.debug("{} Elements outside canvas or touching the border in total".format(len(elementsOutside)))
            for elementOutside in elementsOutside:
                inkex.utils.debug("id={}, status={}".format(
                        elementOutside[0].get('id'), 
                        elementOutside[1]
                        )
                    )    
             
                   
        '''
        Shapes like rectangles, ellipses, arcs, spirals should be converted to svg:path to have more
        convenience in the file
        '''
        if so.checks == "check_all" or so.non_path_shapes is True:          
            inkex.utils.debug("\n---------- Non-path shapes - should be converted to paths")
            nonPathShapes = []
            for element in shapes:
                if not isinstance(element, inkex.PathElement) and not isinstance(element, inkex.Group):
                    nonPathShapes.append(element)
            if so.show_issues_only is False:
                inkex.utils.debug("{} non-path shapes in total".format(len(nonPathShapes)))
            for nonPathShape in nonPathShapes:
                inkex.utils.debug("id={}, type={}".format(nonPathShape.get('id'), nonPathShape.tag.replace("{http://www.w3.org/2000/svg}", "")))         
         
        exit(0)
                             
if __name__ == '__main__':
    LaserCheck().run()
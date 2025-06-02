#!/usr/bin/env python3

'''
Extension for Inkscape 1.0+
 - ToDo: 
    - add more comments
    - add more debug output
    - add documentation about used algorithms at online page
    - add statistics about type counts and path lengths (before/after sub splitting/trimming)
    - add options:
        - replace trimmed paths by bezier paths (calculating lengths and required t parameter)
        - filter/remove overlapping/duplicates in 
            - in original selection (not working bezier but for straight line segments!) We can use another extension for it
            - split bezier
            - ...
        - maybe option: convert abs path to rel path
        - maybe option: convert rel path to abs path
            replacedelement.path = replacedelement.path.to_absolute().to_superpath().to_path()
        - maybe option: break apart while keeping relative/absolute commands (more complex and not sure if we have a great advantage having this)
    - note: running this extension might leave some empty parent groups in some circumstances. run the clean groups extension separately to fix that
    - sort to groups by path type (open, closed, ...)
    
- important to notice
    - this algorithm might be really slow. Reduce flattening quality to speed up
    - the code quality is horrible. We need a lot of asserts and functions to structure that stuff
    - try to adjust snap tolerance and flatness in case of errors, like
      poly_point_isect.py: "KeyError: 'Event(0x21412ce81c0, s0=(47.16, 179.1),
      s1=(47.17, 178.21), p=(47.16, 179.1), type=2, slope=-88.9999999999531)'"
    - this extension does not check for strange paths. Please ensure that your path 'd'
      data is valid (no pointy paths, no duplicates, etc.)     
    - Notes about shapely:
        - we do not use shapely to look for intersections by cutting each line against
          each other line (line1.intersection(line2) using two for-loops) because this 
          kind of logic is really really slow for huge amount. You could use that only 
          for ~50-100 elements. So we use special algorihm (Bentley-Ottmann)
        - intersects() is equivalent to the OR-ing of contains(), crosses(), equals(), touches(), and within().
          So there might be some cases where two lines intersect eachother without crossing, 
          in particular when one line contains another or when two lines are equals.
        - crosses() returns True if the dimension of the intersection is less than the dimension of the one or the other.
          So if two lines overlap, they won't be considered as "crossing". intersection() will return a geometric object.
    - Cool tool to visualize sweep line algorithm Bentley-Ottmann: https://bl.ocks.org/1wheel/464141fe9b940153e636

- things to look at more closely:
    - https://gis.stackexchange.com/questions/203048/split-lines-at-points-using-shapely
    - https://stackoverflow.com/questions/34754777/shapely-split-linestrings-at-intersections-with-other-linestrings
        - There are floating point precision errors when finding a point on a line. Use the distance with an appropriate threshold instead.
            - line.within(point)  # False
            - line.distance(point)  # 7.765244949417793e-11
            - line.distance(point) < 1e-8  # True
    - https://bezier.readthedocs.io/en/stable/python/reference/bezier.hazmat.clipping.html / https://github.com/dhermes/bezier
    - De Casteljau Algorithm

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 09.08.2020 (extension originally called "Contour Scanner")
Last patch: 07.11.2022
License: GNU GPL v3

'''

import sys
import os
import copy
from lxml import etree
import poly_point_isect
from poly_point_isect import isect_segments
import inkex
from inkex import transforms, bezier, PathElement, Color, Circle
from inkex.bezier import csplength
from inkex.paths import Path, CubicSuperPath
from shapely.geometry import LineString, Point, MultiPoint
from shapely.ops import snap, split

idPrefixSubSplit = "subsplit"
idPrefixTrimming = "trimmed"
intersectedVerb = "intersected"
collinearVerb = "collinear"

class ContourScannerAndTrimmer(inkex.EffectExtension):


    def break_contours(self, element, breakelements = None):
        ''' 
        this does the same as "CTRL + SHIFT + K"
        This functions honors the fact of absolute or relative paths!
         '''
        if breakelements == None:
            breakelements = []
        if element.tag == inkex.addNS('path','svg'):
            parent = element.getparent()
            idx = parent.index(element)
            idSuffix = 0
            #raw = str(element.path).split()
            raw = element.path.to_arrays() 
            subPaths = []
            prev = 0
            for i in range(len(raw)): # Breaks compound paths into simple paths
                #if raw[i][0].upper() == 'M' and i != 0:
                if raw[i][0] == 'M' and i != 0:
                    subPath = raw[prev:i]
                    subPaths.append(Path(subPath))
                    prev = i
            subPaths.append(Path(raw[prev:])) #finally add the last path

            for subPath in subPaths:
                replacedelement = copy.copy(element)
                oldId = replacedelement.get('id')
                csp = CubicSuperPath(subPath)
                if len(subPath) > 1 and csp[0][0] != csp[0][1]: #avoids pointy paths like M "31.4794 57.6024 Z"
                    replacedelement.path = subPath
                    if len(subPaths) == 1:
                        replacedelement.set('id', oldId)
                    else:
                        replacedelement.set('id', oldId + str(idSuffix))
                        idSuffix += 1
                    parent.insert(idx, replacedelement)
                    breakelements.append(replacedelement)
            element.delete()
        for child in element.getchildren():
            self.break_contours(child, breakelements)
        return breakelements


    def get_child_paths(self, element, elements = None):
        ''' a function to get child paths from elements (used by "handling groups" option) '''
        if elements == None:
            elements = []
        if element.tag == inkex.addNS('path','svg'):
                elements.append(element)
        for child in element.getchildren():
            self.get_child_paths(child, elements)
        return elements


    def get_path_elements(self):
        ''' get all path elements, either from selection or from whole document. Uses options '''
        pathElements = []
        if len(self.svg.selected) == 0: #if nothing selected we search for the complete document
            pathElements = self.document.xpath('//svg:path', namespaces=inkex.NSS)
        else: # or get selected paths (and children) and convert them to shapely LineString objects
            if self.options.handle_groups is False:
                pathElements = list(self.svg.selection.filter(PathElement).values())
            else:
                for element in self.svg.selection.values():
                    pathElements = self.get_child_paths(element, pathElements)

        if len(pathElements) == 0:
            self.msg('Selection appears to be empty or does not contain any valid svg:path nodes. Try to cast your objects to paths using CTRL + SHIFT + C or strokes to paths using CTRL + ALT + C')
            exit(1)

        if self.options.break_apart is True:
            breakApartElements = None
            for pathElement in pathElements:
                breakApartElements = self.break_contours(pathElement, breakApartElements)
            pathElements = breakApartElements

        if self.options.show_debug is True:
            self.msg("total processing paths count: {}".format(len(pathElements)))

        return pathElements


    def find_group(self, groupId):
        ''' check if a group with a given id exists or not. Returns None if not found, else returns the group element '''
        groups = self.document.xpath('//svg:g', namespaces=inkex.NSS)
        for group in groups:
            #self.msg(str(layer.get('inkscape:label')) + " == " + layerName)
            if group.get('id') == groupId:
                return group
        return None


    def adjust_style(self, element):
        ''' Replace some style attributes of the given element '''
        if element.attrib.has_key('style'):
            style = element.get('style')
            if style:
                declarations = style.split(';')
                for i,decl in enumerate(declarations):
                    parts = decl.split(':', 2)
                    if len(parts) == 2:
                        (prop, val) = parts
                        prop = prop.strip().lower()
                        if prop == 'stroke-width':
                            declarations[i] = prop + ':' + str(self.svg.unittouu(str(self.options.strokewidth) +"px"))
                        if prop == 'fill':
                            declarations[i] = prop + ':none'
                element.set('style', ';'.join(declarations) + ';stroke:#000000;stroke-opacity:1.0')
        else:
            element.set('style', 'stroke:#000000;stroke-opacity:1.0')


    def line_from_segments(self, segs, i, decimals):
        '''builds a straight line for the segment i and the next segment i+2. Returns both point XY coordinates'''
        pseudoPath = Path(segs[i:i+2]).to_arrays()
        x1 = round(pseudoPath[0][1][-2], decimals)
        y1 = round(pseudoPath[0][1][-1], decimals)
        if pseudoPath[1][0] == 'Z': #some crappy code when the path is closed
            pseudoPathEnd = Path(segs[0:2]).to_arrays()
            x2 = round(pseudoPathEnd[0][1][-2], decimals)
            y2 = round(pseudoPathEnd[0][1][-1], decimals)
        else:
            x2 = round(pseudoPath[1][1][-2], decimals)
            y2 = round(pseudoPath[1][1][-1], decimals)
        return x1, y1, x2, y2


    def visualize_self_intersections(self, pathElement, selfIntersectionPoints):
        ''' Draw some circles at given point coordinates (data from array)'''
        selfIntersectionGroup = pathElement.getparent().add(inkex.Group(id="selfIntersectionPoints-{}".format(pathElement.attrib["id"])))
        selfIntersectionPointStyle = {'stroke': 'none', 'fill': self.options.color_self_intersections}
        for selfIntersectionPoint in selfIntersectionPoints:
            cx = selfIntersectionPoint[0]
            cy = selfIntersectionPoint[1]
            selfIntersectionPointCircle = Circle(cx=str(cx),
                            cy=str(cy),
                            r=str(self.svg.unittouu(str(self.options.dotsize_intersections / 2) + "px"))
                            )
            
            if pathElement.getparent() != self.svg.root:
                selfIntersectionPointCircle.transform = -pathElement.getparent().composed_transform()
            selfIntersectionPointCircle.set('id', self.svg.get_unique_id('selfIntersectionPoint-'))
            selfIntersectionPointCircle.style = selfIntersectionPointStyle
            selfIntersectionGroup.add(selfIntersectionPointCircle)
        return selfIntersectionGroup


    def visualize_global_intersections(self, globalIntersectionPoints):
        ''' Draw some circles at given point coordinates (data from array)'''
        if len(globalIntersectionPoints.geoms) > 0: #only create a group and add stuff if there are some elements to work on 
            globalIntersectionGroup = self.svg.root.add(inkex.Group(id="globalIntersectionPoints"))
            globalIntersectionPointStyle = {'stroke': 'none', 'fill': self.options.color_global_intersections}
            for globalIntersectionPoint in globalIntersectionPoints.geoms:
                cx = globalIntersectionPoint.coords[0][0]
                cy = globalIntersectionPoint.coords[0][1]
                globalIntersectionPointCircle = Circle(cx=str(cx),
                    cy=str(cy),
                    r=str(self.svg.unittouu(str(self.options.dotsize_intersections / 2) + "px"))
                    )
                globalIntersectionPointCircle.set('id', self.svg.get_unique_id('globalIntersectionPoint-'))
                globalIntersectionPointCircle.style = globalIntersectionPointStyle
                globalIntersectionGroup.add(globalIntersectionPointCircle)


    def build_trim_line_group(self, subSplitLineArray, subSplitIndex, globalIntersectionPoints): 
        ''' make a group containing trimmed lines'''      
        
        #Check if we should skip or process the path anyway   
        isClosed = subSplitLineArray[subSplitIndex].attrib['originalPathIsClosed']
        if self.options.trimming_path_types == 'open_paths' and isClosed == 'True': return #skip this call
        elif self.options.trimming_path_types == 'closed_paths' and isClosed == 'False': return #skip this call
        elif self.options.trimming_path_types == 'both': pass
     
        csp = Path(subSplitLineArray[subSplitIndex].path.transform(subSplitLineArray[subSplitIndex].composed_transform())).to_arrays() #will be buggy if draw subsplit lines is deactivated

        ls = LineString([(csp[0][1][0], csp[0][1][1]), (csp[1][1][0], csp[1][1][1])])
        
        trimLineStyle = {'stroke': str(self.options.color_trimmed), 'fill': 'none', 'stroke-width': self.options.strokewidth}
           
        linesWithSnappedIntersectionPoints = snap(ls, globalIntersectionPoints, self.options.snap_tolerance)
        trimGroupParentId = subSplitLineArray[subSplitIndex].attrib['originalPathId']
        trimGroupId = '{}-{}-{}'.format(idPrefixTrimming, idPrefixSubSplit, trimGroupParentId)
        trimGroupParent = self.svg.getElementById(trimGroupParentId)
        trimGroup = self.find_group(trimGroupId)

        if trimGroup is None:
            trimGroup = trimGroupParent.getparent().add(inkex.Group(id=trimGroupId))
            trimGroup.transform = -subSplitLineArray[subSplitIndex].composed_transform()
          
        #apply isBezier and original path id information to group (required for bezier splitting the original path at the end)
        trimGroup.attrib['originalPathIsBezier'] = subSplitLineArray[subSplitIndex].attrib['originalPathIsBezier']
        trimGroup.attrib['originalPathIsPolyBezMixed'] = subSplitLineArray[subSplitIndex].attrib['originalPathIsPolyBezMixed']
        trimGroup.attrib['originalPathId'] = subSplitLineArray[subSplitIndex].attrib['originalPathId']

        #split all lines against all other lines using the intersection points
        trimLines = split(linesWithSnappedIntersectionPoints, globalIntersectionPoints)

        splitAt = [] #if the sub split line was split by an intersecting line we receive two trim lines with same assigned original path id!
        prevLine = None
        for j in range(len(trimLines.geoms)):

            trimLineId = "{}-{}".format(trimGroupId, subSplitIndex)
            splitAt.append(trimGroupId)
            if splitAt.count(trimGroupId) > 1: #we detected a lines with intersection on
                trimLineId = "{}-{}".format(trimLineId, self.svg.get_unique_id(intersectedVerb + "-"))
                '''
                so the previous lines was an intersection lines too. so we change the id to include the intersected verb
                (left side and right side of cut) - note: updating element 
                id sometimes seems not to work if the id was used before in Inkscape
                '''
                prevLine.attrib['id'] = "{}-{}".format(trimGroupId, str(subSplitIndex) + "-" + self.svg.get_unique_id(intersectedVerb + "-"))
                prevLine.attrib['intersected'] = 'True' #some dirty flag we need
            prevLine = trimLine = inkex.PathElement(id=trimLineId)
            x, y = trimLines.geoms[j].coords.xy          
            x0 = round(x[0], self.options.decimals)
            x1 = round(x[1], self.options.decimals)
            y0 = round(y[0], self.options.decimals)
            y1 = round(y[1], self.options.decimals)
            if x0 == x1 and y0 == y1: #check if the trimLine is a pointy one (rounded start point equals rounded end point)
                if self.options.show_debug is True:
                    self.msg("pointy trim line (start point equals end point). Skipping ...")
                continue
            
            trimLine.attrib['d'] = 'M {},{} L {},{}'.format(x0, y0, x1, y1) #we set the path of trimLine using 'd' attribute because if we use trimLine.path the decimals get cut off unwantedly
            #trimLine.path = Path([['M', [x0,y0]], ['L', [x1,y1]]])

            #if trimGroupParentTransform is not None:
            #    trimLine.path = trimLine.path.transform(-trimGroupParentTransform)
            if self.options.trimmed_style == "apply_from_trimmed":
                trimLine.style = trimLineStyle
            elif self.options.trimmed_style == "apply_from_original":
                trimLine.style = subSplitLineArray[subSplitIndex].attrib['originalPathStyle']
            trimGroup.add(trimLine)
        return trimGroup


    def slope(self, p0, p1):
        '''
            Calculate the slope (gradient) of a line's start point p0 + end point p1
        '''
        dx = p1[0] - p0[0]
        if dx == 0:
            return sys.float_info.max #vertical
        return (p1[1] - p0[1]) / dx


    def process_set_x(self, working_set):
        if len(working_set) < 2:
            return (True, working_set)
    
        # sort working set left to right
        working_set.sort(key=lambda x: x['p0'][0])
        for i in range(0, len(working_set)):
            for j in range(i + 1, len(working_set)):
    
                # calculate slope from S0P0 to S1P1 and S0P1 to S1P0
                # if slopes all match the working set's slope, we're collinear
                # if not, these segments are parallel but not collinear and should be left alone
                expected_slope = working_set[i]['slope']
                if (abs(self.slope(working_set[i]['p1'], working_set[j]['p0']) - expected_slope) > self.options.collinear_filter_epsilon) \
                or (abs(self.slope(working_set[i]['p0'], working_set[j]['p1']) - expected_slope) > self.options.collinear_filter_epsilon):
                    continue
    
                # the only remaining permissible configuration: collinear segments with a gap between them
                # e.g. ---  -----
                # otherwise we combine segments and flag the set as requiring more processing
                s0x0 = working_set[i]['p0'][0] 
                s0x1 = working_set[i]['p1'][0] 
                s1x0 = working_set[j]['p0'][0] 
                s1x1 = working_set[j]['p1'][0]

                if not (s0x0 < s0x1 and s0x1 < s1x0 and s1x0 < s1x1):
                    # make a duplicate set, omitting segments i and j
                    new_set = [x for (k, x) in enumerate(working_set) if k not in (i, j)]
                    
                    # add a segment representing i and j's furthest points
                    pts = [ working_set[i]['p0'], working_set[i]['p1'], working_set[j]['p0'], working_set[j]['p1'] ]
                    pts.sort(key=lambda x: x[0])

                    new_set.append({
                        'p0': pts[0], 
                        'p1': pts[-1],
                        'slope': self.slope(pts[0], pts[-1]),
                        'id': working_set[i]['id'],
                        'originalPathId': working_set[i]['originalPathId'],
                        'composed_transform': working_set[i]['composed_transform']
                        })
                    return (False, new_set)
    
        return (True, working_set)


    def process_set_y(self, working_set):
        if len(working_set) < 2:
            return (True, working_set)
        
        # sort working set top to bottom
        working_set.sort(key=lambda y: -y['p0'][1])

        for i in range(0, len(working_set)):
            for j in range(i + 1, len(working_set)):
        
                # the only remaining permissible configuration: collinear segments with a gap between them
                # e.g. 
                #   |
                #   |
                #
                #   |
                #   |
                #   |
                #
                # otherwise we combine segments and flag the set as requiring more processing
                s0y0 = working_set[i]['p0'][1] 
                s0y1 = working_set[i]['p1'][1] 
                s1y0 = working_set[j]['p0'][1] 
                s1y1 = working_set[j]['p1'][1]

                if not (s0y0 < s0y1 and s0y1 < s1y0 and s1y0 < s1y1):
                    # make a duplicate set, omitting segments i and j
                    new_set = [y for (k, y) in enumerate(working_set) if k not in (i, j)]
                    
                    # add a segment representing i and j's furthest points
                    pts = [ working_set[i]['p0'], working_set[i]['p1'], working_set[j]['p0'], working_set[j]['p1'] ]
                    pts.sort(key=lambda y: y[1])
                    new_set.append({
                        'p0': pts[0], 
                        'p1': pts[-1],
                        'slope': self.slope(pts[0], pts[-1]),
                        'id': working_set[i]['id'],
                        'originalPathId': working_set[i]['originalPathId'],
                        'composed_transform': working_set[i]['composed_transform']
                        })
                    return (False, new_set)
        
        return (True, working_set)
 
    
    def filter_collinear(self, lineArray):
        ''' Another sweep line algorithm to scan collinear lines
            Loop through a set of lines and find + fiter all overlapping segments / duplicate segments
            finally returns a set of merged-like lines and a set of original items which should be dropped.
            Based on the style of the algorithm we have no good influence on the z-index of the items because 
            it is scanned by slope and point coordinates. That's why we have a more special 
            'remove_trim_duplicates()' function for trimmed duplicates!
        '''
        
        '''
        filter for regular input lines and special vertical lines
        '''
        input_set = []
        input_ids = []

        # collect segments, calculate their slopes, order their points left-to-right
        for line in lineArray:
            #csp = line.path.to_arrays()
            parent = line.getparent()
            if parent is not None:
                csp = Path(line.path.transform(parent.composed_transform())).to_arrays()
            else:
                csp = line.path.to_arrays()
            #self.msg("csp = {}".format(csp))
            x1, y1, x2, y2 = csp[0][1][0], csp[0][1][1], csp[1][1][0], csp[1][1][1]
            # ensure p0 is left of p1
            if x1 < x2:
                s = {
                    'p0': [x1, y1],
                    'p1': [x2, y2]
                }
            else:
                s = {
                    'p0': [x2, y2],
                    'p1': [x1, y1]
                }
            s['slope'] = self.slope(s['p0'], s['p1'])
            s['id'] = line.attrib['id']
            s['originalPathId'] = line.attrib['originalPathId']
            s['composed_transform'] = line.composed_transform()
            #s['d'] = line.attrib['d']
            input_set.append(s)
    
        input_set.sort(key=lambda x: x['slope'])
        #input_set.append(False) # used to clear out lingering contents of working_set_x on last iteration

        input_set_new = []
        
        #loop through input_set to filter out the vertical lines because we need to handle them separately
        vertical_set = []
        vertical_ids = []
        for i in range(0, len(input_set)):
            if input_set[i]['slope'] == sys.float_info.max:
                vertical_set.append(input_set[i])
            else:
                input_set_new.append(input_set[i])
        
        input_set = input_set_new #overwrite the input_set with the filtered one
        input_set.append(False) # used to clear out lingering contents of working_set_x on last iteration

        '''
        process x lines (all lines except vertical ones)
        '''
        working_set_x = []
        working_x_ids = []
        output_set_x = []
        output_x_ids = []
        
        if len(input_set) > 0:
            current_slope = input_set[0]['slope']
            for input in input_set:
                # bin sets of input_set by slope (within a tolerance)
                dm = input and abs(input['slope'] - current_slope) or 0
                if input and dm < self.options.collinear_filter_epsilon:
                    working_set_x.append(input) #we put all lines to working set which have similar slopes
                    if input['id'] != '': input_ids.append(input['id'])
                else: # slope discontinuity, process accumulated set
                    while True:
                        (done, working_set_x) = self.process_set_x(working_set_x)
                        if done:
                            output_set_x.extend(working_set_x)
                            break
    
                    if input: # begin new working set
                        working_set_x = [input]
                        current_slope = input['slope']
                        if input['id'] != '': input_ids.append(input['id'])      
            

            for output_x in output_set_x:
                output_x_ids.append(output_x['id'])
    
            for working_x in working_set_x:
                working_x_ids.append(working_x['id'])
        else:
            if self.options.show_debug is True:
                self.msg("Scanning: no non-vertical input lines found. That might be okay or not ...")  
        
        '''
        process vertical lines
        '''
        working_set_y = []
        working_y_ids = []
        output_set_y = []
        output_y_ids = []

        if len(vertical_set) > 0:
            vertical_set.sort(key=lambda x: x['p0'][0]) #sort verticals by their x coordinate
            vertical_set.append(False) # used to clear out lingering contents of working_set_y on last iteration
            current_x = vertical_set[0]['p0'][0]
            for vertical in vertical_set:
                if vertical and current_x == vertical['p0'][0]:
                    working_set_y.append(vertical) #we put all lines to working set which have same x coordinate
                    if vertical['id'] != '': vertical_ids.append(vertical['id'])
                else: # x coord discontinuity, process accumulated set
                    while True:
                        (done, working_set_y) = self.process_set_y(working_set_y)
                        if done:
                            output_set_y.extend(working_set_y)
                            break
                    if vertical: # begin new working set
                        working_set_y = [vertical]
                        current_x = vertical['p0'][0]
                        if vertical['id'] != '': vertical_ids.append(vertical['id'])
        else:
            if self.options.show_debug is True:
                self.msg("Scanning: no vertical lines found. That might be okay or not ...")  
                   
        for output_y in output_set_y:
            output_y_ids.append(output_y['id'])

        for working_y in working_set_y:
            working_y_ids.append(working_y['id'])

        output_set = output_set_x
        output_set.extend(output_set_y)
        output_ids = []
        for output in output_set:
            #self.msg(output)
            output_ids.append(output['id'])

        #we finally build a list which contains all overlapping elements we want to drop
        dropped_ids = []
        for input_id in input_ids: #if the input_id id is not in the output ids we are going to drop it
            if input_id not in output_ids:
               dropped_ids.append(input_id)
        for vertical_id in vertical_ids: #if the input_id id is not in the output ids we are going to drop it
            if vertical_id not in output_ids:
               dropped_ids.append(vertical_id)

        if self.options.show_debug is True:
            #self.msg("input_set:{}".format(input_set))               
            self.msg("input_ids [{}]:".format(len(input_ids)))
            for input_id in input_ids:
               self.msg(input_id)
            self.msg("*"*24)     
            #self.msg("working_set_x:{}".format(working_set_x))                  
            self.msg("working_x_ids [{}]:".format(len(working_x_ids)))
            for working_x_id in working_x_ids:
               self.msg(working_x_id) 
            self.msg("*"*24)     
            #self.msg("output_set_x:{}".format(output_set_x))                  
            self.msg("output_x_ids [{}]:".format(len(output_x_ids)))
            for output_x_id in output_x_ids:
               self.msg(output_x_id)
            self.msg("*"*24)
            #self.msg("output_set_y:{}".format(output_set_y))                  
            self.msg("output_y_ids [{}]:".format(len(output_y_ids)))
            for output_y_id in output_y_ids:
               self.msg(output_y_id)
            self.msg("*"*24)
            #self.msg("output_set:{}".format(output_set))                  
            self.msg("output_ids [{}]:".format(len(output_ids)))
            for output_id in output_ids:
               self.msg(output_id)
            self.msg("*"*24)
            self.msg("dropped_ids [{}]:".format(len(dropped_ids)))
            for dropped_id in dropped_ids:
               self.msg(dropped_id)
            self.msg("*"*24)     
          
        return output_set, dropped_ids


    def remove_trim_duplicates(self, allTrimGroups):
        ''' 
            find duplicate lines in a given array [] of groups
            note: this function is similar to filter_collinear but we keep it because we have a 'reverse_trim_removal_order' option.
            We can use this option in some special situations where we work without the function 'filter_collinear()'.
        '''
        totalTrimPaths = []
        if self.options.reverse_trim_removal_order is True:
            allTrimGroups = allTrimGroups[::-1]
        for trimGroup in allTrimGroups:
            for element in trimGroup:
                path = element.path.transform(element.composed_transform())
                if path not in totalTrimPaths:
                    totalTrimPaths.append(path)
                else:
                    if self.options.show_debug is True:
                        self.msg("Deleting path {}".format(element.get('id')))
                    element.delete()
            if len(trimGroup) == 0:
                if self.options.show_debug is True:
                    self.msg("Deleting group {}".format(trimGroup.get('id')))
                trimGroup.delete()
                                

    def combine_nonintersects(self, allTrimGroups):
        ''' 
        combine and chain all non intersected sub split lines which were trimmed at intersection points before.
        - At first we sort out all lines by their id: 
            - if the lines id contains intersectedVerb, we ignore it
            - we combine all lines which do not contain intersectedVerb
        - Then we loop through that combined structure and chain their segments which touch each other
        Changes the style according to user setting.
        '''
        
        nonTrimLineStyle = {'stroke': str(self.options.color_nonintersected), 'fill': 'none', 'stroke-width': self.options.strokewidth}
        trimNonIntersectedStyle = {'stroke': str(self.options.color_combined), 'fill': 'none', 'stroke-width': self.options.strokewidth}
        
        for trimGroup in allTrimGroups:
            totalIntersectionsAtPath = 0
            combinedPath = None
            combinedPathData = Path()
            if self.options.show_debug is True:
                self.msg("trim group {} has {} paths".format(trimGroup.get('id'), len(trimGroup)))
            for pElement in trimGroup:
                pId = pElement.get('id')
                #if self.options.show_debug is True:
                #    self.msg("trim paths id {}".format(pId))
                if intersectedVerb not in pId:
                    if combinedPath is None:
                        combinedPath = pElement
                        combinedPathData = pElement.path
                    else:
                        combinedPathData += pElement.path
                        pElement.delete()
                else:
                    totalIntersectionsAtPath += 1
            if len(combinedPathData) > 0:
                segData = combinedPathData.to_arrays()
                newPathData = []
                newPathData.append(segData[0]) 
                for z in range(1, len(segData)): #skip first because we add it statically
                    if segData[z][1] != segData[z-1][1]:
                       newPathData.append(segData[z])
                if self.options.show_debug is True:
                    self.msg("trim group {} has {} combinable segments:".format(trimGroup.get('id'), len(newPathData)))     
                    self.msg("{}".format(newPathData))
                combinedPath.path = Path(newPathData)              
                if self.options.trimmed_style  == "apply_from_trimmed":
                    combinedPath.style = trimNonIntersectedStyle         
                    if totalIntersectionsAtPath == 0:
                        combinedPath.style = nonTrimLineStyle
            else: #the group might consist of intersections only. than we have length of 0
                if self.options.show_debug is True:
                    self.msg("trim group {} has no combinable segments (contains only intersected trim lines)".format(trimGroup.get('id')))  
                       
         
    def trim_bezier(self, allTrimGroups):
        '''
        trim bezier path by checking the lengths and calculating global t parameter from the trimmed sub split lines groups
        This function does not work yet.
        '''  
        for trimGroup in allTrimGroups:
            if (trimGroup.attrib.has_key('originalPathIsBezier') and trimGroup.attrib['originalPathIsBezier'] == "True") or\
            (trimGroup.attrib.has_key('originalPathIsPolyBezMixed') and trimGroup.attrib['originalPathIsPolyBezMixed'] == "True"):
                globalTParameters = []
                if self.options.show_debug is True:
                    self.msg("{}: count of trim lines = {}".format(trimGroup.get('id'), len(trimGroup)))
                totalLength = 0
                for trimLine in trimGroup:
                    ignore, lineLength = csplength(CubicSuperPath(trimLine.get('d')))
                    totalLength += lineLength
                if self.options.show_debug is True:
                    self.msg("total length = {}".format(totalLength))
                chainLength = 0
                for trimLine in trimGroup:
                    ignore, lineLength = csplength(CubicSuperPath(trimLine.get('d')))
                    chainLength += lineLength
                    if trimLine.attrib.has_key('intersected') or trimLine == trimGroup[-1]: #we may not used intersectedVerb because this was used for the affected left as well as the right side of the splitting. This would result in one "intersection" too much.
                        globalTParameter = chainLength / totalLength
                        globalTParameters.append(globalTParameter)
                        if self.options.show_debug is True:
                            self.msg("chain piece length = {}".format(chainLength))
                            self.msg("t parameter = {}".format(globalTParameter))
                        chainLength = 0
                if self.options.show_debug is True:
                    self.msg("Trimming the original bezier path {} at global t parameters: {}".format(trimGroup.attrib['originalPathId'], globalTParameters))
                for globalTParameter in globalTParameters:
                    csp = CubicSuperPath(self.svg.getElementById(trimGroup.attrib['originalPathId']))
                '''
                Sadly, those calculated global t parameters are useless for splitting because we cannot split the complete curve at a t parameter
                Instead we only can split a bezier by getting to commands which build up a bezier path segment.
                - we need to find those parts (segment pairs) of the original path first where the sub split line intersection occurs
                - then we need to calculate the t parameter
                - then we split the bezier part (consisting of two commands) and check the new intersection point. 
                  It should match the sub split lines intersection point.
                  If they do not match we need to adjust the t parameter or loop to previous or next bezier command to find intersection              
                '''
                

    def add_arguments(self, pars):
        pars.add_argument("--nb_main")
        pars.add_argument("--nb_settings_and_actions")
        
        #Settings - General Input/Output
        pars.add_argument("--show_debug", type=inkex.Boolean, default=False, help="Show debug infos")
        pars.add_argument("--break_apart", type=inkex.Boolean, default=False, help="Break apart input paths into sub paths")
        pars.add_argument("--handle_groups", type=inkex.Boolean, default=False, help="Also looks for paths in groups which are in the current selection")
        pars.add_argument("--trimming_path_types", default="closed_paths", help="Process open paths by other open paths, closed paths by other closed paths, or all paths by all other paths")
        pars.add_argument("--flattenbezier", type=inkex.Boolean, default=True, help="Flatten bezier curves to (poly)lines")
        pars.add_argument("--flatness", type=float, default=0.1, help="Minimum flatness = 0.001. The smaller the value the more fine segments you will get (quantization). Large values might destroy the line continuity.")
        pars.add_argument("--decimals", type=int, default=3, help="Accuracy for sub split lines / lines trimmed by shapely")
        pars.add_argument("--snap_tolerance", type=float, default=0.1, help="Snap tolerance for intersection points")
        pars.add_argument("--collinear_filter_epsilon", type=float, default=0.01, help="Epsilon for collinear line filter")
        #Settings - General Style
        pars.add_argument("--strokewidth", type=float, default=1.0, help="Stroke width (px)")   
        pars.add_argument("--dotsize_intersections", type=int, default=30, help="Dot size (px) for self-intersecting and global intersection points")
        pars.add_argument("--removefillsetstroke", type=inkex.Boolean, default=False, help="Remove fill and define stroke for original paths")
        pars.add_argument("--bezier_trimming", type=inkex.Boolean, default=False, help="If true we try to use the calculated t parameters from intersection points to receive splitted bezier curves")
        pars.add_argument("--subsplit_style", default="default", help="Sub split line style")
        pars.add_argument("--trimmed_style", default="apply_from_trimmed", help="Trimmed line style")

        #Removing - Applying to original paths and sub split lines
        pars.add_argument("--remove_relative", type=inkex.Boolean, default=False, help="relative cmd")
        pars.add_argument("--remove_absolute", type=inkex.Boolean, default=False, help="absolute cmd")
        pars.add_argument("--remove_rel_abs_mixed", type=inkex.Boolean, default=False, help="mixed rel/abs cmd (relative + absolute)")
        pars.add_argument("--remove_polylines", type=inkex.Boolean, default=False, help="(poly)line")
        pars.add_argument("--remove_beziers", type=inkex.Boolean, default=False, help="bezier")
        pars.add_argument("--remove_poly_bez_mixed", type=inkex.Boolean, default=False, help="mixed (poly)line/bezier paths")     
        pars.add_argument("--remove_opened", type=inkex.Boolean, default=False, help="opened")
        pars.add_argument("--remove_closed", type=inkex.Boolean, default=False, help="closed")
        pars.add_argument("--remove_self_intersecting", type=inkex.Boolean, default=False, help="self-intersecting")
        #Removing - Applying to sub split lines only
        pars.add_argument("--filter_subsplit_collinear", type=inkex.Boolean, default=True, help="Removes any duplicates by merging (multiple) overlapping line segments into longer lines. Not possible to apply for original paths because this routine does not support bezier type paths.")
        pars.add_argument("--filter_subsplit_collinear_action", default="remove", help="What to do with collinear overlapping lines?")
        #Removing - Applying to original paths only
        pars.add_argument("--delete_original_after_split_trim", type=inkex.Boolean, default=False, help="Delete original paths after sub splitting / trimming") 

        #Highlighting - Applying to original paths and sub split lines
        pars.add_argument("--highlight_relative", type=inkex.Boolean, default=False, help="relative cmd paths")
        pars.add_argument("--highlight_absolute", type=inkex.Boolean, default=False, help="absolute cmd paths")
        pars.add_argument("--highlight_rel_abs_mixed", type=inkex.Boolean, default=False, help="mixed rel/abs cmd (relative + absolute) paths")
        pars.add_argument("--highlight_polylines", type=inkex.Boolean, default=False, help="(poly)line paths")
        pars.add_argument("--highlight_beziers", type=inkex.Boolean, default=False, help="bezier paths")
        pars.add_argument("--highlight_poly_bez_mixed", type=inkex.Boolean, default=False, help="mixed (poly)line/bezier paths")     
        pars.add_argument("--highlight_opened", type=inkex.Boolean, default=False, help="opened paths")
        pars.add_argument("--highlight_closed", type=inkex.Boolean, default=False, help="closed paths")
        #Highlighting - Applying to sub split lines only
        pars.add_argument("--draw_subsplit", type=inkex.Boolean, default=False, help="Draw sub split lines ((poly)lines)")
        pars.add_argument("--highlight_duplicates", type=inkex.Boolean, default=False, help="duplicates (only applies to sub split lines)")
        pars.add_argument("--highlight_merges", type=inkex.Boolean, default=False, help="merges (only applies to sub split lines)")
        #Highlighting - Intersection points
        pars.add_argument("--highlight_self_intersecting", type=inkex.Boolean, default=False, help="self-intersecting paths")
        pars.add_argument("--visualize_self_intersections", type=inkex.Boolean, default=False, help="self-intersecting path points")
        pars.add_argument("--visualize_global_intersections", type=inkex.Boolean, default=False, help="global intersection points")
 
        #Trimming - General trimming settings
        pars.add_argument("--draw_trimmed", type=inkex.Boolean, default=False, help="Draw trimmed lines")
        pars.add_argument("--combine_nonintersects", type=inkex.Boolean, default=True, help="Combine non-intersected lines")
        pars.add_argument("--remove_trim_duplicates", type=inkex.Boolean, default=True, help="Remove duplicate trim lines")
        pars.add_argument("--reverse_trim_removal_order", type=inkex.Boolean, default=False, help="Reverses the order of removal. Relevant for keeping certain styles of elements")
        pars.add_argument("--remove_subsplit_after_trimming", type=inkex.Boolean, default=True, help="Remove sub split lines after trimming")
        #Trimming - Bentley-Ottmann sweep line settings
        pars.add_argument("--bent_ott_use_ignore_segment_endings", type=inkex.Boolean, default=True, help="Whether to ignore intersections of line segments when both their end points form the intersection point")
        pars.add_argument("--bent_ott_use_debug", type=inkex.Boolean, default=False)
        pars.add_argument("--bent_ott_use_verbose", type=inkex.Boolean, default=False)        
        pars.add_argument("--bent_ott_use_paranoid", type=inkex.Boolean, default=False)
        pars.add_argument("--bent_ott_use_vertical", type=inkex.Boolean, default=True)
        pars.add_argument("--bent_ott_number_type", default="native")

        #Colors
        pars.add_argument("--color_subsplit", type=Color, default='1630897151', help="sub split lines")   
        #Colors - path structure
        pars.add_argument("--color_relative", type=Color, default='3419879935', help="relative cmd paths")
        pars.add_argument("--color_absolute", type=Color, default='1592519679', help="absolute cmd paths")
        pars.add_argument("--color_rel_abs_mixed", type=Color, default='3351636735', help="mixed rel/abs cmd (relative + absolute) paths")     
        pars.add_argument("--color_polyline", type=Color, default='4289703935', help="(poly)line paths")
        pars.add_argument("--color_bezier", type=Color, default='258744063', help="bezier paths")
        pars.add_argument("--color_poly_bez_mixed", type=Color, default='4118348031', help="mixed (poly)line/bezier paths")     
        pars.add_argument("--color_opened", type=Color, default='4012452351', help="opened paths")
        pars.add_argument("--color_closed", type=Color, default='2330080511', help="closed paths")
        #Colors - duplicates and merges
        pars.add_argument("--color_duplicates", type=Color, default='897901823', help="duplicates")
        pars.add_argument("--color_merges", type=Color, default='869366527', help="merges")        
        #Colors - intersections
        pars.add_argument("--color_self_intersecting_paths", type=Color, default='2593756927', help="self-intersecting paths")
        pars.add_argument("--color_self_intersections", type=Color, default='6320383', help="self-intersecting path points")
        pars.add_argument("--color_global_intersections", type=Color, default='4239343359', help="global intersection points")
        #Colors - trimming
        pars.add_argument("--color_trimmed", type=Color, default='1923076095', help="trimmed lines")
        pars.add_argument("--color_combined", type=Color, default='3227634687', help="non-intersected lines")
        pars.add_argument("--color_nonintersected", type=Color, default='3045284607', help="non-intersected paths")


    def effect(self):

        so = self.options

        if so.break_apart is True and so.show_debug is True:
            self.msg("Warning: 'Break apart input' setting is enabled. Cannot check accordingly for relative, absolute or mixed paths for breaked elements (they are always absolute)!")
     
        so.strokewidth = self.svg.unittouu("{}px".format(so.strokewidth)) #add unit conversion globally 
     
        #some configuration dependecies
        if so.highlight_self_intersecting is True or \
           so.highlight_duplicates is True or \
           so.highlight_merges is True:
            so.draw_subsplit = True
            
        if so.highlight_duplicates is True or \
           so.highlight_merges is True:
            so.filter_subsplit_collinear = True
     
        if so.filter_subsplit_collinear is True: #this is a must. 
        #if so.draw_subsplit is disabled bu we filter sub split lines and follow with trim operation we lose a lot of elements which may not be deleted!
            so.draw_subsplit = True

        if so.draw_subsplit is False and so.draw_trimmed is True:
            so.delete_original_after_split_trim = True

        if so.draw_trimmed is True:
            so.draw_subsplit = True
            
        if so.bent_ott_use_debug is True:
            so.show_debug = True

        #some constant stuff / styles
        relativePathStyle = {'stroke': str(so.color_relative), 'fill': 'none', 'stroke-width': so.strokewidth}
        absolutePathStyle = {'stroke': str(so.color_absolute), 'fill': 'none', 'stroke-width': so.strokewidth}
        mixedRelAbsPathStyle = {'stroke': str(so.color_rel_abs_mixed), 'fill': 'none', 'stroke-width': so.strokewidth}
        polylinePathStyle = {'stroke': str(so.color_polyline), 'fill': 'none', 'stroke-width': so.strokewidth}
        bezierPathStyle = {'stroke': str(so.color_bezier), 'fill': 'none', 'stroke-width': so.strokewidth}
        mixedPolyBezPathStyle = {'stroke': str(so.color_poly_bez_mixed), 'fill': 'none', 'stroke-width': so.strokewidth}
        openPathStyle = {'stroke': str(so.color_opened), 'fill': 'none', 'stroke-width': so.strokewidth}
        closedPathStyle = {'stroke': str(so.color_closed), 'fill': 'none', 'stroke-width': so.strokewidth}
        duplicatesPathStyle = {'stroke': str(so.color_duplicates), 'fill': 'none', 'stroke-width': so.strokewidth}
        mergesPathStyle = {'stroke': str(so.color_merges), 'fill': 'none', 'stroke-width': so.strokewidth}
        selfIntersectingPathStyle = {'stroke': str(so.color_self_intersecting_paths), 'fill': 'none', 'stroke-width': so.strokewidth}
        basicSubSplitLineStyle = {'stroke': str(so.color_subsplit), 'fill': 'none', 'stroke-width': so.strokewidth}

        #some config for Bentley Ottmann - applies to highlighting, removing, trimming
        poly_point_isect.USE_IGNORE_SEGMENT_ENDINGS = so.bent_ott_use_ignore_segment_endings
        poly_point_isect.USE_DEBUG = so.bent_ott_use_debug
        poly_point_isect.USE_VERBOSE = so.bent_ott_use_verbose
        if so.show_debug is False:
            poly_point_isect.USE_VERBOSE = False
        poly_point_isect.USE_PARANOID = so.bent_ott_use_paranoid
        poly_point_isect.USE_VERTICAL = so.bent_ott_use_vertical
        NUMBER_TYPE = so.bent_ott_number_type
        if NUMBER_TYPE == 'native':
            Real = float
            NUM_EPS = Real("1e-10")
            NUM_INF = Real(float("inf"))
        elif NUMBER_TYPE == 'numpy':
            import numpy
            Real = numpy.float64
            del numpy
            NUM_EPS = Real("1e-10")
            NUM_INF = Real(float("inf"))
        poly_point_isect.Real = Real
        poly_point_isect.NUM_EPS = NUM_EPS
        poly_point_isect.NUM_INF = NUM_INF
        poly_point_isect.NUM_EPS_SQ = NUM_EPS * NUM_EPS
        poly_point_isect.NUM_ZERO = Real(0.0)
        poly_point_isect.NUM_ONE = Real(1.0)

        #get all paths which are within selection or in document and generate sub split lines
        pathElements = self.get_path_elements()
                  
        subSplitLineArray = []
        
        for pathElement in pathElements:
            originalPathId = pathElement.attrib["id"]
            path = pathElement.path.transform(pathElement.composed_transform())
            #inkex.utils.debug(path)

            '''
            check for relative or absolute paths
            '''
            isRelative = False
            isAbsolute = False
            isRelAbsMixed = False
            relCmds = ['m', 'l', 'h', 'v', 'c', 's', 'q', 't', 'a', 'z']
            if any(relCmd in str(path) for relCmd in relCmds):
                isRelative = True
            if any(relCmd.upper() in str(path) for relCmd in relCmds):
                isAbsolute = True
            if isRelative is True and isAbsolute is True: #cannot be both at the same time, so it's mixed
                isRelAbsMixed = True
                isRelative = False
                isAbsolute = False
            if so.remove_absolute is True and isAbsolute is True:
                pathElement.delete()
                continue #skip this loop iteration
            if so.remove_relative is True and isRelative is True:
                pathElement.delete()
                continue #skip this loop iteration
            if so.remove_rel_abs_mixed is True and isRelAbsMixed is True:
                pathElement.delete()
                continue #skip this loop iteration

            '''
            check for bezier or (poly)line paths
            '''
            isPoly = False         
            isBezier = False
            isPolyBezMixed = False
            chars = set('aAcCqQtTsS')
            if any((c in chars) for c in str(path)):
                isBezier = True
            if ('l' in str(path) or 'L' in str(path)):
                isPoly = True
            if isPoly is True and isBezier is True: #cannot be both at the same time, so it's mixed
                isPolyBezMixed = True
                isPoly = False #reset
                isBezier = False #reset
                
            #if so.show_debug is True:
            #    self.msg("sub path in {} is bezier: {}".format(originalPathId, isBezier))               
            if so.remove_beziers is True and isBezier is True:
                pathElement.delete()
                continue #skip this loop iteration
            if so.remove_polylines is True and isPoly is True:
                pathElement.delete()
                continue #skip this loop iteration
            if so.remove_poly_bez_mixed is True and isPolyBezMixed is False:
                pathElement.delete()
                continue #skip this loop iteration

            '''important conversion step'''
            path = pathElement.path.to_absolute().transform(pathElement.composed_transform())  #now we convert to absolute path, because later processing causes some buggy offsets

            '''
            check for closed or open paths
            '''
            isClosed = False
            raw = path.to_arrays()
            #inkex.utils.debug(path)
            if raw[-1][0] == 'Z' or \
                (raw[-1][0] == 'L' and raw[0][1] == raw[-1][1]) or \
                (raw[-1][0] == 'C' and raw[0][1] == [raw[-1][1][-2], raw[-1][1][-1]]) \
                :  #if first is last point the path is also closed. The "Z" command is not required
                isClosed = True
            if so.remove_opened is True and isClosed is False:
                pathElement.delete()
                continue #skip this loop iteration
            if so.remove_closed is True and isClosed is True:
                pathElement.delete()
                continue #skip this loop iteration
  
            if so.draw_subsplit is True:
                subSplitLineGroup = pathElement.getparent().add(inkex.Group(id="{}-{}".format(idPrefixSubSplit, originalPathId)))
           
            #get all sub paths for the path of the element
            subPaths, prev = [], 0
            for i in range(len(raw)): # Breaks compound paths into simple paths
                if raw[i][0] == 'M' and i != 0:
                    subPaths.append(raw[prev:i])
                    prev = i
            subPaths.append(raw[prev:])
            #inkex.utils.debug(subPaths)

            #now loop through all sub paths (and flatten if desired) to build up single lines
            for subPath in subPaths:                     
                subPathData = CubicSuperPath(subPath)

                #flatten bezier curves. If it was already a straight line do nothing! Otherwise we would split straight lines into a lot more straight linesd)
                if so.flattenbezier is True and (isBezier is True or isPolyBezMixed is True):
                    bezier.cspsubdiv(subPathData, so.flatness) #modifies the path
                    flattenedpath = []
                    for seg in subPathData:
                        first = True
                        for csp in seg:
                            cmd = 'L'
                            if first:
                                cmd = 'M'
                            first = False
                            flattenedpath.append([cmd, [csp[1][0], csp[1][1]]])
                    #self.msg("flattened path = " + str(flattenedpath))
                    segs = list(CubicSuperPath(flattenedpath).to_segments())
                else:
                    segs = list(subPathData.to_segments())
                #segs = segs[::-1] #reverse the segments
                
                #build (poly)lines from segment data
                subSplitLines = []
                for i in range(len(segs) - 1): #we could do the same routine to build up (poly)lines using "for x, y in node.path.end_points". See "number nodes" extension
                    x1, y1, x2, y2 = self.line_from_segments(segs, i, so.decimals)
                    #inkex.utils.debug(segs)
                    #self.msg("xy1=({},{}) xy2=({},{})".format(x1, y1, x2, y2))
                    subSplitId = "{}-{}-{}".format(idPrefixSubSplit, originalPathId, i)
                    line = inkex.PathElement(id=subSplitId)
                    #apply line path with composed negative transform from parent element
                    line.attrib['d'] = 'M {},{} L {},{}'.format(x1, y1, x2, y2) #we set the path of Line using 'd' attribute because if we use trimLine.path the decimals get cut off unwantedly
                    #line.path = [['M', [x1, y1]], ['L', [x2, y2]]]
                    if pathElement.getparent() != self.svg.root and pathElement.getparent() != None:
                        line.path = line.path.transform(-pathElement.getparent().composed_transform())
                    line.style = basicSubSplitLineStyle
                    line.attrib['originalPathId'] = originalPathId
                    line.attrib['originalPathIsRelative'] = str(isRelative)
                    line.attrib['originalPathIsAbsolute'] = str(isAbsolute)
                    line.attrib['originalPathIsRelAbsMixed'] = str(isRelAbsMixed)
                    line.attrib['originalPathIsBezier'] = str(isBezier)
                    line.attrib['originalPathIsPoly'] = str(isPoly)
                    line.attrib['originalPathIsPolyBezMixed'] = str(isPolyBezMixed)
                    line.attrib['originalPathIsClosed'] = str(isClosed)
                    line.attrib['originalPathStyle'] = str(pathElement.style)
                    subSplitLineArray.append(line)

                    if so.subsplit_style == "apply_from_highlightings":
                        if line.attrib['originalPathIsRelative'] == 'True':
                            if so.highlight_relative is True:
                                line.style = relativePathStyle
                  
                        if line.attrib['originalPathIsAbsolute'] == 'True':
                            if so.highlight_absolute is True:
                                line.style = absolutePathStyle
                             
                        if line.attrib['originalPathIsRelAbsMixed'] == 'True':
                            if so.highlight_rel_abs_mixed is True:
                                line.style = mixedRelAbsPathStyle
               
                        if line.attrib['originalPathIsPoly'] == 'True':
                            if so.highlight_polylines is True:
                                line.style = polylinePathStyle
                                                   
                        if line.attrib['originalPathIsBezier'] == 'True':
                            if so.highlight_beziers is True:
                                line.style = bezierPathStyle

                        if line.attrib['originalPathIsPolyBezMixed'] == 'True':
                            if so.highlight_poly_bez_mixed is True:
                                line.style = mixedPolyBezPathStyle
    
                        if line.attrib['originalPathIsClosed'] == 'True':
                            if so.highlight_closed is True:
                                line.style = closedPathStyle
                        else:
                            if so.highlight_opened is True:
                                line.style = openPathStyle
                    elif so.subsplit_style == "apply_from_original":
                        line.style = line.attrib['originalPathStyle']

                    if so.draw_subsplit is True:
                        subSplitLineGroup.add(line)
                    subSplitLines.append([(x1, y1), (x2, y2)])
                    
                #check for self intersections using Bentley-Ottmann algorithm.
                isSelfIntersecting = False
                if so.highlight_self_intersecting is True or so.remove_self_intersecting or so.visualize_self_intersections:
                    selfIntersectionPoints = isect_segments(subSplitLines, validate=True)
                    if len(selfIntersectionPoints) > 0:
                        isSelfIntersecting = True
                        if so.show_debug is True:
                            self.msg("{} in {} intersects itself with {} intersections!".format(subSplitId, originalPathId, len(selfIntersectionPoints)))
                        if so.highlight_self_intersecting is True:
                            for subSplitLine in subSplitLineGroup:
                                subSplitLine.style = selfIntersectingPathStyle #adjusts line color
                            #delete cosmetic sub split lines if desired
                            if so.remove_self_intersecting:
                                subSplitLineGroup.delete()
                        if so.visualize_self_intersections is True: #draw points (circles)
                            selfIntersectionGroup = self.visualize_self_intersections(pathElement, selfIntersectionPoints)
    
                        #delete self-intersecting sub split lines and orginal paths
                        if so.remove_self_intersecting:
                            subSplitLineArray = subSplitLineArray[:len(subSplitLineArray) - len(segs) - 1] #remove all last added lines
                            pathElement.delete() #and finally delete the orginal path
                            continue

            #adjust the style of original paths if desired. Has influence to the finally trimmed lines style results too!
            if so.removefillsetstroke is True:
                self.adjust_style(pathElement)

            #apply styles to original paths
            if isRelative is True:
                if so.highlight_relative is True:
                    pathElement.style = relativePathStyle
      
            if isAbsolute is True:
                if so.highlight_absolute is True:
                    pathElement.style = absolutePathStyle
                 
            if isRelAbsMixed is True:
                if so.highlight_rel_abs_mixed is True:
                    pathElement.style = mixedRelAbsPathStyle
            
            if isBezier is True:
                if so.highlight_beziers is True:
                    pathElement.style = bezierPathStyle
                    
            if isPoly is True:
                if so.highlight_polylines is True:
                    pathElement.style = polylinePathStyle

            if isPolyBezMixed is True:
                if so.highlight_poly_bez_mixed is True:
                    pathElement.style = mixedPolyBezPathStyle

            if isClosed is True:
                if so.highlight_closed is True:
                    pathElement.style = closedPathStyle
            else:
                if so.highlight_opened is True:
                    pathElement.style = openPathStyle

            if isSelfIntersecting is True:
                if so.highlight_self_intersecting is True:
                    pathElement.style = selfIntersectingPathStyle

            if so.draw_subsplit is True:
                if subSplitLineGroup is not None: #might get deleted before so we need to check this first
                    subSplitLineGroup = reversed(subSplitLineGroup) #reverse the order to match the original path segment placing

        if so.show_debug is True:
            self.msg("sub split line count: {}".format(len(subSplitLineArray)))   

        '''
        check for collinear lines and apply filters to remove or regroup and to restyle them
        Run this action only if one of the options requires it (to avoid useless calculation cycles)
        '''     
        if so.filter_subsplit_collinear is True or \
           so.highlight_duplicates is True or \
           so.highlight_merges is True:
            if so.show_debug is True: self.msg("filtering collinear overlapping lines / duplicate lines")
            if len(subSplitLineArray) > 0:
                output_set, dropped_ids = self.filter_collinear(subSplitLineArray)
                deleteIndices = []
                deleteIndice = 0
                for subSplitLine in subSplitLineArray:
                    '''
                    Replace the overlapping items with the new merged output
                    '''
                    for output in output_set:
                        if output['id'] == subSplitLine.attrib['id']:
                            originalSplitLinePath = subSplitLine.path
                            output_line = 'M {},{} L {},{}'.format(
                                output['p0'][0], output['p0'][1], output['p1'][0], output['p1'][1])
                            output_line_reversed = 'M {},{} L {},{}'.format(
                                output['p1'][0], output['p1'][1], output['p0'][0], output['p0'][1])
                            subSplitLine.attrib['d'] = output_line #we set the path using 'd' attribute because if we use trimLine.path the decimals get cut off unwantedly
                            mergedSplitLinePath = subSplitLine.path
                            mergedSplitLinePathReversed = Path(output_line_reversed)
                            #subSplitLine.path = [['M', output['p0']], ['L', output['p1']]] 
                            #self.msg("composed_transform = {}".format(output['composed_transform']))
                            #subSplitLine.transform = Transform(-output['composed_transform']) * subSplitLine.transform

                            subSplitLine.path = subSplitLine.path.transform(-output['composed_transform'])
                            if so.highlight_merges is True:
                                if originalSplitLinePath != mergedSplitLinePath and \
                                   originalSplitLinePath != mergedSplitLinePathReversed: #if the path changed we are going to highlight it
                                    subSplitLine.style = mergesPathStyle
                                    
                    
                    '''
                    Delete or move sub split lines which are overlapping
                    '''
                    ssl_id = subSplitLine.get('id')                 
                    if ssl_id in dropped_ids:
                        if so.highlight_duplicates is True:
                            subSplitLine.style = duplicatesPathStyle
                        
                        if so.filter_subsplit_collinear is True:
                            ssl_parent = subSplitLine.getparent()
                            if so.filter_subsplit_collinear_action == "remove":
                                if self.options.show_debug is True:
                                    self.msg("Deleting sub split line {}".format(subSplitLine.get('id')))
                                subSplitLine.delete() #delete the line from XML tree
                                deleteIndices.append(deleteIndice) #store this id to remove it from stupid subSplitLineArray later
                            elif so.filter_subsplit_collinear_action == "separate_group":
                                if self.options.show_debug is True:
                                    self.msg("Moving sub split line {}".format(subSplitLine.get('id')))
                                originalPathId = subSplitLine.attrib['originalPathId']
                                collinearGroupId = '{}-{}'.format(collinearVerb, originalPathId)
                                originalPathElement = self.svg.getElementById(originalPathId)
                                collinearGroup = self.find_group(collinearGroupId)
                                if collinearGroup is None:
                                    collinearGroup = originalPathElement.getparent().add(inkex.Group(id=collinearGroupId))
                                collinearGroup.append(subSplitLine) #move to that group
                            #and delete the containg group if empty (can happen in "remove" or "separate_group" constellation
                            if ssl_parent is not None and len(ssl_parent) == 0:
                                if self.options.show_debug is True:
                                    self.msg("Deleting group {}".format(ssl_parent.get('id')))
                                ssl_parent.delete()
                                
                    deleteIndice += 1 #end the loop by incrementing +1
                
                #shrink the sub split line array to kick out all unrequired indices
                for deleteIndice in sorted(deleteIndices, reverse=True):
                    if self.options.show_debug is True:
                        self.msg("Deleting index {} from subSplitLineArray".format(deleteIndice))
                    del subSplitLineArray[deleteIndice]

        '''
        now we intersect the sub split lines to find the global intersection points using Bentley-Ottmann algorithm (contains self-intersections too!)
        '''
        if so.draw_trimmed is True:     
            try:
                allSubSplitLineStrings = []
                for subSplitLine in subSplitLineArray:
                    csp = Path(subSplitLine.path.transform(subSplitLine.composed_transform())).to_arrays() #will be buggy if draw subsplit lines is deactivated
                    lineString = [(csp[0][1][0], csp[0][1][1]), (csp[1][1][0], csp[1][1][1])]                    
                    #lineStringStyle = {'stroke': '#0000FF', 'fill': 'none', 'stroke-width': str(self.svg.unittouu('1px'))}
                    #line = self.svg.get_current_layer().add(inkex.PathElement(id=self.svg.get_unique_id('lineString')))
                    #line.set('d', "M{:0.6f},{:0.6f} L{:0.6f},{:0.6f}".format(lineString[0][0],lineString[0][1],lineString[1][0],lineString[1][1]))
                    #line.style = lineStringStyle
                    #line.transform = -self.svg.get_current_layer().transform
                    
                    if so.remove_trim_duplicates is True:
                        if lineString not in allSubSplitLineStrings:
                            allSubSplitLineStrings.append(lineString)
                        else:
                            if so.show_debug is True:
                                self.msg("line {} already in sub split line collection. Dropping ...".format(lineString))
                    else: #if false we append all segments without filtering duplicate ones
                        allSubSplitLineStrings.append(lineString)        
                if so.show_debug is True:
                    self.msg("Going to calculate intersections using Bentley Ottmann Sweep Line Algorithm") 
                globalIntersectionPoints = MultiPoint(isect_segments(allSubSplitLineStrings, validate=True))       
                if so.show_debug is True:
                    self.msg("global intersection points count: {}".format(len(globalIntersectionPoints)))   
                if len(globalIntersectionPoints.geoms) > 0:
                    if so.visualize_global_intersections is True:
                        self.visualize_global_intersections(globalIntersectionPoints)
    
                    '''
                    now we trim the sub split lines at all calculated intersection points. 
                    We do this path by path to keep the logic between original paths, sub split lines and the final output
                    '''                            
                    allTrimGroups = [] #container to collect all trim groups for later on processing 
                    for subSplitIndex in range(len(subSplitLineArray)):
                        trimGroup = self.build_trim_line_group(subSplitLineArray, subSplitIndex, globalIntersectionPoints)
                        if trimGroup is not None:
                            if trimGroup not in allTrimGroups:
                                allTrimGroups.append(trimGroup)
                 
                    if so.show_debug is True: self.msg("trim groups count: {}".format(len(allTrimGroups)))
                    if len(allTrimGroups) == 0:
                        self.msg("You selected to draw trimmed lines but no intersections could be calculated.")
                         
                    if so.bezier_trimming is True:
                        if so.show_debug is True: self.msg("trimming beziers - not working yet")
                        self.trim_bezier(allTrimGroups)  
                   
                    if so.remove_trim_duplicates is True:
                        if so.show_debug is True: self.msg("checking for duplicate trim lines and deleting them")
                        self.remove_trim_duplicates(allTrimGroups)
                                         
                    if so.combine_nonintersects is True:
                        if so.show_debug is True: self.msg("glueing together all non-intersected sub split lines to larger path structures again (cleaning up)")
                        self.combine_nonintersects(allTrimGroups)
        
                    if so.remove_subsplit_after_trimming is True:
                        if so.show_debug is True: self.msg("removing unwanted subsplit lines after trimming")
                        for subSplitLine in subSplitLineArray:
                            ssl_parent = subSplitLine.getparent()
                            subSplitLine.delete()
                            if ssl_parent is not None and len(ssl_parent) == 0:
                                if self.options.show_debug is True:
                                    self.msg("Deleting group {}".format(ssl_parent.get('id')))
                                ssl_parent.delete()

            except AssertionError as e:
                self.msg("Error calculating global intersections.\n\
See https://github.com/ideasman42/isect_segments-bentley_ottmann.\n\n\
You can try to fix this by:\n\
- reduce or raise the 'decimals' setting (default is 3 but try to set to 6 for example)\n\
- reduce or raise the 'flatness' setting (if quantization option is used at all; default is 0.100).")
                return

        #clean original paths if selected.
        if so.delete_original_after_split_trim is True:
            if so.show_debug is True: self.msg("cleaning original paths after sub splitting / trimming")
            for pathElement in pathElements:
                pathElement.delete()

if __name__ == '__main__':
    ContourScannerAndTrimmer().run()
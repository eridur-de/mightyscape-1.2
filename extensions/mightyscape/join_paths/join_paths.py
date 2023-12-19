#!/usr/bin/env python3

'''
Inkscape extension to join the selected paths. With the optimized option selected, 
the next path to be joined is the one, which has one of its end nodes closest to the ending
node of the earlier path.

Copyright (C) 2019  Shrinivas Kulkarni

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''

import inkex
from inkex.paths import CubicSuperPath
import sys
import copy
import math

def floatCmpWithMargin(float1, float2, margin):
    return abs(float1 - float2) < margin 
    
def vectCmpWithMargin(vect1, vect2, margin):
    return all(floatCmpWithMargin(vect2[i], vect1[i], margin) for i in range(0, len(vect1)))

def getPartsFromCubicSuper(cspath):
    parts = []
    for subpath in cspath:
        part = []
        prevBezPt = None            
        for i, bezierPt in enumerate(subpath):
            if(prevBezPt != None):
                seg = [prevBezPt[1], prevBezPt[2], bezierPt[0], bezierPt[1]]
                part.append(seg)
            prevBezPt = bezierPt
        parts.append(part)
    return parts
        
def getCubicSuperFromParts(parts):
    cbsuper = []
    for part in parts:
        subpath = []
        lastPt = None
        pt = None
        for seg in part:
            if(pt == None):
                ptLeft = seg[0]
                pt = seg[0]
            ptRight = seg[1]
            subpath.append([ptLeft, pt, ptRight])
            ptLeft = seg[2]
            pt = seg[3]
        subpath.append([ptLeft, pt, pt])
        cbsuper.append(subpath)
    return cbsuper
    
def getArrangedIds(pathMap, startPathId):
    nextPathId = startPathId
    orderPathIds = [nextPathId]
    
    #Arrange in order
    while(len(orderPathIds) < len(pathMap)):
        minDist = 9e+100 #A large float
        closestId = None        
        np = pathMap[nextPathId]
        if np[-1] == []:
            inkex.utils.debug("Warning. Selection seems to contain invalid paths, e.g. pointy paths like M 54,54 Z. Please check and try again!")
            exit(1)
        npPts = [np[-1][-1][-1]]
        if(len(orderPathIds) == 1):#compare both the ends for the first path
            npPts.append(np[0][0][0])
        
        for key in pathMap:
            if(key in orderPathIds):
                continue
            parts = pathMap[key] 
            start = parts[0][0][0]
            end = parts[-1][-1][-1]
            
            for i, npPt in enumerate(npPts):
                dist = abs(start[0] - npPt[0]) + abs(start[1] - npPt[1])
                if(dist < minDist):
                    minDist = dist
                    closestId = key
                dist = abs(end[0] - npPt[0]) + abs(end[1] - npPt[1])
                if(dist < minDist):
                    minDist = dist
                    pathMap[key] = [[[pts for pts in reversed(seg)] for seg in \
                        reversed(part)] for part in reversed(parts)]
                    closestId = key
                    
                #If start point of the first path is closer reverse its direction    
                if(i > 0 and closestId == key):
                    pathMap[nextPathId] = [[[pts for pts in reversed(seg)] for seg in \
                        reversed(part)] for part in reversed(np)]
                    
        orderPathIds.append(closestId)
        nextPathId = closestId
    return orderPathIds
    
def rotate(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.
    """
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy

class JoinPaths(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--optimized", type=inkex.Boolean, default=True)
        pars.add_argument("--reverse", type=inkex.Boolean, default=False)
        pars.add_argument("--margin", type=float, default=0.0100)
        pars.add_argument("--add_dimples", type=inkex.Boolean, default=False)
        pars.add_argument("--draw_dimple_centers", type=inkex.Boolean, default=False)
        pars.add_argument("--draw_arcs_as_paths", type=inkex.Boolean, default=False)
        pars.add_argument("--dimple_invert", type=inkex.Boolean, default=False)
        pars.add_argument("--dimple_type", default="lines")
        pars.add_argument("--dimples_to_group", type=inkex.Boolean, default=False)
        pars.add_argument("--draw_both_sides", type=inkex.Boolean, default=False)
        pars.add_argument("--dimple_height_mode", default="by_height")
        pars.add_argument("--dimple_height", type=float, default=4)
        pars.add_argument("--dimple_angle", type=float, default=45)
        pars.add_argument("--dimple_tab_angle", type=float, default=45)
        pars.add_argument("--dimple_sheetmetal_depth", type=float, default=4)
        pars.add_argument("--dimple_gap_filter", type=inkex.Boolean, default=False)
        pars.add_argument("--dimple_min_gap", type=float, default=1)
        pars.add_argument("--dimple_max_gap", type=float, default=40)
        pars.add_argument("--dimple_gap_filter_units", default="mm")
        pars.add_argument("--dimple_height_units", default="mm")
        pars.add_argument("--tab", default="sampling", help="Tab") 
          
    def effect(self):

        pathNodes = self.document.xpath('//svg:path',namespaces=inkex.NSS)
        if self.options.reverse is True: #helps debugging some strange Z orders (try out)
            pathNodes = pathNodes[::-1]
            #pathNodes[0].path = pathNodes[0].path.reverse()
            #pathNodes[0].path = pathNodes[-1].path.reverse()

        paths = {p.get('id'): getPartsFromCubicSuper(CubicSuperPath(p.get('d'))) for p in pathNodes }
        #paths.keys() Order disturbed
        pathIds = [p.get('id') for p in pathNodes]

        if self.options.dimples_to_group is True:
            dimpleUnifyGroup = self.svg.get_current_layer().add(inkex.Group(id=self.svg.get_unique_id("dimplesCollection")))
        
        if(len(paths) > 1):
            if(self.options.optimized):
                startPathId = pathIds[0]
                pathIds = getArrangedIds(paths, startPathId)                
            newParts = []
            firstElem = None
            for key in pathIds:
                parts = paths[key]
                # ~ parts = getPartsFromCubicSuper(cspath)
                start = parts[0][0][0]
                try:
                    elem = self.svg.selected[key]
            
                    if(len(newParts) == 0):
                        newParts += parts[:]
                        firstElem = elem
                    else:
                        if(vectCmpWithMargin(start, newParts[-1][-1][-1], margin = self.options.margin)) and self.options.add_dimples is False:
                            newParts[-1] += parts[0]
                        else:
                            if self.options.add_dimples is True:
                                if self.options.dimples_to_group is True:
                                    dimpleGroup = dimpleUnifyGroup.add(inkex.Group(id="dimpleGroup-{}".format(elem.attrib["id"])))
                                else:
                                    dimpleGroup = elem.getparent().add(inkex.Group(id="dimpleGroup-{}".format(elem.attrib["id"])))

                                p1 = newParts[-1][-1][-1]
                                p2 = start
                                midPoint = [(p1[0] + p2[0])/2, (p1[1] + p2[1])/2]
                                newParts[-1].append([newParts[-1][-1][-1], newParts[-1][-1][-1], midPoint, midPoint])                
                                newParts[-1].append([newParts[-1][-1][-1], newParts[-1][-1][-1], p2, p2])
                                newParts[-1] += parts[0]
                                
                                #get slope, distance and norm slope
                                dx = midPoint[0]-p1[0]
                                dy = midPoint[1]-p1[1]
                                dist = math.sqrt(dx*dx + dy*dy)
                                dx /= dist
                                dy /= dist
                            
                                dx2 = p2[0]-p1[0]
                                dy2 = p2[1]-p1[1] 
                                dist2 = math.sqrt(dx2*dx2 + dy2*dy2)
                                if dx2 == 0:
                                    slope=sys.float_info.max #vertical
                                else:
                                    slope=(p2[1] - p1[1]) / dx2
                                slope_angle = 90 + math.degrees(math.atan(slope))
                                if (self.options.dimple_gap_filter is True \
                                    and dist2 >= self.svg.unittouu(str(self.options.dimple_min_gap) + self.options.dimple_gap_filter_units) \
                                    and dist2 < self.svg.unittouu(str(self.options.dimple_max_gap) + self.options.dimple_gap_filter_units) 
                                    ) \
                                    or self.options.dimple_gap_filter is False:                                
                                    if self.options.dimple_height_mode == "by_height":
                                        dimple_height = self.svg.unittouu(str(self.options.dimple_height) + self.options.dimple_height_units)
                                    else:
                                        dimple_height = dist * math.sin(math.radians(self.options.dimple_angle))
                                    
                                    x3 = midPoint[0] + (dimple_height)*dy
                                    y3 = midPoint[1] - (dimple_height)*dx
                                    x4 = midPoint[0] - (dimple_height)*dy
                                    y4 = midPoint[1] + (dimple_height)*dx
                                    
                                    dimple_center_style = {'stroke': '#00FFFF', 'fill': 'none', 'stroke-width': str(self.svg.unittouu('1px'))}
                                    dimple_style = {'stroke': '#0000FF', 'fill': 'none', 'stroke-width': str(self.svg.unittouu('1px'))}
                                    
                                    if self.options.draw_dimple_centers is True:
                                        #add a new dimple center cross (4 segments)
                                        line = dimpleGroup.add(inkex.PathElement(id=self.svg.get_unique_id('dimple_center_perp1')))
                                        line.set('d', "M{:0.6f},{:0.6f} L{:0.6f},{:0.6f}".format(midPoint[0], midPoint[1], x3, y3))
                                        line.style = dimple_center_style
                                        line = dimpleGroup.add(inkex.PathElement(id=self.svg.get_unique_id('dimple_center_perp2')))
                                        line.set('d', "M{:0.6f},{:0.6f} L{:0.6f},{:0.6f}".format(midPoint[0], midPoint[1], x4, y4))
                                        line.style = dimple_center_style
                                        line = dimpleGroup.add(inkex.PathElement(id=self.svg.get_unique_id('dimple_center_join1')))
                                        line.set('d', "M{:0.6f},{:0.6f} L{:0.6f},{:0.6f}".format(p1[0], p1[1], midPoint[0], midPoint[1]))
                                        line.style = dimple_center_style
                                        line = dimpleGroup.add(inkex.PathElement(id=self.svg.get_unique_id('dimple_center_join1')))
                                        line.set('d', "M{:0.6f},{:0.6f} L{:0.6f},{:0.6f}".format(midPoint[0], midPoint[1], p2[0], p2[1]))
                                        line.style = dimple_center_style
                                    
                                    ##########
                                    ### LINES
                                    ##########
                                    if self.options.dimple_type == "lines":
                                        line = dimpleGroup.add(inkex.PathElement(id=self.svg.get_unique_id('dimple_line')))
                                        line.set('d', "M{:0.6f},{:0.6f} L{:0.6f},{:0.6f}".format(p1[0], p1[1], p2[0], p2[1]))
                                        line.style = dimple_style
                                              
                                    ##########
                                    ### PEAKS
                                    ##########
                                    elif self.options.dimple_type == "peaks":
                                        if self.options.dimple_invert is True:
                                            x5 = x3
                                            y5 = y3
                                            x3 = x4
                                            y3 = y4
                                            x4 = x5
                                            y4 = y5
                                        #add a new dimple center
                                        line = dimpleGroup.add(inkex.PathElement(id=self.svg.get_unique_id('dimple_peak')))
                                        line.set('d', "M{:0.6f},{:0.6f} L{:0.6f},{:0.6f} L{:0.6f},{:0.6f}".format(p1[0], p1[1], x3, y3, p2[0], p2[1]))
                                        line.style = dimple_style 
                                     
                                        if self.options.draw_both_sides is True:
                                            #add a new opposite dimple center
                                            line = dimpleGroup.add(inkex.PathElement(id=self.svg.get_unique_id('dimple_peak')))
                                            line.set('d', "M{:0.6f},{:0.6f} L{:0.6f},{:0.6f} L{:0.6f},{:0.6f}".format(p1[0], p1[1], x4, y4, p2[0], p2[1]))
                                            line.style = dimple_style
                                    ##########
                                    ### ARCS
                                    ##########
                                    elif self.options.dimple_type == "arcs":
                                        if self.options.draw_arcs_as_paths is False:
                                            ellipse = dimpleGroup.add(inkex.Ellipse(id=self.svg.get_unique_id('dimple_arc')))
                                            ellipse.set('transform', "rotate({:0.6f} {:0.6f} {:0.6f})".format(slope_angle, midPoint[0], midPoint[1]))
                                            ellipse.set('sodipodi:arc-type', "arc")
                                            ellipse.set('sodipodi:type', "arc")
                                            ellipse.set('sodipodi:cx', "{:0.6f}".format(midPoint[0]))
                                            ellipse.set('sodipodi:cy', "{:0.6f}".format(midPoint[1]))
                                            ellipse.set('sodipodi:rx', "{:0.6f}".format(dimple_height))
                                            ellipse.set('sodipodi:ry', "{:0.6f}".format(dist2 / 2))
                                            if self.options.dimple_invert is True:
                                                ellipse.set('sodipodi:start', "{:0.6f}".format(math.radians(90.0)))
                                                ellipse.set('sodipodi:end', "{:0.6f}".format(math.radians(270.0)))
                                            else:
                                                ellipse.set('sodipodi:start', "{:0.6f}".format(math.radians(270.0)))
                                                ellipse.set('sodipodi:end', "{:0.6f}".format(math.radians(90.0)))
                                            ellipse.style = dimple_style
                               
                                            if self.options.draw_both_sides is True:
                                                ellipse = dimpleGroup.add(inkex.Ellipse(id=self.svg.get_unique_id('dimple_arc')))
                                                ellipse.set('transform', "rotate({:0.6f} {:0.6f} {:0.6f})".format(slope_angle, midPoint[0], midPoint[1]))
                                                ellipse.set('sodipodi:arc-type', "arc")
                                                ellipse.set('sodipodi:type', "arc")
                                                ellipse.set('sodipodi:cx', "{:0.6f}".format(midPoint[0]))
                                                ellipse.set('sodipodi:cy', "{:0.6f}".format(midPoint[1]))
                                                ellipse.set('sodipodi:rx', "{:0.6f}".format(dimple_height))
                                                ellipse.set('sodipodi:ry', "{:0.6f}".format(dist2 / 2))
                                            if self.options.dimple_invert is True:
                                                ellipse.set('sodipodi:start', "{:0.6f}".format(math.radians(270.0)))
                                                ellipse.set('sodipodi:end', "{:0.6f}".format(math.radians(90.0)))
                                            else:
                                                ellipse.set('sodipodi:start', "{:0.6f}".format(math.radians(90.0)))
                                                ellipse.set('sodipodi:end', "{:0.6f}".format(math.radians(270.0)))
                                            ellipse.style = dimple_style
                                        else: #if draw_arcs_as_paths is True
                                            #                                    +--- x-end point
                                            #                                    |  
                                            #            counterclockwise ---+   |   +--- y-end point
                                            #                                |   |   |
                                            #<path d="M 85 350 A 150 180 0 0 0  280 79" stroke="red" fill="none"/>
                                            #                     |   |  | |
                                            #  1 Radius x-Axis ---+   |  | +--- 4 short / long way
                                            #                         |  |
                                            #      2 Radius y-Axis ---+  +--- 3 Rotation x 
                                            if self.options.dimple_invert is True:
                                                b1 = 1
                                                b2 = 0
                                            else:
                                                b1 = 0
                                                b2 = 1
                                            ellipse = dimpleGroup.add(inkex.PathElement(id=self.svg.get_unique_id('dimple_arc')))
                                            ellipse.set('d', "M {:0.6f} {:0.6f} A {:0.6f} {:0.6f} {:0.6f} 0 {} {:0.6f} {:0.6f}".format(p1[0], p1[1], dimple_height, dist2 / 2, slope_angle, b1, p2[0], p2[1]))
                                            ellipse.style = dimple_style
                                            if self.options.draw_both_sides is True:
                                                ellipse = dimpleGroup.add(inkex.PathElement(id=self.svg.get_unique_id('dimple_arc')))
                                                ellipse.set('d', "M {:0.6f} {:0.6f} A {:0.6f} {:0.6f} {:0.6f} 0 {} {:0.6f} {:0.6f}".format(p1[0], p1[1], dimple_height, dist2 / 2, slope_angle, b2, p2[0], p2[1]))
                                                ellipse.style = dimple_style  
                                     
                                    ##########
                                    ### TABS
                                    ##########
                                    elif self.options.dimple_type == "tabs":
                                        l_hypo = dimple_height / (math.cos(math.radians(90.0 - self.options.dimple_tab_angle)))
                                        pbottom1 = rotate(p1, [p1[0] + l_hypo * dx, p1[1] + l_hypo * dy], math.radians(-self.options.dimple_tab_angle))
                                        pbottom2 = rotate(p2, [p2[0] - l_hypo * dx, p2[1] - l_hypo * dy], math.radians(-360.0 + self.options.dimple_tab_angle))        
                                        ptop1 = rotate(p1, [p1[0] + l_hypo * dx, p1[1] + l_hypo * dy], math.radians(self.options.dimple_tab_angle))
                                        ptop2 = rotate(p2, [p2[0] - l_hypo * dx, p2[1] - l_hypo * dy], math.radians(360.0 - self.options.dimple_tab_angle))
                                        
    
                                        if self.options.dimple_invert is True:
                                            ptemp1 = pbottom1
                                            ptemp2 = pbottom2
                                            pbottom1 = ptop1
                                            pbottom2 = ptop2
                                            ptop1 = ptemp1
                                            ptop2 = ptemp2
                                            
                                        #add a new tab
                                        line = dimpleGroup.add(inkex.PathElement(id=self.svg.get_unique_id('dimple_tab')))
                                        line.set('d', "M{:0.6f},{:0.6f} L{:0.6f},{:0.6f} L{:0.6f},{:0.6f} L{:0.6f},{:0.6f}".format(
                                            p1[0], p1[1], pbottom1[0], pbottom1[1], pbottom2[0], pbottom2[1], p2[0], p2[1]))
                                        line.style = dimple_style
                                        if self.options.draw_both_sides is True:
                                            line = dimpleGroup.add(inkex.PathElement(id=self.svg.get_unique_id('dimple_tab')))
                                            line.set('d', "M{:0.6f},{:0.6f} L{:0.6f},{:0.6f} L{:0.6f},{:0.6f} L{:0.6f},{:0.6f}".format(
                                                p1[0], p1[1], ptop1[0], ptop1[1], ptop2[0], ptop2[1], p2[0], p2[1]))
                                            line.style = dimple_style
                             
                                    ##########
                                    ### sHEETMETAL
                                    ##########
                                    elif self.options.dimple_type == "sheetmetal":
                                        
                                        if self.options.dimple_invert is True:
                                            self.options.dimple_tab_angle = 360.0 - self.options.dimple_tab_angle
                                        
                                        pbottom1 = rotate(p1, [p1[0] + dimple_height * dx, p1[1] + dimple_height * dy], math.radians(-self.options.dimple_tab_angle))
                                        pbottom2 = rotate(p2, [p2[0] - dimple_height * dx, p2[1] - dimple_height * dy], math.radians(-360.0 + self.options.dimple_tab_angle))                                                

                                        depth = self.svg.unittouu(str(self.options.dimple_sheetmetal_depth) + self.options.dimple_height_units)
                                        poff1 = [p1[0] + (depth)*dx, p1[1] + (depth)*dy]
                                        poff2 = [p2[0] - (depth)*dx, p2[1] - (depth)*dy]          
                                        poff1_start = rotate(poff1, [poff1[0] + dimple_height * dx, poff1[1] + dimple_height * dy], math.radians(180.0 - self.options.dimple_tab_angle))
                                        poff2_end = rotate(poff2, [poff2[0] + dimple_height * dx, poff2[1] + dimple_height * dy], math.radians(self.options.dimple_tab_angle))

                                        line = dimpleGroup.add(inkex.PathElement(id=self.svg.get_unique_id('dimple_sheetmetal_start')))
                                        line.set('d', "M{:0.6f},{:0.6f} L{:0.6f},{:0.6f}".format(
                                            p1[0], p1[1], pbottom1[0], pbottom1[1]))
                                        line.style = dimple_style

                                        line = dimpleGroup.add(inkex.PathElement(id=self.svg.get_unique_id('dimple_sheetmetal_middle')))
                                        line.set('d', "M{:0.6f},{:0.6f} L{:0.6f},{:0.6f} L{:0.6f},{:0.6f} L{:0.6f},{:0.6f}".format(
                                            poff1_start[0], poff1_start[1], poff1[0], poff1[1], poff2[0], poff2[1], poff2_end[0], poff2_end[1]))
                                        line.style = dimple_style

                                        line = dimpleGroup.add(inkex.PathElement(id=self.svg.get_unique_id('dimple_sheetmetal_end')))
                                        line.set('d', "M{:0.6f},{:0.6f} L{:0.6f},{:0.6f}".format(
                                            p2[0], p2[1], pbottom2[0], pbottom2[1]))
                                        line.style = dimple_style

                                    #cleanup groups
                                    if len(dimpleGroup) == 1: ##move up child if group has only one child
                                        for child in dimpleGroup:
                                            dimpleGroup.getparent().insert(elem.getparent().index(elem), child)
                                        dimpleGroup.delete() #delete the empty group now
                                         
                            else:
                                newParts[-1].append([newParts[-1][-1][-1], newParts[-1][-1][-1], start, start])
                                newParts[-1] += parts[0]
    
                        if(len(parts) > 1):
                            newParts += parts[1:]
                    
                    parent = elem.getparent()
                    idx = parent.index(elem)
                    if self.options.add_dimples is False:
                        parent.remove(elem)
                except:
                    pass #elem might come from group item - in this case we need to ignore it
					
            if firstElem is None:
                self.msg('Please select some paths first. Check if you selected a group or an object instead.')
                exit()  
            newElem = copy.copy(firstElem)
            oldId = firstElem.get('id')
            newElem.set('d', CubicSuperPath(getCubicSuperFromParts(newParts)))
            newElem.set('id', oldId + '_joined')
            if self.options.add_dimples is False:
                parent.insert(idx, newElem)

if __name__ == '__main__':
    JoinPaths().run()
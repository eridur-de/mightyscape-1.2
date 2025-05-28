#!/usr/bin/env python3

'''

This extension changes the order of the nodes without changing the shape of the path. It's required to modify paths
like this for example when projecting text to path or applying bezier envelope transformation.

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 19.05.2021
Last patch: 28.05.2025
License: GNU GPL v3
'''

import copy
import inkex
import sys
from inkex import Circle, TextElement, PathElement
from inkex.paths import CubicSuperPath, Path

class MovePathNode(inkex.EffectExtension):
  
    def modify(self, element):

        if self.options.debug is True:
            inkex.utils.debug("raw root path:")
            inkex.utils.debug(element.path)
            inkex.utils.debug("-"*25)

        raw = element.path.to_arrays()
        subpaths, prev = [], 0
        for i in range(len(raw)): # Breaks compound paths into simple paths
            if raw[i][0] == 'M' and i != 0:
                subpaths.append(raw[prev:i])
                prev = i
        subpaths.append(raw[prev:])
        if self.options.debug is True:
            if len(subpaths) == 0:
                inkex.utils.debug("{} has no subpaths").format(element.get('id')) 
            else:
                inkex.utils.debug("{} has {} subpath(s)".format(element.get('id'), len(subpaths)))
            
        subpathNr = 0
        for path in subpaths:
            subpathNr += 1   
            newSubpaths = subpaths #we will overwrite them later
            
            pathIsClosed = False
            if path[-1][0] == 'Z' or \
                (path[-1][0] == 'L' and path[0][1] == path[-1][1]) or \
                (path[-1][0] == 'C' and path[0][1] == [path[-1][1][-2], path[-1][1][-1]]) \
                :  #if first is last point the path is also kind of closed, but not cleanly. We assume that matching of start and end targets to be closed
                pathIsClosed = True
    
            if self.options.debug is True:
                nodeCountInitial = len(path)
                inkex.utils.debug("pathIsClosed = " + str(pathIsClosed))
                inkex.utils.debug("initial nodes = " + str(nodeCountInitial))

            if self.options.closed_only is True and pathIsClosed is False:
                if len(subpaths) == 0:
                    inkex.utils.debug("{}/subpath {} is not closed! Skipping ...".format(element.get('id'), subpathNr))
                else:
                    inkex.utils.debug("{} is not closed! Skipping ...".format(element.get('id'))) 
                continue #skip this open path
    
            if len(path) == 2:
                continue #skip this open path (special case of straight line segment)

            if path[-1][0] == 'Z': #replace Z with another L command (which moves to the coordinates of the first M command in path) to have better overview
                path[-1][0] = 'L'
                path[-1][1] = path[0][1]
    
            #adjust if entered move number is higher than actual node count. We handle as infinite looping
            moves = (self.options.movenode) % len(path)
            if pathIsClosed is True: #if closed start and end collapse and "duplicate"
                moves = (self.options.movenode) % (len(path) - 1)
            if self.options.movenode == 0: #special handling for 0 is required - means "do nothing"
                moves = 0
            if moves < 1:
                if self.options.debug is True: inkex.utils.debug("Nothing to do (0 moves) ...")
            else:
                if self.options.debug is True:
                    inkex.utils.debug("moves to perform = " + str(moves))
                    inkex.utils.debug("raw root path:")
                    inkex.utils.debug(path)
                    inkex.utils.debug("-"*25)

                for i in range(moves):
                    if len(path) > 2: #the path needs at least more than two segments, else we might just get a "pointy path" on an open path

                        #special case for rare paths: check if first node and last node match and if there is a Z between, which doubles up, while showing 1 node less than exspected
                        doubleClosed = False
                        if [path[0][1][-2], path[0][1][-1]] == [path[-2][1][-2], path[-2][1][-1]] and pathIsClosed is True:
                            doubleClosed = True
                            if self.options.debug is True: inkex.utils.debug("doubleClosed = " + str(doubleClosed))

                        #we move the first segment to the end of the list
                        move = path[0]
                        del path[0]
                        path.append(move)
                        oldseg = copy.deepcopy(path[0]) #if we assign like "oldseg = path[0]", it will get overwritten. So we need copy
                            
                        if self.options.debug is True:
                            inkex.utils.debug("moved path (move no. {}):".format(i+1))
                            inkex.utils.debug(path)
                            inkex.utils.debug("-"*25)
                        
                        #Now we messed the integrity of the path. It does not begin with 'M' now. But we need an 'M'. 
                        #It now either starts with L or C. H, V, Z cannot occure here.
                        if path[0][0]  == 'C': #and path[-1][0] == 'M':
                            #inkex.utils.debug("C to M")
                            path[0][1] = [path[0][1][-2], path[0][1][-1]]
                        elif path[0][0]  == 'L': #and path[-1][0] == 'M':
                            #inkex.utils.debug("L to M")
                            path[0][1] = [path[0][1][0], path[0][1][1]]
                        #else:
                        #    inkex.utils.debug("no idea")

                        path[0][0] = 'M' #we really need M. Does not matter if 'L' or 'C'.

                        if doubleClosed is True:
                            del path[-2]
                            
                        if pathIsClosed is True:
                            if path[-1][0] == 'M' and len(oldseg[1]) == 2: #data of an 'L' command
                                path[-1][0] = 'L'
                                path[-1][1] = path[0][1]
                                if self.options.debug is True: inkex.utils.debug("modified M command to L command")
                            elif path[-1][0] == 'M' and len(oldseg[1]) > 2: #data of an 'C' command
                                path[-1][0] = 'C'
                                path[-1][1] = oldseg[1]
                                if self.options.debug is True: inkex.utils.debug("modified M command to C command")
                        else:
                            if path[-1][0] == 'M': #if open path we just drop the dangling 'M' command completely
                                del path[-1]
                                if self.options.debug is True: inkex.utils.debug("delete dangling M command")

                        if pathIsClosed is True and path[-1] != (['Z', []]):
                            path.append(['Z', []])    

                        if self.options.debug is True:
                            nodeCountFinal = len(path)
                            inkex.utils.debug("final nodes = " + str(nodeCountFinal)) #that count must match the inital count!
                            inkex.utils.debug("final path:")                 
                            inkex.utils.debug(path)
                            inkex.utils.debug("-"*25)
                            if nodeCountInitial != nodeCountFinal:
                                inkex.utils.debug("Warning! Node count changed from {} to {}".format(nodeCountInitial, nodeCountFinal))

                        newSubpaths[subpathNr - 1] = path
                    else:
                        if self.options.debug is True:
                            inkex.utils.debug("More moves entered than possible to apply. Path result would be a point, not a line")
                        #return
                
                composedPath = inkex.Path()
                for newSubpath in newSubpaths:
                    composedPath.extend(newSubpath)
                    
                if self.options.debug is True:
                    inkex.utils.debug("Composed path = " + str(composedPath))
            
                element.path = composedPath
    
    def visualizeFirstTwo(self, element):
        """Add a dot label for this path element"""
        group = element.getparent().add(inkex.Group(id="visualize-group-" + element.get('id')))
        dot_group = group.add(inkex.Group(id="dot-group-" + element.get('id')))
        num_group = group.add(inkex.Group(id="num-group-" + element.get('id')))
        group.transform = element.transform
        radius = self.svg.unittouu(self.options.dotsize) / 2
        
        count = 0
        for step, (x, y) in enumerate(element.path.end_points):
            count += 1
            circle = Circle(cx=str(x), cy=str(y), r=str(radius), id="circle-" + element.get('id') + "-" + str(count))
            circle.style = inkex.Style({'stroke': 'none', 'fill': '#000'})

            text = TextElement(x=str(x + radius), y=str(y - radius), id="text-" + element.get('id') + "-" + str(count))
            text.text = str(count) #we start with #1
            text.style = inkex.Style({'font-size': self.svg.unittouu(self.options.fontsize), 'fill-opacity': '1.0', 'stroke': 'none', 
                      'font-weight': 'normal', 'font-style': 'normal', 'fill': '#999'})
            
            dot_group.append(circle)
            num_group.append(text)
            
            if count > 1: #we only display first two points to see the position of the first node and the path direction
                break
      
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--closed_only", type=inkex.Boolean, default=False, help="If disabled we also apply on open (sub)path. Warning: This REMOVES segments!")
        pars.add_argument("--movenode", type=int, default=0, help="Move starting node n nodes further")
        pars.add_argument('--visualize_result', type=inkex.Boolean, default=False, help="If enabled each node gets a number and a dot")
        pars.add_argument("--dotsize", default="10px", help="Size of the dots on the path nodes")
        pars.add_argument("--fontsize", default="20px", help="Size of node labels")
        pars.add_argument("--debug", type=inkex.Boolean, default=False, help="Debug Output")

    def effect(self):
        if len(self.svg.selected) > 0:
            elements = self.svg.selection.filter(PathElement).values()
            if len(elements) > 0:
                for element in elements:
                    #move starting element / change direction
                    self.modify(element)
             
                    #finally apply dots to visualize the result
                    if self.options.visualize_result is True:
                        self.visualizeFirstTwo(element)
            else:
                inkex.errormsg('Selection seems not to contain path elements. Maybe you have selected a group instead?')
                return      
        else:
            inkex.errormsg('Please select some objects first.')
            return
        
if __name__ == '__main__':
    MovePathNode().run()
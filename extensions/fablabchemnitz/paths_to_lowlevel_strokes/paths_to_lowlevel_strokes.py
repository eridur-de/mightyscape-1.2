#!/usr/bin/env python3


from lxml import etree
import inkex
from inkex import bezier, PathElement
from inkex.paths import CubicSuperPath, Path
import copy

class PathsToStrokes(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--flattenbezier", type=inkex.Boolean, default=False, help="Flatten bezier curves to polylines")
        pars.add_argument("--flatness", type=float, default=0.1, help="Minimum flatness = 0.1. The smaller the value the more fine segments you will get (quantization).")
        pars.add_argument("--decimals", type=int, default=3)
        pars.add_argument("--keep_style", type=inkex.Boolean, default=False)

    def effect(self):
        
        def flatten(node):
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

        def break_contours(element, breakelements = None):
            if breakelements == None:
                breakelements = []
            if element.tag == inkex.addNS('path','svg'):
                if self.options.flattenbezier is True:
                    flatten(element)
                parent = element.getparent()
                idx = parent.index(element)
                idSuffix = 0
                raw = element.path.to_arrays() 
                subPaths = []
                prev = 0
                for i in range(len(raw)): # Breaks compound paths into simple paths
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
                break_contours(child, breakelements)
            return breakelements

        if len(self.svg.selected) == 0:
            elementsToWork = break_contours(self.document.getroot())
        else:
            elementsToWork = None
            for element in self.svg.selected.values():
                elementsToWork = break_contours(element, elementsToWork)

        for element in elementsToWork:
            oldId = element.get('id')
            oldStyle = element.style
            path = element.path.to_absolute().to_arrays() #to_arrays() is deprecated. How to make more modern?
            pathIsClosed = False
            if path[-1][0] == 'Z' or \
                (path[-1][0] == 'L' and path[0][1] == path[-1][1]) or \
                (path[-1][0] == 'C' and path[0][1] == [path[-1][1][-2], path[-1][1][-1]]) \
                :  #if first is last point the path is also closed. The "Z" command is not required
                pathIsClosed = True
            parent = element.getparent()
            idx = parent.index(element)
            element.delete()
        
            if len(path) == 2 and pathIsClosed is False:
                ll = inkex.Line(id=oldId)
                ll.set('x1', '{:0.{dec}f}'.format(path[0][1][0], dec=self.options.decimals))
                ll.set('y1', '{:0.{dec}f}'.format(path[0][1][1], dec=self.options.decimals))
                ll.set('x2', '{:0.{dec}f}'.format(path[1][1][0], dec=self.options.decimals))
                ll.set('y2', '{:0.{dec}f}'.format(path[1][1][1], dec=self.options.decimals))
         
            if len(path) > 2 and pathIsClosed is False:
                ll = inkex.Polyline(id=oldId)
                points = ""
                for i in range(0, len(path)):
                    points += '{:0.{dec}f},{:0.{dec}f} '.format(path[i][1][0], path[i][1][1], dec=self.options.decimals)  
                ll.set('points', points)
            
            if len(path) > 2 and pathIsClosed is True:
                ll = inkex.Polygon(id=oldId)
                points = ""
                for i in range(0, len(path) - 1):
                    points += '{:0.{dec}f},{:0.{dec}f} '.format(path[i][1][0], path[i][1][1], dec=self.options.decimals) 
                ll.set('points', points)
            if self.options.keep_style is True:    
                ll.style = oldStyle
            else:
                ll.style = "fill:none;stroke:#0000FF;stroke-width:" + str(self.svg.unittouu("1px"))
            parent.insert(idx, ll)
    
if __name__ == '__main__':
    PathsToStrokes().run()
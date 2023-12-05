#!/usr/bin/env python3

'''
Inkscape extension to subdivide the selected bezier paths based on max length value or count

Copyright (C) 2018  Shrinivas Kulkarni

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
from inkex import bezier
from inkex.paths import CubicSuperPath
import copy
from math import ceil

DEF_ERR_MARGIN = 0.0001

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
        
def floatCmpWithMargin(float1, float2, margin = DEF_ERR_MARGIN):
    return abs(float1 - float2) < margin 
        

class SplitBezier(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument('--maxLength', type = float, default = '10', help = 'Maximum Length of New Segments')
        pars.add_argument('--unit', default = 'mm', help = 'Unit of Measurement')
        pars.add_argument('--precision', type = int, default = '5', help = 'Number of significant digits')
        pars.add_argument("--tab", default="sampling", help="Tab") 
        pars.add_argument("--separateSegs", type=inkex.Boolean, default=True)

    def effect(self):
        
        maxL = None
        separateSegs = self.options.separateSegs
        
        if(self.options.unit != 'perc' and self.options.unit != 'count'):
            maxL = self.options.maxLength * self.svg.unittouu('1'+self.options.unit)
            
        # ~ inkex.errormsg(str(maxL))
        tolerance = 10 ** (-1 * self.options.precision)
        
        selections = self.svg.selected        
        pathNodes = self.document.xpath('//svg:path',namespaces=inkex.NSS)

        paths = [(pathNode.get('id'), CubicSuperPath(pathNode.get('d'))) for pathNode in  pathNodes]

        if(len(paths) > 0):
            for key, cspath in paths:
                parts = getPartsFromCubicSuper(cspath)
                partsSplit = False             
                try:  
                    for i, part in enumerate(parts):
                        
                        newSegs = []
                        for j, seg in enumerate(part):                               
                            segL = bezier.bezierlength((seg[0], seg[1], seg[2], seg[3]), tolerance = tolerance)
				    		
                            if(maxL != None):
                                divL = maxL
                            elif(self.options.unit == 'perc'):
                                divL = segL * self.options.maxLength / 100 
                            else:
                                divL = segL / ceil(self.options.maxLength)
                                
                            if(segL > divL):
                                
                                coveredL = 0
                                s = seg
                                s1 = None
                                s2 = DEF_ERR_MARGIN #Just in case
                                
                                while(not floatCmpWithMargin(segL, coveredL)):
                                    if(s == seg):
                                        sL = segL
                                    else:
                                        sL = bezier.bezierlength((s[0], s[1],  s[2], s[3]), tolerance = tolerance)
                                        
                                    if(floatCmpWithMargin(segL, coveredL + divL)):
                                        s2 = s
                                        break                                    
                                    else:
                                        if(segL > (coveredL + divL)):                                                        
                                            t1L = divL 
                                        else:
                                            t1L = segL - coveredL
                                            
                                        t1 = bezier.beziertatlength((s[0], s[1], s[2], s[3]),  l = t1L / sL , tolerance = tolerance)                
                                        s1, s2 = bezier.beziersplitatt((s[0], s[1], s[2], s[3]), t1)
                                        coveredL += t1L                            
                                        newSegs.append(s1)
                                        s = s2
                                newSegs.append(s2)
                            else:
                                newSegs.append(seg)
                                
                        if(len(newSegs) > len(part)):
                            parts[i] = newSegs
                            partsSplit = True
                    
                    if(partsSplit or separateSegs):
                        elem = selections[key]
                        if(separateSegs):
                            parent = elem.getparent()
                            idx = parent.index(elem)
                            parent.remove(elem)
                            allSegs = [seg for part in parts for seg in part]
                            idSuffix = 0
                            for seg in allSegs:
                                cspath = getCubicSuperFromParts([[seg]])
                                newElem = copy.copy(elem)
                                oldId = newElem.get('id')
                                newElem.set('d', CubicSuperPath(cspath))
                                newElem.set('id', oldId + str(idSuffix).zfill(5))
                                parent.insert(idx, newElem)
                                idSuffix += 1
                        else:
                            cspath = getCubicSuperFromParts(parts)
                            elem.set('d', CubicSuperPath(cspath))
                except:
                    pass
                           
if __name__ == '__main__':
    SplitBezier().run()
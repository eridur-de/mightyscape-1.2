#!/usr/bin/env python3

"""
Extension for InkScape 1.0

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 01.06.2021
Last patch: 02.06.2021
License: GNU GPL v3

Splits a path at value t=0..1 (t=0.5 means 50%) or at a defined length with unit.
Applies independently for each sub path in selection. Use 'Path > Reverse' to change the cutting direction.

"""

import copy
import inkex
from inkex import bezier, CubicSuperPath, PathElement, Path
from inkex.bezier import csplength

class SplitAndBreakBezierAtT(inkex.EffectExtension):

    def breakContours(self, element, breakelements = None):
        ''' this does the same as "CTRL + SHIFT + K" '''
        if breakelements == None:
            breakelements = []
        if element.tag == inkex.addNS('path','svg'):
            parent = element.getparent()
            idx = parent.index(element)
            idSuffix = 0    
            raw = element.path.to_arrays()
            subPaths, prev = [], 0
            for i in range(len(raw)): #breaks compound paths into sub paths
                if raw[i][0] == 'M' and i != 0:
                    subPaths.append(raw[prev:i])
                    prev = i
            subPaths.append(raw[prev:])
            for subpath in subPaths:
                replacedelement = copy.copy(element)
                oldId = replacedelement.get('id')
                csp = CubicSuperPath(subpath)
                if len(subpath) > 1 and csp[0][0] != csp[0][1]: #avoids pointy paths like M "31.4794 57.6024 Z"
                    replacedelement.set('d', csp)
                    replacedelement.set('id', oldId + str(idSuffix))
                    parent.insert(idx, replacedelement)
                    idSuffix += 1
                    breakelements.append(replacedelement)
            parent.remove(element)
        for child in element.getchildren():
            self.breakContours(child, breakelements)
        return breakelements

    def add_arguments(self, pars):
        pars.add_argument('--tab')
        pars.add_argument('--split_select', default="t")
        pars.add_argument('--unit', default="mm")
        pars.add_argument('--target_length', type=float, default=0.5)
        pars.add_argument('--target_t', type=float, default=0.5)
        pars.add_argument('--keep_start', type=inkex.Boolean, default=True)
        pars.add_argument('--keep_end', type=inkex.Boolean, default=True)
        pars.add_argument('--keep_seg', type=inkex.Boolean, default=False)

    def effect(self):    
        #if self.options.split_select == "t" and self.options.target_t == 0.0:
        #    inkex.utils.debug("You have seleted 'percentage (t)' but your t parameter is 0.0. It would simply result in element deletion!")
        #    return
        #if self.options.split_select == "t" and self.options.target_t == 1.0:
        #    inkex.utils.debug("You have seleted 'percentage (t)' but your t parameter is 1.0. It would'nt exist any trim result!")
        #    return
               
        breakApartElements = None
        for element in self.svg.selection.filter(PathElement):
            breakApartElements = self.breakContours(element, breakApartElements)

        if breakApartElements is not None:
            for element in breakApartElements:
                csp = element.path.to_superpath()
                slengths, totalLength = csplength(csp)
                if totalLength == 0:
                    inkex.utils.debug("{} is invalid: zero length (path d='{}'). Skipping ...".format(element.get('id'), element.path))
                    continue
                if self.options.split_select == "t":
                    length_at_target_t = self.options.target_t * totalLength
                elif self.options.split_select == "length":
                    length_at_target_t = self.svg.unittouu(str(self.options.target_length) + self.options.unit)
                    if length_at_target_t > totalLength:
                        inkex.utils.debug("Entered length is larger than length of {}. Skipping ...".format(element.get('id')))
                        continue
                    self.options.target_t = length_at_target_t / totalLength #override

                new = []
                keep = [] #some copy for the segment where the split applies
                lengthSum = 0
                segOfTOccurence = None
                for seg in csp:  
                    new.append([seg[0][:]])      
                    for i in range(1,len(seg)):
                        aSeg = seg[i][0]
                        segLength = bezier.cspseglength(new[-1][-1], seg[i])
                        lengthSum += segLength
                        current_t = lengthSum / totalLength
                        #insert a new breaking node in case we are at the desired t parameter
                        if current_t >= self.options.target_t:
                            if segOfTOccurence is None:
                                segOfTOccurence = i
                                t_dist = 1 - ((lengthSum - length_at_target_t) / segLength)
                                result = bezier.cspbezsplitatlength(new[-1][-1], seg[i], t_dist)
                                better_result = [[list(el) for el in elements] for elements in result]
                                new[-1][-1], nxt, seg[i] = better_result
                                new[-1].append(nxt[:])
                                if self.options.keep_start is True and self.options.keep_end is False:
                                    if segOfTOccurence == 1:
                                        keep.append([seg[i-1][0], seg[i-1][0], seg[i-1][0]])
                                    else:
                                        keep.append([seg[i-1][1], seg[i-1][1], seg[i-1][1]])
                                    keep.append([better_result[0][2], nxt[0], nxt[1]])
                                elif self.options.keep_start is False and self.options.keep_end is True:
                                    keep.append([better_result[0][2], nxt[0], nxt[1]])
                                    keep.append([better_result[1][2], better_result[2][0], seg[i][1]])                               
                                elif self.options.keep_start is True and self.options.keep_end is True:
                                    if segOfTOccurence == 1:
                                        keep.append([seg[i-1][0], seg[i-1][0], seg[i-1][0]])
                                    else:
                                        keep.append([seg[i-1][1], seg[i-1][1], seg[i-1][1]])
                                    keep.append([seg[i-1][2], aSeg, seg[i][1]])

                        new[-1].append(seg[i])
                
                if self.options.keep_seg is False:     
                    newpath = CubicSuperPath(new).to_path(curves_only=True).to_arrays()
                    #insert the splitting at the occurence (we add "m 0,0") to break the path
                    newpath.insert(segOfTOccurence + 1, ['m', [0, 0]])
                    element.path = Path(newpath)
                    breakAparts = self.breakContours(element)
                  
                    if len(breakAparts) > 0:
                        pathStart = breakAparts[0]
                    if len(breakAparts) > 1:    
                        pathEnd = breakAparts[1]
                    if self.options.keep_start is False and len(breakAparts) > 0:
                        pathStart.delete()
                    if self.options.keep_end is False and len(breakAparts) > 1:
                        pathEnd.delete()
    
                else:
                    element.path = CubicSuperPath(keep)
                    
                    #print the breaking point coordinate
                    #for step, (x, y) in enumerate(breakAparts[1].path.end_points):
                    #    self.msg("x={},y={}".format(x, y))
                    #    break
        else:
            inkex.utils.debug("Selection seems to be empty!")
            return
if __name__ == '__main__':
    SplitAndBreakBezierAtT().run()
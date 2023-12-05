#!/usr/bin/env python3

'''
Inkscape extension to copy length of the source path to the selected 
destination path(s)

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

from inkex import bezier, Path, CubicSuperPath, PathElement

class ScaleToPathLength(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument('--scale', type = float, default = '1', help = 'Additionally scale the length by')
        pars.add_argument('--scaleFrom', default = 'center', help = 'Scale Path From')
        pars.add_argument('--precision', type = int, default = '5', help = 'Number of significant digits')
        pars.add_argument("--override_selection", type = inkex.Boolean, default = False, help = "Use a custom length instead using the length of the first object in selection") 
        pars.add_argument("--custom_length", type = float, default = 100.000, help = "Custom length") 
        pars.add_argument("--unit", default = "mm", help = "Units")
        
    def scaleCubicSuper(self, cspath, scaleFactor, scaleFrom):
        bbox = Path(cspath).bounding_box()

        if(scaleFrom == 'topLeft'):
            oldOrigin= [bbox.left, bbox.bottom]
        elif(scaleFrom == 'topRight'):
            oldOrigin= [bbox.right, bbox.bottom]
        elif(scaleFrom == 'bottomLeft'):
            oldOrigin= [bbox.left, bbox.top]
        elif(scaleFrom == 'bottomRight'):
            oldOrigin= [bbox.right, bbox.top]
        else: #if(scaleFrom == 'center'):
            oldOrigin= [bbox.left + (bbox.right - bbox.left) / 2., bbox.bottom + (bbox.top - bbox.bottom) / 2.]
            
        newOrigin = [oldOrigin[0] * scaleFactor , oldOrigin[1] * scaleFactor ]
            
        for subpath in cspath:
            for bezierPt in subpath:
                for i in range(0, len(bezierPt)):
                    
                    bezierPt[i] = [bezierPt[i][0] * scaleFactor, 
                        bezierPt[i][1] * scaleFactor]
                        
                    bezierPt[i][0] += (oldOrigin[0] - newOrigin[0])
                    bezierPt[i][1] += (oldOrigin[1] - newOrigin[1])
                
    def getPartsFromCubicSuper(self, cspath):
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
        
    def getLength(self, cspath, tolerance):
        parts = self.getPartsFromCubicSuper(cspath)
        curveLen = 0
        for i, part in enumerate(parts):
            for j, seg in enumerate(part):
                curveLen += bezier.bezierlength((seg[0], seg[1], seg[2], seg[3]), tolerance = tolerance)
        return curveLen

    def effect(self):
        scale = self.options.scale
        scaleFrom = self.options.scaleFrom
        tolerance = 10 ** (-1 * self.options.precision)
        selections = self.svg.selected
        pathNodes = self.svg.selection.filter(PathElement).values()

        paths = [(pathNode.get('id'), CubicSuperPath(pathNode.get('d'))) for pathNode in pathNodes]

        if self.options.override_selection is False:
            if(len(paths) > 1):
                srcPath = paths[-1][1]
                srclen = self.getLength(srcPath, tolerance)
                paths = paths[:len(paths)-1]
                for key, cspath in paths:
                    curveLen = self.getLength(cspath, tolerance)
                    
                    self.scaleCubicSuper(cspath, scaleFactor = scale * (srclen / curveLen), scaleFrom = scaleFrom)
                    try: #we wrap this in try-except because if the elements are within groups it will cause errors
                        selections[key].set('d', CubicSuperPath(cspath))
                    except:
                        pass
            else:
                inkex.errormsg("Please select at least two paths, with the path whose length is to be copied at the top. You may have to convert the shape to path with path->Object to Path.")
        else:
            if(len(paths) > 0):
                srclen = self.svg.unittouu(str(self.options.custom_length) + self.options.unit) 
                for key, cspath in paths:
                    curveLen = self.getLength(cspath, tolerance)
                    
                    self.scaleCubicSuper(cspath, scaleFactor = scale * (srclen / curveLen), scaleFrom = scaleFrom)
                    try: #we wrap this in try-except because if the elements are within groups it will cause errors
                        selections[key].set('d', CubicSuperPath(cspath))
                    except:
                        pass
            else:
                inkex.errormsg("Please select at least one path. You may have to convert the shape to path with path->Object to Path.")
if __name__ == '__main__':
    ScaleToPathLength().run()

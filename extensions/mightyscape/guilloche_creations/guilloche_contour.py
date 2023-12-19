#! /usr/bin/env python3
'''
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

Quick description:

'''
# standard library
from math import *
from copy import deepcopy
# local library
import inkex
import pathmodifier
import cubicsuperpath
from inkex import paths
from lxml import etree

def getColorAndOpacity(longColor):
    '''
    Convert the long into a #rrggbb color value
    Conversion back is A + B*256^1 + G*256^2 + R*256^3
    '''
    longColor = int(longColor)
        
    if longColor < 0:
        longColor = longColor & 0xFFFFFFFF
    
    hexColor = hex(longColor)
    lhc = len(hexColor)
       
    hexOpacity = hexColor[lhc-2 : ]    
    hexColor = '#' + hexColor[2:-2].rjust(6, '0')
    
    return (hexColor, hexOpacity)
    
def setColorAndOpacity(style, color, opacity):
    declarations = style.split(';')
    strokeOpacityInStyle = False
    newOpacity = round((int(opacity, 16) / 255.0), 8)
    
    for i,decl in enumerate(declarations):
        parts = decl.split(':', 2)
        
        if len(parts) == 2:
            (prop, val) = parts
            prop = prop.strip().lower()
            
            if (prop == 'stroke' and val != color):
                declarations[i] = prop + ':' + color
            
            if prop == 'stroke-opacity':
                if val != newOpacity:
                    declarations[i] = prop + ':' + str(newOpacity)
                
                strokeOpacityInStyle = True
        
    if not strokeOpacityInStyle:
        declarations.append('stroke-opacity' + ':' + str(newOpacity))
    
    return ";".join(declarations)

def getSkeletonPath(d, offs):
    '''
    Recieves a current skeleton path and offset specified by the user if it's line.
    Calculates new skeleton path to use for creating contour with given offset.
    '''
        
    if offs != 0:
        comps = d.split()
        
        if ((comps[2] == 'h' or comps[2] == 'H') and len(comps) == 4):
            startPt = comps[1].split(',')
            startX = float(startPt[0])
            startY = float(startPt[1])
            
            finalX = float(comps[3]) if comps[2] == 'H' else startX + float(comps[3])
            
            if startX < finalX:
                startY -= offs
            else:
                startY += offs
            
            comps[1] = startPt[0] + ',' + str(startY)
        elif ((comps[2] == 'v' or comps[2] == 'V') and len(comps) == 4):
            startPt = comps[1].split(',')
            startX = float(startPt[0])
            startY = float(startPt[1])
            
            finalY = float(comps[3]) if comps[2] == 'V' else startY + float(comps[3])
            
            if startY < finalY:
                startX += offs
            else:
                startX -= offs
            
            comps[1] = str(startX) + ',' + startPt[1]
        elif (comps[0] == 'M' and len(comps) == 3):
            startPt = comps[1].split(',')
            startX = float(startPt[0])
            startY = float(startPt[1])
            
            finalPt = comps[2].split(',')
            finalX = float(finalPt[0])
            finalY = float(finalPt[1])
            
            if startX < finalX:
                if (startY > finalY):
                    startX -= offs
                    finalX -= offs
                else:
                    startX += offs
                    finalX += offs
                startY -= offs
                finalY -= offs
            else:
                if startY > finalY:
                    startX -= offs
                    finalX -= offs
                else:
                    startX += offs
                    finalX += offs
                startY += offs
                finalY += offs
            
            comps[1] = str(startX) + ',' + str(startY)
            comps[2] = str(finalX) + ',' + str(finalY)
        elif (comps[0] == 'm' and len(comps) == 3):
            startPt = comps[1].split(',')
            startX = float(startPt[0])
            startY = float(startPt[1])
            
            finalPt = comps[2].split(',')
            dx = float(finalPt[0])
            dy = float(finalPt[1])
            finalX = startX + dx
            finalY = startY + dy
            
            if startX < finalX:
                if startY > finalY:
                    startX -= offs
                else:
                    startX += offs
                startY -= offs
            else:
                if startY > finalY:
                    startX -= offs
                else:
                    startX += offs
                startY += offs
            
            comps[1] = str(startX) + ',' + str(startY)
            comps[2] = str(dx) + ',' + str(dy)
        
        return paths.CubicSuperPath(paths.Path(' '.join(comps)))
       
    return paths.CubicSuperPath(paths.Path(d))
    
def modifySkeletonPath(skelPath):
    
    resPath = []
    l = len(skelPath)
    resPath += skelPath[0]
        
    if l > 1:
        for i in range(1, l):
                        
            if skelPath[i][0][1] == resPath[-1][1]:
                skelPath[i][0][0] = resPath[-1][0]
                del resPath[-1]
                
            resPath += skelPath[i]
    
    return resPath

def linearize(p, tolerance=0.001):
    '''
    This function receives a component of a 'cubicsuperpath' and returns two things:
    The path subdivided in many straight segments, and an array containing the length of each segment.
    '''
    zero = 0.000001
    i = 0
    d = 0
    lengths=[]
    
    while i < len(p) - 1:
        box = inkex.bezier.pointdistance(p[i][1], p[i][2])
        box += inkex.bezier.pointdistance(p[i][2], p[i+1][0])
        box += inkex.bezier.pointdistance(p[i+1][0], p[i+1][1])
        chord = inkex.bezier.pointdistance(p[i][1], p[i+1][1])
        
        if (box - chord) > tolerance:
            b1, b2 =  inkex.bezier.beziersplitatt([p[i][1], p[i][2], p[i + 1][0], p[i + 1][1]], 0.5)
            p[i][2][0], p[i][2][1] = b1[1]
            p[i + 1][0][0], p[i + 1][0][1] = b2[2]
            p.insert(i + 1, [[b1[2][0], b1[2][1]], [b1[3][0], b1[3][1]], [b2[1][0], b2[1][1]]])
        else:
            d = (box + chord) / 2
            lengths.append(d)
            i += 1

    new = [p[i][1] for i in range(0, len(p) - 1) if lengths[i] > zero]
    new.append(p[-1][1])
    lengths = [l for l in lengths if l > zero]
    
    return (new, lengths)

def isSkeletonClosed(sklCmp):

    requiredPrecision = 0.005
 
    sctest1 = abs(sklCmp[0][0] - sklCmp[-1][0]) > requiredPrecision
    sctest2 = abs(sklCmp[0][1] - sklCmp[-1][1]) > requiredPrecision
            
    if sctest1 or sctest2:
        return False
     
    return True

def getPolygonCentroid(polygon):
    x = 0
    y = 0
    n = len(polygon)
    
    for vert in polygon:
        x += vert[0]
        y += vert[1]
    
    x = x / n
    y = y / n
    
    return [x, y]

def getPoint(p1, p2, x, y):
    x1 = p1[0]
    y1 = p1[1]
    x2 = p2[0]
    y2 = p2[1]
    
    a = (y1 - y2) / (x1 - x2)
    b = y1 - a * x1
    
    if x == None:
        x = (y - b) / a
    else:
        y = a * x + b
    
    return [x, y]

def getPtOnSeg(p1, p2, segLen, l):
    if p1[0] == p2[0]:
        return [p2[0], p2[1] - l] if p2[1] < p1[1] else [p2[0], p2[1] + l]
    
    if p1[1] == p2[1]:
        return [p2[0] - l, p2[1]] if p2[0] < p1[0] else [p2[0] + l, p2[1]]
    
    dy = abs(p1[1] - p2[1])    
    angle = asin(dy / segLen)
    dx = l * cos(angle)
    x = p1[0] - dx if p1[0] > p2[0] else p1[0] + dx
    
    return getPoint(p1, p2, x, None)

def drawfunction(nodes, width, fx):
    # x-bounds of the plane
    xstart = 0.0
    xend = 2 * pi
    # y-bounds of the plane
    ybottom = -1.0
    ytop = 1.0
    # size and location of the plane on the canvas
    height = 2
    left = 15
    bottom = 15 + height
    
    # function specified by the user
    try:
        if fx != "":
            f = eval('lambda x: ' + fx.strip('"'))
    except SyntaxError:
        return []
    
    scalex = width / (xend - xstart)
    xoff = left
    # conver x-value to coordinate
    coordx = lambda x: (x - xstart) * scalex + xoff
    
    scaley = height / (ytop - ybottom)
    yoff = bottom
    # conver y-value to coordinate
    coordy = lambda y: (ybottom - y) * scaley + yoff
    
    # step is the distance between nodes on x
    step = (xend - xstart) / (nodes - 1)
    third = step / 3.0
    # step used in calculating derivatives
    ds = step * 0.001
    
    # initialize function and derivative for 0;
    # they are carried over from one iteration to the next, to avoid extra function calculations. 
    x0 = xstart
    y0 = f(xstart)
    
    # numerical derivative, using 0.001*step as the small differential
    x1 = xstart + ds # Second point AFTER first point (Good for first point)
    y1 = f(x1)
    
    dx0 = (x1 - x0) / ds
    dy0 = (y1 - y0) / ds
    
    # path array
    a = []
    
    # Start curve
    #a.append(['M ', [coordx(x0), coordy(y0)]])
    a.append(['M', [coordx(x0), coordy(y0)]])

    for i in range(int(nodes - 1)):
        x1 = (i + 1) * step + xstart
        x2 = x1 - ds # Second point BEFORE first point (Good for last point)
        y1 = f(x1)
        y2 = f(x2)
        
        # numerical derivative
        dx1 = (x1 - x2) / ds
        dy1 = (y1 - y2) / ds
        
        # create curve
        a.append(['C', [coordx(x0 + (dx0 * third)), coordy(y0 + (dy0 * third)), 
                          coordx(x1 - (dx1 * third)), coordy(y1 - (dy1 * third)),
                          coordx(x1),                 coordy(y1)]])
                          
        # Next segment's start is this segment's end
        x0 = x1
        y0 = y1
        # Assume the function is smooth everywhere, so carry over the derivative too
        dx0 = dx1
        dy0 = dy1
            
    return a

def offset(pathComp, dx, dy):
    for ctl in pathComp:
        for pt in ctl:
            pt[0] += dx
            pt[1] += dy

def stretch(pathComp, xscale, yscale, org):
    for ctl in pathComp:
        for pt in ctl:
            pt[0] = org[0] + (pt[0] - org[0]) * xscale
            pt[1] = org[1] + (pt[1] - org[1]) * yscale

class GuillocheContour(pathmodifier.PathModifier):
    def add_arguments(self, pars):      
        pars.add_argument("--contourFunction", default="sin", help="Function defining the contour")
        pars.add_argument("--tab")
        pars.add_argument("--frequency", type=int, default=10, help="Frequency of the function")
        pars.add_argument("--amplitude", type=int, default=1, help="Amplitude of the function")
        pars.add_argument("--phaseOffset", type=int, default=0, help="Phase offset of the function")
        pars.add_argument("--offset", type=int, default=0, help="Offset of the function")
        pars.add_argument("--nodes", type=int, default=20, help="Count of nodes")
        pars.add_argument("--remove", type=inkex.Boolean, default=False, help="If Ttrue, control object will be removed")
        pars.add_argument("--strokeColor", type=inkex.Color)
        pars.add_argument("--amplitude1", type=float, default=0.0, help="Amplitude of first harmonic")
        pars.add_argument("--phase1", type=int, default=0, help="Phase offset of first harmonic")
        pars.add_argument("--amplitude2", type=float, default=0.0, help="Amplitude of second harmonic")
        pars.add_argument("--phase2", type=int, default=0, help="Phase offset of second harmonic")
        pars.add_argument("--amplitude3", type=float, default=0.0, help="Amplitude of third harmonic")
        pars.add_argument("--phase3", type=int, default=0, help="Phase offset of third harmonic")
        pars.add_argument("--amplitude4", type=float, default=0.0, help="Amplitude of fourth harmonic")
        pars.add_argument("--phase4", type=int, default=0, help="Phase offset of fourth harmonic")
        pars.add_argument("--amplitude5", type=float, default=0.0, help="Amplitude of fifth harmonic")
        pars.add_argument("--phase5", type=int, default=0, help="Phase offset of fifth harmonic")


    def prepareSelectionList(self):            
        self.skeletons = self.svg.selected
        pathmodifier.PathModifier.expand_clones(self, self.skeletons, True, False)
        pathmodifier.PathModifier.objects_to_paths(self, self.skeletons, True)
    
    def linearizePath(self, skelPath, offs):
        comps, lengths = linearize(skelPath)
        
        self.skelCompIsClosed = isSkeletonClosed(comps)
        
        if (self.skelCompIsClosed and offs != 0):
            centroid = getPolygonCentroid(comps)
            
            for i in range(len(comps)):
                pt1 = comps[i]
                dist = inkex.bezier.pointdistance(centroid, pt1)
                
                comps[i] = getPtOnSeg(centroid, pt1, dist, dist + offs)
                
                if i > 0:
                    lengths[i - 1] = inkex.bezier.pointdistance(comps[i - 1], comps[i])
        
        return (comps, lengths)
    
    def getFunction(self, func):
        res = ''
        
        presetAmp1 = presetAmp2 = presetAmp3 = presetAmp4 = presetAmp5 = 0.0
        presetPhOf1 = presetPhOf2 = presetPhOf3 = presetPhOf4 = presetPhOf5 = presetOffs = 0
        
        if (func == 'sin' or func == 'cos'):
            return '(' + str(self.options.amplitude) + ') * ' + func + '(x + (' + str(self.options.phaseOffset / 100.0 * 2 * pi) + '))'
        
        if func == 'env1':
            presetAmp1 = presetAmp3 = 0.495
        elif func == 'env2':
            presetAmp1 = presetAmp3 = 0.65
            presetPhOf1 = presetPhOf3 = 25
        elif func == 'env3':
            presetAmp1 = 0.75
            presetPhOf1 = 25
            presetAmp3 = 0.24
            presetPhOf3 = -25
        elif func == 'env4':
            presetAmp1 = 1.105
            presetAmp3 = 0.27625
            presetPhOf3 = 50
        elif func == 'env5':
            presetAmp1 = 0.37464375
            presetPhOf1 = 25
            presetAmp2 = 0.5655
            presetAmp3 = 0.37464375
            presetPhOf3 = -25
        elif func == 'env6':
            presetAmp1 = 0.413725
            presetPhOf1 = 25
            presetAmp2 = 0.45695
            presetPhOf2 = 50
            presetAmp3 = 0.494
            presetPhOf3 = -25
        elif func == 'env7':
            presetAmp1 = 0.624
            presetPhOf1 = 25
            presetAmp2 = 0.312
            presetAmp3 = 0.624
            presetPhOf3 = 25
        elif func == 'env8':
            presetAmp1 = 0.65
            presetPhOf1 = 50
            presetAmp2 = 0.585
            presetAmp3 = 0.13
        elif func == 'env9':
            presetAmp1 = 0.07605
            presetPhOf1 = 25
            presetAmp2 = 0.33345
            presetPhOf2 = 50
            presetAmp3 = 0.468
            presetPhOf3 = -25
            presetAmp4 = 0.32175
        elif func == 'env10':
            presetAmp1 = 0.3575
            presetPhOf1 = -25
            presetAmp2 = 0.3575
            presetAmp3 = 0.3575
            presetPhOf3 = 25
            presetAmp4 = 0.3575
            presetPhOf4 = 50
        elif func == 'env11':
            presetAmp1 = 0.65
            presetPhOf1 = 25
            presetAmp2 = 0.13
            presetPhOf2 = 50
            presetAmp3 = 0.26
            presetPhOf3 = 25
            presetAmp4 = 0.39
        elif func == 'env12':
            presetAmp1 = 0.5525
            presetPhOf1 = -25
            presetAmp2 = 0.0414375
            presetPhOf2 = 50
            presetAmp3 = 0.15884375
            presetPhOf3 = 25
            presetAmp4 = 0.0966875
            presetAmp5 = 0.28315625
            presetPhOf5 = -25
        
        harm1 = '(' + str(self.options.amplitude * (presetAmp1 + self.options.amplitude1)) + ') * cos(1 * (x + (' + str(self.options.phaseOffset / 100.0 * 2 * pi) + ')) - (' + str((presetPhOf1 + self.options.phase1) / 100.0 * 2 * pi) + '))'
        harm2 = '(' + str(self.options.amplitude * (presetAmp2 + self.options.amplitude2)) + ') * cos(2 * (x + (' + str(self.options.phaseOffset / 100.0 * 2 * pi) + ')) - (' + str((presetPhOf2 + self.options.phase2) / 100.0 * 2 * pi) + '))'
        harm3 = '(' + str(self.options.amplitude * (presetAmp3 + self.options.amplitude3)) + ') * cos(3 * (x + (' + str(self.options.phaseOffset / 100.0 * 2 * pi) + ')) - (' + str((presetPhOf3 + self.options.phase3) / 100.0 * 2 * pi) + '))'
        harm4 = '(' + str(self.options.amplitude * (presetAmp4 + self.options.amplitude4)) + ') * cos(4 * (x + (' + str(self.options.phaseOffset / 100.0 * 2 * pi) + ')) - (' + str((presetPhOf4 + self.options.phase4) / 100.0 * 2 * pi) + '))'
        harm5 = '(' + str(self.options.amplitude * (presetAmp5 + self.options.amplitude5)) + ') * cos(5 * (x + (' + str(self.options.phaseOffset / 100.0 * 2 * pi) + ')) - (' + str((presetPhOf5 + self.options.phase5) / 100.0 * 2 * pi) + '))'
        
        res = harm1 + ' + ' + harm2 + ' + ' + harm3 + ' + ' + harm4 + ' + ' + harm5
        
        return res

    def lengthToTime(self, l):
        '''
        Recieves an arc length l, and returns the index of the segment in self.skelComp 
        containing the corresponding point, together with the position of the point on this segment.

        If the deformer is closed, do computations modulo the total length.
        '''
        if self.skelCompIsClosed:
            l = l % sum(self.lengths)
        
        if l <= 0:
            return 0, l / self.lengths[0]
        
        i = 0
        
        while (i < len(self.lengths)) and (self.lengths[i] <= l):
            l -= self.lengths[i]
            i += 1
        
        t = l / self.lengths[min(i, len(self.lengths) - 1)]
        
        return (i, t)

    def applyDiffeo(self, bpt, vects=()):
        '''
        The kernel of this stuff:
        bpt is a base point and for v in vectors, v'=v-p is a tangent vector at bpt.
        '''
        s = bpt[0] - self.skelComp[0][0]
        i, t = self.lengthToTime(s)
        
        if i == len(self.skelComp) - 1:
            x, y = inkex.bezier.tpoint(self.skelComp[i - 1], self.skelComp[i], t + 1)
            dx = (self.skelComp[i][0] - self.skelComp[i - 1][0]) / self.lengths[-1]
            dy = (self.skelComp[i][1] - self.skelComp[i - 1][1]) / self.lengths[-1]
        else:
            x, y = inkex.bezier.tpoint(self.skelComp[i], self.skelComp[i + 1], t)
            dx = (self.skelComp[i + 1][0] - self.skelComp[i][0]) / self.lengths[i]
            dy = (self.skelComp[i + 1][1] - self.skelComp[i][1]) / self.lengths[i]

        vx = 0
        vy = bpt[1] - self.skelComp[0][1]
        bpt[0] = x + vx * dx - vy * dy
        bpt[1] = y + vx * dy + vy * dx

        for v in vects:
            vx = v[0] - self.skelComp[0][0] - s
            vy = v[1] - self.skelComp[0][1]
            v[0] = x + vx * dx - vy * dy
            v[1] = y + vx * dy + vy * dx

    def effect(self):
    
        if len(self.options.ids) < 1:
            inkex.errormsg(_("This extension requires one selected path."))
            return
        
        self.prepareSelectionList()
        
        for skeleton in self.skeletons.__iter__():
            resPath = []
            pattern = etree.Element(inkex.addNS('path','svg'))
                        
            self.options.strokeHexColor, self.strokeOpacity = getColorAndOpacity(self.options.strokeColor)
            
            # Copy style of skeleton with setting color and opacity
            s = skeleton.get('style')
            
            # Get any path transform for the contour output
            xfm = skeleton.get('transform')
            
            firstSkel = skeleton.get('d')
                        
            if s:
                pattern.set('style', setColorAndOpacity(s, self.options.strokeHexColor, self.strokeOpacity))
                
            if xfm:
                pattern.set('transform', xfm)
                        
            skeletonPath = modifySkeletonPath(getSkeletonPath(skeleton.get('d'), self.options.offset))
            
            self.skelComp, self.lengths = self.linearizePath(skeletonPath, self.options.offset)
            
            length = sum(self.lengths)
            patternWidth = length / self.options.frequency
            selectedFunction = self.getFunction(self.options.contourFunction)
                        
            pattern.set('d', str(paths.Path(drawfunction(self.options.nodes, patternWidth, selectedFunction))))
                            
            # Add path into SVG structure
            skeleton.getparent().append(pattern)
                        
            if self.options.remove:
                skeleton.getparent().remove(skeleton)
                        
            # Compute bounding box
            #pattPath = inkex.paths.Path(skeleton.get('d'))
                        
            patternCubicPath = paths.CubicSuperPath(paths.Path(pattern.get('d')))
            patternPath = inkex.paths.Path(patternCubicPath)
                        
            bbox = patternPath.bounding_box()
                        
            width = bbox.maximum[0] - bbox.minimum[0]
            dx = width
                        
            if dx < 0.01:
                exit(_("The total length of the pattern is too small."))
                        
            curPath = deepcopy(patternCubicPath)
            
            xoffset = self.skelComp[0][0] - bbox.minimum[0]
            yoffset = self.skelComp[0][1] - (bbox.bottom + bbox.top) / 2
            
            patternCopies = max(1, int(round(length / dx)))
            width = dx * patternCopies
                        
            newPath = []
            
            # Repeat pattern to cover whole skeleton
            for subPath in curPath:
                for i in range(0, patternCopies, 1):
                    newPath.append(deepcopy(subPath))
                    offset(subPath, dx, 0)
            
            curPath = newPath
                        
            # Offset pattern to the first node of the skeleton
            for subPath in curPath:
                offset(subPath, xoffset, yoffset)
            
            # Stretch pattern to whole skeleton
            for subPath in curPath:
                stretch(subPath, length / width, 1, self.skelComp[0])
            
            for subPath in curPath:
                for ctlpt in subPath:
                    self.applyDiffeo(ctlpt[1], (ctlpt[0], ctlpt[2]))
            
            # Check if there is a need to close path manually
            if self.skelCompIsClosed:
                firstPtX = round(curPath[0][0][1][0], 8)
                firstPtY = round(curPath[0][0][1][1], 8)
                finalPtX = round(curPath[-1][-1][1][0], 8)
                finalPtY = round(curPath[-1][-1][1][1], 8)
                
                if (firstPtX != finalPtX or firstPtY != finalPtY):
                    curPath[-1].append(curPath[0][0])
            
            resPath += curPath
            
            #  This final step takes the newly constructed contour from a multilevel list to
            #  a formal svg path
            step1rep = paths.CubicSuperPath(resPath).to_path().to_arrays()
            step2rep = str(paths.Path(step1rep))
            pattern.set('d', step2rep)
            
            
if __name__ == '__main__':
    GuillocheContour().run()
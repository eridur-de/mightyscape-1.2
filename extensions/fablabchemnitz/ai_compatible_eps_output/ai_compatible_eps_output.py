#!/usr/bin/env python3
"""
Mainly written by Andras Prim github_at_primandras.hu

Arc to bezier converting method is ported from:
http://code.google.com/p/core-framework/source/browse/trunk/plugins/svg.js
written by Angel Kostadinov, with MIT license
"""

try:
    from lxml import etree as ET
except Exception:
    import xml.etree.ElementTree as ET

import math
import re
import sys

def wrap(text, width):
    """ A word-wrap function that preserves existing line breaks """
    retstr = ""
    for word in text.split(' '):
        if len(retstr)-retstr.rfind('\n')-1 + len(word.split('\n',1)[0]) >= width:
            retstr += ' \n' + word
        else:
            retstr += ' ' + word
    return retstr

def css2dict(css):
    """returns a dictionary representing the given css string"""
    cssdict = {}
    if None == css:
        return cssdict
    for pair in css.split(';'): #TODO: what about escaped separators
        if pair.find(':') >= 0:
            key, value = pair.split(':')
            cssdict[ key.strip() ] = value.strip()
    return cssdict

def cssColor2Eps(cssColor, colors='RGB'):
    """converts css color definition (a hexa code with leading # or 'rgb()')
    to eps color definition"""
    if '#' == cssColor[0]:
        r = float(int(cssColor[1:3],16)) / 255
        g = float(int(cssColor[3:5],16)) / 255
        b = float(int(cssColor[5:7],16)) / 255
    else:
        # assume 'rgb()' color
        rgb = re.sub('[^0-9]+', ' ', cssColor).strip().split()
        r = float(int(rgb[0], 10)) / 255
        g = float(int(rgb[1], 10)) / 255
        b = float(int(rgb[2], 10)) / 255

    if colors == 'RGB':
        return "%f %f %f" % (r, g, b)
    elif colors == 'CMYKRGB':
        if (r == 0) and (g == 0) and (b == 0):
            c = 0
            m = 0
            y = 0
            k = 1
        else:
            c = 1 - r
            m = 1 - g
            y = 1 - b

            # extract out k [0,1]
            min_cmy = min(c, m, y)
            c = (c - min_cmy) / (1 - min_cmy)
            m = (m - min_cmy) / (1 - min_cmy)
            y = (y - min_cmy) / (1 - min_cmy)
            k = min_cmy

        return "%f %f %f %f %f %f %f" % (c, m, y, k, r, g, b)

class Point:
    """Class representing a 2D point"""
    def __init__(self, x, y, relativeTo = None):
        self.x = float(x)
        self.y = float(y)
        if isinstance(relativeTo, Point):
            self.x += relativeTo.x
            self.y += relativeTo.y

    def get_distance(self, otherPoint):
        """Returns the distance between this and the other point"""
        return math.hypot(self.x - otherPoint.x, self.y - otherPoint.y)

    def get_angle(self, otherPoint):
        """Returns the angle of the vector pointing from this to the other point"""
        deltax = otherPoint.x - self.x
        deltay = otherPoint.y - self.y
        return math.atan2(deltay, deltax) * 180 / math.pi

    def get_manhattan_distance(self, otherPoint):
        """Returns the manhattan distance of this and the other point"""
        return abs(self.x - otherPoint.x) + abs(self.y - otherPoint.y)

class TransformationMatrix:
    """Class representing a 2D transformation matrix"""
    def __init__(self, matrix = (1, 0, 0, 1, 0, 0)):
        self.matrix = matrix
    
    def multiply(self, matrix):
        return TransformationMatrix((
            self.matrix[0] * matrix[0] + self.matrix[2] * matrix[1], # + self.matrix[4] * 0
            self.matrix[1] * matrix[0] + self.matrix[3] * matrix[1], # + self.matrix[5] * 0
            self.matrix[0] * matrix[2] + self.matrix[2] * matrix[3], # + self.matrix[4] * 0
            self.matrix[1] * matrix[2] + self.matrix[3] * matrix[3], # + self.matrix[5] * 0
            self.matrix[0] * matrix[4] + self.matrix[2] * matrix[5] + self.matrix[4],
            self.matrix[1] * matrix[4] + self.matrix[3] * matrix[5] + self.matrix[5],
        ))

    def translate(self, tx, ty):
        return self.multiply((1, 0, 0, 1, tx, ty))

    def scale(self, sx, sy):
        return self.multiply((sx, 0, 0, sy, 0, 0))

    def rotate(self, alphaDegree, cx, cy):
        """Applies alpha degree rotation around cx, cy center point to the matrix"""
        alphaRadian = math.radians(alphaDegree)
        rotateMatrix = (
            math.cos(alphaRadian), math.sin(alphaRadian),
            -math.sin(alphaRadian), math.cos(alphaRadian),
            0, 0
        )
        if cx == 0 and cy == 0:
            return self.multiply(rotateMatrix)

        newMatrix = self.multiply((1, 0, 0, 1, cx, cy)) # compensate for center
        newMatrix = newMatrix.multiply(rotateMatrix)

        return newMatrix.multiply((1, 0, 0, 1, -cx, -cy)) # compensate back for center

class TransformationMatrixStack:
    """2D transformation matrix stack"""
    def __init__(self, matrix = None):
        self.matrices = [matrix if matrix != None else TransformationMatrix()]

    def push_matrix_multiply(self, matrix):
        """Matrix multiplies the current matrix with the passed one, and pushes it on the stack"""
        currentMatrix = self.matrices[-1]
        transformedMatrix = currentMatrix.multiply(matrix.matrix)
        self.matrices.append(transformedMatrix)

    def pop(self):
        """Removes last matrix from stack"""
        assert len(self.matrices) > 1, "Cannot pop last matrix from stack"
        self.matrices.pop()

    def transform_point(self, point):
        """Transforms the passed point using the current transformation matrix"""
        # todo: move to TransformationMatrix
        matrix = self.matrices[-1].matrix
        transformedX = matrix[0] * point.x + matrix[2] * point.y + matrix[4]
        transformedY = matrix[1] * point.x + matrix[3] * point.y + matrix[5]

        return Point(transformedX, transformedY)

    def transform_length(self, length):
        """Transforms the passed length using the current transformation matrix"""
        # todo: move to TransformationMatrix
        matrix = self.matrices[-1].matrix
        transformedX = matrix[0] * length
        transformedY = matrix[1] * length

        return math.sqrt(transformedX ** 2 + transformedY ** 2)

class svg2eps:
    def __init__(self, filename=None):
        self.filename = filename
        self.svg = None
        self.rePathDSplit = re.compile('[^a-zA-Z0-9.-]+')
        self.reTransformFind = re.compile('([a-z]+)\\(([^)]+)\\)')
        self.reNumberFind = re.compile('[0-9.eE+-]+')
        # must update reNumberUnitFind, if e is a valid character in a unit
        self.reNumberUnitFind = re.compile('([0-9.eE+-]+)([a-z]*)')
        # px to pt conversion rate varies based on inkscape versions, it is added during parsing
        self.toPt = {'in': 72.0, 'pt': 1.0, 'mm': 2.8346456695, 'cm': 28.346456695, 'm': 2834.6456695, 'pc': 12.0}

    def unitConv(self, string, toUnit):
        match = self.reNumberUnitFind.search(string)
        number = float(match.group(1))
        unit = match.group(2)
        if unit not in self.toPt:
            unit = 'uu'

        if unit == toUnit:
            return number
        else:
            return number * self.toPt[unit] / self.toPt[toUnit]

    def coordConv(self, point):
        """converts svgx, svgy coordinates to eps coordinates using the current transformation matrix"""
        return self.matrices.transform_point(point)

    def alert(self, string, elem):
        """adds an alert to the collection"""
        if not string in self.alerts:
            self.alerts[string] = set()
        elemId = elem.get('id')
        if elemId != None:
            self.alerts[string].add(elemId)

    def showAlerts(self):
        """show alerts collected by the alert() function"""
        for string, ids in self.alerts.iteritems():
            idstring = ', '.join(ids)
            print(string, idstring)

    def elemSvg(self, elem):
        """handles the <svg> element"""
        # DPI changed in inkscape 0.92, so set the px-to-pt rate based on inkscape version
        self.toPt['px'] = 0.75
        inkscapeVersionString = elem.get('{http://www.inkscape.org/namespaces/inkscape}version', '0.92.0')
        mobj = re.match(r'(\d+)\.(\d+)', inkscapeVersionString)
        if mobj != None:
            major = int(mobj.group(1))
            minor = int(mobj.group(2))
            if major == 0 and minor < 92:
                self.toPt['px'] = 0.8

        # by default (without viewbox definition) user unit = pixel
        self.toPt['uu'] = self.toPt['px']
        self.docWidth = self.unitConv(elem.get('width'), 'pt')
        self.docHeight = self.unitConv(elem.get('height'), 'pt')

        viewBoxString = elem.get('viewBox')
        if viewBoxString != None:
            viewBox = viewBoxString.split(' ')
            # theoretically width and height scaling factor could be different,
            # but this script does not support it
            widthUu = float(viewBox[2]) - float(viewBox[0])
            self.toPt['uu'] = self.docWidth / widthUu

        # transform svg units to eps default pt
        scale = self.toPt['uu']

        self.matrices = TransformationMatrixStack(TransformationMatrix([scale, 0, 0, -scale, 0, self.docHeight]))


    def gradientFill(self, elem, gradientId):
        """constructs a gradient instance definition in self.gradientOp"""
        if gradientId not in self.gradients:
            self.alert("fill gradient not defined: " + gradientId, elem)
            return
        gradient = self.gradients[gradientId]
        transformGradient = gradient
        while 'href' in gradient:
            gradientId = gradient['href']
            gradient = self.gradients[gradientId]

        if 'matrix' in transformGradient:
            self.matrices.push_matrix_multiply(transformGradient['matrix'])

        if 'linear' == transformGradient['type']:
            gradient['linUseCount'] += 1
            point1 = self.coordConv(Point(transformGradient['x1'], transformGradient['y1']))
            point2 = self.coordConv(Point(transformGradient['x2'], transformGradient['y2']))
            length = point1.get_distance(point2)
            angle = point1.get_angle(point2)

        elif 'radial' == transformGradient['type']:
            gradient['radUseCount'] += 1
            center = self.coordConv(Point(transformGradient['cx'], transformGradient['cy']))
            right = self.coordConv(Point(transformGradient['cx'] + transformGradient['r'], transformGradient['cy']))
            radius = center.get_distance(right)

        if 'matrix' in transformGradient:
            self.matrices.pop()


        if 'linear' == transformGradient['type']:
            #endPathSegment() will substitute appropriate closeOp in %%s
            self.gradientOp = "\nBb 1 (l_%s) %f %f %f %f 1 0 0 1 0 0 Bg %%s 0 BB" % \
                (gradientId, point1.x, point1.y, angle, length)
        elif 'radial' == transformGradient['type']:
            self.gradientOp = "\nBb 1 (r_%s) %f %f 0 %f 1 0 0 1 0 0 Bg %%s 0 BB" % \
                (gradientId, center.x, center.y, radius)
            self.alert("radial gradients will appear circle shaped", elem)



    def pathStyle(self, elem):
        """handles the style attribute in svg element"""
        if self.clipPath:
            self.closeOp = 'h n'
            return

        css = self.cssStack[-1]
        if 'stroke' in css and css['stroke'] != 'none':
            self.closeOp = 's'
            self.pathCloseOp = 's'
            if '#' == css['stroke'][0] or 'rgb' == css['stroke'][0:3]:
                self.epspath += ' ' + cssColor2Eps(css['stroke']) + ' XA'
            elif 'url' == css['stroke'][0:3]:
                self.alert("gradient strokes not supported", elem)
        if 'fill' in css and css['fill'] != 'none':
            if self.closeOp == 's':
                self.closeOp = 'b'
            else:
                self.closeOp = 'f'
            if '#' == css['fill'][0] or 'rgb' == css['fill'][0:3]:
                self.epspath += ' ' + cssColor2Eps(css['fill']) + ' Xa'
            elif 'url' == css['fill'][0:3]:
                self.gradientFill(elem, css['fill'][5:-1])


        if 'fill-rule' in css:
            if css['fill-rule'] == 'evenodd':
                self.epspath += " 1 XR"
            else:
                self.epspath += " 0 XR"
        if 'stroke-width' in css:
            svgWidth = self.unitConv(css['stroke-width'], 'uu')
            self.epspath += " %f w" % (self.matrices.transform_length(svgWidth), )
        if 'stroke-linecap' in css:
            if css['stroke-linecap'] == 'butt':
                self.epspath += " 0 J"
            elif css['stroke-linecap'] == 'round':
                self.epspath += " 1 J"
            elif css['stroke-linecap'] == 'square':
                self.epspath += " 2 J"
        if 'stroke-linejoin' in css:
            if css['stroke-linejoin'] == 'miter':
                self.epspath += " 0 j"
            elif css['stroke-linejoin'] == 'round':
                self.epspath += " 1 j"
            elif css['stroke-linejoin'] == 'bevel':
                self.epspath += " 2 j"
        if 'stroke-miterlimit' in css:
            self.epspath += " " + css['stroke-miterlimit'] + " M"
        if 'stroke-dasharray' in css:
            phase = 0
            if css['stroke-dasharray'] == 'none':
                dashArray = []
            if css['stroke-dasharray'] != 'none':
                dashArrayIn = css['stroke-dasharray'].replace(',', ' ').split()
                dashArray = list(map(lambda x: "%f" % (x,), filter(lambda x: x > 0, map(lambda x: self.matrices.transform_length(float(x)), dashArrayIn))))
                if 'stroke-dashoffset' in css:
                    phase = float(css['stroke-dashoffset'])

            self.epspath += ' [ %s ] %f d' % (' '.join(dashArray), phase)



    def endPathSegment(self, elem):
        """should be called when a path segment end is reached in a <path> element"""
        if self.removeStrayPoints and self.segmentCommands <= 1:
            self.alert("removing stray point", elem)
            self.epspath = self.epspath[:self.segmentStartIndex]
            return
        if self.autoClose and (self.closeOp == 'f' or self.closeOp == 'b'):
            autoClose = True
        else:
            autoClose = False

        if self.pathExplicitClose or autoClose:
            closeOp = self.closeOp
        else:
            closeOp = self.closeOp.upper()

        if self.pathCurSegment == self.pathSegmentNum and self.gradientOp != None:
            closeOp = self.gradientOp % (closeOp,)

        if self.lastBegin != None:
            if (self.pathExplicitClose or autoClose):
                if self.curPoint.get_manhattan_distance(self.lastBegin) > self.closeDist:
                    lastBeginEps = self.coordConv(self.lastBegin)
                    self.epspath += ' %f %f l' % (lastBeginEps.x, lastBeginEps.y)

            self.epspath += ' ' + closeOp + '\n'

            if self.pathExplicitClose:
                self.curPoint = self.lastBegin

        self.lastBegin = None

    def elemPath(self, elem, pathData=None):
        """handles <path> svg element"""
        if None == pathData:
            pathData = elem.get('d')
        self.pathSegmentNum = pathData.count("m") + pathData.count("M")
        self.pathCurSegment = 0
        self.epspath = ''
        self.segmentStartIndex = 0 # index in self.epspath of first character of current path segment
        self.segmentCommands = 0 # number of handled commands (including first moveto) in current paths segment
        self.closeOp = 'n' # pathStyle(elem) will modify this
        self.gradientOp = None
        self.pathExplicitClose = False
        if elem.get('id'):
            self.epspath += '\n%AI3_Note: ' + elem.get('id') + '\n'

        self.pathStyle(elem)

        tokens = self.rePathDSplit.split(pathData)
        i = 0 # index in path tokens
        cmd = '' # path command
        self.curPoint = Point(0,0)
        self.lastBegin = None

        while i < len(tokens):
            token = tokens[i]
            if token in ['m', 'M', 'c', 'C', 'l', 'L', 'z', 'Z', 'a', 'A', 'q', 'Q', 'h', 'H', 'v', 'V']:
                cmd = token
                i += 1
            elif token.isalpha():
                self.alert('unhandled path command: %s' % (token,), elem)
                cmd = ''
                i += 1
            else: # coordinates after a moveto are assumed to be lineto
                if 'm' == cmd:
                    cmd = 'l'
                elif 'M' == cmd:
                    cmd = 'L'

            if ('M' == cmd or 'm' == cmd) :
                if self.pathCurSegment > 0:
                    self.endPathSegment(elem)
                self.pathCurSegment += 1
                self.pathExplicitClose = False

            if 'M' == cmd or 'm' == cmd:
                if 'M' == cmd or ('m' == cmd and i == 1):
                    self.curPoint = Point(float(tokens[i]), float(tokens[i+1]))
                else:
                    self.curPoint = Point(float(tokens[i]), float(tokens[i+1]), self.curPoint)

                self.segmentStartIndex = len(self.epspath)
                curPointEps = self.coordConv(self.curPoint)
                self.epspath += ' %f %f' % (curPointEps.x, curPointEps.y)
                i += 2
                self.lastBegin = self.curPoint
                self.epspath += ' m'
                self.segmentCommands = 1
            elif 'L' == cmd or 'l' == cmd:
                if 'L' == cmd:
                    self.curPoint = Point(float(tokens[i]), float(tokens[i+1]))
                else:
                    self.curPoint = Point(float(tokens[i]), float(tokens[i+1]), self.curPoint)
                curPointEps = self.coordConv(self.curPoint)
                self.epspath += ' %f %f' % (curPointEps.x, curPointEps.y)
                i += 2
                self.epspath += ' l'
                self.segmentCommands += 1
            elif cmd in ['H', 'h', 'V', 'v']:
                if 'H' == cmd:
                    self.curPoint = Point(float(tokens[i]), self.curPoint.y)
                elif 'h' == cmd:
                    self.curPoint = Point(float(tokens[i]), 0, self.curPoint)
                elif 'V' == cmd:
                    self.curPoint = Point(self.curPoint.x, float(tokens[i]))
                elif 'v' == cmd:
                    self.curPoint = Point(0, float(tokens[i]), self.curPoint)
                curPointEps = self.coordConv(self.curPoint)
                self.epspath += ' %f %f' % (curPointEps.x, curPointEps.y)
                i += 1
                self.epspath += ' l'
                self.segmentCommands += 1
            elif cmd in ('C', 'c'):
                relativeTo = None if cmd == 'C' else self.curPoint
                for j in range(2):
                    controlPointEps = self.coordConv(Point(tokens[i], tokens[i+1], relativeTo))
                    self.epspath += ' %f %f' % (controlPointEps.x, controlPointEps.y)
                    i += 2
                self.curPoint = Point(float(tokens[i]), float(tokens[i+1]), relativeTo)
                curPointEps = self.coordConv(self.curPoint)
                self.epspath += ' %f %f' % (curPointEps.x, curPointEps.y)
                i += 2
                self.epspath += ' c'
                self.segmentCommands += 1
            elif cmd in ('Q', 'q'):
                #export quadratic Bezier as cubic
                relativeTo = None if cmd == 'Q' else self.curPoint
                q0 = self.coordConv(self.curPoint)
                q1 = self.coordConv(Point(float(tokens[i]), float(tokens[i+1]), relativeTo))
                i += 2
                self.curPoint = Point(float(tokens[i]), float(tokens[i+1]), relativeTo)
                q2 = self.coordConv(self.curPoint)
                factor = 2.0 / 3.0
                cx1 = q0.x + factor * (q1.x - q0.x)
                cy1 = q0.y + factor * (q1.y - q0.y)
                cx2 = q2.x - factor * (q2.x - q1.x)
                cy2 = q2.y - factor * (q2.y - q1.y)
                self.epspath += ' %f %f %f %f' % (cx1, cy1, cx2, cy2)
                self.epspath += ' %f %f' % (q2.x, q2.y)
                i += 2
                self.epspath += ' c'
                self.segmentCommands += 1
            elif 'A' == cmd or 'a' == cmd:
                self.alert("elliptic arcs are converted to bezier curves", elem)

# Angel Kostadinov begin
                r1 = abs(float(tokens[i]))
                r2 = abs(float(tokens[i+1]))
                psai = float(tokens[i+2])
                largeArcFlag = int(tokens[i + 3])
                fS = int(tokens[i+4])
                rx = self.curPoint.x
                ry = self.curPoint.y
                if 'A' == cmd:
                    cx, cy = (float(tokens[i+5]), float(tokens[i+6]))
                else:
                    cx, cy = (self.curPoint.x + float(tokens[i+5]), self.curPoint.y +float(tokens[i+6]))

                if r1 > 0 and r2 > 0:
                    ctx = (rx - cx) / 2
                    cty = (ry - cy) / 2
                    cpsi = math.cos(psai*math.pi/180)
                    spsi = math.sin(psai*math.pi/180)
                    rxd = cpsi*ctx + spsi*cty
                    ryd = -1*spsi*ctx + cpsi*cty
                    rxdd = rxd * rxd
                    rydd = ryd * ryd
                    r1x = r1 * r1
                    r2y = r2 * r2
                    lamda = rxdd/r1x + rydd/r2y

                    if lamda > 1:
                        r1 = math.sqrt(lamda) * r1
                        r2 = math.sqrt(lamda) * r2
                        sds = 0
                    else:
                        seif = 1
                        if largeArcFlag == fS:
                            seif = -1
                        sds = seif * math.sqrt((r1x*r2y - r1x*rydd - r2y*rxdd) / (r1x*rydd + r2y*rxdd))

                    txd = sds*r1*ryd / r2
                    tyd = -1 * sds*r2*rxd / r1
                    tx = cpsi*txd - spsi*tyd + (rx+cx)/2
                    ty = spsi*txd + cpsi*tyd + (ry+cy)/2
                    rad = math.atan2((ryd-tyd)/r2, (rxd-txd)/r1) - math.atan2(0, 1)
                    if rad >= 0:
                        s1 = rad
                    else:
                        s1 = 2 * math.pi + rad
                    rad = math.atan2((-ryd-tyd)/r2, (-rxd-txd)/r1) - math.atan2((ryd-tyd)/r2, (rxd-txd)/r1)
                    if rad >= 0:
                        dr = rad
                    else:
                        dr = 2 * math.pi + rad

                    if fS==0 and dr > 0:
                        dr -= 2*math.pi
                    elif fS==1 and dr < 0:
                        dr += 2*math.pi

                    sse = dr * 2 / math.pi
                    if sse < 0:
                        seg = math.ceil(-1*sse)
                    else:
                        seg = math.ceil(sse)
                    segr = dr / seg
                    t = 8.0/3.0 * math.sin(segr/4) * math.sin(segr/4) / math.sin(segr/2)
                    cpsir1 = cpsi * r1
                    cpsir2 = cpsi * r2
                    spsir1 = spsi * r1
                    spsir2 = spsi * r2
                    mc = math.cos(s1)
                    ms = math.sin(s1)
                    x2 = rx - t * (cpsir1*ms + spsir2*mc)
                    y2 = ry - t * (spsir1*ms - cpsir2*mc)

                    for n in range(int(math.ceil(seg))):
                        s1 += segr
                        mc = math.cos(s1)
                        ms = math.sin(s1)

                        x3 = cpsir1*mc - spsir2*ms + tx
                        y3 = spsir1*mc + cpsir2*ms + ty
                        dx = -t * (cpsir1*ms + spsir2*mc)
                        dy = -t * (spsir1*ms - cpsir2*mc)

                        c1 = self.coordConv(Point(x2, y2))
                        c2 = self.coordConv(Point(x3-dx, y3-dy))
                        c3 = self.coordConv(Point(x3, y3))

                        self.epspath += " %f %f %f %f %f %f c" % (c1.x, c1.y, c2.x, c2.y, c3.x, c3.y)

                        x2 = x3 + dx
                        y2 = y3 + dy
                else:
                    # case when one radius is zero: this is a simple line
                    pointEps = self.coordConv(Point(cx, cy))
                    self.epspath += ' %f %f l' % (pointEps.x, pointEps.y)

# Angel Kostadinov end
                self.segmentCommands += 1
                i += 7
                self.curPoint = Point(cx, cy)

            elif 'z' == cmd or 'Z' == cmd:
                self.pathExplicitClose = True
                cmd = ''
            else:
                i += 1

        self.endPathSegment(elem)

        if self.pathSegmentNum > 1:
            self.epspath = " *u\n" + self.epspath + "\n*U "
        self.epsLayers += "\n" + wrap(self.epspath, 70) + "\n"

    def elemRect(self, elem):
        x = float(elem.get('x'))
        y = float(elem.get('y'))
        width = float(elem.get('width'))
        height = float(elem.get('height'))

        # construct an svg <path> d attribute, and call self.elemPath()
        pathData = ""
        rx = elem.get('rx')
        ry = elem.get('ry')
        if rx == None and ry == None:
            rx = 0
            ry = 0
        else:
            # if only one radius is given, it means both are the same
            rx = float(rx) if rx != None else float(ry)
            ry = float(ry) if ry != None else float(rx)

        if rx == 0 and ry == 0:
            pathData = "M %f %f %f %f %f %f %f %f z" % (x, y, x + width,y, x + width, y + height, x, y + height)
        else:
            pathData = "M %f %f A %f %f 0 0 1 %f %f" % (x, y + ry, rx, ry, x+rx, y)
            pathData += " L %f %f A %f %f 0 0 1 %f %f" % (x + width - rx, y, rx, ry, x + width, y + ry)
            pathData += " L %f %f A %f %f 0 0 1 %f %f" % (x + width, y + height - ry, rx, ry, x + width - rx, y + height)
            pathData += " L %f %f A %f %f 0 0 1 %f %f z" % (x + rx, y + height, rx, ry, x, y + height - ry)
        self.elemPath(elem, pathData)

    def elemPolygon(self, elem):
        pathData = 'M ' + elem.get('points').replace(',', ' ').strip() + ' z'
        self.elemPath(elem, pathData)        

    def elemCircle(self, elem):
        r = float(elem.get('r'))
        self.elemEllipseCircleCommon(elem, r, r)

    def elemEllipse(self, elem):
        rx = float(elem.get('rx'))
        ry = float(elem.get('ry'))
        self.elemEllipseCircleCommon(elem, rx, ry)

    def elemEllipseCircleCommon(self, elem, rx, ry):
        cx = float(elem.get('cx'))
        cy = float(elem.get('cy'))
        # todo: test whether PostScript arc is handled by AI and use that instead
        magic = 0.55228475 # I've read it on the internet
        controlx = rx * magic # x distance of control points from center
        controly = ry * magic # y distance of control points from center

        # construct an svg <path> d attribute, and call self.elemPath()
        pathData = "M %f %f" % (cx - rx, cy) # leftmost point
        pathData += " C %f %f %f %f %f %f" % (cx - rx, cy - controly, cx - controlx, cy - ry, cx, cy - ry) # to top
        pathData += " C %f %f %f %f %f %f" % (cx + controlx, cy - ry, cx + rx, cy - controly, cx + rx, cy) # to right
        pathData += " C %f %f %f %f %f %f" % (cx + rx, cy + controly, cx + controlx, cy + ry, cx, cy + ry) # to bottom
        pathData += " C %f %f %f %f %f %f z" % (cx - controlx, cy + ry, cx - rx, cy + controly, cx - rx, cy) # back to left and close
        self.elemPath(elem, pathData)


    def transform_attr_to_matrix(self, transform):
        """Converts a svg transform attribute to a transformation matrix"""
        matrix = TransformationMatrix()
        for ttype, targs in self.reTransformFind.findall(transform):
            targs = list(map(lambda x: float(x), self.reNumberFind.findall(targs)))
            if ttype == 'matrix':
                matrix = matrix.multiply((targs[0], targs[1], targs[2], targs[3], targs[4], targs[5]))
            elif ttype == 'translate':
                tx = targs[0]
                ty = targs[1] if len(targs) > 1 else 0
                matrix = matrix.translate(tx, ty)
            elif ttype == 'scale':
                sx = targs[0]
                sy = targs[1] if len(targs) > 1 else sx
                matrix = matrix.scale(sx, sy)
            elif ttype == 'rotate':
                alpha = targs[0]
                if len(targs) == 1:
                    cx, cy = 0, 0
                else:
                    cx, cy = targs[1], targs[2]
                matrix = matrix.rotate(alpha, cx, cy)
            elif ttype == 'skewX' or ttype == 'skewY':
                self.alert("skewX and skewY transformations are not supported")
                continue
            else:
                print('unknown transform type: ', ttype)
                continue

        return matrix

    def elemGradient(self, elem, grType):
        """handles <linearGradient> and <radialGradient> svg elements"""
        elemId  = elem.get('id')
        if elemId != None:
            self.curGradientId = elemId
            self.gradients[elemId] = {'stops': [], 'linUseCount': 0, 'radUseCount': 0, 'type': grType}
            if 'linear' == grType:
                x1 = elem.get('x1')
                if None != x1:
                    self.gradients[elemId]['x1'] = float(x1)
                    self.gradients[elemId]['y1'] = float(elem.get('y1'))
                    self.gradients[elemId]['x2'] = float(elem.get('x2'))
                    self.gradients[elemId]['y2'] = float(elem.get('y2'))
            elif 'radial' == grType:
                cx = elem.get('cx')
                if None != cx:
                    self.gradients[elemId]['cx'] = float(cx)
                    self.gradients[elemId]['cy'] = float(elem.get('cy'))
                    self.gradients[elemId]['fx'] = float(elem.get('fx'))
                    self.gradients[elemId]['fy'] = float(elem.get('fy'))
                    self.gradients[elemId]['r'] = float(elem.get('r'))

            transform = elem.get('gradientTransform')
            if None != transform:
                self.gradients[elemId]['matrix'] = self.transform_attr_to_matrix(transform)

            href = elem.get('{http://www.w3.org/1999/xlink}href')
            if None != href:
                self.gradients[elemId]['href'] = href[1:]


    def elemStop(self, elem):
        """handles <stop> (gradient stop) svg element"""
        stopColor = elem.get('stop-color')
        if not stopColor:
            style = css2dict(elem.get('style'))
            if 'stop-color' in style:
                stopColor = style['stop-color']
            else:
                stopColor = '#000000'
        color = cssColor2Eps(stopColor, 'CMYKRGB')
        offsetString = elem.get('offset', '0').strip()
        if offsetString[-1] == '%':
            offset = float(offsetString[:-1])
        else:
            offset = float(offsetString) * 100
        self.gradients[self.curGradientId]['stops'].append( (offset, color) )

    def gradientSetup(self):
        """writes used gradient definitions into self.epsSetup"""
        gradientNum = 0
        epsGradients = ""
        for gradientId, gradient in self.gradients.items():

            if gradient['linUseCount'] > 0:
                gradientNum += 1
                epsGradients += ("\n%%AI5_BeginGradient: (l_%s)" + \
                    "\n(l_%s) 0 %d Bd\n[\n") % \
                    (gradientId, gradientId, len(gradient['stops']))
                gradient['stops'].sort(key=lambda x: x[0], reverse=True)

                for offset, color in gradient['stops']:
                    epsGradients += "%s 2 50 %f %%_Bs\n" % (color, offset)
                epsGradients += "BD\n%AI5_EndGradient\n"

            if gradient['radUseCount'] > 0:
                gradientNum += 1
                epsGradients += ("\n%%AI5_BeginGradient: (r_%s)" + \
                    "\n(r_%s) 1 %d Bd\n[\n") % \
                    (gradientId, gradientId, len(gradient['stops']))
                gradient['stops'].sort(key=lambda x: x[0])

                for offset, color in gradient['stops']:
                    epsGradients += "%s 2 50 %f %%_Bs\n" % (color, offset)
                epsGradients += "BD\n%AI5_EndGradient\n"

        if gradientNum > 0:
            self.epsSetup += ("\n%d Bn\n" % gradientNum) + epsGradients


    def layerStart(self, elem):
        self.epsLayers += '\n\n%AI5_BeginLayer\n'
        layerName = elem.get('{http://www.inkscape.org/namespaces/inkscape}label')
        layerName = "".join(map(lambda x: '_' if ord(x)<32 or ord(x) > 127 else x, layerName))
        self.epsLayers += '1 1 1 1 0 0 %d 0 0 0 Lb\n(%s) Ln\n' % \
            (self.layerColor, layerName)
        self.layerColor = (self.layerColor + 1) % 27

    def elemUse(self, elem):
        """handles a <use> svg element"""
        x = self.unitConv(elem.get('x'), 'uu')
        if x == None:
            x = 0
        y = self.unitConv(elem.get('y'), 'uu')
        if y == None:
            y = 0

        if x != 0 or y != 0:
            self.matrices.push_matrix_multiply(self.transform_attr_to_matrix("translate(%f %f)" % (x, y)))

        href = elem.get('{http://www.w3.org/1999/xlink}href')
        usedElem = self.root.find(".//*[@id='%s']" % (href[1:],))
        if usedElem != None:
            self.walkElem(usedElem)
        else:
            self.alert("used Elem not found: " + href, elem)

        if x != 0 or y != 0:
            self.matrices.pop()

    def walkElem(self, elem):
        if '}' in elem.tag:
            uri, shortTag = elem.tag.split('}')
        else:
            shortTag = elem.tag
            uri = ''

        transform = elem.get('transform')
        clipPath = elem.get('clip-path')
        cssNew = css2dict(elem.get('style'))
        css = self.cssStack[-1].copy()
        css.update(cssNew)
        self.cssStack.append(css)
        if self.removeInvisible:
            if 'visibility' in css and (css['visibility'] == 'hidden' or css['visibility'] == 'collapse'):
                return
            if 'display' in css and css['display'] == 'none':
                return
            if shortTag in ('path', 'rect', 'circle', 'ellipse', 'polygon'):
                if 'opacity' in css and css['opacity'] == '0':
                    return
                stroke = False
                if 'stroke' in css and 'none' != css['stroke']:
                    stroke = True
                    if 'stroke-opacity' in css and css['stroke-opacity'] == '0':
                        stroke = False
                    if 'stroke-width' in css and css['stroke-width'] == '0':
                        stroke = False
                fill = False
                if 'fill' in css and 'none' != css['fill']:
                    fill = True
                    if 'fill-opacity' in css and css['fill-opacity'] == '0':
                        stroke = False
                if stroke == False and fill == False:
                    return


        if transform != None:
            self.matrices.push_matrix_multiply(self.transform_attr_to_matrix(transform))

        if None != clipPath:
            clipId = clipPath[5:-1]
            clipElem = self.root.find(".//*[@id='%s']" % (clipId,))
            if clipElem == None:
                self.alert('clipPath not found', elem)
                clipPath = None
            else:
                self.epsLayers += "\nq\n"
                clipPathSave= self.clipPath
                self.clipPath = True
                # output clip path even if it doesn't have visible style
                popRemoveInvisible = self.removeInvisible
                self.removeInvisible = False
                self.walkElem(clipElem)
                self.removeInvisible = popRemoveInvisible
                self.clipPath = clipPathSave
                self.epsLayers += ' W'

        if 'svg' == shortTag:
            self.elemSvg(elem)
        elif 'path' == shortTag:
            # do not output paths that are in defs
            # if they are referenced, they will be used there
            if self.section != 'defs':
                self.elemPath(elem)
        elif 'rect' == shortTag:
            if self.section != 'defs':
                self.elemRect(elem)
        elif 'circle' == shortTag:
            if self.section != 'defs':
                self.elemCircle(elem)
        elif 'ellipse' == shortTag:
            if self.section != 'defs':
                self.elemEllipse(elem)
        elif 'polygon' == shortTag:
            if self.section != 'defs':
                self.elemPolygon(elem)
        elif 'linearGradient' == shortTag:
            self.elemGradient(elem, 'linear')
        elif 'radialGradient' == shortTag:
            self.elemGradient(elem, 'radial')
        elif 'stop' == shortTag:
            self.elemStop(elem)
        elif 'g' == shortTag:
            if 'layer' == elem.get('{http://www.inkscape.org/namespaces/inkscape}groupmode'):
                self.layerStart(elem)
            elif None == clipPath: # clipping makes a group anyway
                self.epsLayers += '\nu\n'
        elif 'use' == shortTag:
            self.elemUse(elem)
        elif 'defs' == shortTag:
            self.section = shortTag
        elif 'namedview' == shortTag:
            self.section = shortTag
        else:
            self.alert("unhandled elem: " + shortTag, elem)


        for child in list(elem):
            self.walkElem(child)

        if None != clipPath:
            self.epsLayers += "\nQ\n"

        if 'g' == shortTag:
            if 'layer' == elem.get('{http://www.inkscape.org/namespaces/inkscape}groupmode'):
                self.epsLayers += '\nLB\n%AI5_EndLayer\n'
            elif None == clipPath:
                self.epsLayers += '\nU\n'
        elif shortTag in ('defs', 'namedview'):
            self.section = None

        if transform != None:
            self.matrices.pop()

        self.cssStack.pop()

    def convert(self, svg = None):
        self.alerts = {}
        if None != svg:
            self.svg = svg
        if None == self.svg and None != self.filename:
            fd = open(self.filename, 'rb')
            self.svg = fd.read()
            fd.close()

        self.autoClose = True # TODO: make it optional
        self.removeInvisible = True # TODO: make it optional
        self.removeStrayPoints = True # TODO: make it optional
        # if last point of a path is further from first point, then an explicit
        # 'lineto' is written to the first point before 'closepath'
        self.closeDist = 0.1
        self.matrices = TransformationMatrixStack()
        self.cssStack = [{}]
        self.gradients = {}
        self.docHeight = 400
        self.docWidth = 400
        self.layerColor = 0
        self.section = None
        self.clipPath = False
        self.epsComments = """%!PS-Adobe-3.0 EPSF-3.0
%%Creator: tzunghaor svg2eps
%%Pages: 1
%%DocumentData: Clean7Bit
%%LanguageLevel: 3
%%DocumentNeededResources: procset Adobe_Illustrator_AI5 1.3 0
%AI5_FileFormat 3
"""
        # TODO: creation date, user etc

        self.epsProlog = """%%BeginProlog
100 dict begin
/tzung_eps_state save def
/dict_count countdictstack def
/op_count count 1 sub def
/Adobe_Illustrator_AI5 where
{ pop } {
    /tzung_strokergb [ 0 0 0 ] def
    /tzung_compound 0 def
    /tzung_closeop { S } def
    /tzung_fillrule 0 def

    /*u { /tzung_compound 1 def newpath /tzung_fillrule 0 def } bind def
    /*U { /tzung_compound 0 def tzung_closeop  } bind def
    /u {} bind def
    /U {} bind def

    /q { clipsave } bind def
    /Q { cliprestore } bind def
    /W { clip } bind def

    /Lb { 10 {pop} repeat } bind def
    /Ln {pop} bind def
    /LB {} bind def


    /w { setlinewidth } bind def
    /J { setlinecap } bind def
    /j { setlinejoin } bind def
    /M { setmiterlimit } bind def
    /d { setdash } bind def

    /m { tzung_compound 0 eq { newpath /tzung_fillrule 0 def } if moveto } bind def
    /l { lineto } bind def
    /c { curveto } bind def

    /XR { /tzung_fillrule exch def } bind def
    /Xa { setrgbcolor } bind def
    /XA { 3 array astore /tzung_strokergb exch def } bind def


    /F { tzung_compound 0 eq {
             tzung_fillrule 0 eq { fill } { eofill } ifelse
         } {
             /tzung_closeop {F} def
         } ifelse } bind def
    /f { closepath F } bind def
    /S { tzung_compound 0 eq {
            tzung_strokergb aload pop setrgbcolor stroke
        } {
             /tzung_closeop {S} def
        } ifelse } bind def
    /s { closepath S } bind def

    /B { tzung_compound 0 eq {
            gsave
            tzung_fillrule 0 eq { fill } { eofill } ifelse
            grestore
            tzung_strokergb aload pop setrgbcolor stroke
         } {
             /tzung_closeop {B} def
        } ifelse } bind def
    /b { closepath B } bind def
    /H { tzung_compound 0 eq {
        }{
            /tzung_closeop {H} def
        } ifelse} bind def
    /h { closepath } bind def
    /N { tzung_compound 0 eq {
        }{
            /tzung_closeop {N} def
        } ifelse} bind def
    /n { closepath N } bind def


    /Bn { /dict_gradients exch dict def} bind def
    /Bd { /tmp_ngradstop exch def /tmp_shadingtype exch def } bind def  %leaves gradient name in stack
    /BD { ]  % this handles only stops that have CMYKRGB color definitions
        % linear gradient stops must be in reverse order, radials in normal order
        aload
        pop
        /tmp_boundaries tmp_ngradstop array def
        /tmp_colors tmp_ngradstop array def
        tmp_shadingtype 0 eq {
            0 1 tmp_ngradstop 1 sub   % for i=0; i<= number of gradient stops - 1; i++
        } {
            tmp_ngradstop 1 sub -1 0   % for i=number of gradient stops - 1; i >= 0; i++
        } ifelse
        {
            /loopvar exch def
            100 div
            tmp_boundaries  loopvar
            3 -1 roll put    %  obj array i => array i obj
            pop % assume gradient middle is always 50
            pop % assume color type is always 2 (CMYKRGB)
            3 array astore
            tmp_colors loopvar
            3 -1 roll put
            pop pop pop pop % drop CMYK values
        } for

        tmp_ngradstop 2 eq {
            /tmp_function 5 dict def
            tmp_boundaries 0 get tmp_boundaries 1 get 2 array astore
            tmp_function /Domain 3 -1 roll put
            tmp_function /FunctionType 2 put
            tmp_function /C0  tmp_colors 0 get put
            tmp_function /C1 tmp_colors 1 get put
            tmp_function /N 1 put

        } {
            /tmp_functions tmp_ngradstop 1 sub array def

            0 1 tmp_ngradstop 2 sub {
                /loopvar exch def
                /tmp_function 5 dict def
                tmp_function /Domain [0 1]  put
                tmp_function /FunctionType 2 put
                tmp_function /C0  tmp_colors loopvar get put
                tmp_function /C1 tmp_colors loopvar 1 add get put
                tmp_function /N 1 put
                tmp_functions loopvar tmp_function put
            } for


            /tmp_function 5 dict def
            tmp_boundaries 0 get tmp_boundaries tmp_ngradstop 1 sub get 2 array astore
            tmp_function /Domain 3 -1 roll  put
            tmp_function /FunctionType 3 put
            tmp_boundaries aload pop
            tmp_ngradstop -1 roll pop pop % remove first and last bounds
            tmp_ngradstop 2 sub array astore
            tmp_function /Bounds 3 -1 roll put
            tmp_function /Functions tmp_functions put

            tmp_ngradstop 1 sub {
                0 1
            } repeat
            tmp_ngradstop 1 sub 2 mul array astore
            tmp_function /Encode 3 -1 roll put

        } ifelse

        /tmp_shading 6 dict def
        tmp_shadingtype 0 eq {
            tmp_shading /ShadingType 2 put
            tmp_shading /Coords [ 0 0 1 0 ] put
        } {
            tmp_shading /ShadingType 3 put
            tmp_shading /Coords [ 0 0 0 0 0 1 ] put
        } ifelse
        tmp_shading /ColorSpace /DeviceRGB put
        tmp_shading /Domain [0 1] put
        tmp_shading /Extend[ true true] put
        tmp_shading /Function tmp_function put

        /tmp_gradient 2 dict def
        tmp_gradient /PatternType 2 put
        tmp_gradient /Shading tmp_shading put

        dict_gradients exch tmp_gradient put % gradient's name is on the top of the stack from Bd operator

    } bind def
    /Lb { 10 { pop } repeat } bind def
    /Ln { pop } bind def
    /Bb { } bind def

    /Bg {
        6 { pop } repeat
        gsave
        4 2 roll
        translate
        exch
        rotate
        dup scale
         exch pop % remove Bg flag
        dict_gradients exch get % now gradient name is on top of the stack
         [ 1 0 0 1 0 0 ]
        makepattern
        /pattern_tmp exch def
        grestore
        pattern_tmp  setpattern
         gsave % save for after pattern fil for possible stroke
    } def
    /BB { grestore 2 eq { s } if } bind def
    /LB { } bind def

} ifelse
"""
        self.epsSetup = """%%BeginSetup
/Adobe_Illustrator_AI5 where
{
    pop
    Adobe_Illustrator_AI5 /initialize get exec
} if
"""
        self.epsLayers = ""
        self.epsTrailer = """%%Trailer
showpage
count op_count sub {pop} repeat
countdictstack dict_count sub {end} repeat
tzung_eps_state restore
end
%%EOF
"""


        self.root = ET.fromstring(self.svg)
        self.walkElem(self.root)
        self.gradientSetup()

        sizeComment = "%%%%BoundingBox: 0 0 %d %d\n" % (math.ceil(self.docWidth), math.ceil(self.docHeight))
        sizeComment += "%%%%HiResBoundingBox: 0 0 %f %f\n" % (self.docWidth, self.docHeight)
        sizeComment += "%%AI5_ArtSize: %f %f\n" % (self.docWidth, self.docHeight)
        pagesetup = """%%%%Page: 1 1
%%%%BeginPageSetup
%%%%PageBoundingBox: 0 0 %d %d
%%%%EndPageSetup
""" % (self.docWidth, self.docHeight)

        eps = self.epsComments + sizeComment + "%%EndComments\n\n"
        eps += self.epsProlog  + "\n%%EndProlog\n\n"
        eps += self.epsSetup + "\n%%EndSetup\n\n"
        eps += pagesetup + self.epsLayers + "\n\n"
        eps += self.epsTrailer

        return eps

# Start of main() entry point

assert len(sys.argv) >= 2, "missing filename"

converter = svg2eps(sys.argv[1])

print(converter.convert())
#TODO: show alerts in dialogbox
#converter.showAlerts()

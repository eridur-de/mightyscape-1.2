#!/usr/bin/env python3
"""
base_transform.py
Base matemathical operations for SVG 3x3 matrices

Copyright (C) 2011 Cosmin Popescu, cosminadrianpopescu@gmail.com

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

import re
import inkex
import os
from math import *

class BaseTransform(inkex.Effect):
    unitMatrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

    def isset(self, v, i = None):
        try:
            if (i is None):
                v
            else:
                v[i]
            return True
        except:
            return False

    def __init__(self):
        inkex.Effect.__init__(self)

    def sizeToPx(self, s, dim = "y"):
        root = self.document.getroot()
        try:
            factor = float(root.attrib[inkex.addNS('export-' + dim + 'dpi', 'inkscape')])
        except:
            factor = 90
        unit = ''
        pattern = '[\\-\\d\\.]+([a-zA-Z][a-zA-Z])'
        if (re.search(pattern, s)):
            res = re.search(pattern, s)
            unit = res.group(1)
        pattern = '^([\\-\\d\\.]*)'
        res = re.search(pattern, s)
        n = float(res.group(1))
        if unit == 'cm':
            return (n / 2.54) * factor
        elif unit == 'ft':
            return n * 12 * factor
        elif unit == 'in':
            return n * factor
        elif unit == 'm':
            return ((n * 10) / 2.54) * factor
        elif unit == 'mm':
            return ((n / 10) / 2.54) * factor
        elif unit == 'pc':
            return ((n * 2.36228956229) / 2.54) * factor
        elif unit == 'pt':
            return (((n / 2.83464646465) / 10) / 2.54) * factor
        elif unit == 'px' or unit == '':
            return n

        return 0

    def transform(self, el):
        result = self.unitMatrix
        if (el.tag == inkex.addNS('svg', 'svg')):
            return result

        if (not self.isset(el.attrib, 'transform')):
            return self.multiply(self.transform(el.getparent()), result)
        pattern = '(matrix|translate|scale|rotate|skewX|skewY)[\\s|,]*\\(([^\\)]*)\\)'
        transforms = re.findall(pattern, el.attrib['transform'])

        for transform in transforms:
            values = re.split('[\\s|,]+', transform[1])
            for i in range(len(values)):
                values[i] = float(values[i])
            function = transform[0]
            if (function == 'matrix'):
                a = [[values[0], values[2], values[4]],
                    [values[1], values[3], values[5]],
                    [0, 0, 1]]
                result = self.multiply(result, a)
            elif (function == 'translate'):
                a = [[1, 0, values[0]],
                    [0, 1, values[1]],
                    [0, 0, 1]]
                result = self.multiply(result, a)
            elif (function == 'scale'):
                a = [[values[0], 0, 0],
                    [0, values[1], 0],
                    [0, 0, 1]]
                result = self.multiply(result, a)
            elif (function == 'rotate'):
                if (len(values) == 1):
                    a = [[math.cos(values[0]), -math.sin(values[0]), 0],
                        [math.sin(values[0]), math.cos(values[0]), 0],
                        [0, 0, 1]]
                    result = self.multiply(result, a)
                else:
                    a = [[1, 0, values[2]],
                        [0, 1, values[2]],
                        [0, 0, 1]]
                    result = self.multiply(result, a)
                    a = [[math.cos(values[0]), -math.sin(values[0]), 0],
                        [math.sin(values[0]), math.cos(values[0]), 0],
                        [0, 0, 1]]
                    result = self.multiply(result, a)
                    a = [[1, 0, -values[2]],
                        [0, 1, -values[2]],
                        [0, 0, 1]]
                    result = self.multiply(result, a)
            elif (function == 'skewX'):
                a = [[1, math.tan(values[0]), 0],
                    [0, 1, 0],
                    [0, 0, 1]]
                result = self.multiply(result, a)
            elif (function == 'skewY'):
                a = [[1, 0, 0],
                    [math.tan(values[0]), 1, 0],
                    [0, 0, 1]]
                result = self.multiply(result, a)

        return self.multiply(self.transform(el.getparent()), result)


    def getPosition(self, el):
        if not self.isset(el.attrib, 'x'):
            return False

        x = self.sizeToPx(el.attrib['x'], 'x')
        y = self.sizeToPx(el.attrib['y'], 'y')
        v = [x, y, 1]
        t = self.transform(el)
        v = self.multiply(t, v)

        return {'coordinates': v, 'matrix': t}

    def setPosition(self, el, position):
        c = position['coordinates']
        a = position['matrix']
        if (not self.isUnitMatrix(a)):
            c = self.multiply(self.inverse(a), c)
        el.set('x', str(c[0]))
        el.set('y', str(c[1]))


    def determinant(self, a):
        if len(a) != 3:
            return False
        if (len(a[0]) != 3):
            return False

        det = a[0][0] * (a[1][1] * a[2][2] - a[2][1] * a[1][2]) - a[0][1] * (a[1][0] * a[2][2] - a[2][0] * a[1][2]) + a[0][2] * (a[1][0] * a[2][1] - a[2][0] * a[1][1])

        if (det == 0):
            det = 0.00001

        return det

    def minors(self, a):
        if len(a) != 3:
            return False
        if (len(a[0]) != 3):
            return False

        return [[a[1][1] * a[2][2] - a[2][1] * a[1][2], a[1][0] * a[2][2] - a[2][0] * a[1][2], a[1][0] * a[2][1] - a[2][0] * a[1][1]],
                [a[0][1] * a[2][2] - a[2][1] * a[0][2], a[0][0] * a[2][2] - a[0][2] * a[2][0], a[0][0] * a[2][1] - a[2][0] * a[0][1]],
                [a[0][1] * a[1][2] - a[1][1] * a[0][2], a[0][0] * a[1][2] - a[0][1] * a[0][2], a[0][0] * a[1][1] - a[1][0] * a[0][1]]
                ]

    def cofactors(self, a):
        if len(a) != 3:
            return False
        if (len(a[0]) != 3):
            return False

        return [[a[0][0], -a[0][1], a[0][2]],
                [-a[1][0], a[1][1], -a[1][2]],
                [a[2][0], -a[2][1], a[2][2]]
                ]

    def adjoint(self, a):
        if len(a) != 3:
            return False
        if (len(a[0]) != 3):
            return False

        return [[a[0][0], a[1][0], a[2][0]],
                [a[0][1], a[1][1], a[2][1]],
                [a[0][2], a[1][2], a[2][2]]
                ]

    def inverse(self, a):
        if len(a) != 3:
            return False
        if (len(a[0]) != 3):
            return False

        det = self.determinant(a)
        m = self.minors(a)
        c = self.cofactors(m)
        adj = self.adjoint(c)

        return [[adj[0][0] / det, adj[0][1] / det, adj[0][2] / det],
                [adj[1][0] / det, adj[1][1] / det, adj[1][2] / det],
                [adj[2][0] / det, adj[2][1] / det, adj[2][2] / det]
                ]

    def multiply(self, a, v):
        if len(a) != 3:
            return False
        if (len(a[0]) != 3):
            return False

        if (len(v) != 3):
            return False

        if (not self.isset(v[0], 0)):
            return [a[0][0] * v[0] + a[0][1] * v[1] + a[0][2] * v[2],
                    a[1][0] * v[0] + a[1][1] * v[1] + a[1][2] * v[2],
                    a[2][0] * v[0] + a[2][1] * v[1] + a[2][2] * v[2]
                    ]
        else:
            return [[a[0][0] * v[0][0] + a[0][1] * v[1][0] + a[0][2] * v[2][0], a[0][0] * v[0][1] + a[0][1] * v[1][1] + a[0][2] * v[2][1], a[0][0] * v[0][2] + a[0][1] * v[1][2] + a[0][2] * v[2][2]],
                    [a[1][0] * v[0][0] + a[1][1] * v[1][0] + a[1][2] * v[2][0], a[1][0] * v[0][1] + a[1][1] * v[1][1] + a[1][2] * v[2][1], a[1][0] * v[0][2] + a[1][1] * v[1][2] + a[1][2] * v[2][2]],
                    [a[2][0] * v[0][0] + a[2][1] * v[1][0] + a[2][2] * v[2][0], a[2][0] * v[0][1] + a[2][1] * v[1][1] + a[2][2] * v[2][1], a[2][0] * v[0][2] + a[2][1] * v[1][2] + a[2][2] * v[2][2]]
                    ]

    def isUnitMatrix(self, a):
        if (len(a) != 3):
            return False
        if (len(a[0]) != 3):
            return False

        for i in range(3):
            for j in range(3):
                if (a[i][j] != self.unitMatrix[i][j]):
                    return False

        return True

    def reParse(self):
        if os.name == 'nt':
            path = os.environ['USERPROFILE']
        else:
            path = os.path.expanduser("~")
        text = inkex.etree.tostring(self.document.getroot())
        f = open(path + '/tmp.svg', 'w')
        f.write(text)
        f.close()
        self.parse(path + '/tmp.svg')

        os.remove(path + '/tmp.svg')

    def matrix2string(self, a):
        return 'matrix(' + str(a[0][0]) + ',' + str(a[1][0]) + ',' + str(a[0][1]) + ',' + str(a[1][1]) + ',' + str(a[0][2]) + ',' + str(a[1][2]) + ')'
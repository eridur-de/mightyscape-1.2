#!/usr/bin/env python3

import os
import inkex
import voronoi
from inkex.transforms import Transform
from inkex.paths import CubicSuperPath, Path
from PIL import Image
from lxml import etree
import base64
from io import BytesIO
import urllib.request as urllib

# A tool for making polygonal art. Can be created with one click with a pass.

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __lt__(self,other):
        return (self.x*self.y<other.x*other.y)
        
    def __le__(self,other):
        return (self.x*self.y<=other.y*other.y)
        
    def __gt__(self,other):
        return (self.x*self.y>other.x*other.y)
        
    def __ge__(self,other):
        return (self.x*self.y>=other.x*other.y)
        
    def __eq__(self,other):
        return (self.x==other.x) and (self.y==other.y)
        
    def __ne__(self,other):
        return (self.x!=other.x) or (self.y!=other.y)

    def __str__(self):
        return "("+str(self.x)+","+str(self.y)+")"


class LowPoly2(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)

    # Clipping a line by a bounding box
    def dot(self, x, y):
        return x[0] * y[0] + x[1] * y[1]

    def intersectLineSegment(self, line, v1, v2):
        s1 = self.dot(line, v1) - line[2]
        s2 = self.dot(line, v2) - line[2]
        if s1 * s2 > 0:
            return (0, 0, False)
        else:
            tmp = self.dot(line, v1) - self.dot(line, v2)
            if tmp == 0:
                return (0, 0, False)
            u = (line[2] - self.dot(line, v2)) / tmp
            v = 1 - u
            return (u * v1[0] + v * v2[0], u * v1[1] + v * v2[1], True)

    def clipEdge(self, vertices, lines, edge, bbox):
        # bounding box corners
        bbc = []
        bbc.append((bbox[0], bbox[2]))
        bbc.append((bbox[1], bbox[2]))
        bbc.append((bbox[1], bbox[3]))
        bbc.append((bbox[0], bbox[3]))

        # record intersections of the line with bounding box edges
        line = (lines[edge[0]])
        interpoints = []
        for i in range(4):
            p = self.intersectLineSegment(line, bbc[i], bbc[(i + 1) % 4])
            if (p[2]):
                interpoints.append(p)

        # if the edge has no intersection, return empty intersection
        if (len(interpoints) < 2):
            return []

        if (len(interpoints) > 2):  #h appens when the edge crosses the corner of the box
            interpoints = list(set(interpoints))  # remove doubles

        # points of the edge
        v1 = vertices[edge[1]]
        interpoints.append((v1[0], v1[1], False))
        v2 = vertices[edge[2]]
        interpoints.append((v2[0], v2[1], False))

        # sorting the points in the widest range to get them in order on the line
        minx = interpoints[0][0]
        maxx = interpoints[0][0]
        miny = interpoints[0][1]
        maxy = interpoints[0][1]
        for point in interpoints:
            minx = min(point[0], minx)
            maxx = max(point[0], maxx)
            miny = min(point[1], miny)
            maxy = max(point[1], maxy)

        if (maxx - minx) > (maxy - miny):
            interpoints.sort()
        else:
            interpoints.sort(key=lambda pt: pt[1])

        start = []
        inside = False  #true when the part of the line studied is in the clip box
        startWrite = False  #true when the part of the line is in the edge segment
        for point in interpoints:
            if point[2]:  #The point is a bounding box intersection
                if inside:
                    if startWrite:
                        return [[start[0], start[1]], [point[0], point[1]]]
                    else:
                        return []
                else:
                    if startWrite:
                        start = point
                inside = not inside
            else:  # The point is a segment endpoint
                if startWrite:
                    if inside:
                        # a vertex ends the line inside the bounding box
                        return [[start[0], start[1]], [point[0], point[1]]]
                    else:
                        return []
                else:
                    if inside:
                        start = point
                startWrite = not startWrite

    # Transformation helpers
    def invertTransform(self, mat):
        det = mat[0][0] * mat[1][1] - mat[0][1] * mat[1][0]
        if det != 0:  #det is 0 only in case of 0 scaling
            # invert the rotation/scaling part
            a11 = mat[1][1] / det
            a12 = -mat[0][1] / det
            a21 = -mat[1][0] / det
            a22 = mat[0][0] / det

            # invert the translational part
            a13 = -(a11 * mat[0][2] + a12 * mat[1][2])
            a23 = -(a21 * mat[0][2] + a22 * mat[1][2])

            return [[a11, a12, a13], [a21, a22, a23]]
        else:
            return [[0, 0, -mat[0][2]], [0, 0, -mat[1][2]]]

    def getGlobalTransform(self, node):
        parent = node.getparent()
        myTrans = Transform(node.get('transform')).matrix
        if myTrans:
            if parent is not None:
                parentTrans = self.getGlobalTransform(parent)
                if parentTrans:
                    return Transform(parentTrans) * Transform(myTrans)
                else:
                    return myTrans
        else:
            if parent is not None:
                return self.getGlobalTransform(parent)
            else:
                return None

    def checkImagePath(self, node):
        """Embed the data of the selected Image Tag element"""
        xlink = node.get('xlink:href')
        if xlink and xlink[:5] == 'data:':
            # No need, data alread embedded
            return

        url = urllib.urlparse(xlink)
        href = urllib.url2pathname(url.path)

        # Primary location always the filename itself.
        path = self.absolute_href(href or '')

        # Backup directory where we can find the image
        if not os.path.isfile(path):
            path = node.get('sodipodi:absref', path)

        if not os.path.isfile(path):
            inkex.errormsg('File not found "{}". Unable to embed image.').format(path)
            return

        if (os.path.isfile(path)):
            return path

    def effect(self):
        # Check that elements have been selected
        if len(self.options.ids) == 0:
            inkex.errormsg("Please select objects!")
            return

        # Drawing styles
        linestyle = {
            'stroke': '#000000',
            'stroke-width': str(self.svg.unittouu('1px')),
            'fill': 'none'
        }

        facestyle = {
            'stroke': '#000000',
            'stroke-width':'0px',# str(self.svg.unittouu('1px')),
            'fill': 'none'
        }

        # Handle the transformation of the current group
        parentGroup = (self.svg.selected[self.options.ids[0]]).getparent()

        svg = self.document.getroot()
        image_element = svg.find('.//{http://www.w3.org/2000/svg}image')
        if image_element is None:
            inkex.utils.debug("No image found")
            exit(1)
        self.path = self.checkImagePath(image_element)  # This also ensures the file exists
        if self.path is None:  # check if image is embedded or linked
            image_string = image_element.get('{http://www.w3.org/1999/xlink}href')
            # find comma position
            i = 0
            while i < 40:
                if image_string[i] == ',':
                    break
                i = i + 1
            img = Image.open(BytesIO(base64.b64decode(image_string[i + 1:len(image_string)])))
        else:
            img = Image.open(self.path)

        extrinsic_image_width=float(image_element.get('width'))
        extrinsic_image_height=float(image_element.get('height'))        
        (width, height) = img.size
        trans = self.getGlobalTransform(parentGroup)
        invtrans = None
        if trans:
            invtrans = self.invertTransform(trans)

        # Recovery of the selected objects
        pts = []
        nodes = []
        seeds = []

        for id in self.options.ids:
            node = self.svg.selected[id]
            nodes.append(node)
            if(node.tag=="{http://www.w3.org/2000/svg}path"):#If it is path
                # Get vertex coordinates of path
                points = CubicSuperPath(node.get('d'))
                for p in points[0]:
                    pt=[p[1][0],p[1][1]]
                    if trans:
                        Transform(trans).apply_to_point(pt)
                    pts.append(Point(pt[0], pt[1]))
                    seeds.append(Point(p[1][0], p[1][1]))
            else: # For other shapes
                bbox = node.bounding_box()
                if bbox:
                    cx = 0.5 * (bbox.left + bbox.top)
                    cy = 0.5 * (bbox.top + bbox.bottom)
                    pt = [cx, cy]
                    if trans:
                        Transform(trans).apply_to_point(pt)
                    pts.append(Point(pt[0], pt[1]))
                    seeds.append(Point(cx, cy))
        pts.sort()
        seeds.sort()

        # In Creation of groups to store the result
        # Delaunay
        groupDelaunay = etree.SubElement(parentGroup, inkex.addNS('g', 'svg'))
        groupDelaunay.set(inkex.addNS('label', 'inkscape'), 'Delaunay')

        scale_x=float(extrinsic_image_width)/float(width)
        scale_y=float(extrinsic_image_height)/float(height)
        # Voronoi diagram generation

        triangles = voronoi.computeDelaunayTriangulation(seeds)
        for triangle in triangles:
            p1 = seeds[triangle[0]]
            p2 = seeds[triangle[1]]
            p3 = seeds[triangle[2]]
            cmds = [['M', [p1.x, p1.y]],
                    ['L', [p2.x, p2.y]],
                    ['L', [p3.x, p3.y]],
                    ['Z', []]]
            path = etree.Element(inkex.addNS('path', 'svg'))
            path.set('d', str(Path(cmds)))
            middleX=(p1.x+p2.x+p3.x)/3.0
            middleY=(p1.y+p2.y+p3.y)/3.0
            if width>middleX and height>middleY and middleX>=0 and middleY>=0:
                pixelColor = img.getpixel((middleX,middleY))
                facestyle["fill"]=str(inkex.Color((pixelColor[0], pixelColor[1], pixelColor[2])))
            else:
                facestyle["fill"]="black"
            path.set('style', str(inkex.Style(facestyle)))
            groupDelaunay.append(path)

if __name__ == '__main__':
    LowPoly2().run()
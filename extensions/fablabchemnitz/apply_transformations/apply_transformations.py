#!/usr/bin/env python3
#
# License: GPL2
# Copyright Mark "Klowner" Riedesel
# https://github.com/Klowner/inkscape-applytransforms
#
import copy
import math
from lxml import etree
import re
import inkex
from inkex.paths import CubicSuperPath, Path
from inkex.transforms import Transform
from inkex.styles import Style

NULL_TRANSFORM = Transform([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])


class ApplyTransformations(inkex.EffectExtension):

    def effect(self):
        if self.svg.selected:
            for id, shape in self.svg.selected.items():
                self.recursiveFuseTransform(shape)
        else:
            self.recursiveFuseTransform(self.document.getroot())

    @staticmethod
    def objectToPath(element):
        if element.tag == inkex.addNS('g', 'svg'):
            return element

        if element.tag == inkex.addNS('path', 'svg') or element.tag == 'path':
            for attName in element.attrib.keys():
                if ("sodipodi" in attName) or ("inkscape" in attName):
                    del element.attrib[attName]
            return element

        return element

    def scaleStrokeWidth(self, element, transf):
        if 'style' in element.attrib:
            style = element.attrib.get('style')
            style = dict(Style.parse_str(style))
            update = False

            if 'stroke-width' in style:
                try:
                    stroke_width = self.svg.unittouu(style.get('stroke-width')) / self.svg.unittouu("1px")
                    stroke_width *= math.sqrt(abs(transf.a * transf.d - transf.b * transf.c))
                    style['stroke-width'] = str(stroke_width)
                    update = True
                except AttributeError as e:
                    pass

            if update:
                element.attrib['style'] = Style(style).to_str()
        if 'stroke-width' in element.attrib:
            style = element.attrib.get('style')
            style = dict(Style.parse_str(style))
            update = False

            try:
                stroke_width = self.svg.unittouu(element.attrib.get('stroke-width')) / self.svg.unittouu("1px")
                stroke_width *= math.sqrt(abs(transf.a * transf.d - transf.b * transf.c))
                element.attrib['stroke-width'] = str(stroke_width)
                update = True
            except AttributeError as e:
                pass

    def transformRectangle(self, node, transf: Transform):
        x = float(node.get('x', '0'))
        y = float(node.get('y', '0'))
        width = float(node.get('width', '0'))
        height = float(node.get('height', '0'))
        rx = float(node.get('rx', '0'))
        ry = float(node.get('ry', '0'))

        # Extract translation, scaling and rotation
        a, b, c, d = transf.a, transf.b, transf.c, transf.d
        tx, ty = transf.e, transf.f
        sx = math.sqrt(a**2 + c**2)
        sy = math.sqrt(b**2 + d**2)
        angle = math.degrees(math.atan2(b, a))

        # Calculate the center of the rectangle
        cx = x + width / 2
        cy = y + height / 2

        # Apply the transformation to the center point
        new_cx, new_cy = transf.apply_to_point((cx, cy))
        new_x = new_cx - (width * sx) / 2
        new_y = new_cy - (height * sy) / 2

        # Update rectangle attributes
        node.set('x', str(new_x))
        node.set('y', str(new_y))
        node.set('width', str(width * sx))
        node.set('height', str(height * sy))

        # Apply scale to rx and ry if they exist
        if rx > 0:
            node.set('rx', str(rx * sx))
        if ry > 0:
            node.set('ry', str(ry * sy))

        # Add rotation if it exists
        if abs(angle) > 1e-6:
            tr = Transform(f"rotate({angle:.6f},{new_cx:.6f},{new_cy:.6f})")
            node.set('transform',tr)

    def recursiveFuseTransform(self, element, transf=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]):

        transf = Transform(transf) @ Transform(element.get("transform", None)) #a, b, c, d = linear transformations / e, f = translations

        if 'transform' in element.attrib:
            del element.attrib['transform']

        element = ApplyTransformations.objectToPath(element)

        if transf == NULL_TRANSFORM:
            # Don't do anything if there is effectively no transform applied
            # reduces alerts for unsupported elements
            pass
        elif 'd' in element.attrib:
            d = element.get('d')
            p = CubicSuperPath(d)
            p = Path(p).to_absolute().transform(transf, True)
            element.set('d', str(Path(CubicSuperPath(p).to_path())))

            self.scaleStrokeWidth(element, transf)

        elif element.tag in [inkex.addNS('polygon', 'svg'),
                          inkex.addNS('polyline', 'svg')]:
            points = element.get('points')
            points = points.strip().split(' ')
            for k, p in enumerate(points):
                if ',' in p:
                    p = p.split(',')
                    p = [float(p[0]), float(p[1])]
                    p = transf.apply_to_point(p)
                    p = [str(p[0]), str(p[1])]
                    p = ','.join(p)
                    points[k] = p
            points = ' '.join(points)
            element.set('points', points)

            self.scaleStrokeWidth(element, transf)

        elif element.tag in [inkex.addNS("ellipse", "svg"), inkex.addNS("circle", "svg")]:

            def isequal(a, b):
                return abs(a - b) <= transf.absolute_tolerance

            if element.TAG == "ellipse":
                rx = float(element.get("rx"))
                ry = float(element.get("ry"))
            else:
                rx = float(element.get("r"))
                ry = rx

            cx = float(element.get("cx"))
            cy = float(element.get("cy"))
            sqxy1 = (cx - rx, cy - ry)
            sqxy2 = (cx + rx, cy - ry)
            sqxy3 = (cx + rx, cy + ry)
            newxy1 = transf.apply_to_point(sqxy1)
            newxy2 = transf.apply_to_point(sqxy2)
            newxy3 = transf.apply_to_point(sqxy3)

            element.set("cx", (newxy1[0] + newxy3[0]) / 2)
            element.set("cy", (newxy1[1] + newxy3[1]) / 2)
            edgex = math.sqrt(
                abs(newxy1[0] - newxy2[0]) ** 2 + abs(newxy1[1] - newxy2[1]) ** 2
            )
            edgey = math.sqrt(
                abs(newxy2[0] - newxy3[0]) ** 2 + abs(newxy2[1] - newxy3[1]) ** 2
            )

            if not isequal(edgex, edgey) and (
                element.TAG == "circle"
                or not isequal(newxy2[0], newxy3[0])
                or not isequal(newxy1[1], newxy2[1])
            ):
                inkex.utils.errormsg(f"Warning: Shape {node.TAG} ({node.get('id')}) is approximate only, try Object to path first for better results")

            if element.TAG == "ellipse":
                element.set("rx", edgex / 2)
                element.set("ry", edgey / 2)
            else:
                element.set("r", edgex / 2)

        # this is unstable at the moment
        elif element.tag == inkex.addNS("use", "svg"):
            href = None
            old_href_key = '{http://www.w3.org/1999/xlink}href'
            new_href_key = 'href'
            if element.attrib.has_key(old_href_key) is True: # {http://www.w3.org/1999/xlink}href (which gets displayed as 'xlink:href') attribute is deprecated. the newer attribute is just 'href'
                href = element.attrib.get(old_href_key)
                #element.attrib.pop(old_href_key)
            if element.attrib.has_key(new_href_key) is True:
                href = element.attrib.get(new_href_key) #we might overwrite the previous deprecated xlink:href but it's okay
                #element.attrib.pop(new_href_key)

            #get the linked object from href attribute
            linkedObject = self.document.getroot().xpath("//*[@id = '%s']" % href.lstrip('#')) #we must remove hashtag symbol
            linkedObjectCopy = copy.copy(linkedObject[0])
            objectType = linkedObject[0].tag
            
            if objectType == inkex.addNS("image", "svg"):
                mask = None #image might have an alpha channel
                new_mask_id = self.svg.get_unique_id("mask")
                newMask = None
                if element.attrib.has_key('mask') is True:
                    mask = element.attrib.get('mask')
                    #element.attrib.pop('mask')

                #get the linked mask from mask attribute. We remove the old and create a new
                if mask is not None:
                    linkedMask = self.document.getroot().xpath("//*[@id = '%s']" % mask.lstrip('url(#').rstrip(')')) #we must remove hashtag symbol
                    linkedMask[0].delete()
                    maskAttributes = {'id': new_mask_id}
                    newMask = etree.SubElement(self.document.getroot(), inkex.addNS('mask', 'svg'), maskAttributes)
            
                width = float(linkedObjectCopy.get('width')) * transf.a
                height = float(linkedObjectCopy.get('height')) * transf.d
                linkedObjectCopy.set('width', '{:1.6f}'.format(width))
                linkedObjectCopy.set('height', '{:1.6f}'.format(height))
                linkedObjectCopy.set('x', '{:1.6f}'.format(transf.e))
                linkedObjectCopy.set('y', '{:1.6f}'.format(transf.f))
                if newMask is not None:
                    linkedObjectCopy.set('mask', 'url(#' + new_mask_id + ')')
                    maskRectAttributes = {'x': '{:1.6f}'.format(transf.e), 'y': '{:1.6f}'.format(transf.f), 'width': '{:1.6f}'.format(width), 'height': '{:1.6f}'.format(height), 'style':'fill:#ffffff;'}
                    maskRect = etree.SubElement(newMask, inkex.addNS('rect', 'svg'), maskRectAttributes)
                self.document.getroot().append(linkedObjectCopy) #for each svg:use we append a copy to the document root
                element.delete() #then we remove the use object
            else:
                #self.recursiveFuseTransform(linkedObjectCopy, transf)
                self.recursiveFuseTransform(element.unlink(), transf)

        elif element.tag == inkex.addNS('rect', 'svg'):
            self.transformRectangle(element, transf)
            self.scaleStrokeWidth(element, transf)

        elif element.tag in [inkex.addNS('text', 'svg'),
                          inkex.addNS('image', 'svg'),
                          inkex.addNS('use', 'svg')]:

            element.attrib['transform'] = str(transf)
            inkex.utils.errormsg(f"Shape {element.TAG} ({element.get('id')}) not yet supported. Not all transforms will be applied. Try Object to path first")
        else:
            # e.g. <g style="...">
            self.scaleStrokeWidth(element, transf)

        for child in element.getchildren():
            self.recursiveFuseTransform(child, transf)

if __name__ == '__main__':
    ApplyTransformations().run()
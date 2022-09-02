#!/usr/bin/env python3

import gettext
import inkex
from math import floor
from cutcraft.core import Point, Rectangle
from lxml import etree

#TODOS
'''
since InkScape 1.0 / Python 3 adjustments are required to fix "TypeError: '<' not supported between instances of 'Pier' and 'Pier'". A __lt__ method has to be implemented
"for this reasion items = sorted([(p[0].area(),p[0]) for p in shape.parts], reverse=True)" was commented out
'''

class CutCraftNode(object):
    def __init__(self, rect):
        self.children = []
        self.rectangle = rect
        self.part = None

    def insert(self, part, shape):
        if len(self.children)>0:
            node = self.children[0].insert(part, shape)
            if node is not None:
                return node
            else:
                return self.children[1].insert(part, shape)

        if self.part is not None:
            return None

        pwidth, pheight = part.bbox().expanded().size()
        nwidth, nheight = self.rectangle.expanded().size()

        if pwidth>nwidth or pheight>nheight:
            # Too small.
            return None
        if pwidth==nwidth and pheight==nheight:
            # This node fits.
            self.part = part
            return self

        nleft, ntop = self.rectangle.expanded().topleft.tup()
        nright, nbottom = self.rectangle.expanded().bottomright.tup()

        if nwidth - pwidth > nheight - pheight:
            r1 = Rectangle(Point(nleft, ntop),
                           Point(nleft+pwidth, nbottom))
            r2 = Rectangle(Point(nleft+pwidth+1.0, ntop),
                           Point(nright, nbottom))
        else:
            r1 = Rectangle(Point(nleft, ntop),
                           Point(nright, ntop+pheight))
            r2 = Rectangle(Point(nleft, ntop+pheight+1.0),
                           Point(nright, nbottom))

        self.children = [CutCraftNode(r1), CutCraftNode(r2)]

        return self.children[0].insert(part, shape)

class CutCraftShape(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--active-tab", default="Options", help="The tab selected when OK was pressed")
        pars.add_argument("--unit", default="mm", help="unit of measure for circular pitch and center diameter")
        pars.add_argument("--thickness", type=float, default=20.0, help="Material Thickness")
        pars.add_argument("--kerf", type=float, default=20.0, help="Laser Cutter Kerf")
        pars.add_argument("--linethickness", default="1px", help="Line Thickness")

    def effect(self):
        self.unit = self.options.unit
        self.thickness = self.svg.unittouu( str(self.options.thickness) + self.unit)
        self.kerf = self.svg.unittouu( str(self.options.kerf) + self.unit)
        self.linethickness = self.svg.unittouu(self.options.linethickness)

        svg = self.document.getroot()
        self.docwidth = self.svg.unittouu(svg.get('width'))
        self.docheight = self.svg.unittouu(svg.get('height'))

        self.parent=self.svg.get_current_layer()

        layer = etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), 'newlayer')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')

    def _debug(self, string):
        inkex.debug( gettext.gettext(str(string)) )

    def _error(self, string):
        inkex.errormsg( gettext.gettext(str(string)) )

    def pack(self, shape):
        # Pack the individual parts onto the current canvas.
        line_style = { 'stroke': '#000000',
                       'stroke-width': str(self.linethickness),
                       'fill': 'none' }

        #items = sorted([(p[0].area(),p[0]) for p in shape.parts], reverse=True)
        items = [(p[0].area(),p[0]) for p in shape.parts]
        #for p in shape.parts:
        #    inkex.utils.debug(p[0])
		
        rootnode = CutCraftNode(Rectangle(Point(0.0, 0.0), Point(floor(self.docwidth), floor(self.docheight))))

        for i, (_, part) in enumerate(items):
            node = rootnode.insert(part, self)
            if node is None:
                self._error("ERROR: Cannot fit parts onto canvas.\n" +
                            "Try a larger canvas and then manually arrange if required.")
                exit()

            bbox = part.bbox().expanded()
            part += -bbox.topleft
            part += node.rectangle.topleft

            line_attribs = { 'style' : str(inkex.Style(line_style)),
                            inkex.addNS('label','inkscape') : 'Test ' + str(i),
                            'd' : part.svg() }
            _ = etree.SubElement(self.parent, inkex.addNS('path','svg'), line_attribs)
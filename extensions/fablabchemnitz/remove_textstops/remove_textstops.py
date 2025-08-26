#!/usr/bin/env python3

"""
Extension for Inkscape 1.4.2
 
What it does: it removes text stops from tspan elements to fix imported text elements from PDF.
If the selection is empty, the whole doc will be parsed

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 12.08.2025
License: GNU GPL v3
"""

import inkex
import os
import sys
from lxml import etree

class RemoveTextStops(inkex.EffectExtension):
    
    def adjust(self, element):
        if element.tag == inkex.addNS('tspan','svg'):
            if element.attrib.has_key('dx'):
                del element.attrib['dx']
            
            # this usually destroys proper line distance if text goes on more than 1 line
            # y attributes are stored in text attribute. We do not need it again in tspan
            # (it will be automatically calculated if missing)
            # We must keep x attribute, because it behaves DIFFERENT!
            if element.attrib.has_key('y'):
                del element.attrib['y']

    def parse(self, element):
        self.adjust(element)
        children = element.getchildren()
        if children is not None:
            for child in children:
                self.adjust(element)
                self.parse(child)

    def effect(self):
        elements = self.svg.selection.values()
        if len(elements) > 0:
            for element in elements:
                self.parse(element)
        else:
            for element in self.document.getroot().iter(tag=etree.Element):
                self.parse(element)

if __name__ == '__main__':
    RemoveTextStops().run()

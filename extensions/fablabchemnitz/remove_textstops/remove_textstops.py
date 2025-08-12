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
    
    def parse(self, element):
        if element.tag == inkex.addNS('tspan','svg'):
            if element.attrib.has_key('dx'):
                del element.attrib['dx']

    def effect(self):

        elements = self.svg.selection.values()
        if len(elements) == 0:
            for element in elements:
                self.parse(element)
        else:
            for element in self.document.getroot().iter(tag=etree.Element):
                self.parse(element)

if __name__ == '__main__':
    RemoveTextStops().run()
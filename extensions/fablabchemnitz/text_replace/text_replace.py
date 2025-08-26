#!/usr/bin/env python3

"""
Extension for Inkscape 1.4.2
 
To replace text content of selected elements with ease.

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 26.08.2025
License: GNU GPL v3
"""

import inkex
import os
import sys
from lxml import etree

class ReplaceText(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--replacewith", default='lorem ipsum', help="New content to insert")
        pars.add_argument("--tspan_merge", default=True, type=inkex.Boolean, help="Merge tspan elements")

    def adjust(self, element):
        if element.tag == inkex.addNS('tspan','svg'):
            element.text = self.options.replacewith

    def mergeTspans(self, element):
        tspans = []
        merged_text = ""
        if element.tag == inkex.addNS('text','svg'):
            children = element.getchildren()
            if children is not None:
                for child in children:
                    if child.tag == inkex.addNS('tspan','svg'):
                        tspans.append(child)
        for tspan in tspans:
            merged_text = "{} {}".format(merged_text, tspan.text)
        if len (tspans) > 0:
            tspans[0].text = merged_text
            for k in range(1, len(tspans)):
                tspans[k].getparent().remove(tspans[k])

    def parse(self, element):
        if self.options.tspan_merge is True:
            self.mergeTspans(element)
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
    ReplaceText().run()
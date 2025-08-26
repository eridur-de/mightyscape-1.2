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

    def parse(self, element):
        if element.tag == inkex.addNS('tspan','svg'):
            element.text = self.options.replacewith
        children = element.getchildren()
        if children is not None:
            for child in children:
                if element.tag == inkex.addNS('tspan','svg'):
                    element.text = self.options.replacewith
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
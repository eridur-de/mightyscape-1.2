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
import re

class ReplaceText(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--replace", default=True, type=inkex.Boolean, help="Enable replacement")
        pars.add_argument("--replacewith", default='lorem ipsum', help="New content to insert")
        pars.add_argument("--tspan_merge", default=True, type=inkex.Boolean, help="Merge tspan elements")
        pars.add_argument("--clean", default=True, type=inkex.Boolean, help="Trim whitespaces")

    def replace(self, element):
        if element.tag == inkex.addNS('tspan','svg'):
            element.text = self.options.replacewith

    def clean(self, element):
        string = str(element.text).strip()
        string = re.compile(r"(?a:\s+)").sub(" ", string)
        string = re.compile(r"(?a:^\s+|\s+$)").sub("", string)
        if string == "None":
            string = ""
        element.text = string

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
            merge = tspan.text
            if merge is None:
                merge = ""
            merged_text = "{} {}".format(merged_text, merge)
        if len (tspans) > 0:
            tspans[0].text = merged_text
            for k in range(1, len(tspans)):
                tspans[k].getparent().remove(tspans[k])

    def work(self, element):
        if self.options.tspan_merge is True:
            self.mergeTspans(element)
        if self.options.replace is True:    
            self.replace(element)
        if self.options.clean is True:    
            self.clean(element)

    def parse(self, element):
        self.work(element)
        children = element.getchildren()
        if children is not None:
            for child in children:
                self.work(element)
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
#!/usr/bin/env python3

import inkex
from inkex import Style
import re
import random

class JitterGradients(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('-j', '--jitter_amount', type=int, default=10, help='Relative to distance between gradient nodes')

    def getUrlFromString(self, text):
        pattern = re.compile(r"url\(#([a-zA-Z0-9_-]+)\)")
        result = re.search(pattern, text)
        if (result):
            return result.group(1)
        else:
            return 0;

    def getFill(self, element):
        if(element.get('fill') and self.getUrlFromString(element.get('fill'))):
            return self.getUrlFromString(element.get('fill'))
        elif (element.get('style') and Style(element.get('style'))['fill'] and self.getUrlFromString(Style(element.get('style'))['fill'])):
            return self.getUrlFromString(Style(element.get('style'))['fill'])
        else:
            return None

    def getGradientFromId(self, elementId):
        element = self.svg.getElementById(elementId)
        if (element is not None and element.tag.find("linearGradient") >= 0):
            return element
        else:
            return None

    def effect(self):
        option = self.options.jitter_amount
        self._main_function(option)

    def _main_function(self, amount):
        for element in self.svg.selected.values():
            fillId = self.getFill(element)
            if (fillId is None): 
                continue
              
            gradient = self.getGradientFromId(fillId)
            if (gradient is None): 
                continue
          
            x1 = self.svg.unittouu(gradient.get("x1"))
            y1 = self.svg.unittouu(gradient.get("y1"))
            x2 = self.svg.unittouu(gradient.get("x2"))
            y2 = self.svg.unittouu(gradient.get("y2"))
            
            x1 += random.uniform(-amount, amount)
            y1 += random.uniform(-amount, amount)
            x2 += random.uniform(-amount, amount)
            y2 += random.uniform(-amount, amount)
            
            gradient.set('x1', str(self.svg.uutounit(x1, self.svg.unit)) + self.svg.unit)
            gradient.set('y1', str(self.svg.uutounit(y1, self.svg.unit)) + self.svg.unit)
            gradient.set('x2', str(self.svg.uutounit(x2, self.svg.unit)) + self.svg.unit)
            gradient.set('y2', str(self.svg.uutounit(y2, self.svg.unit)) + self.svg.unit)

if __name__ == '__main__':
    JitterGradients().run()
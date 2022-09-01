#!/usr/bin/env python3
'''
Copyright (C) 2013 Matthew Dockrey  (gfish @ cyphertext.net)

Based on http://arc.id.au/GearDrawing.html by Dr A.R.Collins
And on the original gears.py by Aaron Spike and Tavmjong Bah
'''

import inkex
from math import *
from lxml import etree

from involute import *

class Gears(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--tab", default="Options", help="The tab selected when OK was pressed")
        pars.add_argument("-t", "--teeth",  type=int, default=24, help="Number of teeth")
        pars.add_argument("-p", "--pressure_angle", type=float,  default="20", help="Pressure angle")
        pars.add_argument("-y", "--size_type", type=int, default="1", help="Size type (1 = module (mm), 2 = pitch diameter (inches), 3 = diametral pitch (inches)")
        pars.add_argument("-s", "--size",  type=float, default="5", help="Size")
        pars.add_argument("-o", "--orientation", type=int, default="1", help="Gear orientation")

    def effect(self):
        Z = self.options.teeth
        phi = self.options.pressure_angle
        size_type = self.options.size_type
        size = self.options.size
        orientation = self.options.orientation

        # Convert size to module (mm) if needed
        if (size_type == 2): 
            # Pitch diameter
            size = 25.4 * size / Z
        elif (size_type == 3): 
            # Diametral pitch
            size = 25.4 / size

        m = self.svg.unittouu(str(size) + "mm")

        if (orientation == 2):
            svg = CreateInternalGear(m, Z, phi)
        else:
            svg = CreateExternalGear(m, Z, phi)

        # Insert as a new element
        gear_style = { 'stroke': '#000000',
                       'stroke-width': self.svg.unittouu(str(0.1) + "mm"),
                       'fill': 'none'
                       }
        g_attribs = {inkex.addNS('label','inkscape'): 'Gear ' + str(Z),
                     'transform': 'translate(' + str( self.svg.namedview.center[0] ) + ',' + str( self.svg.namedview.center[1] ) + ')',
                     'style' : str(inkex.Style(gear_style)),
                     'd' : svg }
        g = etree.SubElement(self.svg.get_current_layer(), inkex.addNS('path','svg'), g_attribs)

if __name__ == '__main__':
    Gears().run()
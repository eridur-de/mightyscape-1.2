#!/usr/bin/env python3

# Program allowing the addition of small grey dots in rectangles created using Inkscape.

# Thomas Guzik, thomas.guzik@laposte.net
# Leo 130 contact@avilab.fr
# Corentin Bettiol - corentin-bettiol@hotmail.fr

#  -Creative Commons License
#  -This work is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.
#  -http://creativecommons.org/licenses/by-nc-sa/4.0/

import inkex
from lxml import etree

def recup(selection, attrib):
    l = []
    for i in selection:
        selec = i
        valr = selec.get(attrib)
        l.append(valr)
    return l

def generCircle(y, x, r):
    circle = etree.Element('{http://www.w3.org/2000/svg}circle')
    circle.set('cy',str(y))
    circle.set('cx',str(x))
    circle.set('r',str(r))
    circle.set('fill','#000000')
    circle.set('stroke','#000000')
    circle.set('stroke-width','0')
    return circle

def toFloat(l):
    for i in range(len(l)):
        l[i] = float(l[i])
    return l

class FillRectangleWithCircle(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--radius', type = float, default = 3.0, help = 'Radius to enter')
        pars.add_argument('--margin', type = float, default = 10.0, help = 'Margin between the edge of the rectangles and the circles')
        pars.add_argument('--space', type = float, default = 30.0, help = 'Spacing between circles')

    def effect(self):
        # svg = self.svg.document.getroot()
        # layer = etree.SubElement(svg, 'g')
        # layer.set(inkex.addNS('label', 'inkscape'), 'Layer')
        # layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        # Should we add the circles on a different layer sheet?

        radius = self.options.radius
        margin = self.options.margin
        space =  self.options.space

        if str(list(self.svg.selected.values())[0]) == 'rect':
            selection = (self.svg.selected).values()
            
            y,x,height,width = [], [], [], []
            
            if (len(selection))>0:
                y = toFloat(recup(selection,'y'))
                x = toFloat(recup(selection,'x'))
                height = toFloat(recup(selection,'height'))
                width = toFloat(recup(selection,'width'))
            
                for i in range(len(selection)):
                    xC = x[i] + margin
                    yC = y[i] + margin
            
                    while xC < (x[i] + width[i] - margin):
                        while yC < (y[i] + height[i] - margin):
                            self.svg.get_current_layer().append(generCircle(yC,xC,radius))
                            yC += (space + radius)
            
                        xC += space + radius
                        yC = y[i] + margin
        else:
            inkex.utils.debug("No rectangle(s) have been selected.")

if __name__ == '__main__':
    FillRectangleWithCircle().run()
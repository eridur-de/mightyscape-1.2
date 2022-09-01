#!/usr/bin/env python3
'''
Mutual Cut Line
This Inkscape extension will take 2 selected line and cut them both
at their intersection point.
Only the first segment of a multi-segment line will be used.
'''
import inkex
from inkex.paths import Path
import simplepath
from math import *
from lxml import etree

def error(message):
    inkex.errormsg(message)
    exit()

class MutualCutLine(inkex.EffectExtension):

    def effect(self):
        if len(self.svg.selected.items()) != 2:
            error('Please select 2 lines before running this effect.')

        line = []
        numPaths = 0
        for id, path in self.svg.selected.items():
            if path.tag == inkex.addNS('path','svg'):
                numPaths += 1
                style = path.get('style')
                np = [style]
                p = Path(path.get('d')).to_arrays()
                for sp in p:
                    np.append([sp[1][0], sp[1][1]])
                line.append(np)
                path.getparent().remove(path) #after cutting we remove the original lines

        if numPaths != 2:
            error('Please select 2 lines before running this effect.')

        # Extract style and points for the first 2 line segments.
        astyle = line[0][0]
        bstyle = line[1][0]
        a1x = line[0][1][0]
        a1y = line[0][1][1]
        a2x = line[0][2][0]
        a2y = line[0][2][1]
        b1x = line[1][1][0]
        b1y = line[1][1][1]
        b2x = line[1][2][0]
        b2y = line[1][2][1]

        # Calculate intersection point.
        adx = a1x - a2x
        ady = a1y - a2y
        bdx = b1x - b2x
        bdy = b1y - b2y

        denom = adx * bdy - ady * bdx
        numa = (a1x * a2y - a1y * a2x)
        numb = (b1x * b2y - b1y * b2x)
        x_num = numa * bdx - numb * adx
        y_num = numa * bdy - numb * ady

        if denom == 0:
            error('Lines don\'t intersect in a single point.')
        x = x_num / denom
        y = y_num / denom

        # TODO: Verify that the 2 segments intersect.
        # Current code will connect outside the line segments.

        # Create 4 line segments from the intersection point.
        svg_path = inkex.addNS('path','svg')
        sega1 = etree.SubElement(self.svg.get_current_layer(), svg_path)
        sega1.set('d', 'M '+str(x)+','+str(y)+' L '+str(a1x)+','+str(a1y))
        sega1.set('style', astyle)

        sega2 = etree.SubElement(self.svg.get_current_layer(), svg_path)
        sega2.set('d', 'M '+str(x)+','+str(y)+' L '+str(a2x)+','+str(a2y))
        sega2.set('style', astyle)

        segb1 = etree.SubElement(self.svg.get_current_layer(), svg_path)
        segb1.set('d', 'M '+str(x)+','+str(y)+' L '+str(b1x)+','+str(b1y))
        segb1.set('style', bstyle)

        segb2 = etree.SubElement(self.svg.get_current_layer(), svg_path)
        segb2.set('d', 'M '+str(x)+','+str(y)+' L '+str(b2x)+','+str(b2y))
        segb2.set('style', bstyle)

if __name__ == '__main__':
    MutualCutLine().run()
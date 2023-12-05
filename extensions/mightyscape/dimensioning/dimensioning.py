#!/usr/bin/env python3
'''
Tool for drawing beautiful DIN-conform dimensioning arrows
(c) 2012 by Johannes B. Rutzmoser, johannes.rutzmoser (at) googlemail (dot) com

Please contact me, if you know a way how the extension module accepts mouse input; this would help to improve the tool

Add this file and the dimensioning.inx file into the following folder to get the feature run:
UNIX:
$HOME/.config/inkscape/extensions/

Mac OS X (when using the binary):
/Applications/Inkscape.app/Contents/Resources/extensions/
or
/Applications/Inkscape.app/Contents/Resources/share/inkscape/extensions

WINDOWS (Filepath may differ, depending where the program was installed):
C:\Program Files\Inkscape\share\extensions

License:
GNU GENERAL PUBLIC LICENSE

'''

import inkex
import numpy as np
import gettext
_ = gettext.gettext
from lxml import etree
from inkex import paths

def norm(a):
    return a/np.sqrt(np.dot(a, a))

def rotate(tangentvec, point):
    if tangentvec[0] == 0:
        angle = - np.pi/2
    else:
        angle = np.arctan(tangentvec[1]/tangentvec[0])
    return 'rotate(' + str(angle/np.pi*180) + ',' + str(point[0]) + ',' + str(point[1]) + ')'


class Dimensioning(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--orientation",  default='horizontal', help="The type of orientation of the dimensioning (horizontal, vertical or parallel)")
        pars.add_argument("--arrow_orientation", default='auto',  help="The type of orientation of the arrows")
        pars.add_argument("--line_scale", type=float, default=1.0,  help="Scale factor for the line thickness")
        pars.add_argument("--overlap", type=float, default=1.0, help="Overlap of the helpline over the dimensioning line")
        pars.add_argument("--distance", type=float, default=1.0, help="Distance of the helpline to the object")
        pars.add_argument("--position", type=float, default=1.0, help="position of the dimensioning line")
        pars.add_argument("--flip",  type=inkex.Boolean, default=False, help="flip side")
        pars.add_argument("--scale_factor", type=float, default=1.0, help="scale factor for the dimensioning text")
        pars.add_argument("--unit", default='px', help="The unit that should be used for the dimensioning")
        pars.add_argument("--rotate", type=inkex.Boolean,  default=True, help="Rotate the annotation?")
        pars.add_argument("--digit", type=int, default=0, help="number of digits after the point")
        pars.add_argument("--tab", default="sampling", help="The selected UI-tab when OK was pressed")
        
    def create_linestyles(self):
        '''
        Create the line styles for the drawings.
        '''

        self.helpline_style = {
                        'stroke'        : '#000000',
                        'stroke-width'  : '{}px'.format(0.5*self.options.line_scale),
                        'fill'          : 'none'
                        }
        self.dimline_style = {
                        'stroke'        : '#000000',
                        'stroke-width'  : '{}px'.format(0.75*self.options.line_scale),
                        'fill'          : 'none',
                        'marker-start'  : 'url(#ArrowDIN-start)',
                        'marker-end'    : 'url(#ArrowDIN-end)'
                        }
        self.text_style = {
                        'font-size'     : '{}px'.format(12*self.options.line_scale),
                        'font-family'   : 'Sans',
                        'font-style'    : 'normal',
                        'text-anchor'   : 'middle'
                        }
        self.helpline_attribs = {'style' : str(inkex.Style(self.helpline_style)),
                                   inkex.addNS('label', 'inkscape') : 'helpline',
                                   'd' : 'm 0,0 100,0'
                                 }
        self.text_attribs = {'style'     : str(inkex.Style(self.text_style)),
                             'x'         : '100',
                             'y'         : '100'
                             }
        self.dimline_attribs = {'style'  : str(inkex.Style(self.dimline_style)),
                               inkex.addNS('label','inkscape') : 'dimline',
                               'd' : 'm 0,0 200,0'
                               }

    def effect(self):
        # will be executed when feature is activated
        self.create_linestyles()
        self.makeGroup()
        self.getPoints()
        self.calcab()
        self.drawHelpline()
        self.drawDimension()
        self.drawText()

    def makeMarkerstyle(self, name, rotate):
        defs = self.svg.getElement('/svg:svg//svg:defs')
        if defs == None:
            defs = etree.SubElement(self.document.getroot(),inkex.addNS('defs','svg'))
        marker = etree.SubElement(defs ,inkex.addNS('marker','svg'))
        marker.set('id', name)
        marker.set('orient', 'auto')
        marker.set('refX', '0.0')
        marker.set('refY', '0.0')
        marker.set('style', 'overflow:visible')
        marker.set(inkex.addNS('stockid','inkscape'), name)

        arrow = etree.Element("path")
        # messy but works; definition of arrows in beautiful DIN-shapes:
        if name.startswith('ArrowDIN-'):
            if rotate:
                arrow.set('d', 'M 8,0 -8,2.11 -8,-2.11 z')
            else:
                arrow.set('d', 'M -8,0 8,-2.11 8,2.11 z')
        if name.startswith('ArrowDINout-'):
            if rotate:
                arrow.set('d', 'M 0,0 16,2.11 16,0.5 26,0.5 26,-0.5 16,-0.5 16,-2.11 z')
            else:
                arrow.set('d', 'M 0,0 -16,2.11 -16,0.5 -26,0.5 -26,-0.5 -16,-0.5 -16,-2.11 z')

        arrow.set('style', 'fill:#000000;stroke:none')
        marker.append(arrow)


    def makeGroup(self):
        '''puts everything of the dimensioning in a group'''
        layer = self.svg.get_current_layer()
        # Group in which the object should be put into
        grp_name = 'dimensioning'
        grp_attributes = {inkex.addNS('label', 'inkscape') :  grp_name}
        self.grp = etree.SubElement(layer, 'g', grp_attributes)

    def getPoints(self):
        self.p1 = np.array([0.,100.])
        self.p1 = np.array([100.,100.])
        # Get variables of a selected object
        for id, node in self.svg.selected.items():
            # if it is a path:
            if node.tag == inkex.addNS('path', 'svg'):
                d = node.get('d')
                p = paths.CubicSuperPath(d)
                # p has all nodes with the anchor points in a list;
                # the rule is [anchorpoint, node, anchorpoint]
                # the points are lists with x and y coordinate
                self.p1 = np.array(p[0][0][1])
                self.p2 = np.array(p[0][-1][1])


    def calcab(self):
        # get p1,p2 ordered for correct dimension direction
        # determine quadrant
        if self.p1[0] <= self.p2[0]:
            if self.p1[1] <= self.p2[1]:
                quad = 1 # p1 is left,up of p2
            else:  quad = 2 # p1 is left,down of p2
        elif self.p1[1] <= self.p2[1]:
            quad = 3 # p1 is right,up of p2
        else: quad = 4 # p1 is right,down of p2
        swap = False if quad ==1 else True
        minp = self.p2 if swap else self.p1
        maxp = self.p1 if swap else self.p2
        # distance between points
        delta = maxp - minp
        # rotation matrix
        rotateMat = np.array([[0,-1],[1,0]])
        # compute the unit vectors e1 and e2 along the cartesian coordinates of the dimension
        if self.options.orientation == 'horizontal':
            if quad == 3: self.e1 = np.array([1.0, 0.0])
            else: self.e1 = np.array([-1.0, 0.0])
        if self.options.orientation == 'vertical':
            if quad == 2:
                self.e1 = np.array([0.0, -1.0])
            else: self.e1 = np.array([0.0, 1.0])
        if self.options.orientation == 'parallel':
            self.e1 = norm(delta)
            #if quad==2 or quad==3: self.e1 *= -1
        self.e2 = np.dot(rotateMat, self.e1)
        if self.options.flip:
            self.e2 *= -1.
        # compute the points a and b, where the dimension line arrow spikes start and end
        dist = self.options.position*self.e2
        if self.options.flip:
            outpt = maxp
            delta *= -1
            if swap:
                self.a = outpt + dist
                self.b = self.a + self.e1*np.dot(self.e1,delta)
            else:
                self.b = outpt + dist
                self.a = self.b + self.e1*np.dot(self.e1,delta)
        else:
            outpt = minp
            if swap:
                self.b = outpt + dist
                self.a = self.b + self.e1*np.dot(self.e1,delta)
            else:
                self.a = outpt + dist
                self.b = self.a + self.e1*np.dot(self.e1,delta)


    def drawHelpline(self):
        # manipulate the start- and endpoints with distance and overlap
        h1_start = self.p1 + norm(self.a - self.p1)*self.options.distance
        h1_end = self.a + norm(self.a - self.p1)*self.options.overlap
        h2_start = self.p2 + norm(self.b - self.p2)*self.options.distance
        h2_end = self.b + norm(self.b - self.p2)*self.options.overlap

        # print the lines
        hline1 = etree.SubElement(self.grp, inkex.addNS('path', 'svg'), self.helpline_attribs)
        hline1.set('d', 'M %f,%f %f,%f' % (h1_start[0], h1_start[1],h1_end[0],h1_end[1],))

        hline2 = etree.SubElement(self.grp, inkex.addNS('path', 'svg'), self.helpline_attribs)
        hline2.set('d', 'M %f,%f %f,%f' % (h2_start[0], h2_start[1],h2_end[0],h2_end[1],))

    def setMarker(self, option):
        if option=='inside':
            # inside
            self.arrowlen = 6.0 * self.options.line_scale
            self.dimline_style['marker-start'] = 'url(#ArrowDIN-start)'
            self.dimline_style['marker-end'] = 'url(#ArrowDIN-end)'
            self.makeMarkerstyle('ArrowDIN-start', False)
            self.makeMarkerstyle('ArrowDIN-end', True)
        else:
            # outside
            self.arrowlen = 0
            self.dimline_style['marker-start'] = 'url(#ArrowDINout-start)'
            self.dimline_style['marker-end'] = 'url(#ArrowDINout-end)'
            self.makeMarkerstyle('ArrowDINout-start', False)
            self.makeMarkerstyle('ArrowDINout-end', True)
        self.dimline_attribs['style'] = str(inkex.Style(self.dimline_style))

    def drawDimension(self):
        # critical length, when inside snaps to outside
        critical_length = 35 * self.options.line_scale
        if self.options.arrow_orientation == 'auto':
            if np.abs(np.dot(self.e1, self.b - self.a)) > critical_length:
                self.setMarker('inside')
            else:
                self.setMarker('outside')
        else:
            self.setMarker(self.options.arrow_orientation)
        # start- and endpoint of the dimension line
        dim_start = self.a + self.arrowlen*norm(self.b - self.a)
        dim_end = self.b - self.arrowlen*norm(self.b - self.a)
        # print
        dimline = etree.SubElement(self.grp, inkex.addNS('path', 'svg'), self.dimline_attribs)
        dimline.set('d', 'M %f,%f %f,%f' % (dim_start[0], dim_start[1], dim_end[0], dim_end[1]))

    def drawText(self):
        # distance of text to the dimension line
        self.textdistance = 5.0 * self.options.line_scale
        if self.e2[1] > 0:
            textpoint = (self.a + self.b)/2 - self.e2*self.textdistance
        elif self.e2[1] == 0:
            textpoint = (self.a + self.b)/2 - np.array([1,0])*self.textdistance
        else:
            textpoint = (self.a + self.b)/2 + self.e2*self.textdistance

        value = np.abs(np.dot(self.e1, self.b - self.a)) / (self.svg.unittouu(str(self.options.scale_factor)+self.options.unit))
        string_value = str(round(value, self.options.digit))
        # chop off last characters if digit is zero or negative
        if self.options.digit <=0:
            string_value = string_value[:-2]
        text = etree.SubElement(self.grp, inkex.addNS('text', 'svg'), self.text_attribs)
        # The alternative for framing with dollars, when LATEX Math export is seeked
        # text.text = '$' + string_value + '$'
        text.text = string_value
        text.set('x', str(textpoint[0]))
        text.set('y', str(textpoint[1]))
        if self.options.rotate:
            text.set('transform', rotate(self.e1, textpoint))

if __name__ == '__main__':
    Dimensioning().run()
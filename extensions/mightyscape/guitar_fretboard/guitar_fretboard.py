#! /usr/bin/env python
'''
MIT License

Copyright (c) 2021 Christophe Grellier

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

__version__ = "0.1"

import inkex
from lxml import etree


class Fretboard:

    def __init__(self, scale=635.0):
        self.scale = scale
        self.nb_frets = 24
        self.fret_width = 2.0
        self.width_nut = 43.0
        self.width_12 = 53.0
        self.extension = 8.0

    def fret_distance_bridge(self, fret):
        return self.scale / pow(2.0, (fret / 12.0))

    def fret_distance_nut(self, fret):
        return self.scale - self.fret_distance_bridge(fret)

    def fb_lenght(self):
        return self.fret_distance_nut(self.nb_frets) + self.extension

    def fb_width_at(self, dist):
        return self.width_nut + 2.0 * (self.width_12 - self.width_nut) * dist / self.scale

    def fret_bounds(self, fret):
        distup = self.fret_distance_nut(fret) - self.fret_width / 2.0
        distdown = self.fret_distance_nut(fret) + self.fret_width / 2.0
        width_up = self.fb_width_at(distup)
        width_down = self.fb_width_at(distdown)
        return distup, distdown, width_up, width_down

    def svg_polyline(self, pts, closed=False):
        svg = ""
        for pt in pts:
            svg += "L {},{} ".format(pt[0], pt[1])
        svg = "M" + svg[1:]
        if closed:
            svg += "Z"
        return svg

    def svg_contour(self):
        lfb = self.fb_lenght()
        lowwidth = self.fb_width_at(lfb)
        pts = [(-self.width_nut / 2.0, 0),
               (self.width_nut / 2.0, 0),
               (lowwidth / 2.0, lfb),
               (-lowwidth / 2.0, lfb)]
        return self.svg_polyline(pts, True)

    def svg_h_line(self, width, y):
        pts = [(-width / 2.0, y),
               (width / 2.0, y)]
        return self.svg_polyline(pts)

    def svg_fret_centerline(self, fret):
        dist = self.fret_distance_nut(fret)
        return self.svg_h_line(self.fb_width_at(dist), dist)

    def svg_fret_contour(self, fret):
        distup, distdown, width_up, width_down = self.fret_bounds(fret)
        pts = [(-width_up / 2.0, distup),
               (width_up / 2.0, distup),
               (width_down / 2.0, distdown),
               (-width_down / 2.0, distdown)]
        return self.svg_polyline(pts, True)

    def svg_fret_end(self, fret, side=1.0):
        distup, distdown, width_up, width_down = self.fret_bounds(fret)
        return 'M {},{} C {},{} {},{} {},{} Z'.format(side * width_up / 2.0, distup,
                                                      side * width_up / 2.0 - side * self.fret_width / 2.0, distup,
                                                      side * width_down / 2.0 - side * self.fret_width / 2.0, distdown,
                                                      side * width_down / 2.0, distdown)

    def svg_fret_cross(self, fret):
        upperfretpos = self.fret_distance_nut(fret - 1)
        lowerfretpos = self.fret_distance_nut(fret)
        markerpos = upperfretpos + (lowerfretpos - upperfretpos) / 2.0
        hline_cross_path = 'M {},{} L {},{}'.format(-self.fb_width_at(markerpos) / 2.0, markerpos,
                                                    self.fb_width_at(markerpos) / 2.0, markerpos)
        vline_cross_path = ' M {},{} L {},{}'.format(0, upperfretpos,
                                                     0, lowerfretpos)
        return hline_cross_path, vline_cross_path


class GuitarFretboard(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("-s", "--scale", default="25in", help="The fingerboard scalelenght")
        pars.add_argument("-w", "--lnut", default="43mm", help="The fingerboard width at nut")
        pars.add_argument("-x", "--l12", default="53mm", help="The fingerboard width at fret 12")
        pars.add_argument("-n", "--numfret", type=int, default=22, help="Number of frets")
        pars.add_argument("-e", "--fbext", default="8mm", help="Lenght of the fingerboard extension below last fret")
        pars.add_argument("-f", "--fretwidth", default="2mm", help="Fret Width")

    def effect(self):
        svg = self.document.getroot()

        # ************ Layer 1 Definition ***************

        layer = etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), 'Fretboard')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')

        # ************ Layer 2 Definition ***************

        layer2 = etree.SubElement(svg, 'g')
        layer2.set(inkex.addNS('label', 'inkscape'), 'Fret positions')
        layer2.set(inkex.addNS('groupmode', 'inkscape'), 'layer')

        # ************ Group Definitions ***************

        fb_id = svg.get_unique_id('fretboard')
        self.box = g = etree.SubElement(layer, 'g', {'id': fb_id})
        fp_id = svg.get_unique_id('fret-positions')
        self.box2 = g3 = etree.SubElement(layer2, 'g', {'id': fp_id})
        fm_id = svg.get_unique_id('fretmarkers')
        self.box4 = g4 = etree.SubElement(layer2, 'g', {'id': fm_id})

        # ************ Style Definition ***************

        fill_black_style = str(inkex.Style({'stroke': 'none', 'fill': '#222222'}))
        fill_grey_style = str(inkex.Style({'stroke': 'none', 'fill': '#aaaaaa'}))
        fill_lightgrey_style = str(inkex.Style({'stroke': 'none', 'fill': '#dddddd'}))
        stroke_black_style = str(inkex.Style({'stroke': '#000000', 'fill': 'none'}))
        stroke_red_style = str(inkex.Style({'stroke': '#ff0000', 'fill': 'none'}))
        text_style = "font-family:DejaVu Sans;font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;fill:#000000;fill-opacity:1;stroke:none;font-size:10px;"
        text_attributes = {'x': '12mm', 'y': '10mm', inkex.addNS("space", "xml"): "preserve", 'style': text_style}

        text = "Scalelenght : {}\n".format(self.options.scale)
        text += "Nut width : {}\n".format(self.options.lnut)
        text += "12th fret width : {}\n".format(self.options.l12)
        text += "Number of frets : {}\n".format(self.options.numfret)
        text += "Extension below last fret : {}\n".format(self.options.fbext)
        text += "Fret width : {}".format(self.options.fretwidth)

        fretboard = Fretboard(svg.unittouu(str(self.options.scale)))
        fretboard.width_nut = svg.unittouu(str(self.options.lnut))
        fretboard.width_12 = svg.unittouu(str(self.options.l12))
        fretboard.extension = svg.unittouu(str(self.options.fbext))
        fretboard.nb_frets = self.options.numfret
        fretboard.fret_width = svg.unittouu(str(self.options.fretwidth))

        fb_body_path = fretboard.svg_contour()
        nut_line = fretboard.svg_fret_centerline(0)
        bridge_line = fretboard.svg_h_line(fretboard.fb_width_at(fretboard.scale), fretboard.scale)

        # ************ Apply style to objects ***************

        fb_body_object = {'style': fill_black_style, 'id': fb_id + '-shape', 'd': fb_body_path}
        nut_line_object = {'style': stroke_black_style, 'id': 'fret-0', 'd': nut_line}
        bridge_line_object = {'style': stroke_black_style, 'id': 'bridge-line', 'd': bridge_line}

        # ************ Add objects to groups ***************

        etree.SubElement(g, inkex.addNS('path', 'svg'), fb_body_object)
        etree.SubElement(g, inkex.addNS('path', 'svg'), bridge_line_object)
        etree.SubElement(g3, inkex.addNS('path', 'svg'), bridge_line_object)
        etree.SubElement(g3, inkex.addNS('path', 'svg'), nut_line_object)

        t = etree.SubElement(layer2, inkex.addNS('text', 'svg'), text_attributes)

        text = str(text).split("\n")
        y = 100
        for s in text:
            span = etree.SubElement(t, inkex.addNS('tspan', 'svg'),
                                    {'x': '12', 'y': str(y),
                                     inkex.addNS("role", "sodipodi"): "line", })
            y += 24
            span.text = str(s)

        for index in range(1, self.options.numfret + 1):

            linefret_path = fretboard.svg_fret_centerline(index)
            fretpos_id = svg.get_unique_id('fretpos-' + str(index))
            linefret_atts = {'style': stroke_black_style, 'id': fretpos_id, 'd': linefret_path}
            etree.SubElement(g3, inkex.addNS('path', 'svg'), linefret_atts)

            line_path = fretboard.svg_fret_contour(index)
            curve_path = fretboard.svg_fret_end(index, 1.0)
            curve_path2 = fretboard.svg_fret_end(index, -1.0)
            fret_id = svg.get_unique_id('fret-' + str(index))
            self.fret = g2 = etree.SubElement(self.box, 'g', {'id': fret_id})

            fretbody_id = svg.get_unique_id('fret-' + str(index) + '-body')
            fretend_id1 = svg.get_unique_id('fret-' + str(index) + '-end1')
            fretend_id2 = svg.get_unique_id('fret-' + str(index) + '-end2')

            line_atts = {'style': fill_grey_style, 'id': fretbody_id, 'd': line_path}
            curve_atts = {'style': fill_lightgrey_style, 'id': fretend_id1, 'd': curve_path}
            curve2_atts = {'style': fill_lightgrey_style, 'id': fretend_id2, 'd': curve_path2}

            etree.SubElement(g2, inkex.addNS('path', 'svg'), line_atts)
            etree.SubElement(g2, inkex.addNS('path', 'svg'), curve_atts)
            etree.SubElement(g2, inkex.addNS('path', 'svg'), curve2_atts)

            # ************ Add inlay cross ***************
            val = index % 12
            if val in [0, 3, 5, 7, 9]:
                hline_cross_path, vline_cross_path = fretboard.svg_fret_cross(index)
                fretpos_id = svg.get_unique_id('marker-cross-' + str(index))
                hline_atts = {'style': stroke_red_style, 'id': fretpos_id, 'd': hline_cross_path}
                vline_atts = {'style': stroke_red_style, 'id': fretpos_id, 'd': vline_cross_path}
                etree.SubElement(g4, inkex.addNS('path', 'svg'), hline_atts)
                etree.SubElement(g4, inkex.addNS('path', 'svg'), vline_atts)


if __name__ == '__main__':
    GuitarFretboard().run()
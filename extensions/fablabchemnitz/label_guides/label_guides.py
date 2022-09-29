#!/usr/bin/env python3
'''
Label Guides Creator

Copyright (C) 2018 John Beard - john.j.beard **guesswhat** gmail.com

## Simple Extension to draw guides and outlines for common paper labels

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 2 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''

import inkex
from lxml import etree

# Colours to use for the guides
GUIDE_COLOURS = {
        'edge': '#00A000',
        'centre': '#A00000',
        'inset': '#0000A0'
}

# Preset list
# Regular grids defined as:
#       'reg', unit, page_szie, l marg, t marg, X size, Y size,
#       X pitch, Y pitch, Number across, Number down, shapes
PRESETS = {
    # Rounded rectangular labels in grid layout
    'L7167':        ['reg', 'mm', 'a4', 5.2, 3.95, 199.6, 289.1, 199.6, 289.1, 1, 1, 'rrect'],
    'L7168':        ['reg', 'mm', 'a4', 5.2, 5, 199.6, 143.5, 199.6, 143.5, 1, 2, 'rrect'],
    'L7169':        ['reg', 'mm', 'a4', 4.65, 9.5, 99.1, 139, 101.6, 139, 2, 2, 'rrect'],
    'L7701':        ['reg', 'mm', 'a4', 9, 24.5, 192, 62, 192, 62, 1, 4, 'rrect'],
    'L7171':        ['reg', 'mm', 'a4', 5, 28.5, 200, 60, 200, 60, 1, 4, 'rrect'],
    'L7166':        ['reg', 'mm', 'a4', 4.65, 8.85, 99.1, 93.1, 101.6, 93.1, 2, 3, 'rrect'],
    'L4760':        ['reg', 'mm', 'a4', 9, 12, 192, 39, 192, 39, 1, 7, 'rrect'],
    'L7165':        ['reg', 'mm', 'a4', 4.65, 13.1, 99.1, 67.7, 101.6, 67.7, 2, 4, 'rrect'],
    'L7664':        ['reg', 'mm', 'a4', 18, 4.9, 70, 71.8, 104, 71.8, 2, 4, 'rrect'],
    'L7667':        ['reg', 'mm', 'a4', 38.5, 15.3, 133, 29.6, 133, 29.6, 1, 9, 'rrect'],
    'L7173':        ['reg', 'mm', 'a4', 4.65, 6, 99.1, 57, 101.6, 57, 2, 5, 'rrect'],
    'J5103':        ['reg', 'mm', 'a4', 4.75, 13.5, 38.1, 135, 40.6, 135, 5, 2, 'rrect'],
    'L7666':        ['reg', 'mm', 'a4', 23, 18.5, 70, 52, 94, 52, 2, 5, 'rrect'],
    'L7783':        ['reg', 'mm', 'a4', 7.85, 21.75, 95.8, 50.7, 98.5, 50.7, 2, 5, 'rrect'],
    'L7164':        ['reg', 'mm', 'a4', 7.25, 4.5, 63.5, 72, 66, 72, 3, 4, 'rrect'],
    'L7671':        ['reg', 'mm', 'a4', 27.55, 9.3, 76.2, 46.4, 78.7, 46.4, 2, 6, 'rrect'],
    'L7177':        ['reg', 'mm', 'a4', 4.65, 21.6, 99.1, 42.3, 101.6, 42.3, 2, 6, 'rrect'],
    'L7163':        ['reg', 'mm', 'a4', 4.65, 15.15, 99.1, 38.1, 101.6, 38.1, 2, 7, 'rrect'],
    'L7668':        ['reg', 'mm', 'a4', 13.5, 21.25, 59, 50.9, 62, 50.9, 3, 5, 'rrect'],
    'L7162':        ['reg', 'mm', 'a4', 4.65, 12.9, 99.1, 33.9, 101.6, 33.9, 2, 8, 'rrect'],
    'L7674':        ['reg', 'mm', 'a4', 32.5, 12.5, 145, 17, 145, 17, 1, 16, 'rrect'],
    'L7161':        ['reg', 'mm', 'a4', 7.25, 8.7, 63.5, 46.6, 66, 46.6, 3, 6, 'rrect'],
    'L7172':        ['reg', 'mm', 'a4', 3.75, 13.5, 100, 30, 102.5, 30, 2, 9, 'rrect'],
    'J5101':        ['reg', 'mm', 'a4', 4.75, 10.5, 38.1, 69, 40.6, 69, 5, 4, 'rrect'],
    'L7160':        ['reg', 'mm', 'a4', 7.25, 15.15, 63.5, 38.1, 66, 38.1, 3, 7, 'rrect'],
    'L7159':        ['reg', 'mm', 'a4', 7.25, 12.9, 63.5, 33.9, 66, 33.9, 3, 8, 'rrect'],
    'L7665':        ['reg', 'mm', 'a4', 22, 21.6, 72, 21.15, 94, 21.15, 2, 12, 'rrect'],
    'L7170':        ['reg', 'mm', 'a4', 38, 16.5, 134, 11, 134, 11, 1, 24, 'rrect'],
    'L6011':        ['reg', 'mm', 'a4', 7.25, 15.3, 63.5, 29.6, 66, 29.6, 3, 9, 'rrect'],
    'LP33_53':      ['reg', 'mm', 'a4', 21, 17.5, 54, 22, 57, 24, 3, 11, 'rrect'],
    'LP36_49':      ['reg', 'mm', 'a4', 4.8, 15.3, 48.9, 29.6, 50.5, 29.6, 4, 9, 'rrect'],
    'L7654':        ['reg', 'mm', 'a4', 9.7, 21.5, 45.7, 25.4, 48.3, 25.4, 4, 10, 'rrect'],
    'L7636':        ['reg', 'mm', 'a4', 9.85, 21.3, 45.7, 21.2, 48.2, 21.2, 4, 12, 'rrect'],
    'LP56_89':      ['reg', 'mm', 'a4', 8, 8.5, 89, 10, 105, 10, 2, 28, 'rrect'],
    'L7651':        ['reg', 'mm', 'a4', 4.75, 10.7, 38.1, 21.2, 40.6, 21.2, 5, 13, 'rrect'],
    'L7656':        ['reg', 'mm', 'a4', 5.95, 15.95, 46, 11.1, 50.7, 12.7, 4, 21, 'rrect'],
    'L7658':        ['reg', 'mm', 'a4', 8.6, 13.5, 25.4, 10, 27.9, 10, 7, 27, 'rrect'],
    'L7657':        ['reg', 'mm', 'a4', 4.75, 13.5, 17.8, 10, 20.3, 10, 10, 27, 'rrect'],

    # Rect labels
    'L7784':        ['reg', 'mm', 'a4', 0, 0, 210, 297, 210, 297, 1, 1, 'rect'],
    'LP2_105':      ['reg', 'mm', 'a4', 0, 0, 105, 297, 105, 297, 2, 1, 'rect'],
    '3655':         ['reg', 'mm', 'a4', 0, 0, 210, 148.5, 210, 148.5, 1, 2, 'rect'],
    'LP3_210':      ['reg', 'mm', 'a4', 0, 0, 210, 99, 210, 99, 1, 3, 'rect'],
    '3483':         ['reg', 'mm', 'a4', 0, 0, 105, 148.5, 105, 148.5, 2, 2, 'rect'],
    'LP4_210':      ['reg', 'mm', 'a4', 0, 0, 210, 74.25, 210, 74.25, 1, 4, 'rect'],
    'LP6_70':       ['reg', 'mm', 'a4', 0, 0, 70, 148.5, 70, 148.5, 3, 2, 'rect'],
    'LP6_105':      ['reg', 'mm', 'a4', 0, 0, 105, 99, 105, 99, 2, 3, 'rect'],
    '3427':         ['reg', 'mm', 'a4', 0, 0, 105, 74.25, 105, 74.25, 2, 4, 'rect'],
    'LP8_105S':     ['reg', 'mm', 'a4', 0, 7.1, 105, 70.7, 105, 70.7, 2, 4, 'rect'],
    'LP10_105':     ['reg', 'mm', 'a4', 0, 0, 105, 59.4, 105, 59.4, 2, 5, 'rect'],
    '3425':         ['reg', 'mm', 'a4', 0, 4.625, 105, 57.55, 105, 57.55, 2, 5, 'rect'],
    'LP12_105':     ['reg', 'mm', 'a4', 0, 0, 105, 49.5, 105, 49.5, 2, 6, 'rect'],
    '3424':         ['reg', 'mm', 'a4', 0, 4.8, 105, 47.9, 105, 47.9, 2, 6, 'rect'],
    '3653':         ['reg', 'mm', 'a4', 0, 0, 105, 42.42, 105, 42.42, 2, 7, 'rect'],
    'LP15_70':      ['reg', 'mm', 'a4', 0, 0, 70, 59.4, 70, 59.4, 3, 5, 'rect'],
    'LP15_70S':     ['reg', 'mm', 'a4', 0, 21.75, 70, 50.7, 70, 50.7, 3, 5, 'rect'],
    '3484':         ['reg', 'mm', 'a4', 0, 0, 105, 37.12, 105, 37.12, 2, 8, 'rect'],
    '3423':         ['reg', 'mm', 'a4', 0, 8.7, 105, 34.95, 105, 34.95, 2, 8, 'rect'],
    '3652':         ['reg', 'mm', 'a4', 0, 0, 70, 42.42, 70, 42.42, 3, 7, 'rect'],
    'LP21_70S':     ['reg', 'mm', 'a4', 0, 15.15, 70, 38.1, 70, 38.1, 3, 7, 'rect'],
    '3474':         ['reg', 'mm', 'a4', 0, 0, 70, 37.12, 70, 37.12, 3, 8, 'rect'],
    '3422':         ['reg', 'mm', 'a4', 0, 8.7, 70, 34.95, 70, 34.95, 3, 8, 'rect'],
    'LP24_70LS':    ['reg', 'mm', 'a4', 0, 12.5, 70, 34, 70, 34, 3, 8, 'rect'],
    '3475':         ['reg', 'mm', 'a4', 0, 4.5, 70, 36, 70, 36, 3, 8, 'rect'],
    'LP27_70S':     ['reg', 'mm', 'a4', 0, 4.725, 70, 31.95, 70, 31.95, 3, 9, 'rect'],
    '3489':         ['reg', 'mm', 'a4', 0, 0, 70, 29.7, 70, 29.7, 3, 10, 'rect'],
    '3421':         ['reg', 'mm', 'a4', 0, 8.8, 70, 25.4, 70, 25.4, 3, 11, 'rect'],
    'L7409':        ['reg', 'mm', 'a4', 19.5, 21, 57, 15, 57, 15, 3, 17, 'rect'],
    'LP56_52':      ['reg', 'mm', 'a4', 0, 0, 52.5, 21.21, 52.5, 21.21, 4, 14, 'rect'],

    # Round labels
    'LP2_115R':     ['reg', 'mm', 'a4', 47.75, 16.65, 114.5, 114.5, 114.5, 149.2, 1, 2, 'circle'],
    'LP6_88R':      ['reg', 'mm', 'a4', 16, 14.5, 88, 88, 90, 90, 2, 3, 'circle'],
    'LP6_85R':      ['reg', 'mm', 'a4', 17.5, 16, 85, 85, 90, 90, 2, 3, 'circle'],
    'LP6_76R':      ['reg', 'mm', 'a4', 27, 31, 76, 76, 80, 79.5, 2, 3, 'circle'],
    'C2244':        ['reg', 'mm', 'a4', 29.7, 33.9, 72, 72, 78.6, 78.6, 2, 3, 'circle'],
    'LP8_69R':      ['reg', 'mm', 'a4', 34.5, 6, 69, 69, 72, 72, 2, 4, 'circle'],
    'L7670':        ['reg', 'mm', 'a4', 5.25, 14.75, 63.5, 63.5, 68, 68, 3, 4, 'circle'],
    'LP15_51R':     ['reg', 'mm', 'a4', 26.5, 17, 51, 51, 53, 53, 3, 5, 'circle'],
    'LP24_45R':     ['reg', 'mm', 'a4', 9, 6, 45, 45, 49, 48, 4, 6, 'circle'],
    'L7780':        ['reg', 'mm', 'a4', 16, 13.5, 40, 40, 46, 46, 4, 6, 'circle'],
    'LP35_37R':     ['reg', 'mm', 'a4', 8.5, 13, 37, 37, 39, 39, 5, 7, 'circle'],
    'LP35_35R':     ['reg', 'mm', 'a4', 9.5, 17, 35, 35, 39, 38, 5, 7, 'circle'],
    'LP40_32R':     ['reg', 'mm', 'a4', 19, 10.35, 32, 32, 35, 34.9, 5, 8, 'circle'],
    'LP54_29R':     ['reg', 'mm', 'a4', 8, 6, 29, 29, 33, 32, 6, 9, 'circle'],
    'LP70_25R':     ['reg', 'mm', 'a4', 11.5, 14.5, 25, 25, 27, 27, 7, 10, 'circle'],
    'LP117_19R':    ['reg', 'mm', 'a4', 11.5, 13, 19, 19, 21, 21, 9, 13, 'circle'],
    'LP216_13R':    ['reg', 'mm', 'a4', 13.25, 10.25, 13, 13, 15.5, 15.5, 12, 18, 'circle'],

    # Oval labels
    'LP2_195OV':    ['reg', 'mm', 'a4', 7.5, 8.5, 195, 138, 195, 142, 1, 2, 'circle'],
    'LP4_90OV':     ['reg', 'mm', 'a4', 14, 12.5, 90, 135, 92, 137, 2, 2, 'circle'],
    'LP8_90OV':     ['reg', 'mm', 'a4', 9.25, 15.95, 90, 62, 101.5, 67.7, 2, 4, 'circle'],
    'LP10_95OV':    ['reg', 'mm', 'a4', 7, 8, 95, 53, 101, 57, 2, 5, 'circle'],
    'LP14_95OV':    ['reg', 'mm', 'a4', 7, 17.5, 95, 34, 101, 38, 2, 7, 'circle'],
    'LP21_60OV':    ['reg', 'mm', 'a4', 11, 10, 60, 34, 64, 40.5, 3, 7, 'circle'],
    'LP32_40OV':    ['reg', 'mm', 'a4', 22, 21.5, 40, 30, 42, 32, 4, 8, 'circle'],
    'LP65_35OV':    ['reg', 'mm', 'a4', 5.975, 13.3, 35.05, 16, 40.75, 21.2, 5, 13, 'circle'],

    # Square labels
    'LP6_95SQ':     ['reg', 'mm', 'a4', 6.5, 3, 95, 95, 98, 98, 2, 3, 'rrect'],
    'LP12_65SQ':    ['reg', 'mm', 'a4', 5, 15.5, 65, 65, 67.5, 67, 3, 4, 'rrect'],
    'LP15_51SQ':    ['reg', 'mm', 'a4', 26.6, 17.2, 51, 51, 52.9, 52.9, 3, 5, 'rrect'],
    'LP35_37SQ':    ['reg', 'mm', 'a4', 8.5 / 12, 13.3, 37, 37, 39, 38.9, 5, 7, 'rrect'],
    'LP70_25SQ':    ['reg', 'mm', 'a4', 11.5, 14.5, 25, 25, 27, 27, 7, 10, 'rrect'],
}


def add_SVG_guide(x, y, orientation, colour, parent):
    """ Create a sodipodi:guide node on the given parent
    """

    try:
        # convert mnemonics to actual orientations
        orientation = {
                'vert': '1,0',
                'horz': '0,1'
        }[orientation]
    except KeyError:
        pass

    attribs = {
            'position': str(x) + "," + str(y),
            'orientation': orientation
    }

    if colour is not None:
        attribs[inkex.addNS('color', 'inkscape')] = colour

    etree.SubElement(
            parent,
            inkex.addNS('guide', 'sodipodi'),
            attribs)


def delete_all_guides(document):
    # getting the parent's tag of the guides
    nv = document.xpath(
            '/svg:svg/sodipodi:namedview', namespaces=inkex.NSS)[0]

    # getting all the guides
    children = document.xpath('/svg:svg/sodipodi:namedview/sodipodi:guide',
                              namespaces=inkex.NSS)

    # removing each guides
    for element in children:
        nv.remove(element)


def draw_SVG_ellipse(rx, ry, cx, cy, style, parent):

    attribs = {
        'style': str(inkex.Style(style)),
        inkex.addNS('cx', 'sodipodi'):   str(cx),
        inkex.addNS('cy', 'sodipodi'):   str(cy),
        inkex.addNS('rx', 'sodipodi'):   str(rx),
        inkex.addNS('ry', 'sodipodi'):   str(ry),
        inkex.addNS('type', 'sodipodi'): 'arc',
    }

    etree.SubElement(parent, inkex.addNS('path', 'svg'), attribs)


def draw_SVG_rect(x, y, w, h, round, style, parent):

    attribs = {
        'style':    str(inkex.Style(style)),
        'height':   str(h),
        'width':    str(w),
        'x':        str(x),
        'y':        str(y)
    }

    if round:
        attribs['ry'] = str(round)

    etree.SubElement(parent, inkex.addNS('rect', 'svg'), attribs)


def add_SVG_layer(parent, gid, label):

    layer = etree.SubElement(parent, 'g', {
        'id': gid,
        inkex.addNS('groupmode', 'inkscape'): 'layer',
        inkex.addNS('label', 'inkscape'): label
    })

    return layer


class LabelGuides(inkex.Effect):

    def __init__(self):

        inkex.Effect.__init__(self)
        self.arg_parser.add_argument('--units', default="mm", help='The units to use for custom label sizing')
        self.arg_parser.add_argument('--preset_tab', default='rrect', help='The preset section that is selected (other sections will be ignored)')
        
        # ROUNDED RECTANGLE PRESET OPTIONS
        self.arg_parser.add_argument('--rrect_preset', default='L7167', help='Use the given rounded rectangle preset template')
        self.arg_parser.add_argument('--rrect_radius', type=float, default=1, help='Rectangle corner radius') # RECTANGULAR PRESET OPTIONS
        self.arg_parser.add_argument('--rect_preset', default='L7784', help='Use the given square-corner rectangle template')
        
        # CIRCULAR PRESET OPTIONS
        self.arg_parser.add_argument('--circ_preset', default='LP2_115R', help='Use the given circular template')
        
        # CUSTOM LABEL OPTIONS
        self.arg_parser.add_argument('--margin_l', type=float, default=8.5, help='Left page margin')
        self.arg_parser.add_argument('--margin_t', type=float, default=13, help='Top page margin')
        self.arg_parser.add_argument('--size_x', type=float, default=37, help='Label X size')
        self.arg_parser.add_argument('--size_y', type=float, default=37, help='Label Y size')
        self.arg_parser.add_argument('--pitch_x', type=float, default=39, help='Label X pitch')
        self.arg_parser.add_argument('--pitch_y', type=float, default=39, help='Label Y pitch')
        self.arg_parser.add_argument('--count_x', type=int,  default=5, help='Number of labels across')
        self.arg_parser.add_argument('--count_y', type=int, default=7, help='Number of labels down')
        self.arg_parser.add_argument('--shapes', default='rect', help='Label shapes to draw')
        
        # GENERAL DRAWING OPTIONS
        self.arg_parser.add_argument('--delete_existing_guides', type=inkex.Boolean, default=False, help='Delete existing guides from document')
        self.arg_parser.add_argument('--draw_edge_guides', type=inkex.Boolean, default=True, help='Draw guides at label edges')
        self.arg_parser.add_argument('--draw_centre_guides', type=inkex.Boolean, default=True, help='Draw guides at label centres')
        self.arg_parser.add_argument('--inset', type=float, default=5, help='Inset to use for inset guides')
        self.arg_parser.add_argument('--draw_inset_guides', type=inkex.Boolean, default=True, help='Draw guides inset to label edges')
        self.arg_parser.add_argument('--draw_shapes', type=inkex.Boolean, default=True, help='Draw label outline shapes')
        self.arg_parser.add_argument('--shape_inset',  default=5, help='Inset to use for inset shapes')
        self.arg_parser.add_argument('--draw_inset_shapes', type=inkex.Boolean, default=True, help='Draw shapes inset in the label outline')
        self.arg_parser.add_argument('--set_page_size', type=inkex.Boolean, default=True, help='Set page size (presets only)')

    def _to_uu(self, val, unit):
        """
        Transform a value in given units to User Units
        """
        return self.svg.unittouu(str(val) + unit)

    def _get_page_size(self, size):
        """
        Get a page size from a definition entry - can be in the form
        [x, y], or a string (one of ['a4'])
        """

        if isinstance(size, (list,)):
            # Explicit size
            return size
        elif size == "a4":
            return [210, 297]

        # Failed to find a useful size, None will inhibit setting the size
        return None

    def _set_SVG_page_size(self, document, x, y, unit):
        """
        Set the SVG page size to the given absolute size. The viewbox is
        also rescaled as needed to maintain the scale factor.
        """

        svg = document.getroot()

        # Re-calculate viewbox in terms of User Units
        new_uu_w = self._to_uu(x, unit)
        new_uu_h = self._to_uu(y, unit)

        # set SVG page size
        svg.attrib['width'] = str(x) + unit
        svg.attrib['height'] = str(y) + unit

        svg.attrib['viewBox'] = "0 0 %f %f" % (new_uu_w, new_uu_h)

    def _read_custom_options(self, options):
        """
        Read custom label geometry options and produce
        a dictionary of parameters for ingestion
        """
        unit = options.units

        custom_opts = {
                'units': options.units,
                'page_size': None,
                'margin': {
                    'l': self._to_uu(options.margin_l, unit),
                    't': self._to_uu(options.margin_t, unit)
                },
                'size': {
                    'x': self._to_uu(options.size_x, unit),
                    'y': self._to_uu(options.size_y, unit)
                },
                'pitch': {
                    'x': self._to_uu(options.pitch_x, unit),
                    'y': self._to_uu(options.pitch_y, unit)
                },
                'count': {
                    'x': options.count_x,
                    'y': options.count_y
                },
                'shapes': options.shapes,
                'corner_rad': None,
        }

        return custom_opts

    def _construct_preset_opts(self, preset_type, preset_id, options):
        """Construct an options object for a preset label template
        """
        preset = PRESETS[preset_id]

        unit = preset[1]

        opts = {
                'units': unit,
                'page_size': self._get_page_size(preset[2]),
                'margin': {
                    'l': self._to_uu(preset[3], unit),
                    't': self._to_uu(preset[4], unit)
                 },
                'size': {
                    'x': self._to_uu(preset[5], unit),
                    'y': self._to_uu(preset[6], unit)
                },
                'pitch': {
                    'x': self._to_uu(preset[7], unit),
                    'y': self._to_uu(preset[8], unit)
                },
                'count': {
                    'x': preset[9],
                    'y': preset[10]
                },
                'shapes': preset[11],
                'corner_rad': None,
        }

        # add addtional options by preset type
        if preset_type == "rrect":
            opts["corner_rad"] = self._to_uu(options.rrect_radius, unit)

        return opts

    def _get_regular_guides(self, label_opts, inset):
        """
        Get the guides for a set of labels defined by a regular grid

        This is done so that irregular-grid presets can be defined if
        needed
        """

        guides = {'v': [], 'h': []}

        x = label_opts['margin']['l']

        # Vertical guides, left to right
        for x_idx in range(label_opts['count']['x']):

            l_pos = x + inset
            r_pos = x + label_opts['size']['x'] - inset

            guides['v'].extend([l_pos, r_pos])

            # Step over to next label
            x += label_opts['pitch']['x']

        # Horizontal guides, bottom to top
        y = label_opts['margin']['t']

        for y_idx in range(label_opts['count']['y']):

            t_pos = y + inset
            b_pos = y + label_opts['size']['y'] - inset

            guides['h'].extend([t_pos, b_pos])

            # Step over to next label
            y += label_opts['pitch']['y']

        return guides

    def _draw_label_guides(self, document, label_opts, inset, colour):
        """
        Draws label guides from a regular guide description object
        """
        # convert to UU
        inset = self._to_uu(inset, label_opts['units'])

        guides = self._get_regular_guides(label_opts, inset)

        # Get parent tag of the guides
        nv = self.svg.namedview

        # Draw vertical guides
        for g in guides['v']:
            add_SVG_guide(g, 0, 'vert', colour, nv)

        # Draw horizontal guides
        for g in guides['h']:
            add_SVG_guide(0, self.svg.viewport_height - g, 'horz', colour, nv)

    def _draw_centre_guides(self, document, label_opts, colour):
        """
        Draw guides in the centre of labels defined by the given options
        """

        guides = self._get_regular_guides(label_opts, 0)
        nv = self.svg.namedview

        for g in range(0, len(guides['v']), 2):
            pos = (guides['v'][g] + guides['v'][g + 1]) / 2
            add_SVG_guide(pos, 0, 'vert', colour, nv)

        for g in range(0, len(guides['h']), 2):
            pos = (guides['h'][g] + guides['h'][g + 1]) / 2
            add_SVG_guide(0, self.svg.viewport_height - pos, 'horz', colour, nv)

    def _draw_shapes(self, document, label_opts, inset):
        """
        Draw label shapes from a regular grid
        """

        style = {
                'stroke': '#000000',
                'stroke-width': self._to_uu(1, "px"),
                'fill': "none"
        }

        inset = self._to_uu(inset, label_opts['units'])

        guides = self._get_regular_guides(label_opts, 0)
        shape = label_opts['shapes']

        shapeLayer = add_SVG_layer(
                self.document.getroot(),
                self.svg.get_unique_id("outlineLayer"),
                "Label outlines")

        # draw shapes between every set of two guides
        for xi in range(0, len(guides['v']), 2):

            for yi in range(0, len(guides['h']), 2):

                if shape == 'circle':
                    cx = (guides['v'][xi] + guides['v'][xi + 1]) / 2
                    cy = (guides['h'][yi] + guides['h'][yi + 1]) / 2

                    rx = cx - guides['v'][xi] - inset
                    ry = cy - guides['h'][yi] - inset

                    draw_SVG_ellipse(rx, ry, cx, cy, style, shapeLayer)

                elif shape in ["rect", "rrect"]:

                    x = guides['v'][xi] + inset
                    w = guides['v'][xi + 1] - x - inset

                    y = guides['h'][yi] + inset
                    h = guides['h'][yi + 1] - y - inset

                    rnd = self._to_uu(label_opts['corner_rad'],
                                      label_opts['units'])

                    draw_SVG_rect(x, y, w, h, rnd, style, shapeLayer)
    def _set_page_size(self, document, label_opts):
        """
        Set the SVG page size from the given label template definition
        """

        size = label_opts['page_size']
        unit = label_opts['units']

        if size is not None:
            self._set_SVG_page_size(document, size[0], size[1], unit)

    def effect(self):
        """
        Perform the label template generation effect
        """

        preset_type = self.options.preset_tab.strip('"')

        if preset_type == "custom":
            # construct from parameters
            label_opts = self._read_custom_options(self.options)
        else:
            # construct from a preset

            # get the preset ID from the relevant enum entry
            preset_id = {
                    "rrect": self.options.rrect_preset,
                    "rect": self.options.rect_preset,
                    "circ": self.options.circ_preset,
            }[preset_type]

            label_opts = self._construct_preset_opts(preset_type, preset_id,
                                                     self.options)

        if self.options.delete_existing_guides:
            delete_all_guides(self.document)

        # Resize page first, otherwise guides won't be in the right places
        if self.options.set_page_size:
            self._set_page_size(self.document, label_opts)

        if self.options.draw_edge_guides:
            self._draw_label_guides(self.document, label_opts, 0,
                                    GUIDE_COLOURS['edge'])

        if self.options.draw_centre_guides:
            self._draw_centre_guides(self.document, label_opts,
                                     GUIDE_COLOURS['centre'])

        if self.options.draw_inset_guides and self.options.inset > 0.0:
            self._draw_label_guides(self.document, label_opts,
                                    self.options.inset,
                                    GUIDE_COLOURS['inset'])

        if self.options.draw_shapes:
            self._draw_shapes(self.document, label_opts, 0)

        if self.options.draw_inset_shapes:
            self._draw_shapes(self.document, label_opts,
                              self.options.shape_inset)


if __name__ == '__main__':
    LabelGuides().run()

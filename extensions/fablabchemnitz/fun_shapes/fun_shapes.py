#!/usr/bin/env python3
# coding=utf-8
#
# Copyright (C) [2021] [Matt Cottam], [mpcottam@raincloud.co.uk]
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
A simple Extension to test if a Gtk3 Gui will work on most Inkscape 1.1+ Systems.
Inkscape 1.1 is the minimum verion.
Draws a simple set of randomly coloured circles and outputs them to the canvas.
"""

import inkex
from inkex.elements import Group, PathElement
from inkex import transforms, styles

import random
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, Gdk
from lxml import etree

# Could not find simplestyle, found this instead in extensions repo
def formatStyle(a):
    """Format an inline style attribute from a dictionary"""
    return ";".join([att + ":" + str(val) for att, val in a.items()])


def random_rgb(self):
    random_red = random.randrange(0, 255)
    random_green = random.randrange(0, 255)
    random_blue = random.randrange(0, 255)

    return f'rgb({random_red}, {random_green}, {random_blue})'


# Generate a circle or circle path
def draw_svg_circle(self, r, cx, cy, parent, is_path):
    style = {'stroke': 'black',
             # 'stroke-opacity': (r/200),
             'stroke-width': '0.1',
             # 'fill': 'none'
             'fill': random_rgb(self)
             }

    attribs = {
        'style': formatStyle(style),
        'r': str(r),
        'cx': str(cx),
        'cy': str(cy)
    }

    my_circle = etree.SubElement(Funshapes.output_group, inkex.addNS('circle', 'svg'), attribs)


def draw_svg_circle_series(self, r, cx, cy, parent, is_path):

    my_list = range(1, 100)
    for item in reversed(my_list):
        draw_svg_circle(self, item, cx, cy, parent, is_path)

    gtk3_add_svg_image(self, Funshapes.output_group)


def draw_svg_circle_series_scale(self, r, cx, cy, parent, is_path):
    Funshapes.output_group.clear()

    upper_range = int(Funshapes.main_window.h_scale.get_value())

    my_list = range(1, upper_range)
    for item in reversed(my_list):
        draw_svg_circle(self, item, cx, cy, parent, is_path)

    gtk3_add_svg_image(self, Funshapes.output_group)



def group_wrapper(self, my_objects, to_layer):
    group_id = 'g' + str(random.randrange(100000, 1000000))

    new_group = self.svg.add(Group.new('#' + group_id))
    # inkex set, takes account of NS attribs etc
    new_group.set('inkscape:groupmode', 'layer')
    new_group.set('inkscape:label', 'My_Layer_' + group_id)

    # When plucking an object from an svg, will only have its own transforms
    # Composed transforms must be applied instead.

    for my_object in my_objects:
        my_object_transforms = my_object.composed_transform()
        my_object.attrib['transform'] = ''
        my_object.transform.add_matrix(my_object_transforms)
        new_group.append(my_object)

    new_group.attrib['id'] = group_id
    return new_group


def object_to_xml_tag(self):
    my_tag = str(self.tostring().decode("utf-8"))
    return my_tag

##########################
# GTK3 GUI SECTION BELOW
##########################


def gtk3_gui(self):

    Funshapes.main_window = Gtk.Window()
    Funshapes.main_window.root_grid = Gtk.Grid()
    Funshapes.main_window.add(Funshapes.main_window.root_grid)

    root_grid = Funshapes.main_window.root_grid
    main_window = Funshapes.main_window

    gtk3_scales(root_grid, Funshapes.main_window)

    main_window.connect("destroy", Gtk.main_quit)
    main_window.show_all()

    draw_svg_circle_series(self, 200, 100, 100, Funshapes.self.svg, 'yes')

    Gtk.main()

    return main_window


def gtk3_scales(grid, inkex_self):
    ad1 = Gtk.Adjustment(value=20, lower=0, upper=100, step_increment=5, page_increment=10, page_size=0)

    inkex_self.h_scale = Gtk.Scale(
        orientation=Gtk.Orientation.HORIZONTAL, adjustment=ad1)

    inkex_self.h_scale.set_digits(0)
    inkex_self.h_scale.set_valign(Gtk.Align.START)

    inkex_self.h_scale.connect("value-changed", draw_svg_circle_series_scale, 50, 100, 100, None, None)

    grid.attach(inkex_self.h_scale, 1, 0, 1, 1)


def gtk3_add_svg_image(self, svg_object):

    Funshapes.base_image = Gtk.Image()
    Funshapes.base_image.set_from_file('white.png')

    random_number = random.randrange(10000, 1000000, 1)

    # convert svg object to svg xml
    svg = object_to_xml_tag(svg_object)

    svg = f'<svg width="200" viewBox="0 0 200 ' \
          f'200" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">{svg}</svg> '

    loader = GdkPixbuf.PixbufLoader()
    loader.write(svg.encode())
    loader.close()
    pixbuf = loader.get_pixbuf()

    Funshapes.preview_image = Gtk.Image.new_from_pixbuf(pixbuf)
    Funshapes.preview_image.show_all()

    if Funshapes.main_window.root_grid.get_child_at(1, 1) is None:
        Funshapes.main_window.root_grid.attach(Funshapes.preview_image, 1, 1, 1, 1)
    else:
        Funshapes.main_window.root_grid.get_child_at(1, 1).destroy()
        Funshapes.main_window.root_grid.attach(Funshapes.preview_image, 1, 1, 1, 1)


class Funshapes(inkex.EffectExtension):

    def effect(self):
        Funshapes.self = self
        output_group_id = f'Funshapes_{random.randrange(10000, 1000000, 1)}'
        Funshapes.output_group = Group.new('#' + output_group_id)
        # create new gtk3 window and attach to effect self
        self.win = gtk3_gui(self)

        # When GTK is exited
        Funshapes.self.svg.append(Funshapes.output_group)


if __name__ == '__main__':
    Funshapes().run()
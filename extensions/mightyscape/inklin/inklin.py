#!/usr/bin/env python3
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

##############################################################################
# Inklin - a collection of things I 'ave an inkling might be useful to someone.
##############################################################################


import inkex
from inkex import Group
import random
from lxml import etree
import math
import gi
import io

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gtk, GdkPixbuf, Gdk
from gi.repository.GdkPixbuf import Pixbuf, InterpType


def group_wrapper(self, my_objects):
    group_id = 'g' + str(random.randrange(100000, 1000000))

    new_group = self.svg.add(Group.new('#' + group_id))
    # inkex set, takes account of NS attribs etc
    new_group.set('inkscape:groupmode', 'layer')
    new_group.set('inkscape:label', 'My_Layer_' + group_id)

    for my_object in my_objects:
        new_group.append(my_object)

    new_group.attrib['id'] = group_id


def svg_arcs(cx, cy, radius, sectors, arc_radius1, arc_radius2, arc_x_rotate, arc_large_flag, arc_sweep_flag,
             outer_circle_checkbutton_bool, point_circles_checkbutton_bool, numbering_checkbutton_bool):

    x_start = cx
    y_start = cy - radius

    point_circles = ''
    point_labels = ''

    angle = 0

    y_start = cy / 2 + (radius * (math.sin(angle)))
    x_start = cx / 2 + (radius * (math.cos(angle)))

    arcs = f'M  {x_start} {y_start}'

    for sector in range(1, sectors + 1):
        angle = (sector * math.pi) / (sectors / 2)

        y = cy / 2 + (radius * (math.sin(angle)))
        x = cx / 2 + (radius * (math.cos(angle)))

        x_start = x
        y_start = y


        # A rx ry x-axis-rotation large-arc-flag sweep-flag x y

        arcs = arcs + f'A {arc_radius1} {arc_radius2} {arc_x_rotate} {arc_large_flag} {arc_sweep_flag} {x} {y} '

        if not point_circles_checkbutton_bool:
            point_circles = ''
        else:
            point_circles = point_circles + f'<circle fill="none" stroke="orange" stroke-width="1" r="{2}" cx="{x}" cy="{y}"/>'

        if not numbering_checkbutton_bool:
            None
        else:
            point_labels = point_labels + f'<text x="{x}" y="{y}">{sector}</text>'

        if not outer_circle_checkbutton_bool:
            outline_circle = ''
        else:
            outline_circle = f'<circle fill="none" stroke="green" stroke-width="1" r="{radius}" cx="{cx / 2}" cy="{cy / 2}"/>'

    #    svg = f'<svg width="{cx}" height="{cy}" viewBox="0 0 {cx} {cy}" ' \
    svg = f'<svg width="{500}" height="{500}" viewBox="0 0 {500} {500}" ' \
          f'xmlns="http://www.w3.org/2000/svg" ' \
          f'xmlns:svg="http://www.w3.org/2000/svg" ' \
          f'>' \
          f'{outline_circle}' \
          f'{point_circles}' \
          f'{point_labels}' \
          f'<path fill="none" stroke="black" d="{arcs} "/>' \
          f'</svg>'

    LoadSvg.master_svg = svg

    gtk3_add_svg_image(svg)


def gtk3_add_svg_image(svg):
    loader = GdkPixbuf.PixbufLoader()
    loader.write(svg.encode())
    loader.close()
    pixbuf = loader.get_pixbuf()

    # pixbuf = pixbuf.scale_simple(500, 500, InterpType.BILINEAR)

    LoadSvg.preview_image.set_from_pixbuf(pixbuf)

    LoadSvg.preview_image.show_all()


def init_arc():
    radius = LoadSvg.builder.get_object('radius_gtk_scale').get_value()
    arc_radius1 = LoadSvg.builder.get_object('arc_radius1_gtk_scale').get_value()
    arc_radius2 = LoadSvg.builder.get_object('arc_radius2_gtk_scale').get_value()
    arc_x_rotate_checkbutton1_bool = LoadSvg.builder.get_object('arc_x_rotate_gtk_checkbutton').get_active()
    arc_radius_checkbutton1_bool = LoadSvg.builder.get_object('arc_radius1_gtk_checkbutton').get_active()
    arc_radius_checkbutton2_bool = LoadSvg.builder.get_object('arc_radius2_gtk_checkbutton').get_active()
    sectors = int(LoadSvg.builder.get_object('sectors_gtk_scale').get_value())
    arc_large_flag = LoadSvg.builder.get_object('arc_large_flag_gtk_checkbutton').get_active()
    arc_sweep_flag = LoadSvg.builder.get_object('arc_sweep_flag_gtk_checkbutton').get_active()

    outer_circle_checkbutton_bool = LoadSvg.builder.get_object('outer_circle_gtk_checkbutton').get_active()
    point_circles_checkbutton_bool = LoadSvg.builder.get_object('point_circles_gtk_checkbutton').get_active()
    numbering_checkbutton_bool = LoadSvg.builder.get_object('numbering_gtk_checkbutton').get_active()

    if not arc_radius_checkbutton1_bool:
        arc_radius1 = radius
        LoadSvg.builder.get_object('arc_radius1_gtk_scale').set_value(radius)

    if not arc_radius_checkbutton2_bool:
        arc_radius2 = radius
        LoadSvg.builder.get_object('arc_radius2_gtk_scale').set_value(radius)

    if not arc_x_rotate_checkbutton1_bool:
        arc_x_rotate = 0
    else:
        arc_x_rotate = LoadSvg.builder.get_object('arc_x_rotate_gtk_scale').get_value()

    if not arc_sweep_flag:
        arc_sweep_flag = 0
    else:
        arc_sweep_flag = 1

    if not arc_large_flag:
        arc_large_flag = 0
    else:
        arc_large_flag = 1


    svg_arcs(500, 500, radius, sectors, arc_radius1, arc_radius2, arc_x_rotate, arc_large_flag, arc_sweep_flag, outer_circle_checkbutton_bool, point_circles_checkbutton_bool, numbering_checkbutton_bool)

    # inkex.errormsg(f'arc1 {arc_radius_checkbutton1_bool} arc2 {arc_radius_checkbutton2_bool}')


########################################################
#        Gtk Section                                   #
########################################################

class Handler:
    def onDestroy(self, *args):
        Gtk.main_quit()

    def onButtonPressed(self, button):
        print("Hello World!")

    # def arcButtonPressed(self, button):
    #     svg_arcs(500, 500, 50, 8)
    # test_print()

    def onScaleChangeRadius(self, scale):
        init_arc()

    def onScaleChangeSides(self, scale):
        init_arc()

    def onScaleChangeArcRadius(self, scale):
        init_arc()

    def arcRadiusCheckbuttonChange(self, scale):
        init_arc()

    def onScaleChangeXRotate(self, scale):
        init_arc()

    def arcXRotateCheckbuttonChange(self, scale):
        init_arc()

    def arcSweepFlagCheckbuttonChange(self, scale):
        init_arc()

    def arcLargeFlagCheckbuttonChange(self, scale):
        init_arc()

    def outerCircleCheckbuttonChange(self, scale):
        init_arc()

    def pointCirclesCheckbuttonChange(self, scale):
        init_arc()

    def numberingCheckbuttonChange(self, scale):
        init_arc()


def run_gtk():
    LoadSvg.builder = Gtk.Builder()
    LoadSvg.builder.add_from_file("inklin.glade")
    LoadSvg.builder.connect_signals(Handler())

    LoadSvg.window = LoadSvg.builder.get_object("main_window")
    LoadSvg.window.show_all()
    LoadSvg.window.set_title('Inklin')

    LoadSvg.preview_image = LoadSvg.builder.get_object('preview_image')

    init_arc()

    Gtk.main()


########################################################
#        Inkex effect section                          #
########################################################

class LoadSvg(inkex.EffectExtension):

    def effect(self):
        run_gtk()

        svg_etree = etree.fromstring(LoadSvg.master_svg)

        group_wrapper(self, svg_etree)


if __name__ == '__main__':
    LoadSvg().run()

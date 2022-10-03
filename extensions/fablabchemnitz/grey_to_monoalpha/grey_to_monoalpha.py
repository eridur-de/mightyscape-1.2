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
# Grey To Mono Alpha *** Convert Greys to Monochrome with varying Opacity
##############################################################################

import math

import inkex
from inkex import Color

# Python Standard Libary

from statistics import mean


def get_attributes(self):
    for att in dir(self):
        inkex.errormsg((att, getattr(self, att)))


def rgba_to_bw_rgba(self, my_objects):
    apply_to = self.options.apply_to_type_radio
    mono_color = self.options.color_picker_mono.to_rgba()
    opacity_lower_threshold = self.options.opacity_lower_threshold
    opacity_upper_threshold = self.options.opacity_upper_threshold
    opacity_range = opacity_upper_threshold - opacity_lower_threshold

    for my_object in my_objects:

        if 'fill' in apply_to and ('fill:none' not in str(my_object.style)):
            my_fill_color = my_object.style.get_color(name='fill').to_rgba()
            my_fill_color_red = my_fill_color[0]
            my_fill_color_green = my_fill_color[1]
            my_fill_color_blue = my_fill_color[2]
            mean_fill_component_value = mean([my_fill_color_red, my_fill_color_blue, my_fill_color_green])

            if mean_fill_component_value > 0:
                mono_opacity = (1 - (mean_fill_component_value / 256)) * opacity_range
                mono_opacity = mono_opacity + opacity_lower_threshold
            else:
                mono_opacity = opacity_upper_threshold

            my_object.style['fill'] = str(mono_color)
            my_object.style['fill-opacity'] = str(mono_opacity)

        if 'stroke' in apply_to and (';stroke:none' not in str(my_object.style)) and ('stroke:' in str(my_object.style)):
            my_stroke_color = my_object.style.get_color(name='stroke').to_rgba()
            my_stroke_color_red = my_stroke_color[0]
            my_stroke_color_green = my_stroke_color[1]
            my_stroke_color_blue = my_stroke_color[2]
            mean_stroke_component_value = mean([my_stroke_color_red, my_stroke_color_blue, my_stroke_color_green])

            if mean_stroke_component_value > 0:
                mono_opacity = (1 - (mean_stroke_component_value / 256)) * opacity_range
                mono_opacity = mono_opacity + opacity_lower_threshold
            else:
                mono_opacity = opacity_upper_threshold

            my_object.style['stroke'] = str(mono_color)
            my_object.style['stroke-opacity'] = str(mono_opacity)


class GreyToMonoAlpha(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--color_picker_mono", type=inkex.colors.Color, default=0)
        pars.add_argument("--apply_to_type_radio", default=None)
        pars.add_argument("--opacity_lower_threshold", type=float, default=0)
        pars.add_argument("--opacity_upper_threshold", type=float, default=1)

    def effect(self):
        my_objects = self.svg.selected
        if len(my_objects) < 1:
            self.msg('Please select some paths first.')
            return
        rgba_to_bw_rgba(self, my_objects)


if __name__ == '__main__':
    GreyToMonoAlpha().run()

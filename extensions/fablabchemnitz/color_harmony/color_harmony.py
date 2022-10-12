#!/usr/bin/env python3

# Color Harmony - Inkscape extension to generate
#                 palettes of colors that go well together
#
# Version 0.2 "golem"
#
# Copyright (C) 2009-2018 Ilya Portnov <portnov84@rambler.ru>
#                         (original 'palette-editor' tool, version 0.0.7)
#                    2020 Maren Hachmann (extension-ification)
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


"""
This extension allows you to automatically add guides to your Inkscape documents.
"""

#from math import sqrt
#import types
import inkex
from inkex import Group, Rectangle
from inkex.colors import is_color
from color_harmony.colorplus import ColorPlus
from color_harmony.harmonies import *
from color_harmony.shades import *


class ColorHarmony(inkex.EffectExtension):
    """Generate palettes of colors that go well together"""

    color = ''

    def add_arguments(self, pars):
        # General options
        pars.add_argument('--tab', default='render', help='Extension functionality to use') # options: render, save, colorize

        # Render tab options
        pars.add_argument('--harmony', default="five", help='Color harmony to generate, options: from_raster, just_opposite, split_complementary, three, four, rectangle, five, similar_3, similar_5, similar_and_opposite')
        pars.add_argument('--sort', default="by_hue", help="Method to sort the palette by, options: by_hue, by_saturation, by_value, hue_contiguous")
        pars.add_argument('--factor', default=50, type=int, help="Factor to affect the result, between 1 and 100. Default is 50. This modifies the angle between the resulting colors on the color wheel.")
        pars.add_argument('--size', default=10, help="Size of the generated palette squares")
        pars.add_argument('--unit', default='mm', help='Units') # options: mm, cm, in, px, pt, pc
        pars.add_argument('--delete_existing', type=inkex.Boolean, help='Delete existing palettes before generating a new one')

        # Shading: cooler, warmer, saturation, value, chroma, luma, hue, hue_luma,  luma_plus_chroma, luma_minus_chroma
        pars.add_argument( '--cooler', type=inkex.Boolean, help='Add shades with cooler color temperature')
        pars.add_argument( '--warmer', type=inkex.Boolean, help='Add shades with warmer color temperature')
        pars.add_argument( '--saturation', type=inkex.Boolean, help='Add shades with saturation steps')
        pars.add_argument( '--value', type=inkex.Boolean, help='Add shades with value steps')
        pars.add_argument( '--chroma', type=inkex.Boolean, help='Add shades with chroma steps')
        pars.add_argument( '--luma', type=inkex.Boolean, help='Add shades with luma steps')
        pars.add_argument( '--hue', type=inkex.Boolean, help='Add shades with hue steps')
        pars.add_argument( '--hue_luma', type=inkex.Boolean, help='Add shades with hue and luma steps')
        pars.add_argument( '--luma_plus_chroma', type=inkex.Boolean, help='Add shades with luma plus chroma steps')
        pars.add_argument( '--luma_minus_chroma', type=inkex.Boolean, help='Add shades with luma minus chroma steps')    
        pars.add_argument('--step_width', type=float, default=0.1, help='Shader step width') # TODO: find out what range this can take on, and adjust min, max, default in inx

        # Save tab options
        pars.add_argument('--palette_format', default='gimp', help='Palette file format')
                          # options: gimp, krita, scribus
        pars.add_argument('--palette_folder', help="Folder to save the palette file in")
        pars.add_argument('--palette_name', help="Name of the palette")

        # Colorize tab options
        # no options currently


    def effect(self):

        if self.options.tab == "render":

            if len(self.svg.selected) == 1:
                for obj_id, obj in self.svg.selected.items():
                    fill = obj.style.get("fill")
                    if is_color(fill):
                        if self.options.delete_existing:
                            self.delete_existing_palettes()
                        self.color = ColorPlus(fill)
                        self.options.factor = self.options.factor/100
                        colors = self.create_harmony()
                        shades = self.create_shades(colors)
                        palettes = [colors] + shades

                        for i in range(len(palettes)):
                            self.render_palette(palettes[i], i)
                    else:
                        raise inkex.AbortExtension(
                            "Please select an object with a plain fill color.")
            else:
                raise inkex.AbortExtension(
                    "Please select one object.")
        elif self.options.tab == "save":
            palettes = self.get_palettes_in_doc()
            if len(palettes) >= 1:
                self.save_palette(palettes[0])
            else:
                raise inkex.AbortExtension(
                    "There is no rendered palette in the document. Please render a palette using the first tab of the dialog before you try to save it.")
        elif self.options.tab == "colorize":
            if len(self.svg.selected) > 0:
                self.colorize()
            else:
                raise inkex.AbortExtension(
                    "Please select an object to colorize!")


    # METHODS FOR EACH TAB
    # --------------------

    # Render tab
    # ==========
    def create_harmony(self):

        harmony_functions = {
            "from_raster": self.palette_from_raster, # not implemented yet
            "just_opposite": self.opposite,
            "split_complementary": self.splitcomplementary,
            "three": self.nhues3,
            "four": self.nhues4,
            "rectangle": self.rectangle,
            "five": self.fivecolors,
            "similar_3": self.similar_3,
            "similar_5": self.similar_5,
            "similar_and_opposite": self.similaropposite,
        }

        # use appropriate function for the selected tab
        colors = harmony_functions[self.options.harmony](self.color)
        colors = self.sort_colors(colors)

        return colors

    def render_palette(self, colors, shift):
        size = self.svg.unittouu(str(self.options.size)+self.options.unit)
        top = 0 + shift * size
        left = 0

        layer = self.svg.get_current_layer() if self.svg.get_current_layer() is not None else self.document.getroot()

        group_attribs = {inkex.addNS('label', 'inkscape'): "Palette ({harmony}, {color}) ".format(color=self.color, harmony=self.options.harmony)}
        palette_group = Group(**group_attribs)

        for color in colors:
            palette_field = Rectangle(x=str(left),
                                      y=str(top),
                                      width=str(size),
                                      height=str(size))
            palette_field.style = {'fill': color}
            palette_group.add(palette_field)
            left += size

        palette_group.transform.add_translate(0, self.svg.viewport_height + size)

        layer.add(palette_group)

    def palette_from_raster(self, color):
        # TODO: implement
        return []

    def opposite(self, color):
        colors = opposite(color)
        return colors

    def splitcomplementary(self, color):
        colors = splitcomplementary(color, self.options.factor)
        return colors

    def nhues3(self, color):
        colors = nHues(color, 3)
        return colors

    def nhues4(self, color):
        colors = nHues(color, 4)
        return colors

    def rectangle(self, color):
        colors = rectangle(color, self.options.factor)
        return colors

    def fivecolors(self, color):
        colors = fiveColors(color, self.options.factor)
        return colors

    def similar_3(self, color):
        colors = similar(color, 3, self.options.factor)
        return colors

    def similar_5(self, color):
        colors = similar(color, 5, self.options.factor)
        return colors

    def similaropposite(self, color):
        colors = similarAndOpposite(color, self.options.factor)
        return colors

    def create_shades(self, colors):
        shades = []
        shading_options = {
            "cooler": cooler,
            "warmer": warmer,
            "saturation": saturation,
            "value": value,
            "chroma": chroma,
            "luma": luma,
            "hue": hue,
            "hue_luma": hue_luma,
            "luma_plus_chroma": luma_plus_chroma,
            "luma_minus_chroma": luma_minus_chroma,
        }

        for option, function in shading_options.items():
            if vars(self.options)[option] == True:
                # shades are created per color,
                # but we want to get one palette per shading step
                shaded_colors = []
                for i in range(len(colors)):
                    shaded_colors.append(function(colors[i], self.options.step_width))

                pals = [list(a) for a in zip(*shaded_colors)]

                shades += pals
        return shades

    def delete_existing_palettes(self):
        """Delete all palettes in the document"""

        for palette in self.get_palettes_in_doc():
            palette.delete()

    # Save tab
    # ========
    def save_palette(self, palette):
        # TODO: implement
        # if not hasattr(self.palette, 'name'):
        #     if type(file_w) in [str, unicode]:
        #         self.palette.name = basename(file_w)
        #     else:
        #         self.palette.name='Colors'
        pass


    # Colorize tab
    # ============

    def colorize(self):
        # TODO: implement
        pass

    # HELPER FUNCTIONS
    # ----------------

    def get_palettes_in_doc(self):
        palettes = []
        for group in self.svg.findall('.//svg:g'):
            if group.get('inkscape:label').startswith('Palette ('):
                palettes.append(group)
        return palettes

    def sort_colors(self, colors):
        if self.options.sort == "by_hue":
            colors.sort(key=lambda color: color.to_hsv()[0])
        elif self.options.sort == "by_saturation":
            colors.sort(key=lambda color: color.to_hsv()[1])
        elif self.options.sort == "by_value":
            colors.sort(key=lambda color: color.to_hsv()[2])
        # this option looks nicer when the palette colors are similar red tones
        # some of which have a hue close to 0
        # and some of which have a hue close to 1
        elif self.options.sort == "hue_contiguous":
            # sort by hue first
            colors.sort(key=lambda color: color.to_hsv()[0])
            # now find out if the hues are maybe clustered around the 0 - 1 boundary
            hues = [color.to_hsv()[0] for color in colors]
            start_hue = 0
            end_hue = 0
            max_dist = 0
            for i in range(len(colors)-1):
                h1 = hues[i]
                h2 = hues[i+1]
                cur_dist = h2-h1
                if cur_dist > max_dist and self.no_colors_in_between(h1, h2, hues):
                    max_dist = cur_dist
                    start_hue = h2
            for i in range(len(colors)):
                sorting_hue = hues[i] - start_hue
                if sorting_hue > 1:
                    sorting_hue -=1
                elif sorting_hue < 0:
                    sorting_hue += 1
                hues[i] = sorting_hue
            sorted_colors = [color for hue, color in sorted(zip(hues,colors))]
            colors = sorted_colors
        else:
            raise inkex.AbortExtension(
                "Please select one of the following sorting options: by_hue, by_saturation, by_value.")
        return colors

    def no_colors_in_between(self, hue1, hue2, hues):
        for hue in hues:
            if hue > hue1 and hue < hue2:
                return False
        return True

if __name__ == '__main__':
    ColorHarmony().run()

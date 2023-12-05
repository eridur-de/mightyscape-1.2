#!/usr/bin/env python3
'''
BSD 3-Clause License

Copyright (c) 2019, Pascal Wagler
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

This Inkscape extension allows you to generate squared squares and squared rectangles from
Bouwkamp codes and table codes.
'''

import re
import inkex
from lxml import etree

class BouwkampCode(inkex.EffectExtension):
    """
    This Inkscape extension allows you to generate squared squares and squared rectangles from
    Bouwkamp codes and table codes.
    """

    def add_arguments(self, pars):
        pars.add_argument('--tab')
        pars.add_argument('--bouwkamp_code', default='21, 112, 112, [50, 35, 27], [8, 19], [15, 17, 11], [6, 24], [29, 25, 9, 2], [7, 18], [16], [42], [4, 37], [33]', help='The Bouwkamp code.'
        )
        pars.add_argument('--wrap_in_group', type=inkex.Boolean,  default=True, help='Should the generated items be wrapped inside a group.'
        )

    def effect(self):
        # compute center of the view
        center = self.svg.namedview.center

        # create the group that holds all the elements
        container = self.svg.get_current_layer()
        if self.options.wrap_in_group:
            group_attributes = {
                inkex.addNS('label', 'inkscape'): 'BouwkampSquares',
                'transform': 'translate' + str(center)
            }
            group = etree.SubElement(self.svg.get_current_layer(), 'g', group_attributes)
            container = group

        # parse the bouwkamp code string as a list
        bouwkamp_code = self.parse_bouwkamp_code_from_string(self.options.bouwkamp_code)

        # show an error message and exit if the bouwkamp code is invalid
        try:
            self.exception_on_invalid_bouwkamp_code(bouwkamp_code)
        except ValueError as exception:
            inkex.errormsg(str(exception))
            return

        # draw the bouwkamp code
        self.draw_bouwkamp_code(container, center, bouwkamp_code)

    @staticmethod
    def exception_on_invalid_bouwkamp_code(bouwkamp_code):
        """
        Raises a ValueError if the passed list is not a valid Bouwkamp code.
        """

        if not bouwkamp_code: #len(bouwkamp_code) == 0
            raise ValueError('Error: Invalid Bouwkamp code.\n\nThe Bouwkamp code is emtpy. ' +
                             'Please specify a valid Bouwkamp code.')

        if len(bouwkamp_code) - 3 != bouwkamp_code[0]:
            raise ValueError('Error: Invalid Bouwkamp code.\n\nThe Bouwkamp code has the wrong ' +
                             'length. The first number needs to specify how many squares ' +
                             'should be drawn.')

    @staticmethod
    def parse_bouwkamp_code_from_string(bouwkamp_code_string):
        """
        Converts a Bouwkamp code string into a list of integers. Any parentheses, commas and
        spaces are stripped. Extended Bouwkamp codes are not supported.
        """

        # replace every character (except numbers) with a space
        text = re.sub('[^0-9]', ' ', bouwkamp_code_string)
        # collapse all spaces to just one space
        text = re.sub(' {1,}', ' ', text).strip()
        # split the string into small strings and convert them to integers
        numbers = [int(x) for x in text.split(" ")]

        return numbers

    def draw_bouwkamp_code(self, parent, center, bouwkamp_code):
        """
        Draws the passed Bouwkamp code (a list of integers) with rectangles.
        """

        order = bouwkamp_code[0]
        width = bouwkamp_code[1]
        # height = bouwkamp_code[2]
        code = bouwkamp_code[3:] # cut the first three elements away

        i = 0
        helper = [0] * 900

        for rectangle in range(0, order):
            i = 0
            for j in range(1, width):
                if helper[j] < helper[i]:
                    i = j

            position = (i, helper[i])
            dimension = (code[rectangle], code[rectangle])
            self.draw_rectangle(position, dimension, parent, center)

            for j in range(0, code[rectangle]):
                helper[i+j] += code[rectangle]

    def draw_rectangle(self, position, dimension, parent, center):
        rectangle_style = {
            'opacity': '1',
            'stroke': '#000000',
            'stroke-width': str(self.svg.unittouu('2px')),
            'fill': '#FFFFFF'
        }

        transform = ""
        if not self.options.wrap_in_group:
            transform = 'translate' + str(center)

        rectangle_attributes = {
            'transform': transform,
            'style': str(inkex.Style(rectangle_style)),
            inkex.addNS('label', 'inkscape'): "Rectangle "+str(dimension[0]),
            'x': str(position[0]),
            'y': str(position[1]),
            'width': str(dimension[0]),
            'height': str(dimension[1])
        }

        etree.SubElement(parent, inkex.addNS('rect', 'svg'), rectangle_attributes)

if __name__ == '__main__':
    BouwkampCode().run()
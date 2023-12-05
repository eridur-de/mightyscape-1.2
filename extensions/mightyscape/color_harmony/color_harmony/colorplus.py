#!/usr/bin/env python
# coding=utf-8
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


from math import cos, acos, sqrt, pi
import colorsys
from inkex.colors import Color

_HCY_RED_LUMA = 0.299
_HCY_GREEN_LUMA = 0.587
_HCY_BLUE_LUMA = 0.114

class ColorPlus(Color):

    #HCYwts = 0.299, 0.587, 0.114

    ## HCY colour space.
    #
    # Copy&Paste from https://raw.githubusercontent.com/mypaint/mypaint/master/gui/colors/uicolor.py
    # Copyright (C) 2012-2013 by Andrew Chadwick <andrewc-git@piffle.org>
    #

    # Frequently referred to as HSY, Hue/Chroma/Luma, HsY, HSI etc.  It can be
    # thought of as a cylindrical remapping of the YCbCr solid: the "C" term is the
    # proportion of the maximum permissible chroma within the RGB gamut at a given
    # hue and luma. Planes of constant Y are equiluminant.
    #
    # ref https://code.google.com/p/colour-space-viewer/
    # ref git://anongit.kde.org/kdelibs in kdeui/colors/kcolorspaces.cpp
    # ref http://blog.publicfields.net/2011/12/rgb-hue-saturation-luma.html
    # ref Joblove G.H., Greenberg D., Color spaces for computer graphics.
    # ref http://www.cs.rit.edu/~ncs/color/t_convert.html
    # ref http://en.literateprograms.org/RGB_to_HSV_color_space_conversion_(C)
    # ref http://lodev.org/cgtutor/color.html
    # ref Levkowitz H., Herman G.T., "GLHS: a generalized lightness, hue, and
    #     saturation color model"

    # For consistency, use the same weights that the Color and Luminosity layer
    # blend modes use, as also used by brushlib's Colorize brush blend mode. We
    # follow http://www.w3.org/TR/compositing/ here. BT.601 YCbCr has a nearly
    # identical definition of luma.

    def __init__(self, color=None, space='rgb'):
        super().__init__(color)

    def to_hcy(self):
        """RGB → HCY: R,G,B,H,C,Y ∈ [0, 1]

        :param rgb: Color expressed as an additive RGB triple.
        :type rgb: tuple (r, g, b) where 0≤r≤1, 0≤g≤1, 0≤b≤1.
        :rtype: tuple (h, c, y) where 0≤h<1, but 0≤c≤2 and 0≤y≤1.

        """
        r, g, b = self.to_floats()

        # Luma is just a weighted sum of the three components.
        y = _HCY_RED_LUMA*r + _HCY_GREEN_LUMA*g + _HCY_BLUE_LUMA*b

        # Hue. First pick a sector based on the greatest RGB component, then add
        # the scaled difference of the other two RGB components.
        p = max(r, g, b)
        n = min(r, g, b)
        d = p - n   # An absolute measure of chroma: only used for scaling.
        if n == p:
            h = 0.0
        elif p == r:
            h = (g - b)/d
            if h < 0:
                h += 6.0
        elif p == g:
            h = ((b - r)/d) + 2.0
        else: # p==b
            h = ((r - g)/d) + 4.0
        h /= 6.0

        # Chroma, relative to the RGB gamut envelope.
        if r == g == b:
            # Avoid a division by zero for the achromatic case.
            c = 0.0
        else:
            # For the derivation, see the GLHS paper.
            c = max((y-n)/y, (p-y)/(1-y))
        return h, c, y

    @staticmethod
    def from_hcy(h, c, y):
        """HCY → RGB: R,G,B,H,C,Y ∈ [0, 1]

        :param hcy: Color expressed as a Hue/relative-Chroma/Luma triple.
        :type hcy: tuple (h, c, y) where 0≤h<1, but 0≤c≤2 and 0≤y≤1.
        :rtype: ColorPlus object.

        >>> n = 32
        >>> diffs = [sum( [abs(c1-c2) for c1, c2 in
        ...                zip( HCY_to_RGB(RGB_to_HCY([r/n, g/n, b/n])),
        ...                     [r/n, g/n, b/n] ) ] )
        ...          for r in range(int(n+1))
        ...            for g in range(int(n+1))
        ...              for b in range(int(n+1))]
        >>> sum(diffs) < n*1e-6
        True

        """

        if c == 0:
            return y, y, y

        h %= 1.0
        h *= 6.0
        if h < 1:
            #implies (p==r and h==(g-b)/d and g>=b)
            th = h
            tm = _HCY_RED_LUMA + _HCY_GREEN_LUMA * th
        elif h < 2:
            #implies (p==g and h==((b-r)/d)+2.0 and b<r)
            th = 2.0 - h
            tm = _HCY_GREEN_LUMA + _HCY_RED_LUMA * th
        elif h < 3:
            #implies (p==g and h==((b-r)/d)+2.0 and b>=g)
            th = h - 2.0
            tm = _HCY_GREEN_LUMA + _HCY_BLUE_LUMA * th
        elif h < 4:
            #implies (p==b and h==((r-g)/d)+4.0 and r<g)
            th = 4.0 - h
            tm = _HCY_BLUE_LUMA + _HCY_GREEN_LUMA * th
        elif h < 5:
            #implies (p==b and h==((r-g)/d)+4.0 and r>=g)
            th = h - 4.0
            tm = _HCY_BLUE_LUMA + _HCY_RED_LUMA * th
        else:
            #implies (p==r and h==(g-b)/d and g<b)
            th = 6.0 - h
            tm = _HCY_RED_LUMA + _HCY_BLUE_LUMA * th

        # Calculate the RGB components in sorted order
        if tm >= y:
            p = y + y*c*(1-tm)/tm
            o = y + y*c*(th-tm)/tm
            n = y - (y*c)
        else:
            p = y + (1-y)*c
            o = y + (1-y)*c*(th-tm)/(1-tm)
            n = y - (1-y)*c*tm/(1-tm)

        # Back to RGB order
        if h < 1:   r, g, b = p, o, n
        elif h < 2: r, g, b = o, p, n
        elif h < 3: r, g, b = n, p, o
        elif h < 4: r, g, b = n, o, p
        elif h < 5: r, g, b = o, n, p
        else:       r, g, b = p, n, o

        return ColorPlus([255*r, 255*g, 255*b])

    def to_hsv(self):
        r, g, b = self.to_floats()
        eps = 0.001
        if abs(max(r,g,b)) < eps:
            return (0,0,0)
        return colorsys.rgb_to_hsv(r, g, b)

    @staticmethod
    def from_hsv(h, s, v):
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return ColorPlus([255*r, 255*g, 255*b])

    # TODO: everything below is not updated yet, maybe not really needed
    def hex(self):
        r,g,b = self.getRGB()
        return "#{:02x}{:02x}{:02x}".format(r,g,b)

    def getRgbString(self):
        r,g,b = self.getRGB()
        return "rgb({}, {}, {})".format(r,g,b)

    def getHsvString(self):
        h,s,v = self.getHSV()
        return "hsv({}, {}, {})".format(h,s,v)

    def invert(self):
        r, g, b = self._rgb
        return Color(255-r, 255-g, 255-b)

    def darker(clr, q):
        h,s,v = clr.getHSV()
        v = clip(v-q)
        return hsv(h,s,v)

    def lighter(clr, q):
        h,s,v = clr.getHSV()
        v = clip(v+q)
        return hsv(h,s,v)

    def saturate(clr, q):
        h,s,v = clr.getHSV()
        s = clip(s+q)
        return hsv(h,s,v)

    def desaturate(clr, q):
        h,s,v = clr.getHSV()
        s = clip(s-q)
        return hsv(h,s,v)

    def increment_hue(clr, q):
        h,s,v = clr.getHSV()
        h += q
        if h > 1.0:
            h -= 1.0
        if h < 1.0:
            h += 1.0
        return hsv(h,s,v)

    def contrast(clr, q):
        h,s,v = clr.getHSV()
        v = (v - 0.5)*(1.0 + q) + 0.5
        v = clip(v)
        return hsv(h,s,v)

    def linear(x, y, q):
        return (1.-q)*x + q*y

    def linear3(v1, v2, q):
        x1, y1, z1 = v1
        x2, y2, z2 = v2
        return (linear(x1, x2, q), linear(y1, y2, q), linear(z1, z2, q))

    def circular(h1, h2, q, circle=1.0):
        #print("Src hues: "+ str((h1, h2)))
        d = h2 - h1
        if h1 > h2:
            h1, h2 = h2, h1
            d = -d
            q = 1.0 - q
        if d > circle/2.0:
            h1 = h1 + circle
            h = linear(h1, h2, q)
        else:
            h = h1 + q*d
        if h >= circle:
            h -= circle
        #print("Hue: "+str(h))
        return h

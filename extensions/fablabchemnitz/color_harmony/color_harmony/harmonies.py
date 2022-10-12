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

from math import sqrt, sin, cos
from color_harmony.colorplus import ColorPlus
from color_harmony.utils import seq, circle_hue


# Each of these functions takes one ColorPlus object
# and returns a list of ColorPlus objects:
__all__ = ['opposite', 'splitcomplementary', 'similar', 'similarAndOpposite', 'rectangle', 'nHues', 'fiveColors']

# Harmony functions
# 180° rotation
def opposite(color):
        h, s, v = color.to_hsv()
        h = h + 0.5
        if h > 1.0:
            h -= 1.0
        return [color, ColorPlus.from_hsv(h, s, v)]

# default value 0.5 corresponds to +-36° deviation from opposite, max. useful value: 89°, min. useful value: 1°
def splitcomplementary(color, parameter=0.5):
    h, s, v = color.to_hsv()
    h += (1.0 - 0.4*parameter)/2.0
    if h > 1.0:
        h -= 1.0
    c1 = ColorPlus.from_hsv(h,s,v)
    h += 0.4*parameter
    if h > 1.0:
        h -= 1.0
    c2 = ColorPlus.from_hsv(h,s,v)
    return [color, c1, c2]

# default value 0.5 corresponds to 36° per step, max. useful value: 360°/n , min. useful value: 1°
def similar(color, n, parameter=0.5):
    h, s, v = color.to_hsv()
    step = 0.2 * parameter
    hmin = h - (n // 2) * step
    hmax = h + (n // 2) * step
    return [ColorPlus.from_hsv(dh % 1.0, s, v) for dh in seq(hmin, hmax, step)]

# default value 0.5 corresponds to 36° deviation from original, max. useful value: 178°, min. useful value: 1°
def similarAndOpposite(color, parameter=0.5):
    h, c, y = color.to_hcy()
    h1 = h + 0.2 * parameter
    if h1 > 1.0:
        h1 -= 1.0
    h2 = h - 0.2 * parameter
    if h2 < 0.0:
        h2 += 1.0
    h3 = h + 0.5
    if h3 > 1.0:
        h3 -= 1.0
    return [ColorPlus.from_hcy(h1,c,y),
            color,
            ColorPlus.from_hcy(h2,c,y),
            ColorPlus.from_hcy(h3,c,y)]

# default value 0.5 corresponds to 36° deviation from original, max. useful angle 180°, min. useful angle 1°
def rectangle(color, parameter=0.5):
    h, c, y = color.to_hcy()
    h1 = (h + 0.2 * parameter) % 1.0
    h2 = (h1 + 0.5) % 1.0
    h3 = (h + 0.5) % 1.0
    return [color,
            ColorPlus.from_hcy(h1,c,y),
            ColorPlus.from_hcy(h2,c,y),
            ColorPlus.from_hcy(h3,c,y)]

# returns n colors that are placed on the hue circle in steps of 360°/n 
def nHues(color, n):
    h, s, v = color.to_hsv()
    return [color] + [ColorPlus.from_hsv(circle_hue(i, n, h), s, v) for i in range(1, n)]

# parameter determines +/- deviation from a the hues +/-120° away, default value 0.5 corresponds to 2.16°, max. possible angle 4.32°
def fiveColors(color, parameter=0.5):
    h0, s, v = color.to_hsv()
    h1s = (h0 + 1.0/3.0) % 1.0
    h2s = (h1s + 1.0/3.0) % 1.0
    delta = 0.06 * parameter
    h1 = (h1s - delta) % 1.0
    h2 = (h1s + delta) % 1.0
    h3 = (h2s - delta) % 1.0
    h4 = (h2s + delta) % 1.0
    return [color] + [ColorPlus.from_hsv(h,s,v) for h in [h1,h2,h3,h4]]

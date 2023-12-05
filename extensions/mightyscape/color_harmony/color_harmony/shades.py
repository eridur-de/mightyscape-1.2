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

from color_harmony.colorplus import ColorPlus
from color_harmony.utils import clip, seq, variate

# Shading functions

# 4 cooler colors
def cooler(color, parameter):
    h,s,v = color.to_hsv()
    if h < 1.0/6.0:
        sign = -1.0
    elif h > 2.0/3.0:
        sign = -1.0
    else:
        sign = 1.0
    step = 0.1 * parameter
    result = []
    for i in range(4):
        h += sign * step
        if h > 1.0:
            h -= 1.0
        elif h < 0.0:
            h += 1.0
        result.append(ColorPlus.from_hsv(h, s, v))
    return result

# 4 warmer colors
def warmer(color, parameter):
    h,s,v = color.to_hsv()
    if h < 1.0/6.0:
        sign = +1.0
    elif h > 2.0/3.0:
        sign = +1.0
    else:
        sign = -1.0
    step = 0.1 * parameter
    result = []
    for i in range(4):
        h += sign * step
        if h > 1.0:
            h -= 1.0
        elif h < 0.0:
            h += 1.0
        result.append(ColorPlus.from_hsv(h, s, v))
    return result

# returns 2 less saturated and 2 more saturated colors
def saturation(color, parameter):
    h, s, v = color.to_hsv()
    ss = [clip(x) for x in variate(s, 0.6*parameter, 1.2*parameter)]
    # we don't want another copy of the original color
    del ss[2]
    return [ColorPlus.from_hsv(h, s, v) for s in ss]

# 2 colors with higher value, and 2 with lower
def value(color, parameter):
    h, s, v = color.to_hsv()
    vs = [clip(x) for x in variate(v, 0.4*parameter, 0.8*parameter)]
    del vs[2]
    return [ColorPlus.from_hsv(h, s, v) for v in vs]

# 2 colors with higher chroma, and 2 with lower
def chroma(color, parameter):
    h, c, y = color.to_hcy()
    cs = [clip(x) for x in variate(c, 0.4*parameter, 0.8*parameter)]
    del cs[2]
    return [ColorPlus.from_hcy(h, c, y) for c in cs]

# 2 colors with higher luma, and 2 with lower
def luma(color, parameter):
    h, c, y = color.to_hcy()
    ys = [clip(x) for x in variate(y, 0.3*parameter, 0.6*parameter)]
    del ys[2]
    return [ColorPlus.from_hcy(h, c, y) for y in ys]

# 2 colors with hue rotated to the left, and 2 rotated to the right
def hue(color, parameter):
    h, c, y = color.to_hcy()
    hs = [clip(x) for x in variate(h, 0.15*parameter, 0.3*parameter)]
    del hs[2]
    return [ColorPlus.from_hcy(h, c, y) for h in hs]

def hue_luma(color, parameter):
    h, c, y = color.to_hcy()
    hs = [clip(x) for x in variate(h, 0.15*parameter, 0.3*parameter)]
    ys = [clip(x) for x in variate(y, 0.3*parameter, 0.6*parameter)]
    del ys[2]
    del hs[2]
    return [ColorPlus.from_hcy(h, c, y) for h,y in zip(hs, ys)]

def luma_plus_chroma(color, parameter):
    h, c, y = color.to_hcy()
    cs = [clip(x) for x in variate(c, 0.4*parameter, 0.8*parameter)]
    ys = [clip(x) for x in variate(y, 0.3*parameter, 0.6*parameter)]
    del cs[2]
    del ys[2]
    return [ColorPlus.from_hcy(h, c, y) for c,y in zip(cs, ys)]

def luma_minus_chroma(color, parameter):
    h, c, y = color.to_hcy()
    cs = [clip(x) for x in variate(c, 0.4*parameter, 0.8*parameter)]
    ys = list(reversed([clip(x) for x in variate(y, 0.3*parameter, 0.6*parameter)]))
    del cs[2]
    del ys[2]
    return [ColorPlus.from_hcy(h, c, y) for c,y in zip(cs, ys)]

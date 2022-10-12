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


# Helper functions
def circle_hue(i, n, h, max=1.0):
    h += i * max / n
    if h > max:
        h -= max
    return h

def seq(start, stop, step=1):
    n = int(round((stop - start)/step))
    if n > 1:
        return([start + step*i for i in range(n+1)])
    else:
        return([])

def variate(x, step=1.0, dmin=1.0, dmax=None):
    if dmax is None:
        dmax = dmin
    return seq(x-dmin, x+dmax, step)

def clip(x, min=0.0, max=1.0):
    if x < min:
        #print("{:.2f} clipped up to {:.2f}".format(x, min))
        return min
    if x > max:
        #print("{:.2f} clipped down to {:.2f}".format(x, max))
        return max
    return x

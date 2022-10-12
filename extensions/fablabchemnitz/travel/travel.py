#!/usr/bin/env python3

"""
Copyright (C) 2018 Rich Pang, rpang.contact@gmail.com.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

from __future__ import division
from copy import deepcopy
import inkex
from inkex.paths import Path, CubicSuperPath
from inkex.transforms import Transform 
import numpy as np
from lxml import etree

# rename common numpy operations
abs = np.abs
sin = np.sin
cos = np.cos
tan = np.tan
exp = np.exp
log = np.log
log10 = np.log10

pi = np.pi

__version__ = '0.1'

def split(l, sizes):
    """Split a list into sublists of specific sizes."""
    if not sum(sizes) == len(l):
        raise ValueError('sum(sizes) must equal len(l)')

    sub_lists = []
    ctr = 0
    for size in sizes:
        sub_lists.append(l[ctr:ctr+size])
        ctr += size

    return sub_lists


class Travel(inkex.Effect):
    
    def __init__(self):
        
        # initialize parent class
        inkex.Effect.__init__(self)
        
        # get params entered by user
        self.arg_parser.add_argument('--x_scale', type=float, default=0, help='x scale')
        self.arg_parser.add_argument('--y_scale', type=float, default=0, help='y scale')
        self.arg_parser.add_argument('--t_start', type=float, default=0, help='t start')
        self.arg_parser.add_argument('--t_end', type=float, default=1, help='t_end')
        self.arg_parser.add_argument('--n_steps', type=int, default=10, help='num steps')
        self.arg_parser.add_argument('--fps', type=float, default=0, help='fps')
        self.arg_parser.add_argument('--dt', type=float, default=0, help='dt')
        self.arg_parser.add_argument('--x_eqn', default='', help='x')
        self.arg_parser.add_argument('--y_eqn', default='', help='y')
        self.arg_parser.add_argument('--x_size_eqn', default='', help='x size')
        self.arg_parser.add_argument('--y_size_eqn', default='', help='y size')
        self.arg_parser.add_argument('--theta_eqn', default='', help='theta')
        self.arg_parser.add_argument('--active-tab', default='options', help='active tab')
        
    def effect(self):
        x_scale = self.options.x_scale
        y_scale = self.options.y_scale
        
        t_start = self.options.t_start
        t_end = self.options.t_end
        n_steps = self.options.n_steps
        fps = self.options.fps
        dt = self.options.dt
        
        x_eqn = self.options.x_eqn
        y_eqn = self.options.y_eqn
        
        x_size_eqn = self.options.x_size_eqn
        y_size_eqn = self.options.y_size_eqn
        
        theta_eqn = self.options.theta_eqn

        # get doc root
        svg = self.document.getroot()
        doc_w = self.svg.unittouu(svg.get('width'))
        doc_h = self.svg.unittouu(svg.get('height'))

        # get selected items and validate
        selected = svg.selection.rendering_order()
		
        if not selected:
            inkex.errormsg('Exactly two objects must be selected: a rect and a template. See "help" for details.')
            return
        elif len(selected) != 2:
            inkex.errormsg('Exactly two objects must be selected: a rect and a template. See "help" for details.')
            return

        # rect
        rect = self.svg.selected[self.options.ids[0]]

        if not rect.tag.endswith('rect'):
            inkex.errormsg('Bottom object must be rect. See "help" for usage.')
            return

        # object
        obj = self.svg.selected[self.options.ids[1]]

        if not (obj.tag.endswith('path') or obj.tag.endswith('g')):
            inkex.errormsg('Template object must be path or group of paths. See "help" for usage.')
            return
        if obj.tag.endswith('g'):
            children = obj.getchildren()
            if not all([ch.tag.endswith('path') for ch in children]):
                msg = 'All elements of group must be paths, but they are: '
                msg += ', '.join(['{}'.format(ch) for ch in children])
                inkex.errormsg(msg)
                return
            objs = children
            is_group = True
        else:
            objs = [obj]
            is_group = False

        # get rect params
        w = float(rect.get('width'))
        h = float(rect.get('height'))

        x_rect = float(rect.get('x'))
        y_rect = float(rect.get('y'))

        # lower left corner
        x_0 = x_rect
        y_0 = y_rect + h

        # get object path(s)
        obj_ps = [Path(obj_.get('d')) for obj_ in objs]
        n_segs = [len(obj_p_) for obj_p_ in obj_ps]
        obj_p = sum(obj_ps, [])

        # compute travel parameters
        if not n_steps:
            # compute dt
            if dt == 0:
                dt = 1./fps
            ts = np.arange(t_start, t_end, dt)
        else:
            ts = np.linspace(t_start, t_end, n_steps)

        # compute xs, ys, stretches, and rotations in arbitrary coordinates
        xs = np.nan * np.zeros(len(ts))
        ys = np.nan * np.zeros(len(ts))
        x_sizes = np.nan * np.zeros(len(ts))
        y_sizes = np.nan * np.zeros(len(ts))
        thetas = np.nan * np.zeros(len(ts))
        
        for ctr, t in enumerate(ts):
            xs[ctr] = eval(x_eqn)
            ys[ctr] = eval(y_eqn)
            x_sizes[ctr] = eval(x_size_eqn)
            y_sizes[ctr] = eval(y_size_eqn)
            thetas[ctr] = eval(theta_eqn) * pi / 180

        # ensure no Infs
        if np.any(np.isinf(xs)):
            raise Exception('Inf detected in x(t), please remove.')
            return
        if np.any(np.isinf(ys)):
            raise Exception('Inf detected in y(t), please remove.')
            return
        if np.any(np.isinf(x_sizes)):
            raise Exception('Inf detected in x_size(t), please remove.')
            return
        if np.any(np.isinf(y_sizes)):
            raise Exception('Inf detected in y_size(t), please remove.')
            return
        if np.any(np.isinf(thetas)):
            raise Exception('Inf detected in theta(t), please remove.')
            return

        # convert to screen coordinates
        xs *= (w/x_scale)
        xs += x_0

        ys *= (-h/y_scale)  # neg sign to invert y for inkscape screen
        ys += y_0

        # get obj center
        b_box = Path(obj_p).bounding_box()
        c_x = 0.5 * (b_box.left + b_box.right)
        c_y = 0.5 * (b_box.top + b_box.bottom)

        # get rotation anchor
        if any([k.endswith('transform-center-x') for k in obj.keys()]):
            k_r_x = [k for k in obj.keys() if k.endswith('transform-center-x')][0]
            k_r_y = [k for k in obj.keys() if k.endswith('transform-center-y')][0]
            r_x = c_x + float(obj.get(k_r_x))
            r_y = c_y - float(obj.get(k_r_y))
        else:
            r_x, r_y = c_x, c_y

        paths = []

        # compute new paths
        for x, y, x_size, y_size, theta in zip(xs, ys, x_sizes, y_sizes, thetas):
            path = deepcopy(obj_p)

            # move to origin
            path = Path(path).translate(-x_0, -y_0) 

            # move rotation anchor accordingly
            r_x_1 = r_x - x_0
            r_y_1 = r_y - y_0

            # scale
            path = Path(path).scale(x_size, y_size)

            # scale rotation anchor accordingly
            r_x_2 = r_x_1 * x_size
            r_y_2 = r_y_1 * y_size

            # move to final location
            path = Path(path).translate(x, y)

            # move rotation anchor accordingly
            r_x_3 = r_x_2 + x
            r_y_3 = r_y_2 + y

            # rotate
            path = Path(path).rotate(-theta, (r_x_3, r_y_3))
            paths.append(path)

        parent = self.svg.get_current_layer()
        group = etree.SubElement(parent, inkex.addNS('g', 'svg'), {})

        for path in paths:

            if is_group:
                group_ = etree.SubElement(group, inkex.addNS('g', 'svg'), {})
                path_components = split(path, n_segs)

                for path_component, child in zip(path_components, children):
                    attribs = {
                        k: child.get(k) for k in child.keys()
                    }
                    attribs['d'] = str(Path(path_component))
                    child_copy = etree.SubElement(group_, child.tag, attribs)

            else:
                attribs = {
                    k: obj.get(k) for k in obj.keys()
                }
                attribs['d'] = str(Path(path))
                obj_copy = etree.SubElement(group, obj.tag, attribs)

if __name__ == '__main__':
    Travel().run()
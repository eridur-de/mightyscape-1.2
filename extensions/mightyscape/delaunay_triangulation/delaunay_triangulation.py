#! /usr/bin/python3

'''
Copyright (C) 2020 Scott Pakin, scott-ink@pakin.org

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301, USA.

'''

import inkex
import numpy as np
import random
import sys
from inkex import Group, Line, Polygon, TextElement
from inkex.styles import Style
from inkex.transforms import Vector2d
from scipy.spatial import Delaunay

class DelaunayTriangulation(inkex.EffectExtension):
    'Overlay selected objects with triangles.'

    def add_arguments(self, pars):
        pars.add_argument('--tab', help='The selected UI tab when OK was pressed')
        pars.add_argument('--joggling', type=inkex.Boolean, default=False,  help='Use joggled input instead of merged facets')
        pars.add_argument('--furthest', type=inkex.Boolean, default=False, help='Furthest-site Delaunay triangulation')
        pars.add_argument('--elt_type', default='poly', help='Element type to generate ("poly" or "line")')
        pars.add_argument('--qhull',  help='Triangulation options to pass to qhull')
        pars.add_argument('--fill_type', help='How to fill generated polygons')
        pars.add_argument('--fill_color', type=inkex.Color, help='Fill color to use with a fill type of "specified"')
        pars.add_argument('--stroke_type', help='How to stroke generated polygons')
        pars.add_argument('--stroke_color',  type=inkex.Color, help='Stroke color to use with a stroke type of "specified"')

    def _path_points(self, elt):
        'Return a list of all points on a path (endpoints, not control points).'
        pts = set()
        first = None
        prev = Vector2d()
        for cmd in elt.path.to_absolute():
            if first is None:
                first = cmd.end_point(first, prev)
            ep = cmd.end_point(first, prev)
            pts.add((ep.x, ep.y))
            prev = ep
        return pts

    def _create_styles(self, n):
        'Return a style to use for the generated objects.'
        # Use either the first or the last element's stroke for line caps,
        # stroke widths, etc.
        fstyle = self.svg.selection.first().style
        lstyle = self.svg.selection[-1].style
        if self.options.stroke_type == 'last_sel':
            style = Style(lstyle)
        else:
            style = Style(fstyle)

        # Apply the specified fill color.
        if self.options.fill_type == 'first_sel':
            fcolor = fstyle.get_color('fill')
            style.set_color(fcolor, 'fill')
        elif self.options.fill_type == 'last_sel':
            fcolor = lstyle.get_color('fill')
            style.set_color(fcolor, 'fill')
        elif self.options.fill_type == 'specified':
            style.set_color(self.options.fill_color, 'fill')
        elif self.options.fill_type == 'random':
            pass  # Handled below
        else:
            sys.exit(inkex.utils.errormsg(_('Internal error: Unrecognized fill type "%s".')) % self.options.fill_type)

        # Apply the specified stroke color.
        if self.options.stroke_type == 'first_sel':
            scolor = fstyle.get_color('stroke')
            style.set_color(scolor, 'stroke')
        elif self.options.stroke_type == 'last_sel':
            scolor = lstyle.get_color('stroke')
            style.set_color(scolor, 'stroke')
        elif self.options.stroke_type == 'specified':
            style.set_color(self.options.stroke_color, 'stroke')
        elif self.options.stroke_type == 'random':
            pass  # Handled below
        else:
            sys.exit(inkex.utils.errormsg(_('Internal error: Unrecognized stroke type "%s".')) % self.options.stroke_type)

        # Produce n copies of the style.
        styles = [Style(style) for i in range(n)]
        if self.options.fill_type == 'random':
            for s in styles:
                r = random.randint(0, 255)
                g = random.randint(0, 255)
                b = random.randint(0, 255)
                s.set_color('#%02x%02x%02x' % (r, g, b), 'fill')
                s['fill-opacity'] = 255
        if self.options.stroke_type == 'random':
            for s in styles:
                r = random.randint(0, 255)
                g = random.randint(0, 255)
                b = random.randint(0, 255)
                s.set_color('#%02x%02x%02x' % (r, g, b), 'stroke')
                s['stroke-opacity'] = 255

        # Return the list of styles.
        return [str(s) for s in styles]

    def _create_polygons(self, triangles):
        'Render triangles as SVG polygons.'
        styles = self._create_styles(len(triangles))
        group = self.svg.get_current_layer().add(Group())
        for tri, style in zip(triangles, styles):
            tri_str = ' '.join(['%.10g %.10g' % (pt[0], pt[1]) for pt in tri])
            poly = Polygon()
            poly.set('points', tri_str)
            poly.style = style
            group.add(poly)

    def _create_lines(self, triangles):
        'Render triangles as individual SVG lines.'
        # First, find all unique lines.
        lines = set()
        for tri in triangles:
            if len(tri) != 3:
                sys.exit(inkex.utils.errormsg(_('Internal error: Encountered a non-triangle.')))
            for i, j in [(0, 1), (0, 2), (1, 2)]:
                xy1 = tuple(tri[i])
                xy2 = tuple(tri[j])
                if xy1 < xy2:
                    lines.update([(xy1, xy2)])
                else:
                    lines.update([(xy2, xy1)])

        # Then, create SVG line elements.
        styles = self._create_styles(len(lines))
        group = self.svg.get_current_layer().add(Group())
        for ([(x1, y1), (x2, y2)], style) in zip(lines, styles):
            line = Line()
            line.set('x1', x1)
            line.set('y1', y1)
            line.set('x2', x2)
            line.set('y2', y2)
            line.style = style
            group.add(line)

    def effect(self):
        'Triangulate a set of objects.'

        # Complain if the selection is empty.
        if len(self.svg.selection) == 0:
            return inkex.utils.errormsg(_('Please select at least one object.'))

        # Acquire a set of all points from all selected objects.
        all_points = set()
        warned_text = False
        for obj in self.svg.selection.values():
            if isinstance(obj, TextElement) and not warned_text:
                sys.stderr.write('Warning: Text elements are not currently supported.  Ignoring all text in the selection.\n')
                warned_text = True
            all_points.update(self._path_points(obj.to_path_element()))

        # Use SciPy to perform the Delaunay triangulation.
        pts = np.array(list(all_points))
        if len(pts) == 0:
            return inkex.utils.errormsg(_('No points were found.'))
        qopts = self.options.qhull
        if self.options.joggling:
            qopts = 'QJ ' + qopts
        simplices = Delaunay(pts, furthest_site=self.options.furthest, qhull_options=qopts).simplices

        # Create either triangles or lines, as request.  Either option uses the
        # style of the first object in the selection.
        triangles = []
        for s in simplices:
            try:
                triangles.append(pts[s])
            except IndexError:
                pass
        if self.options.elt_type == 'poly':
            self._create_polygons(triangles)
        elif self.options.elt_type == 'line':
            self._create_lines(triangles)
        else:
            return inkex.utils.errormsg(_('Internal error: unexpected element type "%s".') % self.options.elt_type)

if __name__ == '__main__':
    DelaunayTriangulation().run()

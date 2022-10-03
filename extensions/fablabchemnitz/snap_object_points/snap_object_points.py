#!/usr/bin/env python3

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

from collections import defaultdict
import inkex
from inkex.paths import Arc, Curve, Horz, Line, Move, Quadratic, Smooth, TepidQuadratic, Vert, ZoneClose


class SnapObjectPoints(inkex.EffectExtension):
    "Snap the points on multiple paths towards each other."

    def add_arguments(self, pars):
        pars.add_argument('--max_dist', type=float, default=25.0, help='Maximum distance to be considered a "nearby" point')
        pars.add_argument('--controls', type=inkex.Boolean, default=True, help='Snap control points')
        pars.add_argument('--ends', type=inkex.Boolean, default=True, help='Snap endpoints')
        pars.add_argument('--first_only', type=inkex.Boolean, default=True, help='Modify only the first selected path')

    def _bin_points(self):
        "Associate each path ID with a list of control points and a list of endpoints."
        cpoints = defaultdict(list)
        epoints = defaultdict(list)
        for node in self.svg.selection.filter(inkex.PathElement).values():
            for cmd in node.path.to_absolute().proxy_iterator():
                pid = node.get_id()
                cpoints[pid].extend(cmd.control_points)
                epoints[pid].append(cmd.end_point)
        return cpoints, epoints

    def _find_nearest(self, pid, x0, y0, other_points):
        '''Find the nearest neighbor to a given point, and return the midpoint
        of the given point and its neighbor.'''
        max_dist2 = self.options.max_dist**2  # Work with squares instead of wasting time on square roots.
        bx, by = x0, y0          # Best new point
        best_dist2 = max_dist2   # Minimal distance observed from (x0, y0)
        for k, pts in other_points.items():
            if k == pid:
                continue  # Don't compare to our own points.
            for vec in pts:
                x1, y1 = vec.x, vec.y
                dist2 = (x1 - x0)**2 + (y1 - y0)**2  # Squared distance
                if dist2 > best_dist2:
                    continue  # Not the nearest point
                best_dist2 = dist2
                bx, by = x1, y1
        return (x0 + bx)/2, (y0 + by)/2

    def _simplify_paths(self):
        'Make all commands absolute, and replace Vert and Horz commands with Line.'
        for node in self.svg.selection.filter(inkex.PathElement).values():
            path = node.path.to_absolute()
            new_path = []
            prev = inkex.Vector2d()
            prev_prev = inkex.Vector2d()
            first = inkex.Vector2d()
            for i, cmd in enumerate(path):
                if i == 0:
                    first = cmd.end_point(first, prev)
                    prev, prev_prev = first, first
                if isinstance(cmd, Vert):
                    cmd = cmd.to_line(prev)
                elif isinstance(cmd, Horz):
                    cmd = cmd.to_line(prev)
                new_path.append(cmd)
                if isinstance(cmd, (Curve, Quadratic, Smooth, TepidQuadratic)):
                    prev_prev = list(cmd.control_points(first, prev, prev_prev))[-2]
                prev = cmd.end_point(first, prev)
            node.path = new_path

    def effect(self):
        """Snap control points to other objects' control points and endpoints
        to other objects' endpoints."""
        # This function uses an O(n^2) algorithm, which shouldn't be too slow
        # for typical point counts.
        #
        # As a preprocessing step, we first simplify the paths to reduce the
        # number of special cases we'll need to deal with.  Then, we associate
        # each path with all of its control points and endpoints.
        if len(self.svg.selection.filter(inkex.PathElement)) < 2:
            raise inkex.utils.AbortExtension(_('Snap Object Points requires that at least two paths be selected.'))
        self._simplify_paths()
        cpoints, epoints = self._bin_points()



        # Process in turn each command on each path.
        for node in self.svg.selection.filter(inkex.PathElement).values():
            pid = node.get_id()
            path = node.path
            new_path = []
            for cmd in path:
                args = cmd.args
                new_args = list(args)
                na = len(args)
                if isinstance(cmd, (Curve, Line, Move, Quadratic, Smooth, TepidQuadratic)):
                    # Zero or more control points followed by an endpoint.
                    if self.options.controls:
                        for i in range(0, na - 2, 2):
                            new_args[i], new_args[i + 1] = self._find_nearest(pid, args[i], args[i + 1], cpoints)
                    if self.options.ends:
                        new_args[na - 2], new_args[na - 1] = self._find_nearest(pid, args[na - 2], args[na - 1], epoints)
                elif isinstance(cmd, ZoneClose):
                    # No arguments at all.
                    pass
                elif isinstance(cmd, Arc):
                    # Non-coordinates followed by an endpoint.
                    if self.options.ends:
                        new_args[na - 2], new_args[na - 1] = self._find_nearest(pid, args[na - 2], args[na - 1], epoints)
                else:
                    # Unexpected command.
                    inkex.errormsg(_('Unexpected path command "%s"' % cmd.name))
                new_path.append(cmd.__class__(*new_args))
            node.path = new_path
            if self.options.first_only:
                break

if __name__ == '__main__':
    SnapObjectPoints().run()

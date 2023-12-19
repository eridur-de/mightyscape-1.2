#!/usr/bin/env python3
# coding=utf-8
#
# Copyright (C) 2020 Juergen Weigert, jnweiger@gmail.com
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
# v0.1, 2020-11-08, jw	- initial draught, finding and printing selected nodes to the terminal...
# v0.2, 2020-11-08, jw	- duplicate the selected nodes in their superpaths, write them back.
# v0.3, 2020-11-21, jw	- find "meta-handles"
# v0.4, 2020-11-26, jw	- alpha and trim math added. trimming with a striaght line implemented, needs fixes.
#                         Option 'cut' added.
# v0.5, 2020-11-28, jw	- Cut operation looks correct. Dummy midpoint for large arcs added, looks wrong, of course.
# v1.0, 2020-11-30, jw	- Code completed. Bot cut and arc work fine.
# v1.1, 2020-12-07, jw	- Replaced boolean 'cut' with a method selector 'arc'/'line'. Added round_corners_092.inx
#                         and started backport in round_corners.py -- attempting to run the same code everywhere.
# v1.2, 2020-12-08, jw  - Backporting continued: option parser hack added. Started effect_wrapper() to prepare self.svg
# v1.3, 2020-12-12, jw  - minimalistic compatibility layer for inkscape 0.92.4 done. It now works in both, 1.0 and 0.92!
# v1.4, 2020-12-15, jw  - find_roundable_nodes() added for auto selecting nodes, if none were selected.
#                         And fix https://github.com/jnweiger/inkscape-round-corners/issues/2
# 2021-01-15, Mario Voigt - removed oboslete InkScape 0.92.* stuff
#
# Bad side-effect: As the node count increases during operation, the list of
# selected nodes is incorrect afterwards. We have no way to give inkscape an update.
#
"""
Rounded Corners

This extension operates on selected sharp corner nodes and converts them to a fillet (bevel,chamfer).
An arc shaped path segment with the given radius is inserted smoothly.
The fitted arc is approximated by a bezier spline, as we are doing path operations here.
When the sides at the corner are straight lines, the operation never move the sides, it just shortens them to fit the arc.
When the sides are curved, the arc is placed on the tanget line, and the curve may thus change in shape.

Selected smooth nodes are skipped.
Cases with insufficient space (180deg turn or too short segments/handles) are warned about.

References:
 - https://gitlab.com/inkscape/extensions/-/wikis/home
 - https://gitlab.com/inkscape/extras/extensions-tutorials/-/blob/master/My-First-Effect-Extension.md
 - https://gitlab.com/inkscape/extensions/-/wikis/uploads/25063b4ae6c3396fcda428105c5cff89/template_effect.zip
 - https://inkscape-extensions-guide.readthedocs.io/en/latest/_modules/inkex/elements.html#ShapeElement.get_path
 - https://inkscape.gitlab.io/extensions/documentation/_modules/inkex/paths.html#CubicSuperPath.to_path

 - https://stackoverflow.com/questions/734076/how-to-best-approximate-a-geometrical-arc-with-a-bezier-curve
 - https://hansmuller-flex.blogspot.com/2011/10/more-about-approximating-circular-arcs.html
 - https://itc.ktu.lt/index.php/ITC/article/download/11812/6479         (Riskus' PDF)

The algorithm of arc_bezier_handles() is based on the approach described in:
A. Riškus, "Approximation of a Cubic Bezier Curve by Circular Arcs and Vice Versa,"
Information Technology and Control, 35(4), 2006 pp. 371-378.
"""

import inkex
import sys
import math
import pprint
import copy
import os

__version__ = '1.4'             # Keep in sync with round_corners.inx line 16
debug = False                   # True: babble on controlling tty

max_trim_factor = 0.90          # 0.5: can cut half of a segment length or handle length away for rounding a corner
max_trim_factor_single = 0.98   # 0.98: we can eat up almost everything, as there are no neighbouring trims to be expected.

class RoundCorners(inkex.EffectExtension):

    def add_arguments(self, pars):              # an __init__ in disguise ...
      try:
        self.tty = open("/dev/tty", 'w')
      except:
        self.tty = open(os.devnull, 'w')  # '/dev/null' for POSIX, 'nul' for Windows.
      if debug: print("RoundedCorners ...", file=self.tty)
      self.nodes_inserted = {}
      self.eps = 0.00001                # avoid division by zero
      self.radius = None
      self.max_trim_factor = max_trim_factor

      self.skipped_degenerated = 0      # not a useful corner (e.g. 180deg corner)
      self.skipped_small_count = 0      # not enough room for arc
      self.skipped_small_len = 1e99     # record the shortest handle (or segment) when skipping.

      pars.add_argument("--radius", type=float, default=2.0, help="Radius [mm] to round selected vertices. Default: 2")
      pars.add_argument("--method", type=str, default="arc", help="operation: one of 'arc' (default), 'line'")


    def effect(self):
        if debug:
          # SvgInputMixin __init__: "id:subpath:position of selected nodes, if any"
          print(self.options.selected_nodes, file=self.tty)

        self.radius = math.fabs(self.options.radius)
        self.cut = False
        if self.options.method in ('line'):
          self.cut = True
        if len(self.options.selected_nodes) < 1:
          # find selected objects and construct a list of selected_nodes for them...
          for p in self.options.ids:
            self.options.selected_nodes.extend(self.find_roundable_nodes(p))
          if len(self.options.selected_nodes) < 1:
            raise inkex.AbortExtension("Could not find nodes inside a path. No path objects selected?")

        if len(self.options.selected_nodes) == 1:
          # when we only trim one node, we can eat up almost everything,
          # no need to leave room for rounding neighbour nodes.
          self.max_trim_factor = max_trim_factor_single

        for node in sorted(self.options.selected_nodes):
          ## we walk through the list sorted, so that node indices are processed within a subpath in ascending numeric order.
          ## that makes adjusting index offsets after node inserts easier.
          ss = self.round_corner(node)


    def find_roundable_nodes(self, path_id):
      """ select all nodes of all (sub)paths. except for
          - the last (one or two) nodes of a closed path (which coindide with the first node)
          - the first and last node of an open path (which cannot be smoothed)
      """
      ret = []
      elem = self.svg.getElementById(path_id)
      if elem.tag != '{'+elem.nsmap['svg']+'}path':
        return ret      # ellipse never works.
      try:
        csp = elem.path.to_superpath()
      except:
        return ret

      for sp_idx in range(0, len(csp)):
        sp = csp[sp_idx]
        if len(sp) < 3:
          continue      # subpaths of 2 or less nodes are ignored
        if self.very_close(sp[0], sp[-1]):
          idx_s = 0     # closed paths count from 0 to either n-1 or n-2
          idx_e = len(sp) - 1
          if self.very_close_xy(sp[-2][1], sp[-1][1]):
            idx_e = len(sp) - 2
        else:
          idx_s = 1     # open paths count from 1 to either n-1
          idx_e = len(sp) - 1
        for idx in range(idx_s, idx_e):
          ret.append("%s:%d:%d" % (path_id, sp_idx, idx))

        if debug:
          print("find_roundable_nodes: ", self.options.selected_nodes, file=sys.stderr)
      return ret


    def very_close(self, n1, n2):
      "deep compare. all elements in sub arrays are compared for (very close) numerical equality"
      return self.very_close_xy(n1[0], n2[0]) and self.very_close_xy(n1[1], n2[1]) and self.very_close_xy(n1[2], n2[2])


    def very_close_xy(self, p1, p2):
      "one 2 element array is compared for (very close) numerical equality"
      eps = 1e-9
      return abs(p1[0]-p2[0]) < eps and abs(p1[1]-p2[1]) < eps


    def round_corner(self, node_id):
      """ round the corner at (adjusted) node_idx of subpath
          Side_effect: store (or increment) in self.inserted["pathname:subpath"] how many points were inserted in that subpath.
          the adjusted node_idx is computed by adding that number (if exists) to the value of the node_id before doing any manipulation
      """
      s = node_id.split(":")
      path_id = s[0]
      subpath_idx = int(s[1])
      subpath_id = s[0] + ':' + s[1]
      idx_adjust = self.nodes_inserted.get(subpath_id, 0)
      node_idx = int(s[2]) + idx_adjust

      elem = self.svg.getElementById(path_id)
      if elem is None:
        print("selected_node %s not found in svg document" % node_id, file=sys.stderr)
        return None

      elem.apply_transform()       # modifies path inplace? -- We save later back to the same element. Maybe we should not?
      path = elem.path
      s = path.to_superpath()
      sp = s[subpath_idx]

      ## call the actual path manipulator, record how many nodes were inserted.
      orig_len = len(sp)
      sp = self.subpath_round_corner(sp, node_idx)
      idx_adjust += len(sp) - orig_len

      # convert the superpath back to a normal path
      s[subpath_idx] = sp
      elem.set_path(s.to_path(curves_only=False))
      self.nodes_inserted[subpath_id] = idx_adjust


      # If we picked up the 'd' attribute of a non-path (e.g. star), we must make sure the object now becomes a path.
      # Otherwise inkscape uses the sodipodi data and ignores our changed 'd' attribute.
      if '{'+elem.nsmap['sodipodi']+'}type' in elem.attrib:
        del(elem.attrib['{'+elem.nsmap['sodipodi']+'}type'])

      # Debugging is no longer available or not yet implemented? This explodes, although it is
      # documented in https://inkscape.gitlab.io/extensions/documentation/inkex.command.html
      # inkex.command.write_svg(self.svg, "/tmp/seen.svg")
      # - AttributeError: module 'inkex' has no attribute 'command'
      # But hey, we can always resort to good old ET.dump(self.document) ...


    def super_node(self, sp, node_idx):
      """ In case of node_idx 0, we need to use either the last, the second-last or the third last node as a previous node.
          For a closed subpath, the last node and the first node are identical. Then, the second last node may be still at the
          same location if it has a handle. If so, we take the third last instead. Gah. It has a certain logic...

          In case of the node_idx being the last node, we already know that the subpath is not closed,
          we use 0 as the next node.

          The direction sn.prev.dir does not really point to the coordinate of the previous node, but to the end of the
          next-handle of the prvious node. This is the same when there are straight lines. The absence of handles is
          denoted by having the same coordinates for handle and node.
          Same for next.dir, it points to the next.prev handle.

          The exact implementation here is:
          - sn.next.handle is set to a relative vector that is the tangent of the curve towards the next point.
            we implement four cases:
            - if neither node nor next have handles, the connection is a straight line, and next.handle points
              in the direction of the next node itself.
            - if the curve between node and next is defined by two handles, then sn.next.handle is in the direction of the
              nodes own handle,
            - if the curve between node and next is defined one handle at the node itself, then sn.next.handle is in the
              direction of the nodes own handle,
            - if the curve between node and next is defined one handle at the next node, then sn.next.handle is in the
              direction from the node to the end of that other handle.
          - when trimming back later, we move along that tangent, instead of following the curve.
            That is an approximation when the segment is curved, and exact when it is straight.
            (Finding exact candidate points on curved lines that have tangents with the desired circle
            is beyond me today. Multiple candidates may exist. Any volunteers?)
      """

      prev_idx = node_idx - 1
      sp_node_idx_ = copy.deepcopy(sp[node_idx])        # if this wraps around, at node_idx=0, we may need to tweak the prev handle
      if node_idx == 0:
        prev_idx = len(sp) - 1
        if self.very_close(sp_node_idx_, sp[prev_idx]):
          prev_idx = prev_idx - 1       # skip one node, it is the 'close marker'
          if self.very_close_xy(sp_node_idx_[1], sp[prev_idx][1]):
            # still no distance, skip more. Needed for https://github.com/jnweiger/inkscape-round-corners/issues/2
            sp_node_idx_[0] = sp[prev_idx][0]       # this sp_node_idx_ must acts as if its prev handle is that one.
            prev_idx = prev_idx - 1
        else:
          self.skipped_degenerated += 1         # path ends here.
          return None, None

      # if debug: pprint.pprint({'node_idx': node_idx, 'len(sp)':len(sp), 'sp': sp}, stream=self.tty)
      if node_idx == len(sp)-1:
        self.skipped_degenerated += 1           # path ends here. On a closed loop, we can never select the last point.
        return None, None

      next_idx = node_idx + 1
      if next_idx >= len(sp): next_idx = 0
      t = sp_node_idx_
      p = sp[prev_idx]
      n = sp[next_idx]
      dir1 = [ p[2][0] - t[1][0], p[2][1] - t[1][1] ]           # direction to the previous node (rel coords)
      dir2 = [ n[0][0] - t[1][0], n[0][1] - t[1][1] ]           # direction to the next node (rel coords)
      dist1 = math.sqrt(dir1[0]*dir1[0] + dir1[1]*dir1[1])      # distance to the previous node
      dist2 = math.sqrt(dir2[0]*dir2[0] + dir2[1]*dir2[1])      # distance to the next node
      handle1 = [ t[0][0] - t[1][0], t[0][1] - t[1][1] ]        # handle towards previous node (rel coords)
      handle2 = [ t[2][0] - t[1][0], t[2][1] - t[1][1] ]        # handle towards next node (rel coords)
      if self.very_close_xy(handle1, [ 0, 0 ]): handle1 = dir1
      if self.very_close_xy(handle2, [ 0, 0 ]): handle2 = dir2

      prev = { 'idx': prev_idx, 'dir':dir1, 'handle':handle1 }
      next = { 'idx': next_idx, 'dir':dir2, 'handle':handle2 }
      sn = { 'idx': node_idx, 'prev': prev, 'next': next, 'x': t[1][0], 'y': t[1][1] }

      if dist1 < self.radius:
        if debug:
          print("subpath node_idx=%d, dist to prev(%d) is smaller than radius: %g < %g" %
                (node_idx, prev_idx, dist1, self.radius), file=sys.stderr)
          pprint.pprint(sn, stream=sys.stderr)
        if self.skipped_small_len > dist1: self.skipped_small_len = dist1
        self.skipped_small_count += 1
        return None, None

      if dist2 < self.radius:
        if debug:
          print("subpath node_idx=%d, dist to next(%d) is smaller than radius: %g < %g" %
                (node_idx, next_idx, dist2, self.radius), file=sys.stderr)
          pprint.pprint(sn, stream=sys.stderr)
        if self.skipped_small_len > dist2: self.skipped_small_len = dist2
        self.skipped_small_count += 1
        return None, None

      len_h1 = math.sqrt(handle1[0]*handle1[0] + handle1[1]*handle1[1])
      len_h2 = math.sqrt(handle2[0]*handle2[0] + handle2[1]*handle2[1])
      prev['hlen'] = len_h1
      next['hlen'] = len_h2

      if len_h1 < self.radius:
        if debug:
          print("subpath node_idx=%d, handle to prev(%d) is shorter than radius: %g < %g" %
                (node_idx, prev_idx, len_h1, self.radius), file=sys.stderr)
          pprint.pprint(sn, stream=sys.stderr)
        if self.skipped_small_len > len_h1: self.skipped_small_len = len_h1
        self.skipped_small_count += 1
        return None, None
      if len_h2 < self.radius:
        if debug:
          print("subpath node_idx=%d, handle to next(%d) is shorter than radius: %g < %g" %
                (node_idx, next_idx, len_h2, self.radius), file=sys.stderr)
          pprint.pprint(sn, stream=sys.stderr)
        if self.skipped_small_len > len_h2: self.skipped_small_len = len_h2
        self.skipped_small_count += 1
        return None, None

      if len_h1 > dist1: # shorten that handle to dist1, avoid overshooting the point
        handle1[0] = handle1[0] * dist1 / len_h1
        handle1[1] = handle1[1] * dist1 / len_h1
        prev['hlen'] = dist1
      if len_h2 > dist2: # shorten that handle to dist2, avoid overshooting the point
        handle2[0] = handle2[0] * dist2 / len_h2
        handle2[1] = handle2[1] * dist2 / len_h2
        next['hlen'] = dist2

      return sn, sp_node_idx_


    def arc_c_m_from_super_node(self, s):
      """
      Given the supernode s and the radius self.radius, we compute and return two points:
      c, the center of the arc and m, the midpoint of the arc.

      Method used:
      - construct the ray c_m_vec that runs though the original point p=[x,y] through c and m.
      - next.trim_pt, [x,y] and c form a rectangular triangle. Thus we can
        compute cdist as the length of the hypothenuses under trim and radius.
      - c is then cdist away from [x,y] along the vector c_m_vec.
      - m is closer to [x,y] than c by exactly radius.
      """

      a = [ s['prev']['trim_pt'][0] - s['x'], s['prev']['trim_pt'][1] - s['y'] ]
      b = [ s['next']['trim_pt'][0] - s['x'], s['next']['trim_pt'][1] - s['y'] ]

      c_m_vec = [ a[0] + b[0],
                  a[1] + b[1] ]
      l = math.sqrt( c_m_vec[0]*c_m_vec[0] + c_m_vec[1]*c_m_vec[1] )

      cdist = math.sqrt( self.radius*self.radius + s['trim']*s['trim'] )    # distance [x,y] to circle center c.

      c = [ s['x'] + cdist * c_m_vec[0] / l,                      # circle center
            s['y'] + cdist * c_m_vec[1] / l ]

      m = [ s['x'] + (cdist-self.radius) * c_m_vec[0] / l,        # spline midpoint
            s['y'] + (cdist-self.radius) * c_m_vec[1] / l ]

      return (c, m)


    def arc_bezier_handles(self, p1, p4, c):
      """
      Compute the control points p2 and p3 between points p1 and p4, so that the cubic bezier spline
      defined by p1,p2,p3,p2 approximates an arc around center c

      Algorithm based on Aleksas Riškus and Hans Muller. Sorry Pomax, saw your works too, but did not use any.
      """
      x1,y1 = p1
      x4,y4 = p4
      xc,yc = c

      ax = x1 - xc
      ay = y1 - yc
      bx = x4 - xc
      by = y4 - yc
      q1 = ax * ax + ay * ay
      q2 = q1 + ax * bx + ay * by
      k2 = 4./3. * (math.sqrt(2 * q1 * q2) - q2) / (ax * by - ay * bx)

      x2 = xc + ax - k2 * ay
      y2 = yc + ay + k2 * ax
      x3 = xc + bx + k2 * by
      y3 = yc + by - k2 * bx

      return ([x2, y2], [x3, y3])


    def subpath_round_corner(self, sp, node_idx):
      sn, sp_node_idx_ = self.super_node(sp, node_idx)
      if sn is None: return sp          # do nothing. stderr messages are already printed.

      # The angle to be rounded is now between the vectors a and b
      #
      a = sn['prev']['handle']
      b = sn['next']['handle']
      a_len = sn['prev']['hlen']
      b_len = sn['next']['hlen']
      try:
        # From https://de.wikipedia.org/wiki/Schnittwinkel_(Geometrie)
        # Wikipedia has an abs() in the formula, which extracts the smaller of the two angles.
        # We don't want that. We need to distinguish betwenn spitzwingklig and stumpfwinklig.
        #
        alpha = math.acos( (a[0]*b[0]+a[1]*b[1]) / ( math.sqrt(a[0]*a[0]+a[1]*a[1]) * math.sqrt(b[0]*b[0]+b[1]*b[1]) ) )
      except:
        # Division by 0 error means path folds back on itself here. No space to apply a radius between the segments.
        self.skipped_degenerated += 1
        return sp

      sn['alpha'] = math.degrees(alpha)

      # find the amount to trim back both sides so that a circle of radius self.radius would perfectly fit.
      if alpha < self.eps:
        # path folds back on itself here. No space to apply a radius between the segments.
        self.skipped_degenerated += 1
        return sp
      if abs(alpha - math.pi) < self.eps:
        # stretched. radius won't be visible, that is just fine. No need to warn about that.
        return sp
      trim = self.radius / math.tan(0.5 * alpha)
      sn['trim'] = trim
      if trim < 0.0:
        print("Error: at node_idx=%d: angle=%g°, trim is negative: %g" % (node_idx, math.degrees(alpha), trim), file=sys.stderr)
        return sp

      # a_len points to the previous node. There we can always allow max_trim_factor_single, as the trim was either already done,
      # or will not be done. Only at b_len we need to reserve space for the next trim.
      # FIXME: also allow max_trim_factor_single at b_len, when we find that the very next node will not be rounded.
      #
      available_len = min(max_trim_factor_single*a_len, self.max_trim_factor*b_len)
      if trim > available_len:
        if debug:
          if trim > max_trim_factor_single*a_len:
            print("Skipping where hlen_a %g * max_trim %g < needed_trim %g" % (a_len, max_trim_factor_single, trim), file=self.tty)
          if trim > self.max_trim_factor*b_len:
            print("Skipping where hlen_b %g * max_trim %g < needed_trim %g" % (b_len, self.max_trim_factor, trim), file=self.tty)
          pprint.pprint(sn, stream=self.tty)
        if self.skipped_small_len > available_len:
          self.skipped_small_len = available_len
        self.skipped_small_count += 1
        return sp
      trim_pt_p = [ sn['x'] + a[0] * trim / a_len, sn['y'] + a[1] * trim / a_len ]
      trim_pt_n = [ sn['x'] + b[0] * trim / b_len, sn['y'] + b[1] * trim / b_len ]
      sn['prev']['trim_pt'] = trim_pt_p
      sn['next']['trim_pt'] = trim_pt_n

      if debug:
        pprint.pprint(sn, stream=self.tty)
        pprint.pprint(self.cut, stream=self.tty)
      # We replace the node_idx node by two nodes node_a, node_b.
      # We need an extra middle node node_m if alpha < 90° -- alpha is the angle between the tangents,
      # as the arc spans the remainder to complete 180° an arc with more than 90° needs the midpoint.

      # We preserve the endpoints of the two outside handles if they are non-0-length.
      # We know that such handles are long enough (because of the above max_trim_factor checks)
      # to not flip around when applying the trim.
      # But we move the endpoints of 0-length outside handles with the point when trimming,
      # so that they don't end up on the inside.
      prev_handle = sp_node_idx_[0][:]
      next_handle = sp_node_idx_[2][:]
      if self.very_close_xy(prev_handle, sp_node_idx_[1]): prev_handle = trim_pt_p[:]
      if self.very_close_xy(next_handle, sp_node_idx_[1]): next_handle = trim_pt_n[:]

      p1 = trim_pt_p[:]
      p7 = trim_pt_n[:]
      arc_c, p4 = self.arc_c_m_from_super_node(sn)
      node_a = [ prev_handle, p1[:], p1[:] ]    # deep copy, as we may want to modify the second handle later
      node_b = [ p7[:], p7[:], next_handle ]    # deep copy, as we may want to modify the first handle later

      if alpha >= 0.5*math.pi or self.cut:
        if self.cut == False:
          # p3,p4,p5 do not exist, we need no midpoint
          p2, p6 = self.arc_bezier_handles(p1, p7, arc_c)
          node_a[2] = p2
          node_b[0] = p6
        if node_idx == 0:
          # use prev idx to know about the extra skip. +1 for the node here, +1 for inclusive.
          # CAUTION: Keep in sync below
          sp = [node_a] + [node_b] + sp[1:sn['prev']['idx']+2]
        else:
          sp = sp[:node_idx] + [node_a] + [node_b] + sp[node_idx+1:]
      else:
        p2, p3 = self.arc_bezier_handles(p1, p4, arc_c)
        p5, p6 = self.arc_bezier_handles(p4, p7, arc_c)
        node_m = [ p3, p4, p5 ]
        node_a[2] = p2
        node_b[0] = p6
        if node_idx == 0:
          # use prev idx to know about the extra skip. +1 for the node here, +1 for inclusive.
          # CAUTION: Keep in sync above
          sp = [node_a] + [node_m] + [node_b] + sp[1:sn['prev']['idx']+2]
        else:
          sp = sp[:node_idx] + [node_a] + [node_m] + [node_b] + sp[node_idx+1:]

      # A closed path is formed by making the last node indentical to the first node.
      # So, if we trim at the first node, then duplicte that trim on the last node, to keep the loop closed.
      if node_idx == 0:
        sp[-1][0] = sp[0][0][:]
        sp[-1][1] = sp[0][1][:]
        sp[-1][2] = sp[0][2][:]

      return sp


    def clean_up(self):         # __fini__
      if self.tty is not None:
        self.tty.close()
      super(RoundCorners, self).clean_up()
      if self.skipped_degenerated:
        print("Warning: Skipped %d degenerated nodes (180° turn or end of path?).\n" % self.skipped_degenerated, file=sys.stderr)
      if self.skipped_small_count:
        print("Warning: Skipped %d nodes with not enough space (Value %g is too small. Try again with a smaller radius or only one node selected).\n" % (self.skipped_small_count, self.skipped_small_len), file=sys.stderr)


if __name__ == '__main__':
    RoundCorners().run()

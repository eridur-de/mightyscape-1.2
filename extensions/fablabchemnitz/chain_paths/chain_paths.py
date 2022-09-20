#!/usr/bin/env python3
#
# Inkscape extension making long continuous paths from shorter pieces.
# (C) 2015 juewei@fabmail.org
#
# code snippets visited to learn the extension 'effect' interface:
# - convert2dashes.py
# - http://github.com/jnweiger/inkscape-silhouette
# - http://github.com/jnweiger/inkscape-gears-dev
# - http://sourceforge.net/projects/inkcut/
# - http://code.google.com/p/inkscape2tikz/
# - http://code.google.com/p/eggbotcode/
#
# 2015-11-15 jw, V0.1 -- initial draught
# 2015-11-16 jw, V0.2 -- fixed endpoints after chaining.
# 2015-11-16 jw, V0.3 -- all possible chains connected. Yeah
# 2015-11-16 jw, V0.4 -- gui fully functional.
# 2015-11-26 jw, V0.5 -- HACK to resolve some self-reversing path segments.
#        https://github.com/fablabnbg/inkscape-chain-paths/issues/1
# 2020-04-10 jw, V0.6 -- Close paths correctly. Self reversing path hack was too eager.
#        Workaround for cubicsuperpath.parsePath/formatPath limitation.
#        Started python3 compatibility.
# 2020-05-27 vi, V0.7 -- Upgrade to Inkscape 1.0. Write debug info to inkex debug dialog.

from __future__ import print_function

__version__ = '0.7'        # Keep in sync with chain_paths.inx ca line 22
__author__ = 'Juergen Weigert <juergen@fabmail.org>'
__credits__ = ['Juergen Weigert', 'Veronika Irvine']

import sys
import math
import re
import inkex
from inkex.paths import CubicSuperPath, Path
from optparse import SUPPRESS_HELP
debug = False

class ChainPaths(inkex.EffectExtension):

  def __init__(self):
    inkex.Effect.__init__(self)

    # For handling an SVG viewbox attribute, we will need to know the
    # values of the document's <svg> width and height attributes as well
    # as establishing a transform from the viewbox to the display.
    self.chain_epsilon = 0.01
    self.snap_ends = True
    self.close_loops = True
    self.segments_done = {}
    self.min_missed_distance_sq = None
    self.chained_count = 0

    self.arg_parser.add_argument('-V', '--version', type=inkex.Boolean, default=False, help = 'Just print version number ("' + __version__ + '") and exit.')
    self.arg_parser.add_argument('-s', '--snap_ends', type=inkex.Boolean, default=True, help='snap end-points together when connecting')
    self.arg_parser.add_argument('-c', '--close_loops', type=inkex.Boolean, default=True, help='close loops (start/end of the same path)')
    self.arg_parser.add_argument('-u', '--units', default="mm", help="measurement unit for epsilon")
    self.arg_parser.add_argument('-e', '--chain_epsilon', type=float, default=0.01, help="Max. distance to connect [mm]")

  def version(self):
    return __version__
  def author(self):
    return __author__

  def calc_unit_factor(self, units='mm'):
        """ return the scale factor for all dimension conversions.
            - The document units are always irrelevant as
              everything in inkscape is expected to be in 90dpi pixel units
        """
        dialog_units = self.svg.unittouu(str(1.0)+units)
        self.unit_factor = 1.0 / dialog_units
        return self.unit_factor

  def reverse_segment(self, seg):
    r = []
    for s in reversed(seg):
      # s has 3 elements: handle1, point, handle2
      # Swap handles.
      s.reverse()
      r.append(s)
    return r

  def set_segment_done(self, id, n, msg=''):
    if not id in self.segments_done:
      self.segments_done[id] = {}
    self.segments_done[id][n] = True
    if debug: inkex.utils.debug("done "+str(id)+" "+str(n)+" "+msg)

  def is_segment_done(self, id, n):
    if not id in self.segments_done:
      return False
    if n in self.segments_done[id]:
      return True
    return False

  def link_segments(self, seg1, seg2):
    if self.snap_ends:
      seg = seg1[:-1]
      p1 = seg1[-1]
      p2 = seg2[0]
      # fuse p1 and p2 to create one new point:
      # first handle from p1, point coordinates averaged, second handle from p2
      seg.append([ [  p1[0][0]                 ,  p1[0][1]                  ],
                   [ (p1[1][0] + p2[1][0]) * .5, (p1[1][1] + p2[1][1]) * .5 ],
                   [             p2[2][0]      ,             p2[2][1]       ] ])
      seg.extend(seg2[1:])
    else:
      seg = seg1[:]
      seg.extend(seg2[:])
    self.chained_count += 1
    return seg

  def near_ends(self, end1, end2):
    """ requires self.eps_sq to be the square of the near distance """
    dx = end1[0] - end2[0]
    dy = end1[1] - end2[1]
    d_sq = dx * dx + dy * dy
    if d_sq > self.eps_sq:
      if self.min_missed_distance_sq is None:
        self.min_missed_distance_sq = d_sq
      elif self.min_missed_distance_sq > d_sq:
        self.min_missed_distance_sq = d_sq
      return False
    else:
      return True

  def effect(self):
    if self.options.version:
      print(__version__)
      sys.exit(0)

    self.calc_unit_factor(self.options.units)

    if self.options.snap_ends     is not None: self.snap_ends     = self.options.snap_ends
    if self.options.close_loops   is not None: self.close_loops   = self.options.close_loops
    if self.options.chain_epsilon is not None: self.chain_epsilon = self.options.chain_epsilon
    if self.chain_epsilon < 0.001: self.chain_epsilon = 0.001        # keep a minimum.
    self.eps_sq = self.chain_epsilon * self.unit_factor * self.chain_epsilon * self.unit_factor

    if not len(self.svg.selected.items()):
      inkex.errormsg("Please select one or more objects.")
      return

    segments = []
    for id, node in self.svg.selected.items():
      if node.tag != inkex.addNS('path', 'svg'):
        inkex.errormsg("Object " + id + " is not a path. Try\n  - Path->Object to Path\n  - Object->Ungroup")
        return
      if debug: inkex.utils.debug("id=" + str(id) + ", tag=" + str(node.tag))
      path_d = CubicSuperPath(Path(node.get('d')))
      sub_idx = -1
      for sub in path_d:
        sub_idx += 1
        # sub = [[[200.0, 300.0], [200.0, 300.0], [175.0, 290.0]], [[175.0, 265.0], [220.37694, 256.99876], [175.0, 240.0]], [[175.0, 215.0], [200.0, 200.0], [200.0, 200.0]]]
        # this is a path of three points. All the bezier handles are included. the Structure is:
        # [[handle0_OUT, point0, handle0_1], [handle1_0, point1, handle1_2], [handle2_1, point2, handle2_OUT]]
        # the _OUT handles at the end of the path are ignored. The data structure has them identical to their points.
        #
        if debug: inkex.utils.debug("   sub=" + str(sub))
        end1 = [sub[ 0][1][0], sub[ 0][1][1]]
        end2 = [sub[-1][1][0], sub[-1][1][1]]

        # Remove trivial self revesal when building candidate segments list.
        if ((len(sub) == 3) and self.near_ends(end1, end2)):
          if debug: inkex.utils.debug("dropping segment from self-reversing path, length:"+str(len(sub)))
          sub.pop()
          end2 = [sub[-1][1][0], sub[-1][1][1]]

        segments.append({'id': id, 'n': sub_idx, 'end1': end1, 'end2':end2, 'seg': sub})
      if node.get(inkex.addNS('type', 'sodipodi')):
        del node.attrib[inkex.addNS('type', 'sodipodi')]
    if debug: inkex.utils.debug("-------- seen: ")
    for s in segments:
      if debug: inkex.utils.debug(str(s['id'])+", "+str(s['n'])+", "+str(s['end1'])+", "+str(s['end2']))

    # chain the segments
    obsoleted = 0
    remaining = 0
    for id, node in self.svg.selected.items():
      path_d = CubicSuperPath(Path(node.get('d')))
      # ATTENTION: for parsePath() it is the same, if first and last point coincide, or if the path is really closed.
      path_closed = True if re.search("z\s*$", node.get('d')) else False
      new = []
      cur_idx = -1
      for chain in path_d:
        cur_idx += 1
        if not self.is_segment_done(id, cur_idx):
          # quadratic algorithm: we check both ends of the current segment.
          # If one of them is near another known end from the segments list, we
          # chain this segment to the current segment and remove it from the
          # list,
          # end1-end1 or end2-end2: The new segment is reversed.
          # end1-end2: The new segment is prepended to the current segment.
          # end2-end1: The new segment is appended to the current segment.
          self.set_segment_done(id, cur_idx, "output")        # do not cross with ourselves.
          end1 = [chain[ 0][1][0], chain[ 0][1][1]]
          end2 = [chain[-1][1][0], chain[-1][1][1]]

          # Remove trivial self revesal when doing the actual chain operation.
          if ((len(chain) == 3) and self.near_ends(end1, end2)):
            chain.pop()
            end2 = [chain[-1][1][0], chain[-1][1][1]]

          segments_idx = 0
          while segments_idx < len(segments):
            seg = segments[segments_idx]
            if self.is_segment_done(seg['id'], seg['n']):
              segments_idx += 1
              continue

            if (self.near_ends(end1, seg['end1']) or
                self.near_ends(end2, seg['end2'])):
              seg['seg'] = self.reverse_segment(seg['seg'])
              seg['end1'], seg['end2'] = seg['end2'], seg['end1']
              if debug: inkex.utils.debug("reversed seg " + str(seg['id']) + ", "+str(seg['n']))

            if self.near_ends(end1, seg['end2']):
              # prepend seg to chain
              self.set_segment_done(seg['id'], seg['n'], 'prepended to ' + str(id) + ' ' + str(cur_idx))
              chain = self.link_segments(seg['seg'], chain)
              end1 = [chain[0][1][0], chain[0][1][1]]
              segments_idx = 0          # this chain changed. re-visit all candidate
              continue

            if self.near_ends(end2, seg['end1']):
              # append seg to chain		  
              self.set_segment_done(seg['id'], seg['n'], 'appended to ' + str(id) + ' ' + str(cur_idx))
              chain = self.link_segments(chain, seg['seg'])
              end2 = [chain[-1][1][0], chain[-1][1][1]]
              segments_idx = 0          # this chain changed. re-visit all candidate
              continue

            segments_idx += 1

          # Now all joinable segments are joined.
          # Finally, we can check, if the resulting path is a closed path:
          # Closing a path here, isolates it from the rest.
          # But as we prefer to make the chain as long as possible, we close late.
          if self.near_ends(end1, end2) and not path_closed and self.close_loops:
              if debug: inkex.utils.debug("closing closeable loop " +str(id))
              if self.snap_ends:
                  # move first point to mid position
                  x1n = (chain[0][1][0] + chain[-1][1][0]) * 0.5
                  y1n = (chain[0][1][1] + chain[-1][1][1]) * 0.5
                  chain[0][1][0], chain[0][1][1] = x1n, y1n
                  # merge handle of the last point to the handle of the first point
                  dx0e = chain[-1][0][0] - chain[-1][1][0]
                  dy0e = chain[-1][0][1] - chain[-1][1][1]
                  if debug: inkex.utils.debug("handle diff: "+ str(dx0e) + str(dy0e))
                  # FIXME: this does not work. cubicsuperpath.formatPath() ignores this handle.
                  chain[0][0][0], chain[0][0][1] = x1n+dx0e, y1n+dy0e
                  # drop last point
                  chain.pop()
                  end2 = [chain[-1][1][0], chain[-1][1][1]]
              path_closed = True
              self.chained_count +=1

          new.append(chain)

      if not len(new):
        # node.clear()
        if node.getparent() is not None:
            node.delete()
            obsoleted += 1
            if debug: inkex.utils.debug("Path node obsoleted: " +str(id))
      else:
        remaining += 1
        # BUG: All previously closed loops, are open, after we convert them back with cubicsuperpath.formatPath()
        p_fmt = str(Path(CubicSuperPath(new).to_path().to_arrays()))
        if path_closed: p_fmt += " z"
        if debug: inkex.utils.debug("new path: "+str(p_fmt))
        node.set('d', p_fmt)

    # statistics:
    if debug: inkex.utils.debug("Path nodes obsoleted: "+str(obsoleted) + "\nPath nodes remaining:"+str(remaining))
    if self.min_missed_distance_sq is not None:
      if debug: inkex.utils.debug("min_missed_distance: "+str(math.sqrt(float(self.min_missed_distance_sq))/self.unit_factor)+'>'+str(self.chain_epsilon)+str(self.options.units))
    if debug: inkex.utils.debug("Successful link operations: "+str(self.chained_count))

if __name__ == '__main__':
    ChainPaths().run()
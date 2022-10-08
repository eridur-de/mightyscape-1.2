#!/usr/bin/env python3

# This file is part of Precut.
#
# Precut is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Precut is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Precut.  If not, see <http://www.gnu.org/licenses/>.

# please, stick to pep8 formatting for this file

# seems to be lost in year 2016 https://wiki.inkscape.org/wiki/index.php?title=Inkscape_Extensions&oldid=99881

"""
Migrator: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 13.08.2020

This plugin - initially called "Precut" - was found deeply on web and was nearly lost in translation. Ported to Python 3.0 for InkScape 1.0. This tool finds path intersections within the complete SVG document. Intersections are going to be marked with little squares.
"""

"""
What do we want to check?
=========================

 * any text objects that are not converted to a path?
     * can be implemented as tag blacklist
 * any outlines? they need to be converted to paths
 * check for crossing paths
     * this is the hardest
     * for lines, this is easy, and can, for example, be done with shapely:

       >>> from shapely.geometry import LineString
       >>> l1 = LineString([(0, 0), (1, 1)])
       >>> l2 = LineString([(0, 1), (1, 0)])
       >>> l1.intersects(l2)
       True
       >>> p = l1.intersection(l2)
       >>> p.x
       0.5
       >>> p.y
       0.5
     * check for self-intersection, too (=> line.is_simple)
        * need to split each complex subpath into its segments
        * then, when doing intersections, remove the `boundary`
          from the intersection set, because two adjacent
          segments from a subpath always intersect in their boundary
     * handle the commands M, Z, L, C, Q, A (parsed via simplepath)
        * M: moveto
        * Z: closepath (straight closing line)
        * L: lineto
        * C: curveto (cubic bezier)
        * Q: curveto (quadratic bezier)
        * A: elliptical arc (circles, ellipsis)
 * paths need to have a minimum distance to other paths
 * if two paths are connected ("T-junction"), this junction needs to be
   exempt from the distance check.
"""

from lxml import etree
import inkex
from inkex import bezier
from inkex.paths import Path
from inkex import Color
import sys
import logging

from shapely.geometry import LineString, MultiLineString, Point, MultiPoint, GeometryCollection
from shapely import speedups

if speedups.available:
    speedups.enable()

logger = logging.getLogger(__name__)

def take_N(seq, n):
    """
    split ``seq`` into slices of length ``n``. the total
    length of ``seq` must be a multiple of ``n``.
    """
    if len(seq) % n != 0:
        raise ValueError("len=%d, n=%d, (%s)" % (len(seq), n, seq))
    sub = []
    for elem in seq:
        sub.append(elem)
        if len(sub) == n:
            yield sub
            sub = []


def linear_interp(a, b, t):
    """
    linearly interpolate between ``a`` and ``b``. ``t`` must be a
    a float between 0 and 1.
    """
    return (1 - t) * a + t * b


def sample(start, stop, num):
    """
    interpolate between start and stop, and yield ``num`` samples
    """
    if num == 0:
        return
    delta = 1.0 / num
    t = 0
    for i in range(num):
        yield linear_interp(start, stop, t)
        t += delta


class CheckerResult(object):

    def __init__(self, msg, elem, extra=None, max_len=50):
        self.msg = msg
        self.elem = elem
        self.extra = extra
        self.max_len = max_len
      
    def fmt(self, s):
        s = ", ".join(["%s: %s" % (k, v) for k, v in s.items()])
        if len(s) > self.max_len:
            return s[:50] + u"…"
        return s

    def __unicode__(self):
        msg, elem, extra = self.msg, self.elem, self.extra
        if extra:
            return "%s: %s (%s)" % (msg, elem.get("id"), self.fmt(extra))
        else:
            return "%s: %s" % (msg, elem.get("id"))

    def __repr__(self):
        return "<CheckerResult: %s>" % self.msg


class Checker(object):
    def __call__(self, elem):
        """
        run a check on ``elem`` and yield (elem, message) tuples
        for each failed check
        """
        raise NotImplementedError("please implement __call__")

    def collect(self):
        """
        run a second stage check on aggregated data
        """
        return []


class StyleChecker(Checker):
    def __call__(self, elem):
        style = elem.get("style")
        if style is None:
            return
        parsed = dict(inkex.Style.parse_str(style))
        if "stroke" in parsed and parsed["stroke"] != "none":
            yield CheckerResult("element with stroke found", elem)


class ElemBlacklistChecker(Checker):
    blacklist = ["text"]

    def __call__(self, elem):
        _, tag = elem.tag.rsplit("}", 1)
        if tag in self.blacklist:
            yield CheckerResult("'%s' element found in document" % tag, elem)


class Subpath(object):
    def __init__(self):
        self.points = []
        self.cursor = None

    def __len__(self):
        return len(self.points)

    @property
    def last_point(self):
        if self.points:
            return self.points[-1]

    @property
    def first_point(self):
        if self.points:
            return self.points[0]

    def moveto(self, point):
        assert len(self) == 0, "moveto may only be called at the beginning of a subpath"
        self.points.append(point)
        self.cursor = point

    def lineto(self, point):
        self.points.append(point)
        self.cursor = point

    def curveto(self, points):
        for p in self.approx_curve([self.cursor] + points):
            self.lineto(p)

    def closepath(self):
        self.lineto(self.first_point)

    def add_points(self, points):
        self.points.extend(points)
        self.cursor = points[-1]

    def as_linestring(self):
        return LineString(self.points)

    def approx_curve(self, points):
        for four in take_N(points, 4):
            # TODO: automatically set number of samples depending on length
            for t in sample(0, 1, 50):
                yield bezier.bezierpointatt(four, t)


class IntersectionChecker(Checker):
    def __init__(self):
        self.paths = []

    def __call__(self, elem):
        # logger.debug(elem.attrib)
        path = elem.get("d")
        if path is None:
            return []
        parsed = Path(path).to_arrays()
        self.paths.append((parsed, elem))
        # logger.debug(parsed)
        return []

    def fixVHbehaviour(self, elem):
        raw = Path(elem.get("d")).to_arrays()
        subpaths, prev = [], 0
        for i in range(len(raw)): # Breaks compound paths into simple paths
            if raw[i][0] == 'M' and i != 0:
                subpaths.append(raw[prev:i])
                prev = i
        subpaths.append(raw[prev:])
        seg = []
        for simpath in subpaths:
            if simpath[-1][0] == 'Z':
                simpath[-1][0] = 'L'
                if simpath[-2][0] == 'L': simpath[-1][1] = simpath[0][1]
                else: simpath.pop()
            for i in range(len(simpath)):
                if simpath[i][0] == 'V': # vertical and horizontal lines only have one point in args, but 2 are required
                    #inkex.utils.debug(simpath[i][0])
                    simpath[i][0]='L' #overwrite V with regular L command
                    add=simpath[i-1][1][0] #read the X value from previous segment
                    simpath[i][1].append(simpath[i][1][0]) #add the second (missing) argument by taking argument from previous segment
                    simpath[i][1][0]=add #replace with recent X after Y was appended
                if simpath[i][0] == 'H': # vertical and horizontal lines only have one point in args, but 2 are required
                    #inkex.utils.debug(simpath[i][0])
                    simpath[i][0]='L' #overwrite H with regular L command
                    simpath[i][1].append(simpath[i-1][1][1]) #add the second (missing) argument by taking argument from previous segment				
                #inkex.utils.debug(simpath[i])
                seg.append(simpath[i])
        elem.set("d", Path(seg))
        return seg
        
    def get_line_strings(self):
        # logger.debug("paths: %s", self.paths)
        for path, elem in self.paths:
            path = self.fixVHbehaviour(elem)
            logger.debug("new path, %s", elem.get("id"))
            current_subpath = Subpath()
            for cmd, coords in path:
                logger.debug("  new command: %s", cmd)
                if cmd != "A":
                    points = list(take_N(coords, n=2))
                else:
                    points = list(take_N(coords, n=7))
                logger.debug("  points: %s", points)
                if cmd == "M":
                    # M starts a new subpath
                    if len(current_subpath) > 1:
                        yield current_subpath, elem
                    current_subpath = Subpath()
                    current_subpath.moveto(points[0])
                    # more than one point means the rest of the points are to
                    # be treated as if cmd was L:
                    # http://www.w3.org/TR/SVG/paths.html#PathDataMovetoCommands
                    if len(points) > 1:
                        points = points[1:]
                        cmd = "L"
                if cmd == "L":
                    current_subpath.add_points(points)
                if cmd == "Z":
                    current_subpath.closepath()
                if cmd == "C":
                    current_subpath.curveto(points)
                if cmd == "Q":
                    logger.warning("quadratic beziers are not supported yet")
                    # current_subpath.moveto(points[-1])
                if cmd == "A":
                    logger.warning("elliptic arcs are not supported yet")
            if len(current_subpath) > 1:
                yield current_subpath, elem
            current_subpath = Subpath()

    def collect(self):
        return self.check_intersections()

    def check_intersections(self):
        checks_done = MultiLineString()
        for subpath, elem in self.get_line_strings():
            line = subpath.as_linestring()
            if not line.is_simple:
                # TODO: find location of self-intersection and introduce some
                # tolerance
                # checks_done = checks_done.union(line)
                yield CheckerResult("self-intersection found", elem)
                # continue
            if checks_done.intersects(line):
                intersection = checks_done.intersection(line)
                yield CheckerResult("intersection found", elem, extra={"intersection": intersection})
            checks_done = checks_done.union(line)


class ErrorVisualization(object):
    def __init__(self, svg, effect, color, group_id="precut_errors"):
        self.svg = svg
        self.color = color

        g = svg.find(".//%s[@id='%s']" % (inkex.addNS("g", "svg"), group_id))
        if g is not None:
            self.g = g
        else:
            parent = svg
            attrs = {"id": group_id, "style": "opacity:.5", inkex.addNS("label", "inkscape"): "Precut Errors"}
            self.g = etree.SubElement(parent, inkex.addNS("g", "svg"), attrs)

    def fmt_point(self, point):
        return "%s %s" % point

    def convert(self, geom):
        """
        convert a shapely geometry to SVG
        """

        def vis_line_string(geom):
            path = []
            point_iter = iter(geom.coords)
            head = next(point_iter)
            tail = list(point_iter)
            path.append("M%s" % self.fmt_point(head))
            for point in tail:
                path.append("L%s" % self.fmt_point(point))
            attrs = {"d": " ".join(path), "style": "stroke:%s;stroke-width:5px;" % self.color}
            etree.SubElement(self.g, inkex.addNS("path", "svg"), attrs)

        def vis_point(geom):
            x, y = geom.x, geom.y
            x1, y1 = x - 5, y - 5
            x2, y2 = x - 5, y + 5
            x3, y3 = x + 5, y + 5
            x4, y4 = x + 5, y - 5
            vis_line_string(LineString([(x1, y1), (x2, y2), (x3, y3), (x4, y4), (x1, y1)]))

        def vis_geom_collection(geom):
            for g in geom.geoms:
                self.convert(g)

        converters = {
            LineString: vis_line_string,
            Point: vis_point,
            MultiLineString: vis_geom_collection,
            MultiPoint: vis_geom_collection,
            GeometryCollection: vis_geom_collection,
        }
        converters[geom.__class__](geom)

    def add_error(self, geom):
        self.convert(geom)


class PathIntersections(inkex.Effect):
    def __init__(self, *args, **kwargs):
        self.check_result = []
        self.checkers = [ElemBlacklistChecker(), StyleChecker(), IntersectionChecker()]
        inkex.Effect.__init__(self, *args, **kwargs)
        self.arg_parser.add_argument("--color", type=Color, default='4012452351', help="Error highlight color")

    def walk(self, elem):
        if elem.get("id") == "precut_errors":
            return
        for child in elem.iterchildren():
            self.visit(child)
            self.walk(child)

    def visit(self, elem):
        logger.debug("visiting %s", elem)
        for checker in self.checkers:
            self.check_result.extend(checker(elem))

    def effect(self):
        svg = self.document.getroot()
        self.walk(svg)
        vis = ErrorVisualization(svg, self, color=self.options.color)
        # additional "collect" pass for "global" analysis
        for checker in self.checkers:
            self.check_result.extend(checker.collect())
        for res in self.check_result:
            #print >>sys.stderr, unicode(res).encode("utf8")
            #print(sys.stderr, str(res.encode("utf8")))
            if res.extra and "intersection" in res.extra:
                # TODO: add visualization for other kinds of errors
                vis.add_error(res.extra["intersection"])


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING, format="%(levelname)s %(message)s")
    PathIntersections().run()

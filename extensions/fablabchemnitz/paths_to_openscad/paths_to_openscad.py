#!/usr/bin/env python3
#
# paths2openscad.py
#
# This is an Inkscape extension to output paths to extruded OpenSCAD polygons
# The Inkscape objects must first be converted to paths (Path > Object to
# Path). Some paths may not work well -- the paths have to be polygons.  As
# such, paths derived from text may meet with mixed results.

# Written by Daniel C. Newman ( dan dot newman at mtbaldy dot us )
#
# 2020-06-18
#   Updated by Sillyfrog (https://github.com/sillyfrog) to support
#   Inkscape v1.0 (exclusively, prior versions) are no longer supported).
#   Updated to run under python3 now python2 is end of life.
#
# 10 June 2012
#
# 15 June 2012
#   Updated by Dan Newman to handle a single level of polygon nesting.
#   This is sufficient to handle most fonts.
#   If you want to nest two polygons, combine them into a single path
#   within Inkscape with "Path > Combine Path".
#
# 15 August 2014
#   Updated by Josef Skladanka to automatically set extruded heights
#
# 2017-03-11, juergen@fabmail.org
#   0.12 parse svg width="400mm" correctly. Came out downscaled by 3...
#
# 2017-04-08, juergen@fabmail.org
#   0.13 allow letter 'a' prefix on zsize values for anti-matter.
#        All anti-matter objects are subtracted from all normal objects.
#        raise: Offset along Z axis, to make cut-outs and balconies.
#        Refactored object_merge_extrusion_values() from convertPath().
#        Inheriting extrusion values from enclosing groups.
#
# 2017-04-10, juergen@fabmail.org
#   0.14 Started merging V7 outline mode by Neon22.
#        (http://www.thingiverse.com/thing:1065500)
#        Toplevel object from http://www.thingiverse.com/thing:1286041
#        is already included.
#
# 2017-04-16, juergen@fabmail.org
#   0.15 Fixed https://github.com/fablabnbg/inkscape-paths2openscad/
#        issues/1#issuecomment-294257592
#        Line width of V7 code became a minimum line width,
#        rendering is now based on stroke-width
#        Refactored LengthWithUnit() from getLength()
#        Finished merge with v7 code.
#        Subpath in subpath are now handled very nicely.
#        Added msg_extrude_by_hull_and_paths() outline mode with nested paths.
#
# 2017-06-12, juergen@fabmail.org
#   0.16 Feature added: scale: XXX to taper the object while extruding.

# 2017-06-15, juergen@fabmail.org
#   0.17 scale is now centered on each path. and supports an optional second
#        value for explicit Y scaling. Renamed the autoheight command line
#        option to 'parsedesc' with default true. Renamed dict auto to
#        extrusion. Rephrased all prose to refer to extrusion syntax rather
#        than auto zsize.
# 2017-06-18, juergen@fabmail.org
#   0.18 pep8 relaxed. all hard 80 cols line breaks removed.
#   Refactored the commands into a separate tab in the inx.
#   Added 'View in OpenSCAD' feature with pidfile for single instance.
#
# 2017-08-10, juergen@fabmail.org
#   0.19 fix style="" elements.
#
# 2017-11-14, juergen@fabmail.org
#   0.20 do not traverse into objects with style="display:none"
#       some precondition checks had 'pass' but should have 'continue'.
#
# 2018-01-21, juergen@fabmail.org
#   0.21 start a new openscad instance if the command has changed.
#
# 2018-01-27, juergen@fabmail.org
#   0.22 command comparison fixed. do not use 0.21 !
#
# 2018-02-18, juergen@fabmail.org
#   0.23 fixed rect with x=0 not rendered.
#        FIXME: should really use inksvg.py here too!
#
# 2018.09-09, juergen@fabmail.org
#   0.24 merged module feature, renamed Height,Raise to Zsize,Zoffset
#
# 2019-01-18, juergen@fabmail.org
#   0.25 Allow Depth,Offset instead of Zsize,Zoffset
#   Simplify the syntax description page.
#   Added parameter line_width_scale.
#   Added parameter chamfer, and module chamfer_sphere for doing minkowski
#
# 2020-03-12, juergen@fabmail.org
#   0.26 DEB: relax dependency on 'openscad' to 'openscad | bash'
#
# 2020-04-05, juergen@fabmail.org
#   0.27 Make pep8 happy again. Give proper error message, when file was not saved.
#
# CAUTION: keep the version number in sync with paths2openscad.inx about page

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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
import sys
import os.path
import inkex
import inkex.paths
import inkex.bezier
from inkex.transforms import Transform
import re
import time
import string
import tempfile
import gettext
import subprocess

VERSION = "0.27"  # CAUTION: Keep in sync with all *.inx files
DEFAULT_WIDTH = 100
DEFAULT_HEIGHT = 100
# Parse all these as 56.7 mm zsize:
#  "path1234_56_7_mm", "pat1234____57.7mm", "path1234_57.7__mm"
#
# The verbs Height and Raise are deprecated. Use Zsize and Zoffset, (or Depth and Offset) instead.
RE_AUTO_ZSIZE_ID = re.compile(r".*?_+([aA]?\d+(?:[_\.]\d+)?)_*mm$")
RE_AUTO_ZSIZE_DESC = re.compile(
    r"^(?:[Hh]eight|[Dd]epth|[Zz]-?size):\s*([aA]?\d+(?:\.\d+)?) ?mm$", re.MULTILINE
)
RE_AUTO_SCALE_DESC = re.compile(
    r"^(?:sc|[Ss]cale|[Tt]aper):\s*(\d+(?:\.\d+)?(?: ?, ?\d+(?:\.\d+)?)?) ?%$",
    re.MULTILINE,
)
RE_AUTO_ZOFFSET_DESC = re.compile(
    r"^(?:[Rr]aise|[Zz]-?offset|[Oo]ffset):\s*(\d+(?:\.\d+)?) ?mm$", re.MULTILINE
)
DESC_TAGS = ["desc", inkex.addNS("desc", "svg")]

# CAUTION: keep these defaults in sync with paths2openscad.inx
INX_SCADVIEW = os.getenv("INX_SCADVIEW", "openscad \"{NAME}.scad\"")
INX_SCAD2STL = os.getenv("INX_SCAD2STL", "openscad \"{NAME}.scad\" -o \"{NAME}.stl\"")
INX_STL_POSTPROCESSING = os.getenv("INX_STL_POSTPROCESSING", "cura \"{NAME}.stl\" &")


def IsProcessRunning(pid):
    """
    Windows code from https://stackoverflow.com/questions/7647167/check-if-a-process-is-running-in-python-in-linux-unix
    """
    sys_platform = sys.platform.lower()
    if sys_platform.startswith("win"):
        with subprocess.Popen(r'tasklist.exe /NH /FI "PID eq %d"' % (pid),  shell=True, stdout=subprocess.PIPE) as ps:
            output = ps.stdout.read()
            ps.wait()
            if str(pid) in output:
                return True
            return False
    else:
        # OSX sys_platform.startswith('darwin'):
        # and Linux
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def parseLengthWithUnits(str, default_unit="px"):
    """
    Parse an SVG value which may or may not have units attached
    This version is greatly simplified in that it only allows: no units,
    units of px, and units of %.  Everything else, it returns None for.
    There is a more general routine to consider in scour.py if more
    generality is ever needed.
    With inkscape 0.91 we need other units too: e.g. svg:width="400mm"
    """

    u = default_unit
    s = str.strip()
    if s[-2:] in ("px", "pt", "pc", "mm", "cm", "in", "ft"):
        u = s[-2:]
        s = s[:-2]
    elif s[-1:] in ("m", "%"):
        u = s[-1:]
        s = s[:-1]

    try:
        v = float(s)
    except Exception:
        return None, None

    return v, u


def pointInBBox(pt, bbox):
    """
    Determine if the point pt=[x, y] lies on or within the bounding
    box bbox=[xmin, xmax, ymin, ymax].
    """

    # if ( x < xmin ) or ( x > xmax ) or ( y < ymin ) or ( y > ymax )
    if (pt[0] < bbox[0]) or (pt[0] > bbox[1]) or (pt[1] < bbox[2]) or (pt[1] > bbox[3]):
        return False
    else:
        return True


def bboxInBBox(bbox1, bbox2):
    """
    Determine if the bounding box bbox1 lies on or within the
    bounding box bbox2.  NOTE: we do not test for strict enclosure.

    Structure of the bounding boxes is

    bbox1 = [ xmin1, xmax1, ymin1, ymax1 ]
    bbox2 = [ xmin2, xmax2, ymin2, ymax2 ]
    """

    # if ( xmin1 < xmin2 ) or ( xmax1 > xmax2 ) or
    # ( ymin1 < ymin2 ) or ( ymax1 > ymax2 )

    if (
        (bbox1[0] < bbox2[0])
        or (bbox1[1] > bbox2[1])
        or (bbox1[2] < bbox2[2])
        or (bbox1[3] > bbox2[3])
    ):
        return False
    else:
        return True


def pointInPoly(p, poly, bbox=None):
    """
    Use a ray casting algorithm to see if the point p = [x, y] lies within
    the polygon poly = [[x1,y1],[x2,y2],...].  Returns True if the point
    is within poly, lies on an edge of poly, or is a vertex of poly.
    """

    if (p is None) or (poly is None):
        return False

    # Check to see if the point lies outside the polygon's bounding box
    if bbox is not None:
        if not pointInBBox(p, bbox):
            return False

    # Check to see if the point is a vertex
    if p in poly:
        return True

    # Handle a boundary case associated with the point
    # lying on a horizontal edge of the polygon
    x = p[0]
    y = p[1]
    p1 = poly[0]
    p2 = poly[1]
    for i in range(len(poly)):
        if i != 0:
            p1 = poly[i - 1]
            p2 = poly[i]
        if (
            (y == p1[1])
            and (p1[1] == p2[1])
            and (x > min(p1[0], p2[0]))
            and (x < max(p1[0], p2[0]))
        ):
            return True

    n = len(poly)
    inside = False

    p1_x, p1_y = poly[0]
    for i in range(n + 1):
        p2_x, p2_y = poly[i % n]
        if y > min(p1_y, p2_y):
            if y <= max(p1_y, p2_y):
                if x <= max(p1_x, p2_x):
                    if p1_y != p2_y:
                        intersect = p1_x + (y - p1_y) * (p2_x - p1_x) / (p2_y - p1_y)
                        if x <= intersect:
                            inside = not inside
                    else:
                        inside = not inside
        p1_x, p1_y = p2_x, p2_y

    return inside


def polyInPoly(poly1, bbox1, poly2, bbox2):
    """
    Determine if polygon poly2 = [[x1,y1],[x2,y2],...]
    contains polygon poly1.

    The bounding box information, bbox=[xmin, xmax, ymin, ymax]
    is optional.  When supplied it can be used to perform rejections.
    Note that one bounding box containing another is not sufficient
    to imply that one polygon contains another.  It's necessary, but
    not sufficient.
    """

    # See if poly1's bboundin box is NOT contained by poly2's bounding box
    # if it isn't, then poly1 cannot be contained by poly2.

    if (bbox1 is not None) and (bbox2 is not None):
        if not bboxInBBox(bbox1, bbox2):
            return False

    # To see if poly1 is contained by poly2, we need to ensure that each
    # vertex of poly1 lies on or within poly2

    for p in poly1:
        if not pointInPoly(p, poly2, bbox2):
            return False

    # Looks like poly1 is contained on or in Poly2

    return True


def subdivideCubicPath(sp, flat, i=1):
    """
    [ Lifted from eggbot.py with impunity ]

    Break up a bezier curve into smaller curves, each of which
    is approximately a straight line within a given tolerance
    (the "smoothness" defined by [flat]).

    This is a modified version of cspsubdiv.cspsubdiv(): rewritten
    because recursion-depth errors on complicated line segments
    could occur with cspsubdiv.cspsubdiv().
    """

    while True:
        while True:
            if i >= len(sp):
                return

            p0 = sp[i - 1][1]
            p1 = sp[i - 1][2]
            p2 = sp[i][0]
            p3 = sp[i][1]

            b = (p0, p1, p2, p3)

            if inkex.bezier.maxdist(b) > flat:
                break

            i += 1

        one, two = inkex.bezier.beziersplitatt(b, 0.5)
        sp[i - 1][2] = one[1]
        sp[i][0] = two[2]
        p = [one[2], one[3], two[1]]
        sp[i:1] = [p]


def msg_linear_extrude(id, prefix):
    msg = (
        "    translate (%s_%d_center) linear_extrude(height=h, convexity=10, scale=0.01*s)\n"
        + "      translate (-%s_%d_center) polygon(%s_%d_points);\n"
    )
    return msg % (id, prefix, id, prefix, id, prefix)


def msg_linear_extrude_by_paths(id, prefix):
    msg = (
        "    translate (%s_%d_center) linear_extrude(height=h, convexity=10, scale=0.01*s)\n"
        + "      translate (-%s_%d_center) polygon(%s_%d_points, %s_%d_paths);\n"
    )
    return msg % (id, prefix, id, prefix, id, prefix, id, prefix)


def msg_extrude_by_hull(id, prefix):
    msg = (
        "    for (t = [0: len(%s_%d_points)-2]) {\n" % (id, prefix)
        + "      hull() {\n"
        + "        translate(%s_%d_points[t]) \n" % (id, prefix)
        + "          cylinder(h=h, r=w/2, $fn=res);\n"
        + "        translate(%s_%d_points[t + 1]) \n" % (id, prefix)
        + "          cylinder(h=h, r=w/2, $fn=res);\n"
        + "      }\n"
        + "    }\n"
    )
    return msg


def msg_extrude_by_hull_and_paths(id, prefix):
    msg = (
        "    for (p = [0: len(%s_%d_paths)-1]) {\n" % (id, prefix)
        + "      pp = %s_%d_paths[p];\n" % (id, prefix)
        + "      for (t = [0: len(pp)-2]) {\n"
        + "        hull() {\n"
        + "          translate(%s_%d_points[pp[t]])\n" % (id, prefix)
        + "            cylinder(h=h, r=w/2, $fn=res);\n"
        + "          translate(%s_%d_points[pp[t+1]])\n" % (id, prefix)
        + "            cylinder(h=h, r=w/2, $fn=res);\n"
        + "        }\n"
        + "      }\n"
        + "    }\n"
    )
    return msg


def remove_umlaut(string):
    """
    Removes umlauts from strings and replaces them with the letter+e convention
    :param string: string to remove umlauts from
    :return: unumlauted string
    """
    u = 'ü'.encode()
    U = 'Ü'.encode()
    a = 'ä'.encode()
    A = 'Ä'.encode()
    o = 'ö'.encode()
    O = 'Ö'.encode()
    ss = 'ß'.encode()

    string = string.encode()
    string = string.replace(u, b'ue')
    string = string.replace(U, b'Ue')
    string = string.replace(a, b'ae')
    string = string.replace(A, b'Ae')
    string = string.replace(o, b'oe')
    string = string.replace(O, b'Oe')
    string = string.replace(ss, b'ss')

    string = string.decode('utf-8')
    return string

class PathsToOpenSCAD(inkex.EffectExtension):

    def add_arguments(self, pars):
        inkex.localization.localize()  # does not help for localizing my *.inx file

        pars.add_argument( "--tab", default="splash", help="The active tab when Apply was pressed", )
        pars.add_argument( "--smoothness", type=float, default=float(0.2), help="Curve smoothing (less for more)", )
        pars.add_argument( "--chamfer", type=float, default=float(1.), help="Add a chamfer radius, displacing all object walls outwards [mm]", )
        pars.add_argument( "--chamfer_fn", type=int, default=int(4), help="Chamfer precision ($fn when generating the minkowski sphere)", )
        pars.add_argument( "--zsize", default="5", help="Depth (Z-size) [mm]", )
        pars.add_argument( "--min_line_width", type=float, default=float(1), help="Line width for non closed curves [mm]", )
        pars.add_argument( "--line_width_scale_perc", type=float, default=float(1), help="Percentage of SVG line width. Use e.g. 26.46 to compensate a px/mm confusion. Default: 100 [%]", )
        pars.add_argument( "--line_fn", type=int, default=int(4), help="Line width precision ($fn when constructing hull)", )
        pars.add_argument( "--force_line", type=inkex.utils.Boolean, default=False, help="Force outline mode.", )
        pars.add_argument( "--fname", default="{NAME}.scad", help="openSCAD output file derived from the svg file name.", )
        pars.add_argument( "--parsedesc",  type=inkex.utils.Boolean, default=True, help="Parse zsize and other parameters from object descriptions", )
        pars.add_argument( "--scadview",  type=inkex.utils.Boolean, default=False, help="Open the file with openscad ( details see --scadviewcmd option )", )
        pars.add_argument( "--scadviewcmd", default=INX_SCADVIEW, help="Command used start an openscad viewer. Use {SCAD} for the openSCAD input.", )
        pars.add_argument( "--scad2stl",  type=inkex.utils.Boolean, default=False, help="Also convert to STL ( details see --scad2stlcmd option )", )
        pars.add_argument( "--scad2stlcmd", default=INX_SCAD2STL, help="Command used to convert to STL. You can use {NAME}.scad for the openSCAD file to read and "
        + "{NAME}.stl for the STL file to write.", )
        pars.add_argument( "--stlpost",  type=inkex.utils.Boolean, default=False, help="Start e.g. a slicer. This implies the --scad2stl option. ( see --stlpostcmd )", )
        pars.add_argument( "--stlpostcmd", default=INX_STL_POSTPROCESSING, help="Command used for post processing an STL file (typically a slicer). You can use {NAME}.stl for the STL file.", )
        pars.add_argument( "--stlmodule", type=inkex.utils.Boolean, default=False, help="Output configured to comment out final rendering line, to create a module file for import.", )

        self.userunitsx = 1.0  # Move to pure userunits per mm for v1.0
        self.userunitsy = 1.0
        self.px_used = False  # raw px unit depends on correct dpi.
        self.cx = float(DEFAULT_WIDTH) / 2.0
        self.cy = float(DEFAULT_HEIGHT) / 2.0
        self.xmin, self.xmax = (1.0E70, -1.0E70)
        self.ymin, self.ymax = (1.0E70, -1.0E70)

        # Dictionary of paths we will construct.  It's keyed by the SVG node
        # it came from.  Such keying isn't too useful in this specific case,
        # but it can be useful in other applications when you actually want
        # to go back and update the SVG document
        self.paths = {}

        # Output file handling
        self.call_list = []
        self.call_list_neg = []  # anti-matter (holes via difference)
        self.pathid = int(0)

        # Output file
        outfile = None

        # For handling an SVG viewbox attribute, we will need to know the
        # values of the document's <svg> width and height attributes as well
        # as establishing a transform from the viewbox to the display.

        self.docWidth = float(DEFAULT_WIDTH)
        self.docHeight = float(DEFAULT_HEIGHT)
        self.docTransform = Transform(None)

        # Dictionary of warnings issued.  This to prevent from warning
        # multiple times about the same problem
        self.warnings = {}

    def getLength(self, name, default):

        """
        Get the <svg> attribute with name "name" and default value "default"
        Parse the attribute into a value and associated units.  Then, accept
        units of cm, ft, in, m, mm, pc, or pt.  Convert to pixels.

        Note that SVG defines 90 px = 1 in = 25.4 mm.
        Note: Since inkscape 0.92 we use the CSS standard of 96 px = 1 in.
        """
        str = self.document.getroot().get(name)
        if str:
            return self.LengthWithUnit(str)
        else:
            # No width specified; assume the default value
            return float(default)

    def LengthWithUnit(self, strn, default_unit="px"):
        v, u = parseLengthWithUnits(strn, default_unit)
        if v is None:
            # Couldn't parse the value
            return None
        elif u == "mm":
            return float(v) * (self.userunitsx)
        elif u == "cm":
            return float(v) * (self.userunitsx * 10.0)
        elif u == "m":
            return float(v) * (self.userunitsx * 1000.0)
        elif u == "in":
            return float(v) * self.userunitsx * 25.4
        elif u == "ft":
            return float(v) * 12.0 * self.userunitsx * 25.4
        elif u == "pt":
            # Use modern "Postscript" points of 72 pt = 1 in instead
            # of the traditional 72.27 pt = 1 in
            return float(v) * (self.userunitsx * 25.4 / 72.0)
        elif u == "pc":
            return float(v) * (self.userunitsx * 25.4 / 6.0)
        elif u == "px":
            self.px_used = True
            return float(v)
        else:
            # Unsupported units
            return None

    def getDocProps(self):
        """
        Get the document's height and width attributes from the <svg> tag.
        Use a default value in case the property is not present or is
        expressed in units of percentages.
        """
        self.inkscape_version = self.document.getroot().get(
            "{http://www.inkscape.org/namespaces/inkscape}version"
        )
        sodipodi_docname = self.document.getroot().get(
            "{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}docname"
        )
        if sodipodi_docname is None:
            sodipodi_docname = "inkscape"
            # the document was not saved. We can assume it is v1 inkscape
        self.basename = re.sub(r"\.SVG", "", sodipodi_docname, flags=re.I).rsplit('/', 1)[-1]
        self.docHeight = self.getLength("height", DEFAULT_HEIGHT)
        self.docWidth = self.getLength("width", DEFAULT_WIDTH)

        if (self.docHeight is None) or (self.docWidth is None):
            return False
        else:
            return True

    def handleViewBox(self):
        """
        Set up the document-wide transform in the event that the document has
        an SVG viewbox, which it should as of v1.0
        For details, see https://wiki.inkscape.org/wiki/index.php/Units_In_Inkscape
        """

        if self.getDocProps():
            viewbox = self.document.getroot().get("viewBox")
            if viewbox:
                vinfo = viewbox.strip().replace(",", " ").split()
                vinfo = [float(i) for i in vinfo]
                unitsx = abs(vinfo[0] - vinfo[2])
                # unitsy = abs(vinfo[1] - vinfo[3])
                self.userunitsx = self.docWidth / unitsx
                # The above wiki page suggests that x and y scaling maybe different
                # however in practice they are not
                self.userunitsy = self.userunitsx
                self.docTransform = Transform(
                    "scale(%f,%f)" % (self.userunitsx, self.userunitsy)
                )

    def getPathVertices(self, path, node=None, transform=None):
        """
        Decompose the path data from an SVG element into individual
        subpaths, each subpath consisting of absolute move to and line
        to coordinates.  Place these coordinates into a list of polygon
        vertices.
        """
        if not path:
            # Path must have been devoid of any real content
            return None

        # Get a cubic super path
        p = inkex.paths.CubicSuperPath(path)
        if (not p) or (len(p) == 0):
            # Probably never happens, but...
            return None

        if transform:
            p = p.transform(transform)

        # Now traverse the cubic super path
        subpath_list = []
        subpath_vertices = []

        sp_xmin = None
        sp_xmax = None
        sp_ymin = None
        sp_ymax = None
        for sp in p:

            # We've started a new subpath
            # See if there is a prior subpath and whether we should keep it
            if len(subpath_vertices):
                subpath_list.append(
                    [subpath_vertices, [sp_xmin, sp_xmax, sp_ymin, sp_ymax]]
                )

            subpath_vertices = []
            subdivideCubicPath(sp, float(self.options.smoothness))

            # Note the first point of the subpath
            first_point = sp[0][1]
            subpath_vertices.append(first_point)
            sp_xmin = first_point[0]
            sp_xmax = first_point[0]
            sp_ymin = first_point[1]
            sp_ymax = first_point[1]

            n = len(sp)

            # Traverse each point of the subpath
            for csp in sp[1:n]:

                # Append the vertex to our list of vertices
                pt = csp[1]
                subpath_vertices.append(pt)

                # Track the bounding box of this subpath
                if pt[0] < sp_xmin:
                    sp_xmin = pt[0]
                elif pt[0] > sp_xmax:
                    sp_xmax = pt[0]
                if pt[1] < sp_ymin:
                    sp_ymin = pt[1]
                elif pt[1] > sp_ymax:
                    sp_ymax = pt[1]

            # Track the bounding box of the overall drawing
            # This is used for centering the polygons in OpenSCAD around the
            # (x,y) origin
            if sp_xmin < self.xmin:
                self.xmin = sp_xmin
            if sp_xmax > self.xmax:
                self.xmax = sp_xmax
            if sp_ymin < self.ymin:
                self.ymin = sp_ymin
            if sp_ymax > self.ymax:
                self.ymax = sp_ymax

        # Handle the final subpath
        if len(subpath_vertices):
            subpath_list.append(
                [subpath_vertices, [sp_xmin, sp_xmax, sp_ymin, sp_ymax]]
            )

        if len(subpath_list) > 0:
            self.paths[node] = subpath_list

    def getPathStyle(self, node):
        style = node.get("style", "")
        # .get default is not reliable, ensure value is a string
        if not style:
            style = ""
        ret = {}
        # fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:10;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1
        for elem in style.split(";"):
            if len(elem):
                try:
                    (key, val) = elem.strip().split(":")
                except Exception:
                    inkex.errormsg(
                        "unparsable element '{1}' in style '{0}'".format(elem, style)
                    )
                ret[key] = val
        return ret

    def convertPath(self, node, outfile):
        def object_merge_extrusion_values(extrusion, node):

            """ Parser for description and ID fields for extrusion parameters.
                This recurse into parents, to inherit values from enclosing
                groups.
            """
            p = node.getparent()
            if p is not None and p.tag in (inkex.addNS("g", "svg"), "g"):
                object_merge_extrusion_values(extrusion, p)

            # let the node override inherited values
            rawid = node.get("id", "")
            if rawid is not None:
                zsize = RE_AUTO_ZSIZE_ID.findall(rawid)
                if zsize:
                    extrusion["zsize"] = zsize[-1].replace("_", ".")
            # let description contents override id contents.
            for tagname in DESC_TAGS:
                desc_node = node.find("./%s" % tagname)
                if desc_node is not None:
                    zsize = RE_AUTO_ZSIZE_DESC.findall(desc_node.text)
                    if zsize:
                        extrusion["zsize"] = zsize[-1]
                    zscale = RE_AUTO_SCALE_DESC.findall(desc_node.text)
                    if zscale:
                        if "," in zscale[-1]:
                            extrusion["scale"] = "[" + zscale[-1] + "]"
                        else:
                            extrusion["scale"] = zscale[-1]
                    zoffset = RE_AUTO_ZOFFSET_DESC.findall(desc_node.text)
                    if zoffset:
                        extrusion["zoffset"] = zoffset[-1]
            if extrusion["zsize"][0] in ("a", "A"):
                extrusion["neg"] = True
                extrusion["zsize"] = extrusion["zsize"][1:]
            # END object_merge_extrusion_values

        path = self.paths[node]
        if (path is None) or (len(path) == 0):
            return

        # Determine which polys contain which

        contains = [[] for i in range(len(path))]
        contained_by = [[] for i in range(len(path))]

        for i in range(0, len(path)):
            for j in range(i + 1, len(path)):
                if polyInPoly(path[j][0], path[j][1], path[i][0], path[i][1]):
                    # subpath i contains subpath j
                    contains[i].append(j)
                    # subpath j is contained in subpath i
                    contained_by[j].append(i)
                elif polyInPoly(path[i][0], path[i][1], path[j][0], path[j][1]):
                    # subpath j contains subpath i
                    contains[j].append(i)
                    # subpath i is contained in subpath j
                    contained_by[i].append(j)

        # Generate an OpenSCAD module for this path
        rawid = node.get("id", "")
        if (rawid is None) or (rawid == ""):
            id = str(self.pathid) + "x"
            rawid = id
            self.pathid += 1
        else:
            id = re.sub("[^A-Za-z0-9_]+", "", rawid)

        style = self.getPathStyle(node)
        stroke_width = style.get("stroke-width", "1")

        # FIXME: works with document units == 'mm', but otherwise untested..
        stroke_width_mm = self.LengthWithUnit(stroke_width, default_unit="mm")
        stroke_width_mm = str(stroke_width_mm * self.userunitsx)  # px to mm
        fill_color = style.get("fill", "#FFF")
        if fill_color == "none":
            filled = False
        else:
            filled = True
        if filled is False and style.get("stroke", "none") == "none":
            inkex.errormsg(
                "WARNING: " + rawid + " has fill:none and stroke:none, object ignored."
            )
            return

        # #### global data for msg_*() functions. ####
        # fold subpaths into a single list of points and index paths.
        prefix = 0
        for i in range(0, len(path)):
            # Skip this subpath if it is contained by another one
            if len(contained_by[i]) != 0:
                continue
            subpath = path[i][0]
            bbox = path[i][1]  # [xmin, xmax, ymin, ymax]

            #
            polycenter = (
                id
                + "_"
                + str(prefix)
                + "_center = [%f,%f]"
                % (
                    (bbox[0] + bbox[1]) * .5 - self.cx,
                    (bbox[2] + bbox[3]) * .5 - self.cy,
                )
            )
            polypoints = id + "_" + str(prefix) + "_points = ["
            # polypaths = [[0,1,2], [3,4,5]]   # this path is two triangle
            polypaths = id + "_" + str(prefix) + "_paths = [["
            if len(contains[i]) == 0:
                # This subpath does not contain any subpaths
                for point in subpath:
                    polypoints += "[%f,%f]," % (
                        (point[0] - self.cx),
                        (point[1] - self.cy),
                    )
                polypoints = polypoints[:-1]
                polypoints += "];\n"
                outfile.write(polycenter + ";\n")
                outfile.write(polypoints)
                prefix += 1
            else:
                # This subpath contains other subpaths
                # collect all points into polypoints
                # also collect the indices into polypaths
                for point in subpath:
                    polypoints += "[%f,%f]," % (
                        (point[0] - self.cx),
                        (point[1] - self.cy),
                    )
                count = len(subpath)
                for k in range(0, count):
                    polypaths += "%d," % (k)
                polypaths = polypaths[:-1] + "],\n\t\t\t\t["
                # The nested paths
                for j in contains[i]:
                    for point in path[j][0]:
                        polypoints += "[%f,%f]," % (
                            (point[0] - self.cx),
                            (point[1] - self.cy),
                        )
                    for k in range(count, count + len(path[j][0])):
                        polypaths += "%d," % k
                    count += len(path[j][0])
                    polypaths = polypaths[:-1] + "],\n\t\t\t\t["
                polypoints = polypoints[:-1]
                polypoints += "];\n"
                polypaths = polypaths[:-7] + "];\n"
                # write the polys and paths
                outfile.write(polycenter + ";\n")
                outfile.write(polypoints)
                outfile.write(polypaths)
                prefix += 1
        # #### end global data for msg_*() functions. ####

        outfile.write("module poly_" + id + "(h, w, s, res=line_fn)\n{\n")
        # Element is transformed to correct size, so scale is now just for the user to
        # tweak after the fact
        outfile.write("  scale([custom_scale_x, -custom_scale_y, 1]) union()\n  {\n")

        # And add the call to the call list
        # Z-size is set by the overall module parameter
        # unless an extrusion zsize is parsed from the description or ID.
        extrusion = {"zsize": "h", "zoffset": "0", "scale": 100.0, "neg": False}
        if self.options.parsedesc is True:
            object_merge_extrusion_values(extrusion, node)

        call_item = "translate ([0,0,%s]) poly_%s(%s, min_line_mm(%s), %s);\n" % (
            extrusion["zoffset"],
            id,
            extrusion["zsize"],
            stroke_width_mm,
            extrusion["scale"],
        )

        if extrusion["neg"]:
            self.call_list_neg.append(call_item)
        else:
            self.call_list.append(call_item)

        prefix = 0
        for i in range(0, len(path)):

            # Skip this subpath if it is contained by another one
            if len(contained_by[i]) != 0:
                continue

            subpath = path[i][0]
            bbox = path[i][1]

            if filled and not self.options.force_line:

                if len(contains[i]) == 0:
                    # This subpath does not contain any subpaths
                    poly = msg_linear_extrude(id, prefix)
                else:
                    # This subpath contains other subpaths
                    poly = msg_linear_extrude_by_paths(id, prefix)

            else:  # filled == False -> outline mode

                if len(contains[i]) == 0:
                    # This subpath does not contain any subpaths
                    poly = msg_extrude_by_hull(id, prefix)
                else:
                    # This subpath contains other subpaths
                    poly = msg_extrude_by_hull_and_paths(id, prefix)

            outfile.write(poly)
            prefix += 1

        # End the module
        outfile.write("  }\n}\n")

    def recursivelyTraverseSvg(
        self, aNodeList, matCurrent=Transform(None), parent_visibility="visible"
    ):

        """
        [ This too is largely lifted from eggbot.py ]

        Recursively walk the SVG document, building polygon vertex lists
        for each graphical element we support.

        Rendered SVG elements:
            <circle>, <ellipse>, <line>, <path>, <polygon>, <polyline>, <rect>

        Supported SVG elements:
            <group>, <use>

        Ignored SVG elements:
            <defs>, <eggbot>, <metadata>, <namedview>, <pattern>,
            processing directives

        All other SVG elements trigger an error (including <text>)
        """

        for node in aNodeList:

            # Ignore invisible nodes
            v = node.get("visibility", parent_visibility)
            if v == "inherit":
                v = parent_visibility
            if v == "hidden" or v == "collapse":
                continue

            s = node.get("style", "")
            if s == "display:none":
                continue

            # First apply the current matrix transform to this node's transform
            matNew = matCurrent @ Transform(node.get("transform"))

            if node.tag == inkex.addNS("g", "svg") or node.tag == "g":

                self.recursivelyTraverseSvg(node, matNew, v)

            elif node.tag == inkex.addNS("use", "svg") or node.tag == "use":

                # A <use> element refers to another SVG element via an
                # xlink:href="#blah" attribute.  We will handle the element by
                # doing an XPath search through the document, looking for the
                # element with the matching id="blah" attribute.  We then
                # recursively process that element after applying any necessary
                # (x,y) translation.
                #
                # Notes:
                #  1. We ignore the height and width attributes as they do not
                #     apply to path-like elements, and
                #  2. Even if the use element has visibility="hidden", SVG
                #     still calls for processing the referenced element.  The
                #     referenced element is hidden only if its visibility is
                #     "inherit" or "hidden".

                refid = node.get(inkex.addNS("href", "xlink"))
                if not refid:
                    continue

                # [1:] to ignore leading '#' in reference
                path = '//*[@id="%s"]' % refid[1:]
                refnode = node.xpath(path)
                if refnode:
                    x = float(node.get("x", "0"))
                    y = float(node.get("y", "0"))
                    # Note: the transform has already been applied
                    if (x != 0) or (y != 0):
                        matNew2 = matNew @ Transform("translate(%f,%f)" % (x, y))
                    else:
                        matNew2 = matNew
                    v = node.get("visibility", v)
                    self.recursivelyTraverseSvg(refnode, matNew2, v)

            elif node.tag == inkex.addNS("path", "svg"):

                path_data = node.get("d")
                if path_data:
                    self.getPathVertices(path_data, node, matNew)

            elif node.tag == inkex.addNS("rect", "svg") or node.tag == "rect":

                # Manually transform
                #
                #    <rect x="X" y="Y" width="W" height="H"/>
                #
                # into
                #
                #    <path d="MX,Y lW,0 l0,H l-W,0 z"/>
                #
                # I.e., explicitly draw three sides of the rectangle and the
                # fourth side implicitly

                # Create a path with the outline of the rectangle
                x = float(node.get("x"))
                y = float(node.get("y"))
                w = float(node.get("width", "0"))
                h = float(node.get("height", "0"))
                a = []
                a.append(["M", [x, y]])
                a.append(["l", [w, 0]])
                a.append(["l", [0, h]])
                a.append(["l", [-w, 0]])
                a.append(["Z", []])
                self.getPathVertices(a, node, matNew)

            elif node.tag == inkex.addNS("line", "svg") or node.tag == "line":

                # Convert
                #
                #   <line x1="X1" y1="Y1" x2="X2" y2="Y2/>
                #
                # to
                #
                #   <path d="MX1,Y1 LX2,Y2"/>

                x1 = float(node.get("x1"))
                y1 = float(node.get("y1"))
                x2 = float(node.get("x2"))
                y2 = float(node.get("y2"))
                if (not x1) or (not y1) or (not x2) or (not y2):
                    continue
                a = []
                a.append(["M", [x1, y1]])
                a.append(["L", [x2, y2]])
                self.getPathVertices(a, node, matNew)

            elif node.tag in ["polygon", "polyline"]:

                # Convert
                #
                #  <polyline points="x1,y1 x2,y2 x3,y3 [...]"/>
                #
                # to
                #
                #   <path d="Mx1,y1 Lx2,y2 Lx3,y3 [...]"/>
                #
                # Note: we ignore polylines with no points

                pl = node.get("points", "").strip()
                if not pl:
                    continue

                pa = pl.split()
                d = "".join(
                    [
                        "M " + pa[i] if i == 0 else " L " + pa[i]
                        for i in range(0, len(pa))
                    ]
                )
                d = []
                first = True
                for part in pl.split():
                    x, y = part.split(",")
                    coords = [float(x), float(y)]
                    if first:
                        d.append(["M", coords])
                        first = False
                    else:
                        d.append(["L", coords])
                if node.TAG == "polygon":
                    d.append(["Z", []])
                self.getPathVertices(d, node, matNew)

            elif (
                node.tag == inkex.addNS("ellipse", "svg")
                or node.tag == "ellipse"
                or node.tag == inkex.addNS("circle", "svg")
                or node.tag == "circle"
            ):

                # Convert circles and ellipses to a path with two 180 degree
                # arcs. In general (an ellipse), we convert
                #
                #   <ellipse rx="RX" ry="RY" cx="X" cy="Y"/>
                #
                # to
                #
                #   <path d="MX1,CY A RX,RY 0 1 0 X2,CY A RX,RY 0 1 0 X1,CY"/>
                #
                # where
                #
                #   X1 = CX - RX
                #   X2 = CX + RX
                #
                # Note: ellipses or circles with a radius attribute of value 0
                # are ignored

                if node.tag == inkex.addNS("ellipse", "svg") or node.tag == "ellipse":
                    rx = float(node.get("rx", "0"))
                    ry = float(node.get("ry", "0"))
                else:
                    rx = float(node.get("r", "0"))
                    ry = rx
                if rx == 0 or ry == 0:
                    continue

                cx = float(node.get("cx", "0"))
                cy = float(node.get("cy", "0"))
                x1 = cx - rx
                x2 = cx + rx
                d = [
                    ["M", (x1, cy)],
                    ["A", (rx, ry, 0, 1, 0, x2, cy)],
                    ["A", (rx, ry, 0, 1, 0, x1, cy)],
                ]
                self.getPathVertices(d, node, matNew)

            elif node.tag == inkex.addNS("pattern", "svg") or node.tag == "pattern":
                pass

            elif node.tag == inkex.addNS("metadata", "svg") or node.tag == "metadata":
                pass

            elif node.tag == inkex.addNS("defs", "svg") or node.tag == "defs":
                pass

            elif node.tag == inkex.addNS("desc", "svg") or node.tag == "desc":
                pass

            elif (
                node.tag == inkex.addNS("namedview", "sodipodi")
                or node.tag == "namedview"
            ):
                pass

            elif node.tag == inkex.addNS("eggbot", "svg") or node.tag == "eggbot":
                pass

            elif node.tag == inkex.addNS("text", "svg") or node.tag == "text":
                texts = []
                plaintext = ""
                for tnode in node.iterfind(".//"):  # all subtree
                    if tnode is not None and tnode.text is not None:
                        texts.append(tnode.text)
                if len(texts):
                    plaintext = "', '".join(texts).encode("latin-1")
                    inkex.errormsg('Warning: text "%s"' % plaintext)
                    inkex.errormsg(
                        "Warning: unable to draw text, please convert it to a path first."
                    )

            elif node.tag == inkex.addNS("title", "svg") or node.tag == "title":
                pass

            elif node.tag == inkex.addNS("image", "svg") or node.tag == "image":
                if "image" not in self.warnings:
                    inkex.errormsg(
                        gettext.gettext(
                            "Warning: unable to draw bitmap images; please convert them to line art first.  "
                            'Consider using the "Trace bitmap..." tool of the "Path" menu.  Mac users please '
                            "note that some X11 settings may cause cut-and-paste operations to paste in bitmap copies."
                        )
                    )
                    self.warnings["image"] = 1

            elif node.tag == inkex.addNS("pattern", "svg") or node.tag == "pattern":
                pass

            elif (
                node.tag == inkex.addNS("radialGradient", "svg")
                or node.tag == "radialGradient"
            ):
                # Similar to pattern
                pass

            elif (
                node.tag == inkex.addNS("linearGradient", "svg")
                or node.tag == "linearGradient"
            ):
                # Similar in pattern
                pass

            elif node.tag == inkex.addNS("style", "svg") or node.tag == "style":
                # This is a reference to an external style sheet and not the
                # value of a style attribute to be inherited by child elements
                pass

            elif node.tag == inkex.addNS("cursor", "svg") or node.tag == "cursor":
                pass

            elif (
                node.tag == inkex.addNS("color-profile", "svg")
                or node.tag == "color-profile"
            ):
                # Gamma curves, color temp, etc. are not relevant to single
                # color output
                pass

            elif not isinstance(node.tag, (str, bytes)):
                # This is likely an XML processing instruction such as an XML
                # comment.  lxml uses a function reference for such node tags
                # and as such the node tag is likely not a printable string.
                # Further, converting it to a printable string likely won't
                # be very useful.
                pass

            else:
                inkex.errormsg(
                    "Warning: unable to draw object <%s>, please convert it to a path first."
                    % node.tag
                )
                pass

    def recursivelyGetEnclosingTransform(self, node):
        # Determine the cumulative transform which node inherits from its chain of ancestors.
        node = node.getparent()
        if node is not None:
            parent_transform = self.recursivelyGetEnclosingTransform(node)
            node_transform = node.get("transform", None)
            if node_transform is None:
                return parent_transform
            else:
                tr = Transform(node_transform)
                if parent_transform is None:
                    return tr
                else:
                    return parent_transform @ tr
        else:
            return self.docTransform

    def effect(self):
        # Viewbox handling
        self.handleViewBox()

        # First traverse the document (or selected items), reducing
        # everything to line segments.  If working on a selection,
        # then determine the selection's bounding box in the process.
        # (Actually, we just need to know its extrema on the x-axis.)

        if self.options.ids:
            # Traverse the selected objects
            for id in self.options.ids:
                transform = self.recursivelyGetEnclosingTransform(self.svg.selected[id])
                self.recursivelyTraverseSvg([self.svg.selected[id]], transform)
        else:
            # Traverse the entire document building new, transformed paths
            self.recursivelyTraverseSvg(self.document.getroot(), self.docTransform)

        # Determine the center of the drawing's bounding box
        self.cx = self.xmin + (self.xmax - self.xmin) / 2.0
        self.cy = self.ymin + (self.ymax - self.ymin) / 2.0

        # Determine which polygons lie entirely within other polygons
        try:
            self.options.fname = self.options.fname.format(**{"NAME": self.basename})
            if os.sep not in self.options.fname and "PWD" in os.environ:
                # current working directory of an extension seems to be the extension dir.
                # Workaround using PWD, if available...
                self.options.fname = os.environ["PWD"] + "/" + self.options.fname
            scad_fname = os.path.expanduser(self.options.fname)
            if "/" != os.sep:
                scad_fname = scad_fname.replace("/", os.sep)
  
            with open(scad_fname, 'w') as outfile:
                outfile = open(scad_fname, "w")
                outfile.write(
                    "// Generated by inkscape %s + inkscape-paths2openscad %s\n"
                    % (self.inkscape_version, VERSION)
                )
                outfile.write('// %s from "%s.svg"\n' % (time.ctime(), self.basename))
                # for use in options.fname basename is derived from the sodipodi_docname by
                # stripping the svg extension - or if there is no sodipodi_docname basename is 'inkscape'.
                # for use in scadviewcmd, scad2stlcmd and stlpostcmd basename is rederived from
                # options.fname by stripping an scad extension.
                self.basename = re.sub(r"\.scad", "", scad_fname, flags=re.I)
    
                outfile.write(
                """
// Module names are of the form poly_<inkscape-path-id>().  As a result,
// you can associate a polygon in this OpenSCAD program with the corresponding
// SVG element in the Inkscape document by looking for the XML element with
// the attribute id=\"inkscape-path-id\".

// fudge value is used to ensure that subtracted solids are a tad taller
// in the z dimension than the polygon being subtracted from.  This helps
// keep the resulting .stl file manifold.
fudge = 0.1;
"""
                )
                if self.options.chamfer < 0.001:
                    self.options.chamfer = None
    
                outfile.write("user_unit_scale_x = %s;\n" % (self.userunitsx))
                outfile.write("user_unit_scale_y = %s;\n" % (self.userunitsy))
                outfile.write("custom_scale_x = 1;\n")
                outfile.write("custom_scale_y = 1;\n")
    
                # writeout users parameters
                outfile.write("zsize = %s;\n" % (self.options.zsize))
                outfile.write("line_fn = %d;\n" % (self.options.line_fn))
                if self.options.chamfer:
                    outfile.write("chamfer = %s;\n" % (self.options.chamfer))
                    outfile.write("chamfer_fn = %d;\n" % (self.options.chamfer_fn))
                outfile.write("min_line_width = %s;\n" % (self.options.min_line_width))
                outfile.write(
                    "line_width_scale = %s;\n" % (self.options.line_width_scale_perc * 0.01)
                )
                outfile.write(
                    "function min_line_mm(w) = max(min_line_width, w * line_width_scale) * %g;\n\n"
                    % self.userunitsx
                )
    
                for key in self.paths:
                    outfile.write("\n")
                    self.convertPath(key, outfile)
    
                if self.options.chamfer:
                    outfile.write(
                    """
module chamfer_sphere(rad=chamfer, res=chamfer_fn)
{
  if(res <= 4)
  {
    // octaeder: 3 sided faces = 8
    polyhedron(
      points = [ [.0, .0, rad], [.0, .0, -rad], [ rad, .0, .0], [-rad, .0, .0], [.0, rad, .0], [.0, -rad, .0] ],
      faces = [ [4, 2, 0], [3, 4, 0], [5, 3, 0], [2, 5, 0], [5, 2, 1], [3, 5, 1], [4, 3, 1], [2 , 4, 1] ]);
  }
  else
  {
    sphere(r=rad, center=true, $fn=res);
  }
}
"""
                    )
    
                # Come up with a name for the module based on the file name.
                name = os.path.splitext(os.path.basename(self.options.fname))[0]
                # Remove all punctuation except underscore.
                badchars = string.punctuation.replace("_", "") + " "
                name = re.sub("[" + badchars + "]", "_", name)
                name = remove_umlaut(name)
    
                outfile.write("\nmodule %s(h)\n{\n" % name)
                mi = ""
                if self.options.chamfer:
                    mi = "  "
                    outfile.write("  minkowski()\n  {\n")
    
                # Now output the list of modules to call
                outfile.write(
                    "%s  difference()\n%s  {\n%s    union()\n%s    {\n" % (mi, mi, mi, mi)
                )
                for call in self.call_list:
                    outfile.write("%s      %s" % (mi, call))
                outfile.write("%s    }\n%s    union()\n%s    {\n" % (mi, mi, mi))
                for call in self.call_list_neg:
                    outfile.write("%s      %s" % (mi, call))
                outfile.write("%s    }\n%s  }\n" % (mi, mi))
                if self.options.chamfer:
                    outfile.write("    chamfer_sphere();\n  }\n")
    
                # The module that calls all the other ones.
                if self.options.stlmodule is True:
                    self.options.scad2stl = False #otherwise program will fail because modules are not renderable
                    outfile.write("}\n\n//%s(zsize);\n" % (name))
                else:
                    outfile.write("}\n\n%s(zsize);\n" % (name))
    
                outfile.close()
        except IOError as e:
            inkex.errormsg("Unable to write file " + self.options.fname)
            inkex.errormsg("ERROR: " + str(e))
            
        ################################################################
        # Call OpenSCAD
        ################################################################
        if self.options.scadview is True:
            #inkex.utils.debug("Calling OpenSCAD ...")
            pidfile = os.path.join(tempfile.gettempdir(), "paths2openscad.pid")
            running = False
            cmd = self.options.scadviewcmd.format(**{"SCAD": scad_fname, "NAME": self.basename})
            try:
                with open(pidfile) as pfile:
                    m = re.match(r"(\d+)\s+(.*)", pfile.read())
                    oldpid = int(m.group(1))
                    oldcmd = m.group(2)
                    # print >> sys.stderr, "pid {1} seen in {0}".format(pidfile, oldpid)
                    # print >> sys.stderr, "cmd {0},  oldcmd {1}".format(cmd, oldcmd)
                    if cmd == oldcmd:
                        # we found a pidfile and the cmd in there is still identical.
                        # If we change the filename in the inkscape extension gui, the cmd differs, and
                        # the still running openscad would not pick up our changes.
                        # If the command is identical, we check if the pid in the pidfile is alive.
                        # If so, we assume, the still running openscad will pick up the changes.
                        #
                        # WARNING: too much magic here. We cannot really test, if the last assumption holds.
                        # Comment out the next line to always start a new instance of openscad.
                        running = IsProcessRunning(oldpid)
                        # print >> sys.stderr, "running {0}".format(running)
            except Exception:
                pass
            if not running:
                try:
                    tty = open("/dev/tty", "w")
                except Exception:
                    tty = subprocess.PIPE
                try:
                    with subprocess.Popen(cmd, shell=True, stdin=tty, stdout=tty, stderr=tty) as proc:
                        proc.wait()
                except OSError as e:
                    raise OSError("%s failed: errno=%d %s" % (cmd, e.errno, e.strerror))
                try:
                    with open(pidfile, "w") as pfile:
                        pfile.write(str(proc.pid) + "\n" + cmd + "\n")
                except Exception:
                    pass
            else:
                # BUG alert:
                # If user changes the file viewed in openscad (save with different name, re-open that name
                #     without closing openscad, again, the still running openscad does not
                #     pick up the changes. and we have no way to tell the difference if it did.
                pass

        ################################################################
        # Call OpenSCAD to STL conversion
        ################################################################
        if self.options.scad2stl is True or self.options.stlpost is True:
            #inkex.utils.debug("Calling OpenSCAD to STL conversion...")
            stl_fname = self.basename + ".stl"
            scad2stlcmd = self.options.scad2stlcmd.format(**{"SCAD": scad_fname, "STL": stl_fname, "NAME": self.basename})
            try:
                os.unlink(stl_fname)
            except Exception:
                pass

            with subprocess.Popen(scad2stlcmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                proc.wait()
                stdout, stderr = proc.communicate()
                len = -1
                try:
                    len = os.path.getsize(stl_fname)
                except Exception:
                    pass
                if len < 1000:
                    inkex.errormsg("CMD: {} WARNING: {} is very small: {} bytes.".format(scad2stlcmd, stl_fname, len))
                    inkex.errormsg("= " * 24)
                    inkex.errormsg("STDOUT:\n{}".format(stdout.decode('UTF-8')))
                    inkex.errormsg("= " * 24)
                    inkex.errormsg("STDERR:\n{}".format(stderr.decode('UTF-8')))
                    inkex.errormsg("= " * 24)
                    if len <= 0:  # something is wrong. better stop here
                        self.options.stlpost = False
                
                ################################################################
                # Call OpenSCAD post processing
                ################################################################
                if self.options.stlpost is True:
                    #inkex.utils.debug("Calling OpenSCAD post processing...")
                    stlpostcmd = self.options.stlpostcmd.format(
                        **{"STL": self.basename + ".stl", "NAME": self.basename}
                    )
                    try:
                        with subprocess.Popen(stlpostcmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                            proc.wait()
                            stdout, stderr = proc.communicate()
                            if stdout or stderr:
                                inkex.errormsg("CMD: {}".format(stlpostcmd))
                                inkex.errormsg("= " * 24)
                            if stdout:
                                inkex.errormsg("STDOUT: {}".format(stdout.decode('UTF-8')))
                                inkex.errormsg("= " * 24)
                            if stderr:
                                inkex.errormsg("STDERR: {}".format(stderr.decode('UTF-8')))
                                inkex.errormsg("= " * 24)
                    except OSError as e:
                        raise OSError("%s failed: errno=%d %s" % (stlpostcmd, e.errno.decode('UTF-8'), e.strerror.decode('UTF-8')))

if __name__ == '__main__':
    PathsToOpenSCAD().run()
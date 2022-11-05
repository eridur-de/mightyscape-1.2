#!/usr/bin/env python3
#
# Copyright (C) 2007 John Beard john.j.beard@gmail.com
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
"""
This extension draws 3d objects from a Wavefront .obj 3D file stored in a local folder
Many settings for appearance, lighting, rotation, etc are available.

                              ^y
                              |
        __--``|               |_--``|     __--
  __--``      |         __--``|     |_--``
 |       z    |        |      |_--``|
 |       <----|--------|-----_0-----|----------------
 |            |        |_--`` |     |
 |      __--``     <-``|      |_--``
 |__--``           x   |__--``|
  IMAGE PLANE           SCENE|
                              |

 Vertices are given as "v" followed by three numbers (x,y,z).
 All files need a vertex list
 v  x.xxx   y.yyy   z.zzz

 Faces are given by a list of vertices
 (vertex 1 is the first in the list above, 2 the second, etc):
 f  1   2   3

 Edges are given by a list of vertices. These will be broken down
 into adjacent pairs automatically.
 l  1   2   3

 Faces are rendered according to the painter's algorithm and perhaps
 back-face culling, if selected. The parameter to sort the faces by
 is user-selectable between max, min and average z-value of the vertices
"""

import os
from math import acos, cos, floor, pi, sin, sqrt
import numpy
import tempfile
import openmesh as om

import inkex
from inkex import Group, Circle, Color
from inkex.utils import pairwise
from inkex.paths import Move, Line


def draw_circle(r, cx, cy, width, fill, name, parent):
    """Draw an SVG circle"""
    circle = parent.add(Circle(cx=str(cx), cy=str(cy), r=str(r)))
    circle.style = {'stroke': '#000000', 'stroke-width': str(width), 'fill': fill}
    circle.label = name


def draw_line(x1, y1, x2, y2, width, name, parent):
    elem = parent.add(inkex.PathElement())
    elem.style = {'stroke': '#000000', 'stroke-width': str(width), 'fill': 'none',
                  'stroke-linecap': 'round'}
    elem.set('inkscape:label', name)
    elem.path = [Move(x1, y1), Line(x2, y2)]

def draw_poly(pts, face, st, name, parent):
    """Draw polygone"""
    style = {'stroke': '#000000', 'stroke-width': str(st.th), 'stroke-linejoin': st.linejoin,
             'stroke-opacity': st.s_opac, 'fill': st.fill, 'fill-opacity': st.fill_opacity}
    path = inkex.Path()
    for facet in face:
        if not path:  # for first point
            path.append(Move(pts[facet - 1][0], -pts[facet - 1][1]))
        else:
            path.append(Line(pts[facet - 1][0], -pts[facet - 1][1]))
    path.close()

    poly = parent.add(inkex.PathElement())
    poly.label = name
    poly.style = style
    poly.path = path


def draw_edges(edge_list, pts, st, parent):
    for edge in edge_list:  # for every edge
        pt_1 = pts[edge[0] - 1][0:2]  # the point at the start
        pt_2 = pts[edge[1] - 1][0:2]  # the point at the end
        name = 'Edge' + str(edge[0]) + '-' + str(edge[1])
        draw_line(pt_1[0], -pt_1[1], pt_2[0], -pt_2[1], st.th, name, parent)


def draw_faces(faces_data, pts, obj, shading, fill_col, st, parent):
    for face in faces_data:  # for every polygon that has been sorted
        if shading:
            st.fill = get_darkened_colour(fill_col, face[1] / pi)  # darken proportionally to angle to lighting vector
        else:
            st.fill = get_darkened_colour(fill_col, 1)  # do not darken colour

        face_no = face[3]  # the number of the face to draw
        draw_poly(pts, obj.fce[face_no], st, 'Face:' + str(face_no), parent)


def get_darkened_colour(rgb, factor):
    """return a hex triplet of colour, reduced in lightness 0.0-1.0"""
    return '#' + "%02X" % floor(factor * rgb[0]) \
           + "%02X" % floor(factor * rgb[1]) \
           + "%02X" % floor(factor * rgb[2])  # make the colour string


def make_rotation_log(options):
    """makes a string recording the axes and angles of each rotation, so an object can be repeated"""
    return options.r1_ax + str('%.2f' % options.r1_ang) + ':' + \
           options.r2_ax + str('%.2f' % options.r2_ang) + ':' + \
           options.r3_ax + str('%.2f' % options.r3_ang) + ':' + \
           options.r1_ax + str('%.2f' % options.r4_ang) + ':' + \
           options.r2_ax + str('%.2f' % options.r5_ang) + ':' + \
           options.r3_ax + str('%.2f' % options.r6_ang)

def normalise(vector):
    """return the unit vector pointing in the same direction as the argument"""
    length = sqrt(numpy.dot(vector, vector))
    return numpy.array(vector) / length

def get_normal(pts, face):
    """normal vector for the plane passing though the first three elements of face of pts"""
    return numpy.cross(
        (numpy.array(pts[face[0] - 1]) - numpy.array(pts[face[1] - 1])),
        (numpy.array(pts[face[0] - 1]) - numpy.array(pts[face[2] - 1])),
    ).flatten()

def get_unit_normal(pts, face, cw_wound):
    """
    Returns the unit normal for the plane passing through the
    first three points of face, taking account of winding
    """
    # if it is clockwise wound, reverse the vector direction
    winding = -1 if cw_wound else 1
    return winding * normalise(get_normal(pts, face))

def rotate(matrix, rads, axis):
    """choose the correct rotation matrix to use"""
    if axis == 'x':
        trans_mat = numpy.array([
            [1, 0, 0], [0, cos(rads), -sin(rads)], [0, sin(rads), cos(rads)]])
    elif axis == 'y':
        trans_mat = numpy.array([
            [cos(rads), 0, sin(rads)], [0, 1, 0], [-sin(rads), 0, cos(rads)]])
    elif axis == 'z':
        trans_mat = numpy.array([
            [cos(rads), -sin(rads), 0], [sin(rads), cos(rads), 0], [0, 0, 1]])
    return numpy.matmul(trans_mat, matrix)

class Style(object):  # container for style information
    def __init__(self, options):
        self.th = options.th
        self.fill = '#ff0000'
        self.col = '#000000'
        self.r = 2
        self.s_opac = str(options.s_opac / 100.0)
        self.fill_opacity = options.fill_color.alpha
        self.linecap = 'round'
        self.linejoin = 'round'


class WavefrontObj(object):
    """Wavefront based 3d object defined by the vertices and the faces (eg a polyhedron)"""
    name = property(lambda self: self.meta.get('name', None))

    def __init__(self, filename):
        self.meta = {
            'name': os.path.basename(filename).rsplit('.', 1)[0]
        }
        self.vtx = []
        self.edg = []
        self.fce = []
        self._parse_file(filename)

    def _parse_file(self, filename):
        if not os.path.isfile(filename):
            raise IOError("Can't find wavefront object file {}".format(filename))
        with open(filename, 'r') as fhl:
            for line in fhl:
                self._parse_line(line.strip())

    def _parse_line(self, line):
        if line.startswith('#'):
            if ':' in line:
                name, value = line.split(':', 1)
                self.meta[name.lower()] = value
        elif line:
            (kind, line) = line.split(None, 1)
            kind_name = 'add_' + kind
            if hasattr(self, kind_name):
                getattr(self, kind_name)(line)

    @staticmethod
    def _parse_numbers(line, typ=str):
        # Ignore any slash options and always pick the first one
        return [typ(v.split('/')[0]) for v in line.split()]

    def add_v(self, line):
        """Add vertex from parsed line"""
        vertex = self._parse_numbers(line, float)
        if len(vertex) == 3:
            self.vtx.append(vertex)

    def add_l(self, line):
        """Add line from parsed line"""
        vtxlist = self._parse_numbers(line, int)
        # we need at least 2 vertices to make an edge
        if len(vtxlist) > 1:
            # we can have more than one vertex per line - get adjacent pairs
            self.edg.append(pairwise(vtxlist))

    def add_f(self, line):
        """Add face from parsed line"""
        vtxlist = self._parse_numbers(line, int)
        # we need at least 3 vertices to make an edge
        if len(vtxlist) > 2:
            self.fce.append(vtxlist)

    def get_transformed_pts(self, trans_mat):
        """translate vertex points according to the matrix"""
        transformed_pts = []
        for vtx in self.vtx:
            transformed_pts.append((numpy.matmul(trans_mat, numpy.array(vtx).T)).T.tolist())
        return transformed_pts

    def get_edge_list(self):
        """make an edge vertex list from an existing face vertex list"""
        edge_list = []
        for face in self.fce:
            for j, edge in enumerate(face):
                # Ascending order of vertices (for duplicate detection)
                edge_list.append(sorted([edge, face[(j + 1) % len(face)]]))
        return [list(x) for x in sorted(set(tuple(x) for x in edge_list))]

class Import3DMesh(inkex.GenerateExtension):
    
    """Generate a polyhedron from a wavefront 3d model file"""
    def add_arguments(self, pars):
        pars.add_argument("--tab", default="object")

        # MODEL FILE SETTINGS
        pars.add_argument("--obj", default='cube')
        pars.add_argument("--input_choice", default='default')
        pars.add_argument("--spec_file", default='great_rhombicuboct.obj')
        pars.add_argument("--cw_wound", type=inkex.Boolean, default=True)
        # VEIW SETTINGS
        pars.add_argument("--r1_ax", default="x")
        pars.add_argument("--r2_ax", default="x")
        pars.add_argument("--r3_ax", default="x")
        pars.add_argument("--r4_ax", default="x")
        pars.add_argument("--r5_ax", default="x")
        pars.add_argument("--r6_ax", default="x")
        pars.add_argument("--r1_ang", type=float, default=0.0)
        pars.add_argument("--r2_ang", type=float, default=0.0)
        pars.add_argument("--r3_ang", type=float, default=0.0)
        pars.add_argument("--r4_ang", type=float, default=0.0)
        pars.add_argument("--r5_ang", type=float, default=0.0)
        pars.add_argument("--r6_ang", type=float, default=0.0)
        pars.add_argument("--scl", type=float, default=100.0)
        # STYLE SETTINGS
        pars.add_argument("--show", type=self.arg_method('gen'))
        pars.add_argument("--shade", type=inkex.Boolean, default=True)
        pars.add_argument("--fill_color", type=Color, default='1943148287', help="Fill color")
        pars.add_argument("--s_opac", type=int, default=100)
        pars.add_argument("--th", type=float, default=2)
        pars.add_argument("--lv_x", type=float, default=1)
        pars.add_argument("--lv_y", type=float, default=1)
        pars.add_argument("--lv_z", type=float, default=-2)
        pars.add_argument("--back", type=inkex.Boolean, default=False)
        pars.add_argument("--z_sort", type=self.arg_method('z_sort'), default=self.z_sort_min)

    def get_filename(self):
        """Get the filename for the spec file"""
        if self.options.input_choice == 'custom':
            return self.options.spec_file
        if self.options.input_choice == 'default':
            moddir = self.ext_path()
            return os.path.join(moddir, 'Poly3DObjects', self.options.obj + '.obj')

    def generate(self):
        so = self.options

        if not os.path.exists(self.get_filename()):
            inkex.utils.debug("The input file does not exist.")
            exit(1)

        input_mesh = om.read_polymesh(self.get_filename()) #read input file
        output_obj = os.path.join(tempfile.gettempdir(), "input_mesh.obj")
        om.write_mesh(output_obj, input_mesh)
        #write to obj file

        obj = WavefrontObj(output_obj)

        scale = self.svg.unittouu('1px')  # convert to document units
        st = Style(so)  # initialise style

        # we will put all the rotations in the object name, so it can be repeated in
        poly = Group.new(obj.name + ':' + make_rotation_log(so))
        (pos_x, pos_y) = self.svg.namedview.center
        #poly.transform.add_translate(pos_x, pos_y)
        poly.transform.add_scale(scale)

        # TRANSFORMATION OF THE OBJECT (ROTATION, SCALE, ETC)
        trans_mat = numpy.identity(3, float)  # init. trans matrix as identity matrix
        for i in range(1, 7):  # for each rotation
            axis = getattr(so, 'r{}_ax'.format(i))
            angle = getattr(so, 'r{}_ang'.format(i)) * pi / 180
            trans_mat = rotate(trans_mat, angle, axis)
        # scale by linear factor (do this only after the transforms to reduce round-off)
        trans_mat = trans_mat * so.scl

        # the points as projected in the z-axis onto the viewplane
        transformed_pts = obj.get_transformed_pts(trans_mat)
        so.show(obj, st, poly, transformed_pts)
        return poly

    def gen_vtx(self, obj, st, poly, transformed_pts):
        """Generate Vertex"""
        for i, pts in enumerate(transformed_pts):
            draw_circle(st.r, pts[0], pts[1], st.th, '#000000', 'Point' + str(i), poly)

    def gen_edg(self, obj, st, poly, transformed_pts):
        """Generate edges"""
        # we already have an edge list
        edge_list = obj.edg
        if obj.fce:
            # we must generate the edge list from the faces
            edge_list = obj.get_edge_list()

        draw_edges(edge_list, transformed_pts, st, poly)

    def gen_fce(self, obj, st, poly, transformed_pts):
        """Generate face"""
        so = self.options
        # colour tuple for the face fill
        # unit light vector
        lighting = normalise((so.lv_x, -so.lv_y, so.lv_z))
        # we have a face list
        if obj.fce:
            z_list = []

            for i, face in enumerate(obj.fce):
                # get the normal vector to the face
                norm = get_unit_normal(transformed_pts, face, so.cw_wound)
                # get the angle between the normal and the lighting vector
                angle = acos(numpy.dot(norm, lighting))
                z_sort_param = so.z_sort(transformed_pts, face)

                # include all polygons or just the front-facing ones as needed
                if so.back or norm[2] > 0:
                    # record the maximum z-value of the face and angle to
                    # light, along with the face ID and normal
                    z_list.append((z_sort_param, angle, norm, i))

            z_list.sort(key=lambda x: x[0])  # sort by ascending sort parameter of the face
            draw_faces(z_list, transformed_pts, obj, so.shade, self.options.fill_color, st, poly)

        else:  # we cannot generate a list of faces from the edges without a lot of computation
            raise inkex.AbortExtension("Face data not found.")

    @staticmethod
    def z_sort_max(pts, face):
        """returns the largest z_value of any point in the face"""
        return max([pts[facet - 1][2] for facet in face])

    @staticmethod
    def z_sort_min(pts, face):
        """returns the smallest z_value of any point in the face"""
        return min([pts[facet - 1][2] for facet in face])

    @staticmethod
    def z_sort_cent(pts, face):
        """returns the centroid z_value of any point in the face"""
        return sum([pts[facet - 1][2] for facet in face]) / len(face)

if __name__ == '__main__':
    Import3DMesh().run()

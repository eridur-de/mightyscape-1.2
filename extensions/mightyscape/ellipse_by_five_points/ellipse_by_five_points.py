#!/usr/bin/env python3
# Copyright (c) 2012 Stuart Pernsteiner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import inkex
from inkex.paths import Path
import gettext
_ = gettext.gettext
from copy import deepcopy
import math
from math import sqrt

class EllipseByFivePoints(inkex.EffectExtension):

    def effect(self):
        if len(self.svg.selected) == 0:
            sys.exit(_("Error: You must select at least one path"))

        for pathId in self.svg.selected:
            path = self.svg.selected[pathId]
            pathdata = Path(path.get('d')).to_arrays()
            if len(pathdata) < 5:
                sys.exit(_("Error: The selected path has %d points, " +
                        "but 5 are needed.") % len(pathdata))

            points = []
            for i in range(5):
                # pathdata[i] is the i'th segment of the path
                # pathdata[i][1] is the list of coordinates for the segment
                # pathdata[i][1][-2] is the x-coordinate of the last x,y pair
                #    in the segment definition
                segpoints = pathdata[i][1]
                x = segpoints[-2]
                y = segpoints[-1]
                points.append((x,y))

            conic = solve_conic(points)
            [a,b,c,d,e,f] = conic

            if bareiss_determinant([[a,b/2,d/2],[b/2,c,e/2],[d/2,e/2,f]]) == 0 or a*c - b*b/4 <= 0:
                sys.exit(_("Error: Could not find an ellipse that passes " +
                    "through the provided points"))

            center = ellipse_center(conic)
            [ad1, ad2] = ellipse_axes(conic)
            al1 = ellipse_axislen(conic, center, ad1)
            al2 = ellipse_axislen(conic, center, ad2)

            # Create an <svg:ellipse> object with the appropriate cx,cy and
            # with the major axis in the x direction.  Then add a transform to
            # rotate it to the correct angle.

            if al1 > al2:
                major_dir = ad1
                major_len = al1
                minor_len = al2
            else:
                major_dir = ad2
                major_len = al2
                minor_len = al1

            # add sodipodi magic to turn the path into an ellipse
            def sodi(x):
                return inkex.addNS(x, 'sodipodi')
            path.set(sodi('cx'), str(center[0]))
            path.set(sodi('cy'), str(center[1]))
            path.set(sodi('rx'), str(major_len))
            path.set(sodi('ry'), str(minor_len))
            path.set(sodi('type'), 'arc')

            #inkex.utils.debug(str(center[0]))
            #inkex.utils.debug(str(center[1]))
			
            angle = math.atan2(major_dir[1], major_dir[0])
            if angle > math.pi / 2:
                angle -= math.pi
            if angle < -math.pi / 2:
                angle += math.pi
            path.apply_transform()
            path.set('transform', 'rotate(%f %f %f)' % (angle * 180 / math.pi, center[0], center[1]))
            # NASTY BUGFIX: We do apply_transform and path.set twice because otherwise the ellipse will not be rendered correctly. Reason unknown!
            path.apply_transform()
            path.set('transform', 'rotate(%f %f %f)' % (angle * 180 / math.pi, center[0], center[1]))

def solve_conic(pts):
    # Find the equation of the conic section passing through the five given
    # points.
    #
    # This technique is from
    # http://math.fullerton.edu/mathews/n2003/conicfit/ConicFitMod/Links/ConicFitMod_lnk_9.html
    # (retrieved 31 Jan 2012)
    rowmajor_matrix = []
    for i in range(5):
        (x,y) = pts[i]
        row = [x*x, x*y, y*y, x, y, 1]
        rowmajor_matrix.append(row)

    full_matrix = []
    for i in range(6):
        col = []
        for j in range(5):
            col.append(rowmajor_matrix[j][i])
        full_matrix.append(col);

    coeffs = []
    sign = 1
    for i in range(6):
        mat = []
        for j in range(6):
            if j == i:
                continue
            mat.append(full_matrix[j])
        coeffs.append(bareiss_determinant(mat) * sign)
        sign = -sign
    return coeffs

def bareiss_determinant(mat_orig):
    # Compute the determinant of the matrix using Bareiss's algorithm.  It
    # doesn't matter whether 'mat' is in row-major or column-major layout,
    # because  det(A) = det(A^T)

    # Algorithm from:
    # Yap, Chee, "Linear Systems", Fundamental Problems of Algorithmic Algebra
    # Lecture X, Section 2
    # http://cs.nyu.edu/~yap/book/alge/ftpSite/l10.ps.gz

    mat = deepcopy(mat_orig);

    size = len(mat)
    last_akk = 1
    for k in range(size-1):
        if last_akk == 0:
            return 0
        for i in range(k+1, size):
            for j in range(k+1, size):
                mat[i][j] = (mat[i][j] * mat[k][k] - mat[i][k] * mat[k][j]) / last_akk
        last_akk = mat[k][k]
    return mat[size-1][size-1]

def ellipse_center(conic):
    # From
    # http://en.wikipedia.org/wiki/Matrix_representation_of_conic_sections#Center
    [a,b,c,d,e,f] = conic
    x = (b*e - 2*c*d) / (4*a*c - b*b);
    y = (d*b - 2*a*e) / (4*a*c - b*b);
    return (x,y)

def ellipse_axes(conic):
    # Compute the axis directions of the ellipse.
    # This technique is from
    # http://en.wikipedia.org/wiki/Matrix_representation_of_conic_sections#Axes
    [a,b,c,d,e,f] = conic

    # Compute the eigenvalues of
    #    /  a   b/2 \
    #    \ b/2   c  /
    # This algorithm is from
    # http://www.math.harvard.edu/archive/21b_fall_04/exhibits/2dmatrices/index.html
    # (retrieved 31 Jan 2012)
    ma = a
    mb = b/2
    mc = b/2
    md = c
    mdet = ma*md - mb*mc
    mtrace = ma + md

    (l1,l2) = solve_quadratic(1, -mtrace, mdet);

    # Eigenvalues (\lambda_1, \lambda_2)
    #l1 = mtrace / 2 + sqrt(mtrace*mtrace/4 - mdet)
    #l2 = mtrace / 2 - sqrt(mtrace*mtrace/4 - mdet)

    if mb == 0:
        return [(0,1), (1,0)]
    else:
        return [(mb, l1-ma), (mb, l2-ma)]

def ellipse_axislen(conic, center, direction):
    # Compute the axis length as a multiple of the magnitude of 'direction'
    [a,b,c,d,e,f] = conic
    (cx,cy) = center
    (dx,dy) = direction

    dlen = sqrt(dx*dx + dy*dy)
    dx /= dlen
    dy /= dlen

    # Solve for t:
    #   a*x^2 + b*x*y + c*y^2 + d*x + e*y + f = 0
    #   x = cx + t * dx
    #   y = cy + t * dy
    # by substituting, we get  qa*t^2 + qb*t + qc = 0, where:
    qa = a*dx*dx + b*dx*dy + c*dy*dy
    qb = a*2*cx*dx + b*(cx*dy + cy*dx) + c*2*cy*dy + d*dx + e*dy
    qc = a*cx*cx + b*cx*cy + c*cy*cy + d*cx + e*cy + f

    (t1,t2) = solve_quadratic(qa,qb,qc)

    return max(t1,t2)

def solve_quadratic(a,b,c):
    disc = b*b - 4*a*c
    disc_root = sqrt(b*b - 4*a*c)
    x1 = (-b + disc_root) / (2*a)
    x2 = (-b - disc_root) / (2*a)
    return (x1,x2)

if __name__ == '__main__':
    EllipseByFivePoints().run()
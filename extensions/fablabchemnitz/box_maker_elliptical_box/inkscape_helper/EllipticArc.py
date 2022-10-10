from inkscape_helper.PathSegment import *
from inkscape_helper.Coordinate import Coordinate
from inkscape_helper.Ellipse import Ellipse

from math import sqrt, pi
import copy


class EllipticArc(PathSegment):

    ell_dict = {}

    def __init__(self, start, end, rx, ry, axis_rot, pos_dir=True, large_arc=False):
        self.rx = rx
        self.ry = ry
        # calculate ellipse center
        # the center is on two ellipses one with its center at the start point, the other at the end point
        # for simplicity take the  one ellipse at the origin and the other with offset (tx, ty),
        # find the center and translate back to the original offset at the end
        axis_rot *=  pi / 180 # convert to radians
        # start and end are mutable objects, copy to avoid modifying them
        r_start = copy.copy(start)
        r_end = copy.copy(end)
        r_start.t -= axis_rot
        r_end.t -= axis_rot
        end_o = r_end - r_start # offset end vector

        tx = end_o.x
        ty = end_o.y

        # some helper variables for the intersection points
        # used sympy to come up with the equations
        ff = (rx**2*ty**2 + ry**2*tx**2)
        cx = rx**2*ry*tx*ty**2 + ry**3*tx**3
        cy = rx*ty*ff
        sx = rx*ty*sqrt(4*rx**4*ry**2*ty**2 - rx**4*ty**4 + 4*rx**2*ry**4*tx**2 - 2*rx**2*ry**2*tx**2*ty**2 - ry**4*tx**4)
        sy = ry*tx*sqrt(-ff*(-4*rx**2*ry**2 + rx**2*ty**2 + ry**2*tx**2))

        # intersection points
        c1 = Coordinate((cx - sx) / (2*ry*ff), (cy + sy) / (2*rx*ff))
        c2 = Coordinate((cx + sx) / (2*ry*ff), (cy - sy) / (2*rx*ff))

        if end_o.cross_norm(c1 - r_start) < 0: # c1 is to the left of end_o
            left = c1
            right = c2
        else:
            left = c2
            right = c1

        if pos_dir != large_arc: #center should be on the left of end_o
            center_o = left
        else: #center should be on the right of end_o
            center_o = right

        #re-use ellipses with same rx, ry to save some memory
        if (rx, ry) in self.ell_dict:
            self.ellipse = self.ell_dict[(rx, ry)]
        else:
            self.ellipse = Ellipse(rx, ry)
            self.ell_dict[(rx, ry)] = self.ellipse

        self.start = start
        self.end = end
        self.axis_rot = axis_rot
        self.pos_dir = pos_dir
        self.large_arc = large_arc
        self.start_theta = self.ellipse.theta_at_angle((-center_o).t)
        self.end_theta = self.ellipse.theta_at_angle((end_o - center_o).t)

        # translate center back to original offset
        center_o.t += axis_rot
        self.center = center_o + start

    @property
    def length(self):
        return self.ellipse.dist_from_theta(self.start_theta, self.end_theta)

    def t_to_theta(self, t):
        """convert t (always between 0 and 1) to angle theta"""
        start = self.start_theta
        end = self.end_theta

        if self.pos_dir and end < start:
            end += 2 * pi

        if not self.pos_dir and start < end:
            end -= 2 * pi
        arc_size = end - start

        return (start + (end - start) * t) % (2 * pi)

    def theta_to_t(self, theta):
        full_arc_size = (self.end_theta - self.start_theta + 2 * pi) % (2 * pi)
        theta_arc_size = (theta - self.start_theta + 2 * pi) % (2 * pi)
        return theta_arc_size / full_arc_size

    def curvature(self, t):
        theta = self.t_to_theta(t)
        return self.ellipse.curvature(theta)

    def tangent(self, t):
        theta = self.t_to_theta(t)
        return self.ellipse.tangent(theta)

    def t_at_length(self, length):
        """interpolated t where the curve is at the given length"""
        theta = self.ellipse.theta_from_dist(length, self.start_theta)
        return self.theta_to_t(theta)

    def length_at_t(self, t):
        return self.ellipse.dist_from_theta(self.start_theta, self.t_to_theta(t))

    def pathpoint_at_t(self, t):
        """pathpoint on the curve from t=0 to point at t."""
        centered = self.ellipse.coordinate_at_theta(self.t_to_theta(t))
        centered.t += self.axis_rot
        return PathPoint(t, centered + self.center, self.tangent(t), self.curvature(t), self.length_at_t(t))

    # identical to Bezier code
    def subdivide(self, part_length, start_offset=0):
        nr_parts = int((self.length - start_offset) // part_length)
        k_o = start_offset / self.length
        k2t = lambda k : k_o + k * part_length / self.length
        points = [self.pathpoint_at_t(k2t(k)) for k in range(nr_parts + 1)]
        return(points, self.length - points[-1].c_dist)

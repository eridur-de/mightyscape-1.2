from __future__ import division

from PathSegment import *
from math import hypot

class BezierCurve(PathSegment):
    nr_points = 10
    def __init__(self, P): # number of points is limited to 3 or 4

        if len(P) == 3: # quadratic
            self.B = lambda t : (1 - t)**2 * P[0] + 2 * (1 - t) * t * P[1] + t**2 * P[2]
            self.Bd = lambda t : 2 * (1 - t) * (P[1] - P[0]) + 2 * t * (P[2] - P[1])
            self.Bdd = lambda t : 2 * (P[2] - 2 * P[1] + P[0])
        elif len(P) == 4: #cubic
            self.B = lambda t : (1 - t)**3 * P[0] + 3 * (1 - t)**2 * t * P[1] + 3 * (1 - t) * t**2 * P[2] + t**3 * P[3]
            self.Bd = lambda t : 3 * (1 - t)**2 * (P[1] - P[0]) + 6 * (1 - t) * t * (P[2] - P[1]) + 3 * t**2 * (P[3] - P[2])
            self.Bdd = lambda t : 6 * (1 - t) * (P[2] - 2 * P[1] + P[0]) + 6 * t * (P[3] - 2 * P[2] + P[1])

        self.tangent = lambda t : self.Bd(t)
 #       self.curvature = lambda t : (Bd(t).x * Bdd(t).y - Bd(t).y * Bdd(t).x) / hypot(Bd(t).x, Bd(t).y)**3


        self.distances = [0]    # cumulative distances for each 't'
        prev_pt = self.B(0)
        for i in range(self.nr_points):
            t = (i + 1) / self.nr_points
            pt = self.B(t)
            self.distances.append(self.distances[-1] + hypot(prev_pt.x - pt.x, prev_pt.y - pt.y))
            prev_pt = pt
        self._length = self.distances[-1]

    def curvature(self, t):
        n = self.Bd(t).x * self.Bdd(t).y - self.Bd(t).y * self.Bdd(t).x
        d = hypot(self.Bd(t).x, self.Bd(t).y)**3
        if d == 0:
            return n * float('inf')
        else:
            return n / d

    @classmethod
    def quadratic(cls, start, c, end):
        bezier = cls()

    @classmethod
    def cubic(cls, start, c1, c2, end):
        bezier = cls()

    def __make_eq__(self):
        pass

    @property
    def length(self):
        return self._length

    def subdivide(self, part_length, start_offset=0):
        nr_parts = int((self.length - start_offset) // part_length)
        k_o = start_offset / self.length
        k2t = lambda k : k_o + k * part_length / self.length
        points = [self.pathpoint_at_t(k2t(k)) for k in range(nr_parts + 1)]
        return(points, self.length - points[-1].c_dist)


    def pathpoint_at_t(self, t):
        """pathpoint on the curve from t=0 to point at t."""
        step = 1 / self.nr_points
        pt_idx = int(t / step)
        length = self.distances[pt_idx]
        ip_fact = (t - pt_idx * step) / step

        if ip_fact > 0 and t < 1: # not a perfect match, need to interpolate
            length += ip_fact * (self.distances[pt_idx + 1] - self.distances[pt_idx])

        return PathPoint(t, self.B(t), self.tangent(t), self.curvature(t), length)


    def t_at_length(self, length):
        """interpolated t where the curve is at the given length"""
        if length == self.length:
            return 1
        i_small = 0
        i_big = self.nr_points + 1

        while i_big - i_small > 1:  # binary search
            i_half = i_small + (i_big - i_small) // 2
            if self.distances[i_half] <= length:
                i_small = i_half
            else:
                i_big = i_half

        small_dist = self.distances[i_small]
        return  i_small / self.nr_points + (length - small_dist) * (self.distances[i_big] - small_dist) # interpolated length


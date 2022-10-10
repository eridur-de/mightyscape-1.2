from __future__ import division
from math import *
from inkscape_helper.Coordinate import Coordinate

class Ellipse(object):
    """Used as a base class for EllipticArc."""
    nr_points = 1024 #used for piecewise linear circumference calculation (ellipse circumference is tricky to calculate)
    # approximate circumfere: c = pi * (3 * (a + b) - sqrt(10 * a * b + 3 * (a ** 2 + b ** 2)))

    def __init__(self, x_radius, y_radius):
        self.y_radius = y_radius
        self.x_radius = x_radius
        self.distances = [0]
        theta = 0
        self.angle_step = 2 * pi / self.nr_points

        for i in range(self.nr_points):
            prev_dist = self.distances[-1]
            prev_coord = self.coordinate_at_theta(theta)
            theta += self.angle_step
            x, y = x_radius * cos(theta), y_radius * sin(theta)
            self.distances.append(prev_dist + hypot(prev_coord.x - x, prev_coord.y - y))

    @property
    def circumference(self):
        return self.distances[-1]

    def curvature(self, theta):
        c = self.coordinate_at_theta(theta)
        return (self.x_radius*self.y_radius)/((cos(theta)**2*self.y_radius**2 + sin(theta)**2*self.x_radius**2)**(3/2))

    def tangent(self, theta):
        angle = self.theta_at_angle(theta)
        return Coordinate(cos(angle), sin(angle))

    def coordinate_at_theta(self, theta):
        """Coordinate of the point at theta."""
        return Coordinate(self.x_radius * cos(theta), self.y_radius * sin(theta))

    def dist_from_theta(self, theta_start, theta_end):
        """Distance accross the surface from point at angle theta_end to point at angle theta_end. Measured in positive (CCW) sense."""
        #print 'thetas ', theta_start, theta_end # TODO: figure out why are there so many with same start and end?
        # make sure thetas are between 0 and 2 * pi
        theta_start %= 2 * pi
        theta_end %= 2 * pi
        i1 = int(theta_start / self.angle_step)
        p1 = theta_start % self.angle_step
        l1 = self.distances[i1 + 1] - self.distances[i1]
        i2 = int(theta_end / self.angle_step)
        p2 = theta_end % self.angle_step
        l2 = self.distances[i2 + 1] - self.distances[i2]
        if theta_start <= theta_end:
            len = self.distances[i2] - self.distances[i1] + l2 * p2 - l1 * p1
        else:
            len = self.circumference + self.distances[i2] - self.distances[i1]
        return len

    def theta_from_dist(self, theta_start, dist):
        """Returns the angle that you get when starting at theta_start and moving a distance (dist) in CCW direction"""
        si = int(theta_start / self.angle_step) % self.nr_points
        p = theta_start % self.angle_step

        piece_length = self.distances[si + 1] - self.distances[si]
        start_dist = self.distances[si] + p * piece_length
        end_dist = dist + start_dist

        if end_dist > self.circumference:  # wrap around zero angle
            end_dist -= self.circumference

        min_idx = 0
        max_idx = self.nr_points
        while max_idx - min_idx > 1:  # binary search
            half_idx = min_idx + (max_idx - min_idx) // 2
            if self.distances[half_idx] < end_dist:
                min_idx = half_idx
            else:
                max_idx = half_idx
        step_dist = self.distances[max_idx] - self.distances[min_idx]
        return (min_idx + (end_dist - self.distances[min_idx]) / step_dist) * self.angle_step

    def theta_at_angle(self, angle):
        cf = 0
        if angle > pi / 2:
            cf = pi
        if angle > 3 * pi / 2:
            cf = 2 * pi
        return atan(self.x_radius/self.y_radius * tan(angle)) + cf

    def skewTransform(self, l, a2, b2):
        x0 = a2**2
        x1 = b2**2
        x2 = l**2
        x3 = x0*x2
        x4 = x0 - x1 + x3
        x5 = 2*a2*b2
        x6 = x0 + x1 + x3
        x7 = sqrt((-x5 + x6)*(x5 + x6))
        x9 = 1/(x4 - x7)
        x10 = x6 - x7
        x11 = l*x10
        x12 = b2**4
        x13 = 4*x12
        x14 = x10**2
        x15 = 4*x1
        x16 = sqrt(-x10*x15 + x13 + x14*x2 + x14)
        x17 = 2*atan(x9*(x11 - x16))
        x18 = sqrt(2)
        x19 = sqrt(x10)
        x20 = b2*x18*x19/2
        x21 = x0/2
        x22 = x1/2
        x23 = x2*x21
        x24 = x21 - x22 + x23
        x25 = x7/2
        x27 = 1/(x24 - x25)
        x28 = x21 + x22 + x23
        x29 = x28 - x25
        x30 = l*x29
        x31 = x14/4
        x32 = 2*x1
        x33 = sqrt(x12 + x2*x31 - x29*x32 + x31)
        x34 = 2*atan(x27*(x30 - x33))
        x35 = x20*sqrt(1/(-x1*cos(x34)**2 + x29))*sin(x34)
        x36 = x18/2
        x37 = -x19*x36
        x39 = 2*atan(x9*(x11 + x16))
        x40 = 2*atan(x27*(x30 + x33))
        x41 = x20*sqrt(1/(-x1*cos(x40)**2 + x29))*sin(x40)
        x42 = 1/(x4 + x7)
        x43 = x6 + x7
        x44 = l*x43
        x45 = x43**2
        x46 = sqrt(x13 - x15*x43 + x2*x45 + x45)
        x47 = 2*atan(x42*(x44 - x46))
        x48 = sqrt(x43)
        x49 = b2*x18*x48/2
        x50 = 1/(x24 + x25)
        x51 = x25 + x28
        x52 = l*x51
        x53 = x45/4
        x54 = sqrt(x12 + x2*x53 - x32*x51 + x53)
        x55 = 2*atan(x50*(x52 - x54))
        x56 = x49*sqrt(1/(-x1*cos(x55)**2 + x51))*sin(x55)
        x57 = -x36*x48
        x59 = 2*atan(x42*(x44 + x46))
        x60 = 2*atan(x50*(x52 + x54))
        x61 = x49*sqrt(1/(-x1*cos(x60)**2 + x51))*sin(x60)

        #solutions (alpha, a1, b1)
        (x17, -x35, x19*x36)
        (x17, x35, x37)
        (x39, -x41, x19*x36)
        (x39, x41, x37)
        (x47, -x56, x36*x48)
        (x47, x56, x57)
        (x59, -x61, x36*x48)
        (x59, x61, x57)

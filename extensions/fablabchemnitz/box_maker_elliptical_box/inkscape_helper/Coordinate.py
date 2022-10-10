from math import *

def inner_product(a, b):
    return a.x * b.x + a.y * b.y

class Coordinate(object):
    """
    Basic (x, y) coordinate class (or should it be called vector?) which allows some simple operations.
    """
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    #polar coordinates
    @property
    def t(self):
        angle = atan2(self.y, self.x)
        if angle < 0:
            angle += pi * 2
        return angle

    @t.setter
    def t(self, value):
        length = self.r
        self.x = cos(value) * length
        self.y = sin(value) * length


    @property
    def r(self):
        return hypot(self.x, self.y)

    @r.setter
    def r(self, value):
        angle = self.t
        self.x = cos(angle) * value
        self.y = sin(angle) * value

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "(%f, %f)" % (self.x, self.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __add__(self, other):
        return Coordinate(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Coordinate(self.x - other.x, self.y - other.y)

    def __mul__(self, factor):
        return Coordinate(self.x * factor, self.y * factor)

    def __neg__(self):
        return Coordinate(-self.x, -self.y)

    def __rmul__(self, other):
        return self * other

    def __div__(self, quotient):
        return Coordinate(self.x / quotient, self.y / quotient)

    def __truediv__(self, quotient):
        return self.__div__(quotient)

    def dot(self, other):
        """dot product"""
        return self.x * other.x + self.y * other.y

    def cross_norm(self, other):
        """"the norm of the cross product"""
        self.x * other.y - self.y * other.x

    def close_enough_to(self, other, limit=1E-9):
        return (self - other).r < limit


class IntersectionError(ValueError):
        """Raised when two lines do not intersect."""

def on_segment(pt, start, end):
    """Check if pt is between start and end. The three points are presumed to be collinear."""
    pt -= start
    end -= start
    ex, ey = end.x, end.y
    px, py = pt.x, pt.y
    px *= cmp(ex, 0)
    py *= cmp(ey, 0)
    return px >= 0 and px <= abs(ex) and py >= 0 and py <= abs(ey)

def intersection (s1, e1, s2, e2, on_segments = True):
    D = (s1.x - e1.x) * (s2.y - e2.y) - (s1.y - e1.y) * (s2.x - e2.x)
    if D == 0:
        raise IntersectionError("Lines from {s1} to {e1} and {s2} to {e2} are parallel")
    N1 = s1.x * e1.y - s1.y * e1.x
    N2 = s2.x * e2.y - s2.y * e2.x
    I = ((s2 - e2) * N1 - (s1 - e1) * N2) / D

    if on_segments and not (on_segment(I, s1, e1) and on_segment(I, s2, e2)):
        raise IntersectionError("Intersection {0} is not on line segments [{1} -> {2}] [{3} -> {4}]".format(I, s1, e1, s2, e2))
    return I

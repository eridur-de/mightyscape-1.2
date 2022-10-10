from inkscape_helper.PathSegment import *

class Line(PathSegment):

    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.pp = lambda t : PathPoint(t, self.start + t * (self.end - self.start), self.end - self.start, 0, t * self.length)

    @property
    def length(self):
        return (self.end - self.start).r

    def subdivide(self, part_length, start_offset=0): # note: start_offset should be smaller than part_length
        nr_parts = int((self.length - start_offset) // part_length)
        k_o = start_offset / self.length
        k2t = lambda k : k_o + k * part_length / self.length
        points = [self.pp(k2t(k)) for k in range(nr_parts + 1)]
        return(points, self.length - points[-1].c_dist)

    def pathpoint_at_t(self, t):
        return self.pp(t)

    def t_at_length(self, length):
        return length / self.length

from collections import namedtuple

PathPoint = namedtuple('PathPoint', 't coord tangent curvature c_dist')

class PathSegment(object):

    def __init__(self):
        raise NotImplementedError

    @property
    def lenth(self):
        raise NotImplementedError

    def subdivide(self, part_length):
        raise NotImplementedError

    def pathpoint_at_t(self, t):
        raise NotImplementedError

    def t_at_length(self, length):
        raise NotImplementedError

    # also need:

    #   find a way do do curvature dependent spacing
    #       - based on deviation from a standard radius?
    #       - or ratio between thickness and curvature?
    #def point_at_distance(d):
    #    pass

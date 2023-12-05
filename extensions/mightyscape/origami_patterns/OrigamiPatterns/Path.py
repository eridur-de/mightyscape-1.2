"""
Path Class

Defines a path and what it is supposed to be (mountain, valley, edge)

"""

import inkex
from math import sin, cos, pi, sqrt
from lxml import etree

class Path:
    """ Class that defines an svg stroke to be drawn in Inkscape

    Attributes
    ---------
    points: tuple or list of tuples
        Points defining stroke lines.
    style: str
        Single character defining style of stroke. Default values are:
        'm' for mountain creases
        'v' for valley creases
        'e' for edge borders
        Extra possible values:
        'u' for universal creases
        's' for semicreases
        'c' for kirigami cuts
    angle: float
        From 0 to 180 degrees, converted to an opacity level from 0 to 1. This is how OrigamiSimulator encodes maximum
        fold angles
    closed: bool
        Tells if desired path should contain a last stroke from the last point to the first point, closing the path
    radius: float
        If only one point is given, it's assumed to be a circle and radius sets the radius


    Methods
    ---------
    invert(self)
        Inverts path

    Overloaded Operators
    ---------
    __add__(self, offsets)
        Adding a tuple to a Path returns a new path with all points having an offset defined by the tuple

    __mul__(self, transform)
        Define multiplication of a Path to a vector in complex exponential representation


    Static Methods
    ---------
    draw_paths_recursively(path_tree, group, styles_dict)
        Draws strokes defined on "path_tree" to "group". Styles dict maps style of path_tree element to the definition
        of the style. Ex.:
        if path_tree[i].style = 'm', styles_dict must have an element 'm'.


    generate_hgrid(cls, xlims, ylims, nb_of_divisions, style, include_edge=False)
        Generate list of Path instances, in which each Path is a stroke defining a horizontal grid dividing the space
        xlims * ylims nb_of_divisions times.

    generate_vgrid(cls, xlims, ylims, nb_of_divisions, style, include_edge=False)
        Generate list of Path instances, in which each Path is a stroke defining a vertical grid dividing the space
        xlims * ylims nb_of_divisions times.

    generate_separated_paths(cls, points, styles, closed=False)
        Generate list of Path instances, in which each Path is the stroke between each two point tuples, in case each
        stroke must be handled separately

    reflect(cls, path, p1, p2)
        Reflects each point of path on line defined by two points and return new Path instance with new reflected points

    list_reflect(cls, paths, p1, p2)
        Generate list of new Path instances, rotation each path by transform

    list_rotate(cls, paths, theta, translation=(0, 0))
        Generate list of new Path instances, rotation each path by transform

    list_add(cls, paths, offsets)
        Generate list of new Path instances, adding a different tuple for each list

    list_mul(cls, paths, transf)
        Generate list of new Path instances, multiplying a different tuple for each list
        
    list_simplify(cls, paths)
        Gets complicated path-tree list and converts it into 
        a simple list.

    list_invert(cls, paths)
        Invert list of paths and points of each path.

    debug_points(cls, paths):
        Plots points of path tree in drawing order.
    """

    def __init__(self, points, style, closed=False, invert=False, radius=0.1, separated=False, fold_angle = 180.0):
        """ Constructor

        Parameters
        ---------
        points: list of 2D tuples
            stroke will connect all points
        style: str
            Single character defining style of stroke. For use with the OrigamiPatterns class (probably the only
            project that will ever use this file) the default values are:
            'm' for mountain creases
            'v' for valley creases
            'e' for edge borders
        closed: bool 
            if true, last point will be connected to first point at the end
        invert: bool
            if true, stroke will start at the last point and go all the way to the first one
        """
        if type(points) == list and len(points) != 1:
            self.type = 'linear'
            if invert:
                self.points = points[::-1]
            else:
                self.points = points

        elif (type(points) == list and len(points) == 1):
            self.type = 'circular'
            self.points = points
            self.radius = radius

        elif (type(points) == tuple and len(points) == 2):
            self.type = 'circular'
            self.points = [points]
            self.radius = radius

        else:
            raise TypeError("Points must be tuple of length 2 (for a circle) or a list of tuples of length 2 each")

        self.fold_angle = max(min(fold_angle, 180.), 0.)
        self.style = style
        self.closed = closed

    def invert(self):
        """ Inverts path
        """
        self.points = self.points[::-1]

    """ 
        Draw path recursively
        - Static method
        - Draws strokes defined on "path_tree" to "group"
        - Inputs:
        -- path_tree [nested list] of Path instances
        -- group [etree.SubElement]
        -- styles_dict [dict] containing all styles for path_tree
        """
    @staticmethod
    def draw_paths_recursively(path_tree, group, styles_dict):
        """ Static method, draw list of Path instances recursively
        """
        for subpath in path_tree:
            if type(subpath) == list:
                if len(subpath) == 1:
                    subgroup = group
                else:
                    subgroup = etree.SubElement(group, 'g')
                Path.draw_paths_recursively(subpath, subgroup, styles_dict)
            else:
                # ~ if subpath.style != 'n':
                if subpath.style != 'n' and styles_dict[subpath.style]['draw']:
                    if subpath.type == 'linear':

                        points = subpath.points
                        path = 'M{},{} '.format(*points[0])
                        for i in range(1, len(points)):
                            path = path + 'L{},{} '.format(*points[i])
                        if subpath.closed:
                            path = path + 'L{},{} Z'.format(*points[0])

                        attribs = {'style': str(inkex.Style(styles_dict[subpath.style])),
                                   'd': path,
                                   'opacity': str(subpath.fold_angle/180)}
                        etree.SubElement(group, inkex.addNS('path', 'svg'), attribs)
                    else:
                        attribs = {'style': str(inkex.Style(styles_dict[subpath.style])),
                                   'cx': str(subpath.points[0][0]), 'cy': str(subpath.points[0][1]),
                                   'r': str(subpath.radius),
                                   'opacity': str(subpath.fold_angle/180)}
                        etree.SubElement(group, inkex.addNS('circle', 'svg'), attribs)

    @classmethod
    def get_average_point(cls, paths):
        points = cls.get_points(paths)
        n = len(points)
        x, y = 0, 0
        for p in points:
            x += p[0]
            y += p[1]
        return (x/n, y/n)


    @classmethod
    def get_square_points(cls, width, height, center = None, rotation = 1):
        """ Get points of a square at given center or origin

        Parameters
        ---------
        width: float
        height: float
        center: list of floats
        rotation: float
            rotation in degrees

        Returns
        ---------
        points: list of tuples
        """
        if center is None:
            center = [width/2, height/2]

        #TODO: Implement rotation
        # c = cos(rotation * pi / 180)
        # s = sin(rotation * pi / 180)

        points = [
            (center[0] - 0.5*width, center[1] + 0.5*height),  # top left
            (center[0] + 0.5*width, center[1] + 0.5*height),  # top right
            (center[0] + 0.5*width, center[1] - 0.5*height),  # bottom right
            (center[0] - 0.5*width, center[1] - 0.5*height)]  # bottom left
        # points = [
            # (center[0] + (-0.5*width*c - 0.5*height*s), center[1] + (-0.5*width*s + 0.5*height*c)),  # top left
            # (center[0] + (+0.5*width*c - 0.5*height*s), center[1] + (+0.5*width*s + 0.5*height*c)),  # top right
            # (center[0] + (+0.5*width*c + 0.5*height*s), center[1] - (+0.5*width*s - 0.5*height*c)),  # bottom right
            # (center[0] + (-0.5*width*c + 0.5*height*s), center[1] - (-0.5*width*s - 0.5*height*c))]  # bottom left
        return points

    @classmethod
    def generate_square(cls, width, height, style ='e', fold_angle=180, center = None, rotation = 0):
        """ Generate a closed square at given center or origin

        Parameters
        ---------
        width: float
        height: float
        style: str
        fold_angle: float
        center: list of floats
        rotation: float
            rotation in degrees

        Returns
        ---------
        path: path instance
        """
        points = cls.get_square_points(width, height, center, rotation)
        return Path(points, style, fold_angle=fold_angle, closed=True)

    @classmethod
    def generate_hgrid(cls, xlims, ylims, nb_of_divisions, style, include_edge=False, fold_angle = 180):
        """ Generate list of Path instances, in which each Path is a stroke defining
        a horizontal grid dividing the space xlims * ylims nb_of_divisions times.

        All lines are alternated, to minimize Laser Cutter unnecessary movements

        Parameters
        ---------
        xlims: tuple
            Defines x_min and x_max for space that must be divided.
        ylims: tuple
            Defines y_min and y_max for space that must be divided.
        nb_of_divisions: int
            Defines how many times it should be divided.
        style: str
            Single character defining style of stroke.
        include_edge: bool 
            Defines if edge should be drawn or not.
        fold_angle: float

        Returns
        ---------
        paths: list of Path instances
        """
        rect_len = (ylims[1] - ylims[0])/nb_of_divisions
        hgrid = []
        for i in range(1 - include_edge, nb_of_divisions + include_edge):
            hgrid.append(cls([(xlims[0], ylims[0]+i*rect_len),
                              (xlims[1], ylims[0]+i*rect_len)],
                             style=style, invert=i % 2 == 0, fold_angle = fold_angle))
        return hgrid

    @classmethod
    def generate_vgrid(cls, xlims, ylims, nb_of_divisions, style, include_edge=False, fold_angle = 180):
        """ Generate list of Path instances, in which each Path is a stroke defining
        a vertical grid dividing the space xlims * ylims nb_of_divisions times.

        All lines are alternated, to minimize Laser Cutter unnecessary movements

        Parameters
        ---------
        -> refer to generate_hgrid

        Returns
        ---------
        paths: list of Path instances
        """
        rect_len = (xlims[1] - xlims[0])/nb_of_divisions
        vgrid = []
        for i in range(1 - include_edge, nb_of_divisions + include_edge):
            vgrid.append(cls([(xlims[0]+i*rect_len, ylims[0]),
                              (xlims[0]+i*rect_len, ylims[1])],
                             style=style, invert=i % 2 == 0, fold_angle = fold_angle))
        return vgrid

    @classmethod
    def generate_polygon(cls, sides, radius, style, center=(0, 0), fold_angle = 180):
        points = []
        for i in range(sides):
            points.append((radius * cos((1 + i * 2) * pi / sides),
                           radius * sin((1 + i * 2) * pi / sides)))
        return Path(points, style, closed=True, fold_angle = fold_angle)

    @classmethod
    def generate_separated_paths(cls, points, styles, closed=False, fold_angle = 180):
        """ Generate list of Path instances, in which each Path is the stroke
        between each two point tuples, in case each stroke must be handled separately.

        Returns
        ---------
        paths: list
            list of Path instances
        """
        paths = []
        if type(styles) == str:
            styles = [styles] * (len(points) - 1 + int(closed))
        elif len(styles) != len(points) - 1 + int(closed):
            raise TypeError("Number of paths and styles don't match")
        for i in range(len(points) - 1 + int(closed)):
            j = (i+1)%len(points)
            paths.append(cls([points[i], points[j]],
                             styles[i], fold_angle = fold_angle))
        return paths
        

    def __add__(self, offsets):
        """ " + " operator overload.
        Adding a tuple to a Path returns a new path with all points having an offset
        defined by the tuple
        """
        if type(offsets) == list:
            if len(offsets) != 1 or len(offsets) != len(self.points):
                raise TypeError("Paths can only be added by a tuple of a list of N tuples, "
                                "where N is the same number of points")

        elif type(offsets) != tuple:
            raise TypeError("Paths can only be added by tuples")
        else:
            offsets = [offsets] * len(self.points)

        # if type(self.points) == list:
        points_new = []
        for point, offset in zip(self.points, offsets):
            points_new.append((point[0]+offset[0],
                               point[1]+offset[1]))

        if self.type == 'circular':
            radius = self.radius
        else:
            radius = 0.2

         # if self.type == 'circular' else 0.1

        return Path(points_new, self.style, self.closed, radius=radius, fold_angle=self.fold_angle)

    @classmethod
    def list_add(cls, paths, offsets):
        """ Generate list of new Path instances, adding a different tuple for each list

        Parameters
        ---------
        paths: Path or list
            list of N Path instances
        offsets: tuple or list
            list of N tuples

        Returns
        ---------
        paths_new: list
            list of N Path instances
        """
        if type(paths) == Path and type(offsets) == tuple:
            paths = [paths]
            offsets = [offsets]
        elif type(paths) == list and type(offsets) == tuple:
            offsets = [offsets] * len(paths)
        elif type(paths) == Path and type(offsets) == list:
            paths = [paths] * len(offsets)
        elif type(paths) == list and type(offsets) == list:
            if len(paths) == 1:
                paths = [paths[0]] * len(offsets)
            elif len(offsets) == 1:
                offsets = [offsets[0]] * len(paths)
            elif len(offsets) != len(paths):
                raise TypeError("List of paths and list of tuples must have same length. {} paths and {} offsets "
                                " where given".format(len(paths), len(offsets)))
            else:
                pass

        paths_new = []
        for path, offset in zip(paths, offsets):
            if type(path) == Path:
                paths_new.append(path+offset)
            elif type(path) == list:
                paths_new.append(
                    cls.list_add(path, offset)
                )

        return paths_new

    @classmethod
    def list_mul(cls, paths, offsets):
        """ Generate list of new Path instances, multiplying a different tuple for each list

        Parameters
        ---------
        paths: Path or list
            list of N Path instances
        offsets: tuple or list
            list of N tuples

        Returns
        ---------
        paths_new: list
            list of N Path instances
        """
        if type(paths) == Path and type(offsets) == tuple:
            paths = [paths]
            offsets = [offsets]
        elif type(paths) == list and type(offsets) == tuple:
            offsets = [offsets] * len(paths)
        elif type(paths) == Path and type(offsets) == list:
            paths = [paths] * len(offsets)
        elif type(paths) == list and type(offsets) == list:
            if len(paths) == 1:
                paths = [paths[0]] * len(offsets)
            elif len(offsets) == 1:
                offsets = [offsets[0]] * len(paths)
            elif len(offsets) != len(paths):
                raise TypeError("List of paths and list of tuples must have same length. {} paths and {} offsets "
                                " where given".format(len(paths), len(offsets)))
            else:
                pass

        paths_new = []
        for path, offset in zip(paths, offsets):
            paths_new.append(path*offset)

        return paths_new

    def break_path(self, lengths, styles = None):
        if len(self.points) != 2:
            raise ValueError('Path breaking only implemented for straight lines with 2 points')

        if styles is None:
            styles = [self.style]*len(lengths)
        elif len(styles) != len(lengths):
            raise ValueError('Different number of lenghts and styles')

        p0 = self.points[0]
        p1 = self.points[1]
        d = (p1[0]-p0[0], p1[1]-p0[1])
        L = sqrt(d[0]**2 + d[1]**2)
        dx = d[0] / L
        dy = d[1] / L
        paths = []
        start = 0
        p0_ = p0
        for l, s in zip(lengths, styles):
            p1_ = (p0_[0] + dx*l, p0_[1] + dy*l)
            paths.append(Path([p0_, p1_], style = s))
            p0_ = p1_
        return paths



    def __mul__(self, transform):
        """ " * " operator overload.
        Define multiplication of a Path to a vector in complex exponential representation

        Parameters
        ---------
        transform: float of tuple of length 2 or 4
            if float, transform represents magnitude
                Example: path * 3
            if tuple length 2, transform[0] represents magnitude and transform[1] represents angle of rotation
                Example: path * (3, pi)
            if tuple length 4, transform[2],transform[3] define a different axis of rotation
                Example: path * (3, pi, 1, 1)
        """
        points_new = []

        # "temporary" (probably permanent) compatibility hack
        try:
            long_ = long
        except:
            long_ = int
            
        if isinstance(transform, (int, long_, float)):
            for p in self.points:
                points_new.append((transform * p[0],
                                   transform * p[1]))

        elif isinstance(transform, (list, tuple)):
            if len(transform) == 2:
                u = transform[0]*cos(transform[1])
                v = transform[0]*sin(transform[1])
                x_, y_ = 0, 0
            elif len(transform) == 4:
                u = transform[0]*cos(transform[1])
                v = transform[0]*sin(transform[1])
                x_, y_ = transform[2:]
            else:
                raise IndexError('Paths can only be multiplied by a number or a tuple/list of length 2 or 4')

            for p in self.points:
                x, y = p[0]-x_, p[1]-y_
                points_new.append((x_ + x * u - y * v,
                                   y_ + x * v + y * u))
        else:
            raise TypeError('Paths can only be multiplied by a number or a tuple/list of length 2 or 4')

        if self.type == 'circular':
            radius = self.radius
        else:
            radius = 0.2

        return Path(points_new, self.style, self.closed, radius=radius, fold_angle=self.fold_angle)

    def shape(self):
        points = self.points
        x = [p[0] for p in points]
        y = [p[1] for p in points]
        return [min(x), max(x), min(y), max(y)]

    @classmethod
    def list_create_from_points(cls, points, styles, fold_angles = None):
        """ Generate list of new Path instances, between each two points

            Parameters
            ---------
            points: list of tuples
                list of points
            styles: str or list of str
                styles
            fold_angles: list of floats
                list of maximum fold angle values

            Returns
            ---------
            paths_new: list
                list of N Path instances
            """
        if fold_angles is None:
            fold_angles = [180]
        elif type(fold_angles) != list:
            fold_angles = [fold_angles]

        return [Path([points[i], points[i+1]],
                     styles[i % len(styles)],
                     fold_angle=fold_angles[i % len(fold_angles)]) for i in range(len(points)-1)]

    @classmethod
    def list_rotate_symmetry(cls, paths, n, translation=(0,0)):
        """ Generate list of new Path instances, rotation each path by transform

        Parameters
        ---------
        paths: Path or list
            list of N Path instances
        n: int
            number of rotations
        translation: tuple or list 2
            axis of rotation

        Returns
        ---------
        paths_new: list
            list of N Path instances
        """

        theta = 2*pi/n
        paths_new = []
        for i in range(n):
            ith_rotation = cls.list_rotate(paths, theta, translation=translation)
            if type(paths) == list:
                paths_new += ith_rotation
            else:
                paths_new.append(ith_rotation)
        return paths_new


    @classmethod
    def list_rotate(cls, paths, theta, translation=(0, 0)):
        """ Generate list of new Path instances, rotation each path by transform

        Parameters
        ---------
        paths: Path or list
            list of N Path instances
        theta: float (radians)
            angle of rotation
        translation: tuple or list 2
            axis of rotation

        Returns
        ---------
        paths_new: list
            list of N Path instances
        """
        if len(translation) != 2:
            TypeError("Translation must have length 2")

        if type(paths) != list:
            paths = [paths]

        paths_new = []
        for path in paths:
            if type(path) == Path:
                paths_new.append(path*(1, theta, translation[0], translation[1]))
            elif type(path) == list:
                paths_new.append(cls.list_rotate(path, theta, translation))

        if len(paths_new) == 1:
            paths_new = paths_new[0]
        return paths_new

    # TODO:
    # Apparently it's not working properly, must be debugged and tested
    @classmethod
    def reflect(cls, path, p1, p2):
        """ Reflects each point of path on line defined by two points and return new Path instance with new reflected points

        Parameters
        ---------
        path: Path
        p1: tuple or list of size 2
        p2: tuple or list of size 2

        Returns
        ---------
        path_reflected: Path
        """

        (x1, y1) = p1
        (x2, y2) = p2

        if x1 == x2 and y1 == y2:
            ValueError("Duplicate points don't define a line")
        elif x1 == x2:
            t_x = [-1, 0, 2*x1, 1]
            t_y = [0, 1, 0, 1]
        else:
            m = (y2 - y1)/(x2 - x1)
            t = y1 - m*x1
            t_x = [1 - m**2, 2*m, -2*m*t, m**2 + 1]
            t_y = [2*m, m**2 - 1, +2*t, m**2 + 1]

        points_new = []
        for p in path.points:
            x_ = (t_x[0]*p[0] + t_x[1]*p[1] + t_x[2]) / t_x[3]
            y_ = (t_y[0]*p[0] + t_y[1]*p[1] + t_y[2]) / t_y[3]
            points_new.append((x_, y_))

        return Path(points_new, path.style, path.closed, fold_angle=path.fold_angle)

    # TODO:
    # Apparently it's not working properly, must be debugged and tested
    @classmethod
    def list_reflect(cls, paths, p1, p2):
        """ Generate list of new Path instances, rotation each path by transform

        Parameters
        ---------
        paths: Path or list
            list of N Path instances
        p1: tuple or list of size 2
        p2: tuple or list of size 2

        Returns
        ---------
        paths_new: list
            list of N Path instances
        """

        if type(paths) == Path:
            paths = [paths]

        paths_new = []
        for path in paths:
            paths_new.append(Path.reflect(path, p1, p2))

        return paths_new
        
    @classmethod
    def list_simplify(cls, paths):
        """ Gets complicated path-tree list and converts it into 
        a simple list.

        Returns
        ---------
        paths: list
            list of Path instances
        """
        if type(paths) == Path:
            return paths

        simple_list = []
        for i in range(len(paths)):
            if type(paths[i]) == Path:
                simple_list.append(paths[i])
            elif type(paths[i]) == list:
                simple_list = simple_list + Path.list_simplify(paths[i])
        return simple_list

    @classmethod
    def list_invert(cls, paths):
        """ Invert list of paths and points of each path.

        Returns
        ---------
        paths: list
            list of Path instances
        """

        if type(paths) == Path:
            # return Path(paths.points[::-1], paths.style, paths.closed, paths.invert)
            return Path(paths.points, paths.style, paths.closed, True)
        elif type(paths) == list:
            paths_inverted = []
            # n = len(paths)
            # for i in range(n):
            #     # paths_inverted.append(Path.list_invert(paths[n-1-i]))
            #     paths_inverted.append(Path.list_invert(paths[i]))
            for path in paths:
                # paths_inverted.append(Path.list_invert(paths[n-1-i]))
                paths_inverted.append(Path.list_invert(path))
            return paths_inverted[::-1]

    @classmethod
    def debug_points(cls, paths):
        """ Plots points of path tree in drawing order.

        """
        if type(paths) == Path:
            inkex.debug(paths.points)
        elif type(paths) == list:
            for sub_path in paths:
                Path.debug_points(sub_path)

    @classmethod
    def get_points(cls, paths):
        """ Get points of path tree in drawing order.

        """
        points = []
        if type(paths) == Path:
            points = points + paths.points
        elif type(paths) == list:
            for sub_path in paths:
                points = points + Path.get_points(sub_path)
        return points



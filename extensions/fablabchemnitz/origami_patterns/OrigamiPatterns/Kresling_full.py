#! /usr/bin/env python
# -*- coding: utf-8 -*-
from math import sin, cos, sqrt, asin, pi, ceil
import inkex

from Path import Path
from Pattern import Pattern
from Kresling import Kresling


class Kresling_Full(Kresling):
    
    def __init__(self):
        """ Constructor
        """
        Kresling.__init__(self)  # Must be called in order to parse common options

        self.add_argument('--measure_value', type=self.float, default=10.0)
        self.add_argument('--measure_type', type=self.str, default=60)
        self.add_argument('--parameter_type', type=self.str, default=60)
        self.add_argument('--radial_ratio', type=self.float, default=0.5)
        self.add_argument('--angle_ratio', type=self.float, default=0.5)
        self.add_argument('--lambdatheta', type=self.float, default=45)

    def generate_path_tree(self):
        """ Convert radial to angular ratio, then call regular Kresling constructor
        """
        n = self.options.sides
        theta = pi*(n-2)/(2*n)   
        # define ratio parameter
        parameter = self.options.parameter_type
        if parameter == 'radial_ratio':
            radial_ratio = self.options.radial_ratio
            max_radial_ratio = sin((pi/4)*(1. - 2./n))
            if radial_ratio > max_radial_ratio:
                inkex.errormsg(_("For polygon of {} sides, the maximal radial ratio is = {}".format(n, max_radial_ratio)))
                radial_ratio = max_radial_ratio
            self.options.angle_ratio = 1 - 2*n*asin(radial_ratio)/((n-2)*pi)

        elif parameter == 'lambdatheta':
            lambdatheta = self.options.lambdatheta
            angle_min = 45. * (1 - 2. / n)
            angle_max = 2 * angle_min
            if lambdatheta < angle_min:
                inkex.errormsg(_(
                    "For polygon of {} sides, phi must be between {} and {} degrees, \nsetting lambda*theta = {}\n".format(
                        n, angle_min, angle_max, angle_min)))
                lambdatheta = angle_min
            elif lambdatheta > angle_max:
                inkex.errormsg(_(
                    "For polygon of {} sides, phi must be between {} and {} degrees, \nsetting lambda*theta = {}\n".format(
                        n, angle_min, angle_max, angle_max)))
                lambdatheta = angle_max
            self.options.angle_ratio = lambdatheta * n / (90. * (n - 2.))


        # define some length
        mtype = self.options.measure_type
        mvalue = self.options.measure_value
        angle_ratio = self.options.angle_ratio
        if mtype == 'a':
            radius = 0.5*mvalue / (sin(pi/n))
        if mtype == 'b':
            A = cos(theta*(1-angle_ratio))
            B = sin(pi/n)
            C = cos(theta*angle_ratio)
            radius = 0.5*mvalue / sqrt(A**2 + B**2 - 2*A*B*C)
        elif mtype == 'l':
            radius = 0.5*mvalue/cos(theta*(1-angle_ratio))
        elif mtype == 'radius_external':
            radius = mvalue
        elif mtype == 'radius_internal':
            radius = mvalue/(sin(theta*(1-angle_ratio)))
        elif mtype == 'diameter_external':
            radius = 0.5*mvalue
        elif mtype == 'diameter_internal':
            radius = 0.5*mvalue/sin(theta*(1-angle_ratio))

        # inkex.errormsg(_("Value = {}, Mode = {}, Radius = {}".format(mvalue, mtype, radius)))

        if self.options.pattern == 'mirrowed':
            self.options.mirror_cells = True
        else:
            self.options.mirror_cells = False
        self.options.radius = radius

        Kresling.generate_path_tree(self)


if __name__ == '__main__':
    e = Kresling_Full()
    e.draw()

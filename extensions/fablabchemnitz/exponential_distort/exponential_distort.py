#!/usr/bin/env python3

from __future__ import print_function
import sys
import math
import inkex
from inkex.paths import CubicSuperPath

class ExponentialDistort(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        #pars.add_argument('-a', '--axis', default='x', help='distortion axis. Valid values are "x", "y", or "xy". Default is "x"')
        pars.add_argument('-x', '--exponent', type=float, default=1.3, help='distortion factor. 1=no distortion, default 1.3')
        pars.add_argument('-p', '--padding_perc', type=float, default=0, help='pad at origin. Padding 100% runs the exponential curve through [0.5 .. 1.0] -- default 0% runs through [0.0 .. 1.0]')

    def x_exp(self, bbox, x):
        """ reference implementation ignoring padding. unused. """
        xmin = bbox[0]      # maps to 0
        xmax = bbox[1]      # maps to 1
        w = xmax-xmin       # maps to 1
        # convert world to math coordinates
        xm = (x-xmin)/w
        # apply function with properties  f(1.0) == 1.0 and f(0.0) == 0.0
        xm = xm**self.options.exponent    # oh, parabola or logarithm?
        # convert back from math to world coordinates.
        return x*w + xmin

    def x_exp_p(self, bbox, x):
        """ parabola mapping with padding
            CAUTION: the properties f(1.0) == 1.0 and f(0.0) == 0.0
            do not really hold, as our x does not run the full range [0.0 .. 1.0]
            FIXME: if you expect some c**xm here, instead of xm**c, think about c==1 ...
        """
        xmin = bbox[0]                                                 # maps to 0 when padding=0,
        xmax = bbox[1]                                                 # maps to 1
        xzero = xmin - (xmax-xmin)*self.options.padding_perc*0.01      # maps to 0, after applying padding
        w = xmax - xzero
        w = w * (1+self.options.padding_perc*0.01)
        # convert world to math coordinates
        xm = (x-xzero)/w
        # apply function with properties  f(1.0) == 1.0 and f(0.0) == 0.0
        xm = xm**self.options.exponent  # oh, parabola or logarithm?
        return xm

    def x_exp_p_inplace(self, bbox, xm):
        """ back from mat to world coordinates, retaining xmin and xmax

            Algorithm: (pre)compute a linear mapping function by explicitly
            running x_exp_p for the two points xmin and xmax.
            Then use the resulting linear function to map back any xm into world coordinates x.

            An obvious speedup by factor 3 is waiting for you here.
        """

        xmin = bbox[0]
        xmax = bbox[1]
        ## assert that xmin maps to xmin and xmax maps to xmax, whatever x_exp_p() does to us.
        f_xmin = self.x_exp_p(bbox, xmin)
        f_xmax = self.x_exp_p(bbox, xmax)
        f_x    = self.x_exp_p(bbox, xm)
        x = (f_x - f_xmin) * (xmax-xmin) / (f_xmax-f_xmin) + xmin
        return x

    def computeBBox(self, pts):
        """ 'improved' version of simplepath.computeBBox, this one includes b-spline handles."""
        xmin = None
        xmax = None
        ymin = None
        ymax = None
        for p in pts:
          for pp in p:
            for ppp in pp:
              if xmin is None: xmin = ppp[0]
              if xmax is None: xmax = ppp[0]
              if ymin is None: ymin = ppp[1]
              if ymax is None: ymax = ppp[1]

              if xmin > ppp[0]: xmin = ppp[0]
              if xmax < ppp[0]: xmax = ppp[0]
              if ymin > ppp[1]: ymin = ppp[1]
              if ymax < ppp[1]: ymax = ppp[1]
        return (xmin, xmax, ymin, ymax)

    def effect(self):

        if len(self.svg.selected) == 0:
            inkex.errormsg("Please select an object to perform the " +
                             "exponential-distort transformation on.")
            return

        for id, node in self.svg.selected.items():
            type = node.get("{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}type", "path")
            if node.tag != '{http://www.w3.org/2000/svg}path' or type != 'path':
                inkex.errormsg(node.tag + " is not a path. Type="+type+". Please use 'Path->Object to Path' first.")
            else:
                pts = CubicSuperPath(node.get('d'))
                bbox = self.computeBBox(pts)
                ## bbox (60.0, 160.0, 77.0, 197.0)
                ## pts [[[[60.0, 77.0], [60.0, 77.0], [60.0, 77.0]], [[60.0, 197.0], [60.0, 197.0], [60.0, 197.0]], [[70.0, 197.0], ...
                for p in pts:
                  for pp in p:
                    for ppp in pp:
                      ppp[0] = self.x_exp_p_inplace(bbox, ppp[0])

                node.set('d', str(pts))

if __name__ == '__main__':
    ExponentialDistort().run()
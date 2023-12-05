#!/usr/bin/env python3
# coding=utf-8
#
# Copyright (C) 2020 Dylan Simon, dylan@dylex.net
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
Perform fixed-depth IFS repeated duplicate-and-transform.
"""

import inkex

class IFSFractals(inkex.EffectExtension):
    NXFORM = 5
    XFORM_PARAMS = list("ABCDEF")

    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--iter", type=int, default=3, help="number of iterations")
        for i in range(self.NXFORM):
            pars.add_argument("--xform%d"%i, type=inkex.Boolean, default=False, help="enable transformation %d"%i)
            for p in self.XFORM_PARAMS:
                pars.add_argument("--%s%d"%(p,i), type=float, help="transformation matrix %d %s"%(i,p))

    def effect(self):
        xforms = []
        for i in range(self.NXFORM):
            if getattr(self.options,'xform%d'%i):
                t = [getattr(self.options,"%s%d"%(p,i)) for p in self.XFORM_PARAMS]
                xforms.append(inkex.Transform(t))

        if not xforms:
            inkex.errormsg(_('There are no transforms to apply'))
            return False

        if not self.svg.selected:
            inkex.errormsg(_('There is no selection to duplicate'))
            return False

        nodes = self.svg.selected.values()
        grp = inkex.Group('IFS')
        layer = self.svg.get_current_layer().add(grp)

        for i in range(self.options.iter):
            n = []
            for node in nodes:
                for x in xforms:
                    d = node.copy()
                    d.transform = x @ d.transform
                    n.append(d)
            g = inkex.Group('IFS iter %d'%i)
            g.add(*n)
            grp.add(g)
            nodes = n

        return True

if __name__ == '__main__':
    IFSFractals().run()

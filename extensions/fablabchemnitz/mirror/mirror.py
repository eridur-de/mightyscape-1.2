#!/usr/bin/env python3
"""
Derived from the "envelope" extension by Aaron Spike, aaron@ekips.org
By Apex 2011
New version Jens Kober 2017, 2020

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
import inkex
from inkex.localization import inkex_gettext as _

class Mirror(inkex.EffectExtension):

    def effect(self):
        if len(self.options.ids) < 2:
            raise inkex.AbortExtension(_("This extension requires two selected objects. \nThe second must be a path, exactly two nodes long."))

        #trafo is selected second
        obj = self.svg.selected[self.options.ids[0]]
        trafo = self.svg.selected[self.options.ids[1]]

        if isinstance(trafo, inkex.PathElement):
            #distil trafo into two node points
            trafoPath = trafo.path.transform(trafo.composed_transform()).to_superpath()
            if len(trafoPath[0]) != 2:
                raise inkex.AbortExtension(_("The second selected object must be exactly two nodes long."))
            
            # origin of mirror line
            ox = trafoPath[0][0][1][0]
            oy = trafoPath[0][0][1][1]
            # vector along mirror line
            vx = trafoPath[0][1][1][0] - ox
            vy = trafoPath[0][1][1][1] - oy

            # the transformation first translates the origin of the mirror line to [0 0], then rotates the mirror line onto the x-axis, 
            # reflects everything over the x-axis, undoes the rotation, and finally undoes the translation

            # alpha = atan2(vy, vx);

            #                  [1 0 ox] [cos(alpha) -sin(alpha) 0] [1  0 0] [cos(-alpha) -sin(-alpha) 0] [1 0 -ox]
            # Transformation = [0 1 oy]*[sin(alpha)  cos(alpha) 0]*[0 -1 0]*[sin(-alpha)  cos(-alpha) 0]*[0 1 -oy]
            #                  [0 0  1] [         0           0 1] [0  0 1] [          0            0 1] [0 0   1]

            # after some simplifications (or using your favorite symbolic math software):

            #                  [(vx^2-vy^2)/(vx^2+vy^2)    (2 vx vy)/(vx^2+vy^2)  (2 vy (ox vy-oy vx))/(vx^2+vy^2)]
            # Transformation = [  (2 vx vy)/(vx^2+vy^2) -(vx^2-vy^2)/(vx^2+vy^2) -(2 vx (ox vy-oy vx))/(vx^2+vy^2)]
            #                  [                      0                        0                                 1]
            
            denom = vx**2 + vy**2
            a00 = (vx**2 - vy**2) / denom
            a01 = (2 * vx * vy) / denom
            a02 = 2 * (ox * vy - oy * vx) / denom
            mat=[[a00, a01, vy * a02], [a01, -a00, -vx * a02]]
            obj.transform = inkex.Transform(mat) @ obj.transform
            
        else:
            if isinstance(trafo, inkex.Group):
                raise inkex.AbortExtension(_("The second selected object is a group, not a path.\nTry using the procedure Object->Ungroup."))
            else:
                raise inkex.AbortExtension(_("The second selected object is not a path.\nTry using the procedure Path->Object to Path."))

if __name__ == '__main__':
    Mirror().run()
#!/usr/bin/env python3
# coding=utf-8
#
# Copyright (C) 2020 Ellen Wasboe, ellen@wasbo.net
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
"""
Remove all z-s from all selected paths
My purpose: to open paths of single line fonts with a temporary closing to fit into .ttf/.otf format files
"""

import inkex, re
from inkex import PathElement

class OpenClosedPath(inkex.EffectExtension):
# Extension to open a closed path by z or by last node

    def effect(self):
        elements = self.svg.selection.filter(PathElement).values()
        for elem in elements:
            pp = elem.path.to_absolute() #remove transformation matrix
            elem.path = re.sub(r"Z","",str(pp))
           
            sp = elem.path.to_superpath()
            if sp[0] == sp[-1]:  #if first is last point the path is also closed. The "Z" command is not required
                raw = elem.path.to_arrays()
                del raw[-1] #delete last point in path
                elem.path = raw
                
if __name__ == '__main__':
    OpenClosedPath().run()
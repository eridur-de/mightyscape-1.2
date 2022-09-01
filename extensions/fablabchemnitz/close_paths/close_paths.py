#!/usr/bin/env python3
"""
Copyright (C) 2009 Nick Drobchenko, nick@cnc-club.ru
based on gcode.py (C) 2007 hugomatic... 
based on addnodes.py (C) 2005,2007 Aaron Spike, aaron@ekips.org
based on dots.py (C) 2005 Aaron Spike, aaron@ekips.org

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

#	
#	This extension close paths by adding 'z' before each 'm' if it is not the first 'm' and it is not prepended by 'z' already.
#

import inkex
import re
from inkex.paths import Path
			
class ClosePaths(inkex.EffectExtension):

	def effect(self):
		for id, node in self.svg.selected.items():
			if node.tag == inkex.addNS('path','svg'):
				d = node.get('d')
				d = str(Path((Path(d).to_arrays())))
				d = re.sub(r'(?i)(m[^mz]+)',r'\1 Z ',d)
				d = re.sub(r'(?i)\s*z\s*z\s*',r' Z ',d)
				node.set('d', d)	

if __name__ == '__main__':
    ClosePaths().run()
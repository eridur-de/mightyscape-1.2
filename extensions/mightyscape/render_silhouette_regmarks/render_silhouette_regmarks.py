#
# Copyright (C) 2021 miLORD1337
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110, USA.
#
"""
Base module for rendering regmarks for Silhouette CAMEO products in Inkscape.
"""

import inkex
from lxml import etree

SVG_URI = u'http://www.w3.org/2000/svg'

class SilhouetteCameoRegistrationMarks(inkex.EffectExtension):

	def add_arguments(self, pars):
		# Define string option "--what" with "-w" shortcut and default value "World".
		# Layer name static, since self.document.getroot() not available on initialization
		self.layername = 'silhouette-regmark'
		
		# Parse arguments
		pars.add_argument("-X", "--reg-x", "--regwidth",	type = float, dest = "regwidth", default = 180.0, help="X mark distance [mm]")
		pars.add_argument("-Y", "--reg-y", "--reglength", type = float, dest = "reglength", default = 230.0, help="Y mark distance [mm]")
		pars.add_argument("--rego-x",  "--regoriginx", type = float, dest = "regoriginx", default = 15.0, help="X mark origin from left [mm]")
		pars.add_argument("--rego-y", "--regoriginy", type = float, dest = "regoriginy", default = 20.0, help="X mark origin from top [mm]")
	
	#SVG rect element generation routine
	def drawRect(self, size, pos, name):
		x, y = pos
		w, h = size
		rect = etree.Element('{%s}rect' % SVG_URI)
		rect.set('x', str(x))
		rect.set('y', str(y))
		rect.set('id', name)
		rect.set('width', str(w))
		rect.set('height', str(h))
		rect.set('style', 'fill: black;')
		return rect
		
	#SVG line element generation routine
	def drawLine(self, posStart, posEnd, name):
		x1, y1 = posStart
		x2, y2, = posEnd
		line = etree.Element('{%s}line' % SVG_URI)
		line.set('x1', str(x1))
		line.set('y1', str(y1))
		line.set('x2', str(x2))
		line.set('y2', str(y2))
		line.set('id', name)
		line.set('style', 'stroke: black; stroke-width: 0.5;')
		return line
	
	def effect(self):
		svg = self.document.getroot()
		
		# Create a new layer.
		layer = etree.SubElement(svg, 'g')
		layer.set(inkex.addNS('label', 'inkscape'), self.layername)
		layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
	
		# Create square in top left corner
		layer.append(self.drawRect((5,5), (self.options.regoriginx,self.options.regoriginy), 'TopLeft'))
		
		# Create group for top right corner
		topRight = etree.Element('{%s}g' % SVG_URI)
		topRight.set('id', 'TopRight')
		topRight.set('style', 'fill: black;')
		
		# Create horizontal and vertical lines in group
		topRight.append(self.drawLine((self.options.regwidth-20,self.options.regoriginy), (self.options.regwidth,self.options.regoriginy), 'Horizontal'))
		topRight.append(self.drawLine((self.options.regwidth,self.options.regoriginy), (self.options.regwidth,self.options.regoriginy + 20), 'Vertical'))
		layer.append(topRight)
		
		# Create group for top right corner
		bottomLeft = etree.Element('{%s}g' % SVG_URI)
		bottomLeft.set('id', 'BottomLeft')
		bottomLeft.set('style', 'fill: black;')
		
		# Create horizontal and vertical lines in group
		bottomLeft.append(self.drawLine((self.options.regoriginx,self.options.reglength), (self.options.regoriginx+20,self.options.reglength), 'Horizontal'))
		bottomLeft.append(self.drawLine((self.options.regoriginx,self.options.reglength), (self.options.regoriginx,self.options.reglength - 20), 'Vertical'))
		layer.append(bottomLeft)
		
		#Lock layer
		layer.set(inkex.addNS('insensitive', 'sodipodi'), 'true') 
		
if __name__ == '__main__':
	SilhouetteCameoRegistrationMarks().run()
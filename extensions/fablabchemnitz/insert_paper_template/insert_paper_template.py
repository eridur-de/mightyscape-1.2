#!/usr/bin/env python3


# Copyright 2016 Luke Phillips (lukerazor@hotmail.com)
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
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# Extension dirs
# linux:~/.config/inkscape/extensions
# windows: D:\Program Files\Inkscape\share\extensions
from lxml import etree
import inkex

inkex.NSS[u'cs'] = u'http://www.razorfoss.org/tuckboxextension/'

class InsertPaperTemplate(inkex.EffectExtension):
	
	def add_arguments(self, pars):
		pars.add_argument('-p', '--papertype')
		pars.add_argument('-s', '--show_type', type=inkex.Boolean, default=True)

	def effect(self):

		self.Group = etree.SubElement(self.svg.get_current_layer(), inkex.addNS('g','svg'), {} )

		papertypes = {}
		papertypes["A7"]       = (74  , 105 , "#7f7f7f") # grey
		papertypes["A6"]       = (105 , 148 , "#00ffff") # cyan
		papertypes["A5"]       = (148 , 210 , "#ffeeaa") # yellow
		papertypes["A4"]       = (210 , 297 , "#ffccaa") # orange
		papertypes["A3"]       = (297 , 420 , "#afdde9") # blue
		papertypes["A2"]       = (420 , 594 , "#ccaaff") # purple
		papertypes["A1"]       = (594 , 841 , "#afe9c6") # green
		papertypes["A0"]       = (841 , 1189, "#ffd5d5") # red
		papertypes["B6"]       = (125 , 176 , "#ffccaa") # orange
		papertypes["B5"]       = (176 , 250 , "#afdde9") # blue
		papertypes["C6"]       = (114 , 162 , "#ccaaff") # purple
		papertypes["C5"]       = (162 , 228 , "#afe9c6") # green
		papertypes["DIN_LANG"] = (110 , 220 , "#ffd5d5") # red
		papertypes["POKER"]    = (63.5, 88  , "#ffffff") # white
		papertypes["BRIDGE"]   = (56  , 88  , "#ffffff") # white
		papertypes["MINI_US"]  = (41  , 63  , "#ffffff") # white
		papertypes["MINI_EU"]  = (44  , 68  , "#ffffff") # white
		papertypes["TAROT"]    = (70  , 120 , "#ffffff") # white

		if self.options.papertype in papertypes:
			self.CreateTemplate(self.options.papertype, *(papertypes[self.options.papertype]))
		else:
			raise Exception("Paper type '{0}' is undefined".format(self.options.papertype))

	def CreateTemplate(self, label, width, height, color):
		x = 0
		y = 0
		self._CreateRectangleInMillimetres(width, height, x, y, color)
		if self.options.show_type is True:
			self._CreateText(label, x + width/2 , y + height/2)

	def _CreateText(self, labelText, x, y):
		style = {'stroke': '#000000',
			'stroke-width': '0.25',
			'fill' : '#000000',
			'font-size' : "11px",
			'text-align' : 'center',
			'text-anchor' : 'middle'
			}

		attribs = {
			'style': str(inkex.Style(style)), 
			'x': "{}".format(x), 
			'y': "{}".format(y)
			}

		text = etree.Element(inkex.addNS('text','svg'), attribs)
		text.text = labelText

		self.Group.append(text)

	def _CreateRectangleInMillimetres(self, width, height, x, y, color):
		style = {
			'stroke': '#000000', 
			'stroke-width': '0.25', 
			'fill' : color
			}
		attribs = {
			'style': str(inkex.Style(style)), 
			'height': "{}".format(height), 
			'width': "{}".format(width), 
			'x': "{}".format(x), 
			'y': "{}".format(y)
			}
		etree.SubElement(self.Group, inkex.addNS('rect','svg'), attribs )

if __name__ == '__main__':
	InsertPaperTemplate().run()
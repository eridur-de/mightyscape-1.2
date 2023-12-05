#!/usr/bin/env python3
# Copyright 2015 Jo Pol
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

from __future__ import division
from math import pi, sin, cos, tan, radians
from lxml import etree

# We will use the inkex module with the predefined 
# Effect base class.
import inkex

__author__ = 'Jo Pol'
__credits__ = ['Veronika Irvine','Jo Pol','Mark Shafer']
__license__ = 'GPLv3'

class PolarGrid(inkex.EffectExtension):
	
	def add_arguments(self, pars):
		pars.add_argument('-a', '--angle',  type=float, default=45, help='grid angle (degrees)')
		pars.add_argument('-d', '--dots',  type=int, default=180, help='number of dots on a circle')
		pars.add_argument('-o', '--outerDiameter', type=float, default=160, help='outer diameter (mm)')
		pars.add_argument('-i', '--innerDiameter', type=float, default=100, help='minimum inner diameter (mm)')
		pars.add_argument('-f', '--fill',  type=inkex.Color, default='-6711040', help='dot color')
		pars.add_argument('-A', '--alignment', default='outside', help='exact diameter on [inside|outside]')
		pars.add_argument('-s', '--size',  type=float, default=0.5, help='dot diameter (mm)')
		pars.add_argument('-v', '--variant',  default='', help='omit rows to get [|rectangle|hexagon1]')
		pars.add_argument('-cu', '--circleDiameterUnits', default = 'mm', help = 'Circle diameter is measured in these units')
		pars.add_argument('-du', '--dotUnits',  default = 'px', help = 'Dot diameter is measured in these unites')

	def group(self, diameter):
		"""
		Create a group labeled with the diameter
		"""
		label = 'diameter: {0:.2f} mm'.format(diameter)
		attribs = {inkex.addNS('label', 'inkscape'):label}
		return etree.SubElement(self.gridContainer, inkex.addNS('g', 'svg'), attribs)

	def dots(self, diameter, circleNr, group):
		"""
		Draw dots on a grid circle
		"""
		offset = (circleNr % 2) * 0.5
		for dotNr in range (0, self.options.dots):
			a = (dotNr + offset) * self.alpha
			x = (diameter / 2.0) * cos(a)
			y = (diameter / 2.0) * sin(a)
			attribs = {'style':self.dotStyle, 'cx':str(x * self.circleScale), 'cy':str(y * self.circleScale), 'r':self.dotR}
			etree.SubElement(group, inkex.addNS('circle', 'svg'), attribs)

	def iterate(self, diameter, circleNr):
		"""
		Create a group with a ring of dots.
		Returns half of the arc length between the dots
		which becomes the distance to the next ring.
		"""
		group = self.group(diameter)
		self.dots(diameter, circleNr, group)
		self.generatedCircles.append(group)
		return diameter * self.change

	def generate(self):
		"""
		Generate rings with dots, either inside out or outside in
		"""
		circleNr = 0
		flag_error = False
		minimum = 2 * self.options.size * self.options.dots /pi
		if minimum < self.options.innerDiameter:
			minimum = self.options.innerDiameter
		else:
			flag_error = True
		if self.options.alignment == 'outside':
			diameter = self.options.outerDiameter
			while diameter > minimum:
				diameter -= self.iterate(diameter, circleNr)
				circleNr += 1
		else:
			diameter = minimum
			while diameter < self.options.outerDiameter:
				diameter += self.iterate(diameter, circleNr)
				circleNr += 1
		# Display message
		if flag_error:
			# Leave message on top
			font_height = 8
			text_style = { 'font-size': str(font_height),
							'font-family': 'sans-serif',
							'text-anchor': 'middle',
							'text-align': 'center',
							'fill': '#000000' }
			text_atts = {'style':str(inkex.Style(text_style)),
						'x': '0', 'y': '0'}
			text = etree.SubElement(self.gridContainer, 'text', text_atts)
			text.text = "Dots overlap. inner changed to %4.1f" % (minimum)

	def removeGroups(self, start, increment):
		"""
		Remove complete rings with dots
		"""
		for i in range(start, len(self.generatedCircles), increment):
			self.svg.get_current_layer().remove(self.generatedCircles[i])

	def removeDots(self, i, offset, step):
		"""
		Remove dots from one circle
		"""
		group = self.generatedCircles[i]
		dots = list(group)
		start = len(dots) - 1 - offset
		for j in range(start, -1, 0-step):
			group.remove(dots[j])

	def computations(self, angle):
		self.alpha = radians(360.0 / self.options.dots)
		correction = pi / (4 * self.options.dots)
		correction *= tan(angle*0.93)
		self.change = tan(angle - correction) * pi / self.options.dots

	def effect(self):
		"""
		Effect behaviour.
		Overrides base class' method and draws something.
		"""

		# constants
		self.dotStyle = str(inkex.Style({'fill': self.options.fill.to_rgb(),'stroke':'none'}))
		self.dotScale = self.svg.unittouu("1" + self.options.dotUnits)
		self.dotR = str(self.options.size * (self.dotScale/2))
		self.circleScale = self.svg.unittouu("1" + self.options.circleDiameterUnits)
		self.computations(radians(self.options.angle))

		# processing variables
		self.generatedCircles = []
		self.gridContainer =  self.svg.get_current_layer()

		self.generate()

		if self.options.variant == 'rectangle':
			self.removeGroups(1, 2)
		elif self.options.variant == 'hexagon1':
			self.removeGroups(0, 3)
		elif self.options.variant == 'hexagon2' or self.options.variant == 'snow2':
			for i in range(0, len(self.generatedCircles), 1):
				self.removeDots(i, (((i%2)+1)*2)%3, 3)
		elif self.options.variant == 'hexagon3':
			for i in range(0, len(self.generatedCircles), 2):
				self.removeDots(i, (i//2+1)%2, 2)
		elif self.options.variant == 'hexagon4':
			self.removeGroups(0, 4)
		elif self.options.variant == 'hexagon5' or self.options.variant == 'snow1':
			for i in range(0, len(self.generatedCircles), 2):
				self.removeDots(i, 1, 2)

		self.dotStyle = str(inkex.Style({'fill': 'none','stroke':self.options.fill.to_rgb(),'stroke-width':0.7}))
		self.dotR = str((((self.options.innerDiameter * pi) / self.options.dots) / 2) * self.dotScale)
		self.generatedCircles = []
		if self.options.variant == 'snow2':
			self.options.dots = self.options.dots // 3
			self.computations(radians(self.options.angle))
			self.generate()
		elif self.options.variant == 'snow1':
			self.generate()
			self.removeGroups(1, 2)
			for i in range(0, len(self.generatedCircles), 2):
				self.removeDots(i, i%4, 2)
			for i in range(0, len(self.generatedCircles), 2):
				self.removeDots(i, (i+1)%2, 2)
			for i in range(2, len(self.generatedCircles), 4):
				self.removeDots(i, 0, self.options.dots)

if __name__ == '__main__':
	PolarGrid().run()
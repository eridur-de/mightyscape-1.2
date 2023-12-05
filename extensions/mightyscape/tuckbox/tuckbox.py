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
# windows: [Drive]:\Program Files\Inkscape\share\extensions

from lxml import etree
import inkex
import copy

CUTOUT_TOP = 1
CUTOUT_BOTTOM = 2
CUTOUT_LEFT = 4
CUTOUT_RIGHT = 8

inkex.NSS[u'cs'] = u'http://www.razorfoss.org/tuckboxextension/'

class EffectDimensionProvider():
	def __init__(self, effect, x = 0, y = 0):
		self.Effect = effect

		self.Layer = effect.svg.get_current_layer()

		self.Width = effect.options.DeckWidth
		self.Height = effect.options.DeckHeight
		self.Depth = effect.options.DeckDepth
		self.Allowance = effect.options.DeckAllowance

		self.X = x
		self.Y = y

	def MMtoUU(self, mmval):
		if hasattr(self.Effect.svg, "unittouu"):
			return str(self.Effect.svg.unittouu("{0}mm".format(mmval)))
		else:
			MM_TO_PIXELS = 3.5433071

			return str(MM_TO_PIXELS * mmval)

	def MaximiseHeight(self):
		if self.Height < self.Width: # always choose the smallest to be the "width"
			temp = self.Width
			self.Width = self.Height
			self.Height = temp

class BoxBase():
	def __init__(self, dimensionProvider):
		#create a group
		self.DimProvider = dimensionProvider
		self.Group = etree.SubElement(dimensionProvider.Layer, inkex.addNS('g','svg'), {} )

		self.Width = dimensionProvider.Width + dimensionProvider.Allowance
		self.Height = dimensionProvider.Height + dimensionProvider.Allowance
		self.Depth = dimensionProvider.Depth + dimensionProvider.Allowance
		self.X = dimensionProvider.X
		self.Y = dimensionProvider.Y
		self.MinY = 0
		self.MinX = 0

		### init some common sizes ###
		self.ThumbSize = 20

		# tuck flap size
		self.FlapOffset = 1.5
		self.FlapHeight = self.Depth
		if self.Depth < 7 or self.Depth > 25:
			self.FlapHeight = 20

		# main flap size
		self.MainFlapHeight = (4 * self.Depth)/3
		if self.MainFlapHeight < self.ThumbSize:
			self.MainFlapHeight = 24

		### colour ###
		self.Fill = '#ffffff'
		self.StrokeWidth = self.DimProvider.MMtoUU(0.5)

	def _CreateRectangleInMillimetres(self, height, width, x, y):
		style = {'stroke': '#000000', 'stroke-width': self.StrokeWidth, 'fill' : self.Fill}
		attribs = {'style': str(inkex.Style(style)), 'height': self.DimProvider.MMtoUU(height), 'width': self.DimProvider.MMtoUU(width), 'x': self.DimProvider.MMtoUU(x), 'y': self.DimProvider.MMtoUU(y)}
		etree.SubElement(self.Group, inkex.addNS('rect','svg'), attribs )

	def _CreateRectangleInMillimetresWithCutouts(self, height, width, x, y, cutoutPositions):
		cmds = []

		t = self.ThumbSize
		cr = (3*t)/4 # curve ratio

		# start position
		cmds.append(["m", x, y])

		# Top side
		if cutoutPositions & CUTOUT_TOP == CUTOUT_TOP:
			cmds.append(["h", (self.Width - t)/2])
			cmds.append(["c", 0, cr,
						 t, cr,
						 t, 0])
			cmds.append(["h", (self.Width - t)/2])
		else:
			cmds.append(["h", width])

		# Right Side
		if cutoutPositions & CUTOUT_RIGHT == CUTOUT_RIGHT:
			cmds.append(["v", (self.Height - t)/2])
			cmds.append(["c", -cr, 0,
						 -cr, t,
						 0, t])
			cmds.append(["v", (self.Height - t)/2])
		else:
			cmds.append(["v", height])

		# Bottom Side
		if cutoutPositions & CUTOUT_BOTTOM == CUTOUT_BOTTOM:
			cmds.append(["h", -(self.Width - t)/2])
			cmds.append(["c", 0, -cr,
						 -t, -cr,
						 -t, 0])
			cmds.append(["h", -(self.Width - t)/2])
		else:
			cmds.append(["h", -width])

		# Left Side
		if cutoutPositions & CUTOUT_LEFT == CUTOUT_LEFT:
			cmds.append(["v", -(self.Height - t)/2])
			cmds.append(["c", cr, 0,
						 cr, -t,
						 0, -t])
			cmds.append(["v", -(self.Height - t)/2])
		else:
			cmds.append(["v", -height])

		self._CreatePathinMillimetres(cmds)

	def _CreatePathinMillimetres(self, cmds):
		pathStr = ""
		for cmd in cmds:
			pathStr += cmd[0] + " "
			for coord in cmd[1:]:
				pathStr += self.DimProvider.MMtoUU(coord) + " "

		pathStr += "z"
		#raise Exception(pathStr)

		style = {'stroke': '#000000', 'stroke-width': self.StrokeWidth, 'fill' : self.Fill}
		attribs = {'style': str(inkex.Style(style)), 'd': pathStr}
		etree.SubElement(self.Group, inkex.addNS('path','svg'), attribs )

class SingleFlappedTuckBox(BoxBase):
	def __init__(self, dimensionProvider):
		BoxBase.__init__(self, dimensionProvider)

	def Create(self):
		self.FlapOffset = 1.5
		self.FlapHeight = min(20, self.Depth)

		# Figure out some row and column values,
		# note rows and cols work left to right, top to bottom, but both calculated in reverse
		col5 = self.X - self.Depth
		col4 = col5 - self.Width
		col3 = col4 - self.Depth
		col2 = col3 - self.Width
		col1 = col2 - self.Depth
		self.MinX = col1

		row4 = self.Y - self.Depth
		row3 = row4 - self.Height
		row2 = row3 - self.Depth
		row1 = row2 - self.Depth
		self.MinY = row1

		### COLUMN 1 ###
		#create left glue panel
		self._CreateRectangleInMillimetres(self.Height, self.Depth, col1, row3)

		### COLUMN 2 ###
		#create box back print panel
		self._CreateRectangleInMillimetresWithCutouts(self.Height, self.Width, col2, row3, CUTOUT_TOP)

		#create box bottom glue panel
		self._CreateRectangleInMillimetres(self.Depth, self.Width, col2, row4)

		### COLUMN 3 ###
		#create left flap
		self._CreatePathinMillimetres(
			[
				["m", col3, row3],
				["h", self.Depth],
				["l", -self.FlapOffset, -self.FlapHeight],
				["h", -(self.Depth - (2*self.FlapOffset))],
			])

		#create left print panel
		self._CreateRectangleInMillimetres(self.Height, self.Depth, col3, row3)

		#create bottom left glue panel
		self._CreateRectangleInMillimetres(self.Depth, self.Depth, col3, row4)

		### COLUMN 4 ###
		#create main flap
		self._CreatePathinMillimetres(
			[
				["m", col4, row2],
				["c", 0, -self.MainFlapHeight, self.Width, -self.MainFlapHeight, self.Width, 0]
			])

		#create box top print panel
		self._CreateRectangleInMillimetres(self.Depth, self.Width, col4, row2)

		#create box front print panel
		self._CreateRectangleInMillimetres(self.Height, self.Width, col4, row3)

		#create box bottom print panel
		self._CreateRectangleInMillimetres(self.Depth, self.Width, col4, row4)

		### COLUMN 5 ###
		#create right flap
		self._CreatePathinMillimetres(
			[
				["m", col5, row3],
				["h", self.Depth],
				["l", -self.FlapOffset, -self.FlapHeight],
				["h", -(self.Depth - (2*self.FlapOffset))],
			])

		#create right print panel
		self._CreateRectangleInMillimetres(self.Height, self.Depth, col5, row3)

		#create bottom right glue panel
		self._CreateRectangleInMillimetres(self.Depth, self.Depth, col5, row4)

class DoubleFlappedTuckBox(BoxBase):
	def __init__(self, dimensionProvider):
		BoxBase.__init__(self, dimensionProvider)

	def Create(self):

		# Figure out some row and column values,
		# note rows and cols work left to right, top to bottom
		col5 = self.X - self.Depth
		col4 = col5 - self.Width
		col3 = col4 - self.Depth
		col2 = col3 - self.Width
		col1 = col2 - self.Depth
		self.MinX = col1

		row5 = self.Y - self.Depth
		row4 = row5 - self.Depth
		row3 = row4 - self.Height
		row2 = row3 - self.Depth
		row1 = row2 - self.Depth
		self.MinY = row1

		### COLUMN 1 ###
		#create left glue panel
		self._CreateRectangleInMillimetres(self.Height, self.Depth, col1, row3)

		### COLUMN 2 ###
		#create box back print panel
		self._CreateRectangleInMillimetresWithCutouts(self.Height, self.Width, col2, row3, CUTOUT_TOP | CUTOUT_BOTTOM)

		### COLUMN 3 ###
		#create top left flap
		self._CreatePathinMillimetres(
			[
				["m", col3, row3],
				["h", self.Depth],
				["l", -self.FlapOffset, -self.FlapHeight],
				["h", -(self.Depth - (2*self.FlapOffset))],
			])

		#create left print panel
		self._CreateRectangleInMillimetres(self.Height, self.Depth, col3, row3)

		#create bottom left flap
		self._CreatePathinMillimetres(
			[
				["m", col3, row4],
				["h", self.Depth],
				["l", -self.FlapOffset, self.FlapHeight],
				["h", -(self.Depth - (2*self.FlapOffset))],
			])

		### COLUMN 4 ###
		#create top main flap
		self._CreatePathinMillimetres(
			[
				["m", col4, row2],
				["c", 0, -self.MainFlapHeight, self.Width, -self.MainFlapHeight, self.Width, 0]
			])

		#create box top print panel
		self._CreateRectangleInMillimetres(self.Depth, self.Width, col4, row2)

		#create box front print panel
		self._CreateRectangleInMillimetres(self.Height, self.Width, col4, row3)

		#create box bottom print panel
		self._CreateRectangleInMillimetres(self.Depth, self.Width, col4, row4)

		#create bottom main flap
		self._CreatePathinMillimetres(
			[
				["m", col4, row5],
				["c", 0, self.MainFlapHeight, self.Width, self.MainFlapHeight, self.Width, 0]
			])

		### COLUMN 5 ###
		#create top right flap
		self._CreatePathinMillimetres(
			[
				["m", col5, row3],
				["h", self.Depth],
				["l", -self.FlapOffset, -self.FlapHeight],
				["h", -(self.Depth - (2*self.FlapOffset))],
			])

		#create right print panel
		self._CreateRectangleInMillimetres(self.Height, self.Depth, col5, row3)

		#create bottom right flap
		self._CreatePathinMillimetres(
			[
				["m", col5, row4],
				["h", self.Depth],
				["l", -self.FlapOffset, self.FlapHeight],
				["h", -(self.Depth - (2*self.FlapOffset))],
			])

class SlipcaseTuckBox(BoxBase):
	def __init__(self, dimensionProvider):
		BoxBase.__init__(self, dimensionProvider)

	def Create(self):
		self.FlapOffset = 1.5

		# Figure out some row and column values,
		# note rows and cols work left to right, top to bottom
		col5 = self.X - self.Depth
		col4 = col5 - self.Width
		col3 = col4 - self.Depth
		col2 = col3 - self.Width
		col1 = col2 - self.Depth

		row1 = self.Y - self.Height
		self.MinY = row1

		### COLUMN 1 ###
		#create left glue flap
		self._CreatePathinMillimetres(
			[
				["m", col2, row1],
				["v", self.Height],
				["l", -(self.Depth - self.FlapOffset), -self.FlapOffset],
				["v", -(self.Height - (2*self.FlapOffset))],
			])

		### COLUMN 2 ###
		#create box back print panel
		self._CreateRectangleInMillimetres(self.Height, self.Width, col2, row1)

		### COLUMN 3 ###
		#create left print panel
		self._CreateRectangleInMillimetres(self.Height, self.Depth, col3, row1)

		### COLUMN 4 ###
		#create box front print panel
		self._CreateRectangleInMillimetres(self.Height, self.Width, col4, row1)

		### COLUMN 5 ###
		#create right print panel
		self._CreateRectangleInMillimetres(self.Height, self.Depth, col5, row1)

class Matchbox(BoxBase):
	def __init__(self, dimensionProvider, numFlaps):
		BoxBase.__init__(self, dimensionProvider)

		self.DimProvider.MaximiseHeight()
		self.NumFlaps = numFlaps

	def Create(self):
		if self.NumFlaps == 2:
			tuckbox = DoubleFlappedTuckBox(self.DimProvider)
		else:
			tuckbox = SingleFlappedTuckBox(self.DimProvider)
		tuckbox.Create()

		#################################
		# Create Drawer for inside the box
		dimProvider = copy.copy(self.DimProvider)
		dimProvider.Width -= 2
		dimProvider.Height -= 2
		dimProvider.Depth -= 2
		dimProvider.Y = tuckbox.MinY - 20
		drawer = MatcboxDrawer(dimProvider)
		drawer.Create()

class TelescopingBox(BoxBase):
	def __init__(self, dimensionProvider):
		BoxBase.__init__(self, dimensionProvider)
		self.DimProvider.MaximiseHeight()

	def Create(self):
		#################################
		# Create box top
		top = MatcboxDrawer(self.DimProvider, includeFingerCutouts=True)
		top.Create()

		#################################
		# Create box bottom
		dimProvider = copy.copy(self.DimProvider)
		dimProvider.Width -= 1
		dimProvider.Height -= 1
		dimProvider.Depth -= 1
		dimProvider.Y = top.MinY - 20
		drawer = MatcboxDrawer(dimProvider)
		drawer.Create()

class MatcboxDrawer(BoxBase):
	def __init__(self, dimensionProvider, includeFingerCutouts=False):
		BoxBase.__init__(self, dimensionProvider)

		self.IncludeFingerCutouts = includeFingerCutouts

	def Create(self):

		fudgeDepth = self.Depth - 2 # overlap panels should be a little smaller to avoid touching box base
		# Figure out some row and column co-ord values,
		# note rows and cols work left to right, top to bottom, values start at 0 and go negative
		col5 = self.X - fudgeDepth
		col4 = col5 - self.Depth
		col3 = col4 - self.Width
		col2 = col3 - self.Depth
		col1 = col2 - fudgeDepth

		row5 = self.Y - fudgeDepth
		row4 = row5 - self.Depth
		row3 = row4 - self.Height
		row2 = row3 - self.Depth
		row1 = row2 - fudgeDepth
		self.MinY = row1

		### COLUMN 1 ###
		#create left overlap panel
		if self.IncludeFingerCutouts:
			self._CreateRectangleInMillimetresWithCutouts(self.Height, fudgeDepth, col1, row3, CUTOUT_RIGHT)
		else:
			self._CreateRectangleInMillimetres(self.Height, fudgeDepth, col1, row3)

		### COLUMN 2 ###
		#create top left flap
		self._CreatePathinMillimetres(
			[
				["m", col2, row3],
				["h", self.Depth],
				["l", -self.FlapOffset, -self.FlapHeight],
				["h", -(self.Depth - (2*self.FlapOffset))],
			])

		#create box left side print panel
		if self.IncludeFingerCutouts:
			self._CreateRectangleInMillimetresWithCutouts(self.Height, self.Depth, col2, row3, CUTOUT_LEFT)
		else:
			self._CreateRectangleInMillimetres(self.Height, self.Depth, col2, row3)

		#create bottom left flap
		self._CreatePathinMillimetres(
			[
				["m", col2, row4],
				["h", self.Depth],
				["l", -self.FlapOffset, self.FlapHeight],
				["h", -(self.Depth - (2*self.FlapOffset))],
			])

		### COLUMN 3 ###

		#create top side overlap panel
		self._CreateRectangleInMillimetres(fudgeDepth, self.Width, col3, row1)

		#create top box side panel
		self._CreateRectangleInMillimetres(self.Depth, self.Width, col3, row2)

		#create box bottom
		self._CreateRectangleInMillimetres(self.Height, self.Width, col3, row3)

		#create bottom box side panel
		self._CreateRectangleInMillimetres(self.Depth, self.Width, col3, row4)

		#create bottom side overlap panel
		self._CreateRectangleInMillimetres(fudgeDepth, self.Width, col3, row5)

		### COLUMN 4 ###
		#create top right flap
		self._CreatePathinMillimetres(
			[
				["m", col4, row3],
				["h", self.Depth],
				["l", -self.FlapOffset, -self.FlapHeight],
				["h", -(self.Depth - (2*self.FlapOffset))],
			])

		#create box right side print panel
		if self.IncludeFingerCutouts:
			self._CreateRectangleInMillimetresWithCutouts(self.Height, self.Depth, col4, row3, CUTOUT_RIGHT)
		else:
			self._CreateRectangleInMillimetres(self.Height, self.Depth, col4, row3)

		#create bottom right flap
		self._CreatePathinMillimetres(
			[
				["m", col4, row4],
				["h", self.Depth],
				["l", -self.FlapOffset, self.FlapHeight],
				["h", -(self.Depth - (2*self.FlapOffset))],
			])

		### COLUMN 5 ###
		#create right overlap panel
		if self.IncludeFingerCutouts:
			self._CreateRectangleInMillimetresWithCutouts(self.Height, fudgeDepth, col5, row3, CUTOUT_LEFT)
		else:
			self._CreateRectangleInMillimetres(self.Height, fudgeDepth, col5, row3)

class Tuckbox(inkex.EffectExtension):
	def __init__(self):
		inkex.Effect.__init__(self)
		self.arg_parser.add_argument('-t', '--type', type = str, dest = 'BoxType')
		self.arg_parser.add_argument('-n', '--num_flaps', type = int, dest = 'NumFlaps')
		self.arg_parser.add_argument('-w', '--deck_width', type = float, dest = 'DeckWidth')
		self.arg_parser.add_argument('-r', '--deck_height', type = float, dest = 'DeckHeight')
		self.arg_parser.add_argument('-d', '--deck_depth', type = float, dest = 'DeckDepth')
		self.arg_parser.add_argument('-a', '--box_allowance', type = float, dest = 'DeckAllowance')

	def GetPaths(self):
		paths = []

	def effect(self):
		dimProvider = EffectDimensionProvider(self)

		if self.options.BoxType == "TUCKBOX":
			if self.options.NumFlaps == 2:
				box = DoubleFlappedTuckBox(dimProvider)
			else:
				box = SingleFlappedTuckBox(dimProvider)
		elif self.options.BoxType == "SLIPCASE":
			box = SlipcaseTuckBox(dimProvider)
		elif self.options.BoxType == "MATCHBOX":
			box = Matchbox(dimProvider, self.options.NumFlaps)
		elif self.options.BoxType == "TELESCOPE":
			box = TelescopingBox(dimProvider)
		elif self.options.BoxType == "DISH":
			box = MatcboxDrawer(dimProvider)
		else:
			raise Exception("Box type '{0}' is undefined".format(self.options.BoxType))

		box.Create()

if __name__ == '__main__':
	Tuckbox().run()
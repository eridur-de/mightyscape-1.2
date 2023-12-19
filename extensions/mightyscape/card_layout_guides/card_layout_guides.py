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
import math

FOLD_GAP = 5
CROP_GAP = 2
CROP_LENGTH = 3

inkex.NSS[u'cs'] = u'http://www.razorfoss.org/cardlayoutguides/'

def PrintDebug(string):
	inkex.utils.debug( _(str(string)) )

def RoundAndDeduplicatePoints(points):
	return sorted(list(set(map(lambda x: round(x, 3), points))))

class Point():
	def __init__(self, x, y):
		self.x = x
		self.y = y

	def rotate(self, angle, origin):
		"""
		Rotate a point counterclockwise by a given angle around a given origin.

		The angle should be given in degrees.
		"""
		rads = math.radians(angle)
		newX = origin.x + math.cos(rads) * (self.x - origin.x) - math.sin(rads) * (self.y - origin.y)
		newY = origin.y + math.sin(rads) * (self.x - origin.x) + math.cos(rads) * (self.y - origin.y)

		return Point(newX, newY)

	def add(self, point):
		return Point(self.x + point.x, self.y + point.y)

	@staticmethod
	def parsePoint(pointString):
		x, y = map(lambda v: float(v), pointString.split(","))
		return Point(x, y)

	@staticmethod
	def parse(pointString, orientationString=None):
		p1 = Point.parsePoint(pointString)
		p = Point(p1.x, p1.y)

		if orientationString != None:
			po = Point.parsePoint(orientationString)
			p = p1.add(po.rotate(270, Point(0, 0)))

		return p

class LineGeneratorBase(object):
	def __init__(self, card_width, card_height, card_margin, bleed_margin, pageWidth, pageHeight, page_margin, unitConverterFunc):
		self.UnitConverterFunc = unitConverterFunc
		self.card_width = card_width
		self.card_height = card_height
		self.card_margin = card_margin
		self.bleed_margin = bleed_margin

		self.PageWidth = pageWidth
		self.PageHeight = pageHeight
		self.page_margin = page_margin

		self.ContainerWidth = -1
		self.ContainerHeight = -1

		self.GuideOffsetsWithFold = [
			0,
			self.bleed_margin, self.card_margin, self.card_height - 2*self.card_margin, self.card_margin, self.bleed_margin,
			2*FOLD_GAP,
			self.bleed_margin, self.card_margin, self.card_height - 2*self.card_margin, self.card_margin, self.bleed_margin
		]

		self.GuideOffsetsNoFold = [
			0,
			self.bleed_margin, self.card_margin,
			self.card_width - 2*self.card_margin,
			self.card_margin, self.bleed_margin
		]

	def CalcPageLeftMargin(self):
		return (self.PageWidth - self.ContentWidth) / 2.0

	def CalcPageBottomMargin(self):
		return (self.PageHeight - self.ContentHeight) / 2.0

	def DrawGuide(self, xmlParent, xpos, ypos):
		posString = "{},{}".format(xpos, ypos)
		attribs = {'position': posString, 'orientation': posString}

		etree.SubElement(xmlParent, inkex.addNS('guide',"sodipodi"), attribs)

	def ConvertPoint(self, p):
		# convert point into svg approriate values, including catering for inkscapes "alternative" axis sytem ie 0, 0 is bottom left not top left
		newX = self.UnitConverterFunc("{}mm".format(p.x))
		newY = self.PageHeight - self.UnitConverterFunc("{}mm".format(p.y))

		return Point(newX, newY)

	def DrawLine(self, xmlParent, p1, p2):
		cp1 = self.ConvertPoint(p1)
		cp2 = self.ConvertPoint(p2)

		pathStr = "M {},{} {}, {}".format(cp1.x, cp1.y, cp2.x, cp2.y)
		style = {'stroke': '#000000', 'stroke-width': self.UnitConverterFunc('0.25mm'), 'fill': 'none'}
		attribs = {'style': str(inkex.Style(style)), 'd': pathStr}

		etree.SubElement(xmlParent, inkex.addNS('path','svg'), attribs )

	def DrawVerticleGuides(self, xmlParent, positions, gap):
		curPos = self.CalcPageLeftMargin()
		lastPos = -1
		while curPos + self.ContainerWidth <= self.PageWidth - self.page_margin:
			for offset in positions:
				curPos += offset
				if curPos != lastPos: # don't double draw
					self.DrawGuide(xmlParent, curPos, 0)

				lastPos = curPos

			curPos += gap

	def DrawHorizontalGuides(self, xmlParent, positions, gap):
		curPos = self.CalcPageBottomMargin()
		lastPos = -1
		while curPos + self.ContainerHeight <= self.PageHeight - self.page_margin:
			for offset in positions:
				curPos += offset
				if curPos != lastPos: # don't double draw
					self.DrawGuide(xmlParent, 0, curPos)

				lastPos = curPos

			curPos += gap

	def GenerateFoldLines(self, xmlParent):
		lines = self.GetFoldLinePositions()

		for line in lines:
			self.DrawLine(xmlParent, line[0], line[1])

	def GenerateCropMarks(self, xmlParent):
		lines = self.GetCropMarkLines()

		for line in lines:
			self.DrawLine(xmlParent, line[0], line[1])

	@staticmethod
	def CreateLineGenerator(layout, orientation, card_width, card_height, card_margin, bleed_margin, pageWidth, pageHeight, page_margin, unitConverterFunc):
		if layout == "SIMPLE":
			return SimpleGridLineGenerator(orientation, card_width, card_height, card_margin, bleed_margin, pageWidth, pageHeight, page_margin, unitConverterFunc)

		if orientation == "HORIZONTAL":
			return LineGeneratorForHorizontalCards(card_width, card_height, card_margin, bleed_margin, pageWidth, pageHeight, page_margin, unitConverterFunc)

		return LineGeneratorForVerticalCards(card_width, card_height, card_margin, bleed_margin, pageWidth, pageHeight, page_margin, unitConverterFunc)

class SimpleGridLineGenerator(LineGeneratorBase):
	def __init__(self, orientation, card_width, card_height, card_margin, bleed_margin, pageWidth, pageHeight, page_margin, unitConverterFunc):
		if orientation == "HORIZONTAL":
			super(SimpleGridLineGenerator, self).__init__(card_height, card_width, card_margin, bleed_margin, pageWidth, pageHeight, page_margin, unitConverterFunc)
		else:
			super(SimpleGridLineGenerator, self).__init__(card_width, card_height, card_margin, bleed_margin, pageWidth, pageHeight, page_margin, unitConverterFunc)

		self.ContainerWidth = self.card_width + 2 * bleed_margin
		self.ContainerHeight = self.card_height + 2 * bleed_margin

		# num across
		# num down
		self.NumContainersAcross = int((self.PageWidth - 2*self.page_margin) // self.ContainerWidth)	# round down division
		self.NumContainersDown = int((self.PageHeight - 2*self.page_margin) // self.ContainerHeight)	# round down division

		# content sizes
		self.ContentWidth = self.NumContainersAcross * self.ContainerWidth
		self.ContentHeight = self.NumContainersDown * self.ContainerHeight

	def GenerateGuides(self, xmlParent):
		horizontalOffsets = self.GuideOffsetsNoFold = [
			0,
			self.bleed_margin, self.card_margin,
			self.card_width - 2*self.card_margin,
			self.card_margin, self.bleed_margin
		]

		verticalOffsets = self.GuideOffsetsNoFold = [
			0,
			self.bleed_margin, self.card_margin,
			self.card_height - 2*self.card_margin,
			self.card_margin, self.bleed_margin
		]

		self.DrawVerticleGuides(xmlParent, horizontalOffsets, 0)
		self.DrawHorizontalGuides(xmlParent, verticalOffsets, 0)

	def GetFoldLinePositions(self):
		return [] # no fold lines in simple grid

	def GetCropMarkLines(self):
		lines = []

		leftMargin = self.CalcPageLeftMargin()
		bottomMargin = self.CalcPageBottomMargin()

		#determine all horizontal crop marks, duplicates possible
		# figure out the ypos
		horizontal_ypos = []
		for idx in range(self.NumContainersDown):
			bottomY = self.bleed_margin
			topY = bottomY + self.card_height
			containerOffset = bottomMargin + idx*self.ContainerHeight

			horizontal_ypos.append(containerOffset + bottomY)
			horizontal_ypos.append(containerOffset + topY)

		horizontal_ypos = RoundAndDeduplicatePoints(horizontal_ypos) # remove duplicate positions

		horizontal_xpos = [leftMargin - CROP_GAP, self.PageWidth - leftMargin + CROP_GAP + CROP_LENGTH]
		for xpos in horizontal_xpos:
			for ypos in horizontal_ypos:
				lines.append([
					Point(xpos - CROP_LENGTH, ypos),
					Point(xpos, ypos)
				])

		#determine all vertical crop marks, duplicates possible
		# figure out the xpos
		vertical_xpos = []
		for idx in range(self.NumContainersAcross):
			leftX = self.bleed_margin
			rightX = leftX + self.card_width
			containerOffset = leftMargin + idx*self.ContainerWidth

			vertical_xpos.append(containerOffset + leftX)
			vertical_xpos.append(containerOffset + rightX)

		vertical_xpos = RoundAndDeduplicatePoints(vertical_xpos) # remove duplicate positions

		vertical_ypos = [bottomMargin - CROP_GAP, self.PageHeight - bottomMargin + CROP_GAP + CROP_LENGTH]
		for xpos in vertical_xpos:
			for ypos in vertical_ypos:
				lines.append([
					Point(xpos, ypos),
					Point(xpos, ypos - CROP_LENGTH)
				])

		return lines

class LineGeneratorForVerticalCards(LineGeneratorBase):
	def __init__(self, card_width, card_height, card_margin, bleed_margin, pageWidth, pageHeight, page_margin, unitConverterFunc):
		super(LineGeneratorForVerticalCards, self).__init__(card_width, card_height, card_margin, bleed_margin, pageWidth, pageHeight, page_margin, unitConverterFunc)

		self.ContainerWidth = card_width + 2*bleed_margin
		self.ContainerHeight = 2*(card_height + 2*bleed_margin + FOLD_GAP)

		# num across
		self.NumContainersAcross = int((self.PageWidth - 2*self.page_margin) // self.ContainerWidth)	# round down division

		# num down
		contentHeight = lambda n: n * self.ContainerHeight + (n - 1)*(2*FOLD_GAP)
		workingHeight = self.PageHeight - 2*self.page_margin

		self.NumContainersDown = int(workingHeight // self.ContainerHeight) # round down division for nominal value
		if contentHeight(self.NumContainersDown) > workingHeight:
			self.NumContainersDown -= 1

		# content sizes
		self.ContentWidth = self.NumContainersAcross * self.ContainerWidth
		self.ContentHeight = contentHeight(self.NumContainersDown)

	def GenerateGuides(self, xmlParent):
		self.DrawVerticleGuides(xmlParent, self.GuideOffsetsNoFold, 0)
		self.DrawHorizontalGuides(xmlParent, self.GuideOffsetsWithFold, 2*FOLD_GAP)

	def GetFoldLinePositions(self):
		lines = []
		leftMargin = self.CalcPageLeftMargin()

		for idx in range(self.NumContainersDown):
			foldY = self.CalcPageBottomMargin() + idx*(self.ContainerHeight + 2*FOLD_GAP) + self.ContainerHeight/2
			lines.append([Point(leftMargin, foldY), Point(self.PageWidth - leftMargin, foldY)])

		return lines

	def GetCropMarkLines(self):
		lines = []

		leftMargin = self.CalcPageLeftMargin()
		bottomMargin = self.CalcPageBottomMargin()
		vertical_ypos = []
		# determine all of the hornzontal facing crop marks, no duplicates possible
		for idx in range(self.NumContainersDown):
			bottomY = self.bleed_margin
			topY = bottomY + self.card_height
			containerOffset = bottomMargin + idx*(self.ContainerHeight + 2*FOLD_GAP)
			vertical_ypos += [
				containerOffset - CROP_GAP,
				containerOffset + 2*self.bleed_margin + 2*self.card_margin + self.card_height + CROP_GAP + CROP_LENGTH
			] # stash for later

			for ypos in [containerOffset + bottomY, containerOffset + topY]:
				for xpos in [leftMargin - CROP_GAP, self.PageWidth - leftMargin + CROP_GAP + CROP_LENGTH]:
					lines.append([
						Point(xpos, ypos),
						Point(xpos - CROP_LENGTH, ypos)
					])

		#determine all vertical crop marks, duplicates possible
		# figure out the xpos
		vertical_xpos = []
		for idx in range(self.NumContainersAcross):
			leftX = self.bleed_margin
			rightX = leftX + self.card_width
			containerOffset = leftMargin + idx*self.ContainerWidth

			vertical_xpos.append(containerOffset + leftX)
			vertical_xpos.append(containerOffset + rightX)

		vertical_xpos = list(set(vertical_xpos)) # remove duplicate positions

		for xpos in vertical_xpos:
			for ypos in vertical_ypos:
				lines.append([
					Point(xpos, ypos),
					Point(xpos, ypos - CROP_LENGTH)
				])

		return lines

class LineGeneratorForHorizontalCards(LineGeneratorBase):
	def __init__(self, card_width, card_height, card_margin, bleed_margin, pageWidth, pageHeight, page_margin, unitConverterFunc):
		super(LineGeneratorForHorizontalCards, self).__init__(card_width, card_height, card_margin, bleed_margin, pageWidth, pageHeight, page_margin, unitConverterFunc)

		self.ContainerWidth = 2*(card_height + 2 * bleed_margin + FOLD_GAP)
		self.ContainerHeight = card_width + 2 * bleed_margin

		# num across
		contentWidth = lambda n: n * self.ContainerWidth + (n - 1)*(2*FOLD_GAP)
		workingWidth = self.PageWidth - 2*self.page_margin

		self.NumContainersAcross = int(workingWidth // self.ContainerWidth) # round down division for nominal value
		if contentWidth(self.NumContainersAcross) > workingWidth:
			self.NumContainersAcross -= 1

		# num down
		self.NumContainersDown = int((self.PageHeight - 2*self.page_margin) // self.ContainerHeight)	# round down division

		# content sizes
		self.ContentWidth = contentWidth(self.NumContainersAcross)
		self.ContentHeight = self.NumContainersDown * self.ContainerHeight

	def GenerateGuides(self, xmlParent):
		self.DrawVerticleGuides(xmlParent, self.GuideOffsetsWithFold, 2*FOLD_GAP)
		self.DrawHorizontalGuides(xmlParent, self.GuideOffsetsNoFold, 0)

	def GetFoldLinePositions(self):
		lines = []
		bottomMargin = self.CalcPageBottomMargin()

		for idx in range(self.NumContainersAcross):
			foldX = self.CalcPageLeftMargin() + idx*(self.ContainerWidth + 2*FOLD_GAP) + self.ContainerWidth/2
			lines.append([Point(foldX, bottomMargin), Point(foldX, self.PageHeight - bottomMargin)])

		return lines

	def GetCropMarkLines(self):
		lines = []

		leftMargin = self.CalcPageLeftMargin()
		bottomMargin = self.CalcPageBottomMargin()
		horizontal_xpos = []

		# determine all of the vertical facing crop marks, no duplicates possible
		for idx in range(self.NumContainersAcross):
			leftX = self.bleed_margin
			rightX = leftX + self.card_height
			containerOffset = leftMargin + idx*(self.ContainerWidth + 2*FOLD_GAP)
			horizontal_xpos += [
				containerOffset - CROP_GAP,
				containerOffset + 2*self.bleed_margin + 2*self.card_margin + self.card_height + CROP_GAP + CROP_LENGTH
			] # stash for later

			for xpos in [containerOffset + leftX, containerOffset + rightX]:
				for ypos in [bottomMargin - CROP_GAP, self.PageHeight - bottomMargin + CROP_GAP + CROP_LENGTH]:
					lines.append([
						Point(xpos, ypos),
						Point(xpos, ypos - CROP_LENGTH)
					])

		#determine all horizontal crop marks, duplicates possible
		# figure out the xpos
		horizontal_ypos = []
		for idx in range(self.NumContainersDown):
			bottomY = self.bleed_margin
			topY = bottomY + self.card_width
			containerOffset = bottomMargin + idx*self.ContainerHeight

			horizontal_ypos.append(containerOffset + bottomY)
			horizontal_ypos.append(containerOffset + topY)

		horizontal_ypos = RoundAndDeduplicatePoints(horizontal_ypos) # remove duplicate positions

		for ypos in horizontal_ypos:
			for xpos in horizontal_xpos:
				lines.append([
					Point(xpos, ypos),
					Point(xpos - CROP_LENGTH, ypos)
				])

		return lines

class CardLayoutGuides(inkex.EffectExtension):
	
	def add_arguments(self, pars):
		pars.add_argument('-l', '--layout')
		pars.add_argument('-w', '--card_width', type = float)
		pars.add_argument('-d', '--card_height', type = float)
		pars.add_argument('-o', '--orientation')
		pars.add_argument('-c', '--card_margin', type = float)
		pars.add_argument('-b', '--bleed_margin', type = float)
		pars.add_argument('-p', '--page_margin', type = float)

	def effect(self):
		# find dimensions of page		
		pageWidth = inkex.units.convert_unit(self.svg.viewport_width, "mm", "px")
		pageHeight = inkex.units.convert_unit(self.svg.viewport_height, "mm", "px")

		opt = self.options

		guideParent = self.document.xpath('//sodipodi:namedview',namespaces=inkex.NSS)[0]

		### GUIDES
		# remove all the existing guides
		[node.delete() for node in self.document.xpath('//sodipodi:guide',namespaces=inkex.NSS)]

		# create the generator object
		gen = LineGeneratorBase.CreateLineGenerator(opt.layout, opt.orientation, opt.card_width, opt.card_height, opt.card_margin, opt.bleed_margin, pageWidth, pageHeight, opt.page_margin, self.svg.unittouu)

		gen.GenerateGuides(guideParent)

		### FOLD LINES
		# remove any existing 'Crop marks' layer
		[node.delete() for node in self.document.xpath("//svg:g[@inkscape:label='Crop Marks']",namespaces=inkex.NSS)]

		svg = self.document.xpath('//svg:svg', namespaces=inkex.NSS)[0]
		layer = etree.SubElement(svg, inkex.addNS('g',"svg"), {})
		layer.set(inkex.addNS('label', 'inkscape'), "Crop Marks")
		layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
		#layer.set(inkex.addNS('insensitive', 'sodipodi'), 'true')

		gen.GenerateFoldLines(layer)

		### CROP MARKS
		gen.GenerateCropMarks(layer)

if __name__ == '__main__':
	CardLayoutGuides().run()
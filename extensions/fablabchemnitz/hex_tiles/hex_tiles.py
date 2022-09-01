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

from lxml import etree
import inkex
import copy
import math

FOLD_GAP = 5
CROP_GAP = 2
CROP_LENGTH = 3

inkex.NSS[u'cs'] = u'http://www.razorfoss.org/tuckboxextension/'

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

class HexGeneratorBase(object):
	def __init__(self, hexDiameter, hexMargin, bleedMargin, pageWidth, pageHeight, pageMargin, unitConverterFunc):
		self.UnitConverterFunc = unitConverterFunc
		self.HexDiameter = hexDiameter
		self.HexMargin = hexMargin
		self.BleedMargin = bleedMargin

		self.PageWidth = pageWidth
		self.PageHeight = pageHeight
		self.PageMargin = pageMargin

		self.ContainerWidth = -1
		self.ContainerHeight = -1

	def CalcPageLeftMargin(self):
		return (self.PageWidth - self.ContentWidth) / 2.0

	def CalcPageBottomMargin(self):
		return (self.PageHeight - self.ContentHeight) / 2.0

	def DrawGuide(self, xmlParent, xpos, ypos):
		posString = "{},{}".format(xpos, ypos)
		attribs = {'position': posString, 'orientation': posString}

		etree.SubElement(xmlParent, inkex.addNS('guide',"sodipodi"), attribs)

	def DrawAngledGuide(self, xmlParent, xpos, ypos, angle):
		# Angles are taken from the horizontal axis, positive angles move clockwise
		posString = "{},{}".format(xpos, ypos)
		orientationString = "{}, {}".format(math.sin(math.radians(angle)), math.cos(math.radians(angle)))
		attribs = {'position': posString, 'orientation': orientationString}

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
		while curPos + self.ContainerWidth <= self.PageWidth - self.PageMargin:
			for offset in positions:
				curPos += offset
				if curPos != lastPos: # don't double draw
					self.DrawGuide(xmlParent, curPos, 0)

				lastPos = curPos

			curPos += gap

	def DrawHorizontalGuides(self, xmlParent, positions, gap):
		curPos = self.CalcPageBottomMargin()
		lastPos = -1
		while curPos + self.ContainerHeight <= self.PageHeight - self.PageMargin:
			for offset in positions:
				curPos += offset
				if curPos != lastPos: # don't double draw
					self.DrawGuide(xmlParent, 0, curPos)

				lastPos = curPos

			curPos += gap

	def DrawAngledGuides(self, xmlParent, offsetPositions, angle, gap):

		numExtraTopContainers = 0
		numExtraBottomContainers = 0
		if angle > 0:
			numExtraTopContainers = math.ceil(self.NumContainersAcross / 2.0) - 1
		if angle < 0:
			numExtraBottomContainers = math.ceil(self.NumContainersAcross / 2.0) - 1

		# draw sets of guides per point avoiding duplicate lines
		# NOTE: Effectivly we draw the bottom guides first and then move up (ie y is increasing)
		curPos = self.CalcPageBottomMargin() - numExtraBottomContainers * self.ContainerHeight
		lastPos = -1

		while curPos + self.ContainerHeight <= self.PageHeight - self.PageMargin + numExtraTopContainers*self.ContainerHeight:
			for offset in offsetPositions:
				curPos += offset
				if curPos != lastPos: # don't double draw
					self.DrawAngledGuide(xmlParent, self.CalcPageLeftMargin() + self.ContainerWidth/2, curPos, angle)

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
	def CalculateBorderVerticalOffset(borderWidth):
		if borderWidth == 0:
			return 0

		return borderWidth / math.sin(math.radians(60))

	@staticmethod
	def CreateHexGenerator(hexDiameter, hexMargin, bleedMargin, pageWidth, pageHeight, pageMargin, unitConverterFunc):
		return SimpleHexGridLineGenerator(hexDiameter, hexMargin, bleedMargin, pageWidth, pageHeight, pageMargin, unitConverterFunc)

class SimpleHexGridLineGenerator(HexGeneratorBase):
	def __init__(self, hexDiameter, hexMargin, bleedMargin, pageWidth, pageHeight, pageMargin, unitConverterFunc):
		super(SimpleHexGridLineGenerator, self).__init__(hexDiameter, hexMargin, bleedMargin, pageWidth, pageHeight, pageMargin, unitConverterFunc)

		self.HexWidth = math.sqrt(3) * (hexDiameter/2)
		self.ContainerWidth = self.HexWidth + 2*bleedMargin
		self.ContainerHeight = hexDiameter + 2*HexGeneratorBase.CalculateBorderVerticalOffset(bleedMargin)

		# num across
		# num down
		self.NumContainersAcross = int((self.PageWidth - 2*self.PageMargin) // self.ContainerWidth)	# round down division
		self.NumContainersDown = int((self.PageHeight - 2*self.PageMargin) // self.ContainerHeight)	# round down division

		# content sizes
		self.ContentWidth = self.NumContainersAcross * self.ContainerWidth
		self.ContentHeight = self.NumContainersDown * self.ContainerHeight

	def GenerateGuides(self, xmlParent):
		verticalGuideOffsets = [
			0,
			self.BleedMargin,
			self.HexMargin,
			self.HexWidth - 2*self.HexMargin,
			self.HexMargin,
			self.BleedMargin
		]

		bleedVerticalOffset = HexGeneratorBase.CalculateBorderVerticalOffset(self.BleedMargin)
		hexMarginVerticalOffset = HexGeneratorBase.CalculateBorderVerticalOffset(self.HexMargin)
		horizontalGuideOffsets = [
			0,
			bleedVerticalOffset,
			hexMarginVerticalOffset,
			self.HexDiameter - 2*hexMarginVerticalOffset,
			hexMarginVerticalOffset,
			bleedVerticalOffset
		]

		self.DrawVerticleGuides(xmlParent, verticalGuideOffsets, 0)
		self.DrawAngledGuides(xmlParent, horizontalGuideOffsets, -30, 0)
		self.DrawAngledGuides(xmlParent, horizontalGuideOffsets, 30, 0)

	def GetFoldLinePositions(self):
		return [] # no fold lines in simple grid

	def GetCropMarkLines(self):
		lines = []

		leftMargin = self.CalcPageLeftMargin()
		bottomMargin = self.CalcPageBottomMargin()
		bleedVerticalOffset = HexGeneratorBase.CalculateBorderVerticalOffset(self.BleedMargin)

		def CalcOppositeDeltaGivenAdjacentDelta(xdelta, angle):
			return math.tan(math.radians(angle)) * xdelta

		#---------------------------------------------------------------------------------
		#determine all vertical crop marks, duplicates possible
		# figure out the xpos'
		vertical_xpos = []
		for idx in range(self.NumContainersAcross):
			leftX = self.BleedMargin
			rightX = leftX + self.HexWidth
			containerOffset = leftMargin + idx * self.ContainerWidth

			vertical_xpos.append(containerOffset + leftX)
			vertical_xpos.append(containerOffset + rightX)

		vertical_xpos = RoundAndDeduplicatePoints(vertical_xpos)

		# add to list of lines
		vertical_ypos = [bottomMargin - CROP_GAP, self.PageHeight - bottomMargin + CROP_GAP + CROP_LENGTH]
		for xpos in vertical_xpos:
			for ypos in vertical_ypos:
				lines.append([
					Point(xpos, ypos),
					Point(xpos, ypos - CROP_LENGTH)
				])

		#---------------------------------------------------------------------------------
		# figure out NW, SW, NE and SE crop marks for both sides of the page
		vertical_ypos_nw = []
		vertical_ypos_sw = []
		vertical_ypos_ne = []
		vertical_ypos_se = []

		yoffset = CalcOppositeDeltaGivenAdjacentDelta(self.ContainerWidth/2 + CROP_GAP, 30)

		lastColumnHasHalfStep = (self.NumContainersAcross % 2) == 0 # an even numbered containers across means that the last column is 1/2 a continer up and has 1 less container
		staggeredContainerOffset = 0
		if lastColumnHasHalfStep:
			staggeredContainerOffset = self.ContainerHeight/2

		for idx in range(self.NumContainersDown):
			leftContainerOffset = idx * self.ContainerHeight + bottomMargin
			rightContainerOffset = leftContainerOffset + staggeredContainerOffset

			bottomY = bleedVerticalOffset
			topY = self.ContainerHeight - bleedVerticalOffset

			vertical_ypos_nw.append(leftContainerOffset + topY + yoffset)
			vertical_ypos_nw.append(leftContainerOffset + bottomY + yoffset)

			vertical_ypos_sw.append(leftContainerOffset + topY - yoffset)
			vertical_ypos_sw.append(leftContainerOffset + bottomY - yoffset)

			vertical_ypos_ne.append(rightContainerOffset + topY + yoffset)
			vertical_ypos_ne.append(rightContainerOffset + bottomY + yoffset)

			vertical_ypos_se.append(rightContainerOffset + topY - yoffset)
			vertical_ypos_se.append(rightContainerOffset + bottomY - yoffset)

		# sort out a staggered last col
		if lastColumnHasHalfStep: # if it's a half step column we need to remove the last container and add acouple of extra lines
			vertical_ypos_ne = vertical_ypos_ne[:-2]
			vertical_ypos_se = vertical_ypos_se[:-2]
			vertical_ypos_ne.append(max(vertical_ypos_ne) + 2*bleedVerticalOffset)
			vertical_ypos_se.append(min(vertical_ypos_se) - 2*bleedVerticalOffset)

		# remove duplicate positions
		vertical_ypos_nw = RoundAndDeduplicatePoints(vertical_ypos_nw)
		vertical_ypos_sw = RoundAndDeduplicatePoints(vertical_ypos_sw)
		vertical_ypos_ne = RoundAndDeduplicatePoints(vertical_ypos_ne)
		vertical_ypos_se = RoundAndDeduplicatePoints(vertical_ypos_se)

		# add to list of lines
		xpos_left = leftMargin - CROP_GAP
		xpos_right = self.PageWidth - leftMargin + CROP_GAP
		yoffset = CalcOppositeDeltaGivenAdjacentDelta(CROP_LENGTH, 30)

		for ypos in vertical_ypos_nw:
			lines.append([
					Point(xpos_left, ypos),
					Point(xpos_left - CROP_LENGTH, ypos + yoffset)
				])

		for ypos in vertical_ypos_sw:
			lines.append([
					Point(xpos_left, ypos),
					Point(xpos_left - CROP_LENGTH, ypos - yoffset)
				])

		for ypos in vertical_ypos_ne:
			lines.append([
					Point(xpos_right, ypos),
					Point(xpos_right + CROP_LENGTH, ypos + yoffset)
				])

		for ypos in vertical_ypos_se:
			lines.append([
					Point(xpos_right, ypos),
					Point(xpos_right + CROP_LENGTH, ypos - yoffset)
				])

		#---------------------------------------------------------------------------------
		# figure out NW, SW, NE and SE crop marks for top and bottom of the page
		xpos_nw = []
		xpos_sw = []
		xpos_ne = []
		xpos_se = []

		xoffset_near = CalcOppositeDeltaGivenAdjacentDelta(bleedVerticalOffset + CROP_GAP, 60)
		xoffset_far = CalcOppositeDeltaGivenAdjacentDelta(self.ContainerHeight - bleedVerticalOffset + CROP_GAP, 60)

		for idx in range(0, self.NumContainersAcross, 2): #we only need to do every other container because of the stepping
			containerOffset = idx * self.ContainerWidth + leftMargin
			topY = self.ContainerHeight - bleedVerticalOffset
			bottomY = bleedVerticalOffset
			xpos = self.ContainerWidth/2

			xpos_nw.append(containerOffset + xpos - xoffset_near)
			xpos_nw.append(containerOffset + xpos - xoffset_far)

			xpos_sw.append(containerOffset + xpos - xoffset_near)
			xpos_sw.append(containerOffset + xpos - xoffset_far)

			xpos_ne.append(containerOffset + xpos + xoffset_near)
			xpos_ne.append(containerOffset + xpos + xoffset_far)

			xpos_se.append(containerOffset + xpos + xoffset_near)
			xpos_se.append(containerOffset + xpos + xoffset_far)


		# remove duplicate positions
		xpos_nw = RoundAndDeduplicatePoints(xpos_nw)
		xpos_sw = RoundAndDeduplicatePoints(xpos_sw)
		xpos_ne = RoundAndDeduplicatePoints(xpos_ne)
		xpos_se = RoundAndDeduplicatePoints(xpos_se)

		# add to list of lines
		ypos_bottom = bottomMargin - CROP_GAP
		ypos_top = self.PageHeight - bottomMargin + CROP_GAP
		yoffset = CalcOppositeDeltaGivenAdjacentDelta(CROP_LENGTH, 30)

		for xpos in xpos_nw:
			if xpos > 0 and xpos < self.PageWidth:
				lines.append([
					Point(xpos, ypos_top),
					Point(xpos - CROP_LENGTH, ypos_top + yoffset)
				])

		for xpos in xpos_sw:
			if xpos > 0 and xpos < self.PageWidth:
				lines.append([
					Point(xpos, ypos_bottom),
					Point(xpos - CROP_LENGTH, ypos_bottom - yoffset)
				])

		for xpos in xpos_ne:
			if xpos > 0 and xpos < self.PageWidth:
				lines.append([
					Point(xpos, ypos_top),
					Point(xpos + CROP_LENGTH, ypos_top + yoffset)
				])

		for xpos in xpos_se:
			if xpos > 0 and xpos < self.PageWidth:
				lines.append([
					Point(xpos, ypos_bottom),
					Point(xpos + CROP_LENGTH, ypos_bottom - yoffset)
				])

		#---------------------------------------------------------------------------------
		return lines

class HexTiles(inkex.EffectExtension):
	
	def add_arguments(self, pars):
		pars.add_argument('-d', '--hex_diameter', type = float, dest = 'HexDiameter')
		pars.add_argument('-c', '--hex_margin', type = float, dest = 'HexMargin')
		pars.add_argument('-b', '--bleed_margin', type = float, dest = 'BleedMargin')
		pars.add_argument('-p', '--page_margin', type = float, dest = 'PageMargin')

	def effect(self):
		# find dimensions of page
		pageWidth = inkex.units.convert_unit(self.svg.viewport_width, "mm", "px")
		pageHeight = inkex.units.convert_unit(self.svg.viewport_height, "mm", "px")

		opt = self.options

		guideParent = self.document.xpath('//sodipodi:namedview',namespaces=inkex.NSS)[0]

		### GUIDES
		# remove all the existing guides
		[node.delete() for node in self.document.xpath('//sodipodi:guide',namespaces=inkex.NSS)]

		# create the object generator
		gen = HexGeneratorBase.CreateHexGenerator(opt.HexDiameter, opt.HexMargin, opt.BleedMargin, pageWidth, pageHeight, opt.PageMargin, self.svg.unittouu)

		gen.GenerateGuides(guideParent)

		### CROP MARKS
		# remove any existing 'Crop marks' layer
		[node.delete() for node in self.document.xpath("//svg:g[@inkscape:label='Crop Marks']",namespaces=inkex.NSS)]

		svg = self.document.xpath('//svg:svg', namespaces=inkex.NSS)[0]
		layer = etree.SubElement(svg, inkex.addNS('g',"svg"), {})
		layer.set(inkex.addNS('label', 'inkscape'), "Crop Marks")
		layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
		#layer.set(inkex.addNS('insensitive', 'sodipodi'), 'true')

		gen.GenerateCropMarks(layer)

if __name__ == '__main__':
	HexTiles().run()
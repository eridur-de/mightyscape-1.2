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

import inkex
import math
inkex.NSS[u'cs'] = u'http://www.razorfoss.org/tuckboxextension/'

def printDebug(string):
	inkex.utils.debug( _(str(string)) )

def isAlmost0(num):
	return (abs(num) < 0.000001)

def formatFloat(f):
	if f == None:
		return "None"

	return "{:.3f}".format(f)

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

class GuideDefiniton():
	def __init__(self, xmlNode):
		self.node = xmlNode
		self.id = self.node.attrib["id"]

		self.p1 = Point.parse(self.node.attrib["position"])
		self.p2 = Point.parse(self.node.attrib["position"], self.node.attrib["orientation"])

		# calculate the slope and y intercept
		self.slope = None # default to vertical line
		self.yIntercept = None
		self.xIntercept = self.p1.x

		if not isAlmost0(self.p1.x - self.p2.x): # not vertical
			self.slope = (self.p2.y - self.p1.y)/(self.p2.x - self.p1.x)

			self.yIntercept = self.p1.y - (self.slope*self.p1.x)
			if not isAlmost0(self.slope): # horizontal
				self.xIntercept = -(self.yIntercept)/self.slope
			else:
				self.slope=0
				self.xIntercept = None

		#printDebug(self.toString())

	def interceptSerial(self):
		s = "{},{}".format(formatFloat(self.xIntercept), formatFloat(self.yIntercept))
		return s

	def toString(self):
		#return "{} - p1:({}, {}) p2:({}, {}) - {}, {}, {}".format(self.id, self.p1.x, self.p1.y, self.p2.x, self.p2.y, self.slope, self.xIntercept, self.yIntercept)
		return "{} - {}".format(self.id, self.interceptSerial())

class RemoveDuplicateGuides(inkex.EffectExtension):

	def effect(self):
		# enumerate all guides
		guideNodes = list(map(lambda n: GuideDefiniton(n), self.document.xpath('//sodipodi:guide',namespaces=inkex.NSS)))

		# sort guides into match xy intercept groups
		groups = {}
		for guide in guideNodes:
			serial = guide.interceptSerial()
			if serial not in groups:
				groups[serial] = []

			groups[serial].append(guide)


		# now remove all the excess guides
		for serial in groups:
			for guide in groups[serial][1:]: # keep the first member of group
				guide.node.delete()

if __name__ == '__main__':
	effect = RemoveDuplicateGuides().run()
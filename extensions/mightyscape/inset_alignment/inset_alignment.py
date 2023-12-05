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

import inkex

def BoundingBoxArea(node):
	bb = node.bounding_box()
	return bb.width * bb.height

class InsetAlignment(inkex.EffectExtension):
	
	def add_arguments(self, pars):
		pars.add_argument('-a', '--anchor_node')
		pars.add_argument('-v', '--relative_to_v')
		pars.add_argument('-t', '--relative_to_h')
		pars.add_argument('-x', '--inset_x', type = float)
		pars.add_argument('-y', '--inset_y', type = float)

	def GetPaths(self):
		paths = []

	def effect(self):
		# make sure we have at least 2 nodes selected
		if len(self.options.ids) < 2:
			inkex.utils.debug("You must select at least 2 nodes")
			return

		# pick the achor node
		anchor_nodeId = self.options.ids[0] # first selected
		if self.options.anchor_node ==  "LAST_SEL": # last selected
			#inkex.utils.debug("last sel")
			#inkex.utils.debug(self.options.ids)
			anchor_nodeId = self.options.ids[-1]
		elif self.options.anchor_node == "LARGEST": # largest
			anchor_nodeId = None
			largestArea = 0
			for nodeId, node in self.svg.selected.items():
				nodeArea = BoundingBoxArea(node)
				if nodeArea > largestArea:
					anchor_nodeId = nodeId
					largestArea = nodeArea

		anchorBBox = self.svg.selected[anchor_nodeId].bounding_box()

		# calculate the offsets in mm
		insetH = self.svg.unittouu("{0}mm".format(self.options.inset_x))
		insetV = self.svg.unittouu("{0}mm".format(self.options.inset_y))

		otherNodes = [n for i, n in self.svg.selected.items() if i != anchor_nodeId]
		# for every other Node
		for node in otherNodes:
			bbox = node.bounding_box()

			# sort out vertical offset
			deltaV = (anchorBBox.top - bbox.top) + insetV # ALIGN TOP
			if self.options.relative_to_v in "BOTTOM":
				deltaV = (anchorBBox.bottom - bbox.bottom) - insetV # ALIGN BOTTOM
			if self.options.relative_to_v == "CENTRE":
				deltaV = (anchorBBox.top + anchorBBox.height/2 - bbox.height/2) - bbox.top # ALIGN CENTRE

			# sort out the horizontal offset
			deltaH = (anchorBBox.left - bbox.left) + insetH # ALIGN LEFT
			if self.options.relative_to_h == "RIGHT":
				deltaH = (anchorBBox.right - bbox.right) - insetH # ALIGN RIGHT
			if self.options.relative_to_h == "MIDDLE":
				deltaH = (anchorBBox.left + anchorBBox.width/2 - bbox.width/2) - bbox.left # ALIGN MIDDLE

			tform = inkex.Transform("translate({0}, {1})".format(deltaH, deltaV))
			node.transform = tform @ node.transform

if __name__ == '__main__':
	InsetAlignment().run()
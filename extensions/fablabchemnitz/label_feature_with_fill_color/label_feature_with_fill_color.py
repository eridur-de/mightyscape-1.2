#!/usr/bin/env python3


"""
A inkscape plugin to label features with their fill colour


Copyright (C) 2019 Christoph Fink

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
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import inkex
from inkex.paths import CubicSuperPath, Path
from lxml import etree

class LabelFeatureWithFillColor(inkex.EffectExtension):

    def effect(self):
        if len(self.svg.selected) > 0:
            for id, node in self.svg.selected.items():
                self.labelFeature(node)

    def labelFeature(self, node):
        style = node.get('style')
        if style:
            nodeStyle = dict(inkex.Style.parse_str(node.attrib["style"]))
            nodeColour, labelColour = self.getNodeAndLabelColours(nodeStyle["fill"])
            nodeX, nodeY, nodeWidth, nodeHeight = self.getNodeDimensions(node)
            parent = node.getparent()
            label = etree.SubElement(
                parent,
                inkex.addNS("text", "svg"),
                {
                    "font-size": str(nodeHeight/4),
                    "x": str(nodeX + (nodeWidth/2)),
                    "y": str(nodeY + (nodeHeight/2)),
                    "dy": "0.5em",
                    "style": str(inkex.Style({
                        "fill": labelColour,
                        "stroke": "none",
                        "text-anchor": "middle"
                    }))
                }
            )
            labelTextSpan = etree.SubElement(
                label,
                inkex.addNS("tspan", "svg"),
                {}
            )
            labelTextSpan.text = nodeColour


    def getNodeAndLabelColours(self, nodeStyleFill):
        if nodeStyleFill[:5] == "url(#":
            nodeFill = self.svg.getElementById(nodeStyleFill[5:-1])
            if "Gradient" in nodeFill.tag:
                nodeColour, labelColour = self.getNodeAndLabelColourForGradient(nodeFill)
            else:
                nodeColour = ""
                labelColour = ""

        else:
            nodeColour = nodeStyleFill
            labelColour = self.getLabelColour(nodeColour)

        return (nodeColour, labelColour)

    def getNodeAndLabelColourForGradient(self, gradientNode):
        stops = self.getGradientStops(gradientNode)

        nodeColours = []

        for stop in stops:
            offset = float(stop[0])
            colour = stop[1]
            nodeColours.append("{colour:s}{offset:s}".format(
                colour=colour,
                offset="" if offset in (0, 1) else " ({:0.2f})".format(offset)
            ))
        nodeColour = u" ↔ ".join(nodeColours)

        avgNodeColour = [sum([inkex.Color(stop[1]).to_rgb()[c] for stop in stops]) / len(stops) for c in range(3)]

        labelColour = str(inkex.Color(avgNodeColour))

        return (nodeColour, labelColour)

    def getGradientStops(self, gradientNode):
        while "{http://www.w3.org/1999/xlink}href" in gradientNode.attrib:
            gradientNode = self.svg.getElementById(gradientNode.attrib["{http://www.w3.org/1999/xlink}href"][1:])  # noqa:E129

        stops = []

        for child in gradientNode:
            if "stop" in child.tag:
                stopStyle = dict(inkex.Style.parse_str(child.attrib["style"]))
                stops.append((child.attrib["offset"], stopStyle["stop-color"]))

        # if only opacity differs (colour == same), return one stop only:
        if len(set([s[1] for s in stops])) == 1:
            stops = [(0, stops[0][1])]

        return stops

    def getLabelColour(self, nodeColour):
        labelColour = "#000000"

        try:
            nodeColour = inkex.Color(nodeColour).to_rgb()
            if sum(nodeColour) / len(nodeColour) < 128:
                labelColour = "#ffffff"
        except (
            TypeError,
            ZeroDivisionError  # if parseColor returns ""
        ):
            pass

        return labelColour

    def getNodeDimensions(self, node):
        bbox = node.bounding_box()
        nodeX = bbox.left
        nodeY = bbox.top
        nodeWidth = bbox.right - bbox.left
        nodeHeight = bbox.bottom - bbox.top
            
        return nodeX, nodeY, nodeWidth, nodeHeight

if __name__ == '__main__':
    LabelFeatureWithFillColor().run()
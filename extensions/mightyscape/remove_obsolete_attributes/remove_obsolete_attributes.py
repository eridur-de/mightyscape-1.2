#!/usr/bin/env python3

"""
Removes attributes sodipodi:absref, sodipodi:docbase and sodipodi:docname from all elements that contain them.

full names of attributes
sodipodi:absref
{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}absref
sodipodi:docbase
{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}docbase
sodipodi:docname
{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}docname

element.attrib.pop("{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}absref", None)
"""

import inkex
import sys

class RemoveObsoleteAttributes(inkex.EffectExtension):
	def __init__(self):
		inkex.Effect.__init__(self)
		self.arg_parser.add_argument("-a", "--removeAbsref", type=inkex.Boolean, default=True, help="Remove sodipodi:absref")
		self.arg_parser.add_argument("-b", "--removeDocbase", type=inkex.Boolean, default=True, help="Remove sodipodi:docbase")
		self.arg_parser.add_argument("-n", "--removeDocname", type=inkex.Boolean, default=True, help="Remove sodipodi:docname")

	def effect(self):
		if self.options.removeAbsref:
			elements = self.document.xpath("//*[@sodipodi:absref]", namespaces=inkex.NSS)
			for element in elements:
				element.attrib.pop("{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}absref", None)

		if self.options.removeDocbase:
			elements = self.document.xpath("//*[@sodipodi:docbase]", namespaces=inkex.NSS)
			for element in elements:
				element.attrib.pop("{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}docbase", None)
		
		if self.options.removeDocname:
			elements = self.document.xpath("//*[@sodipodi:docname]", namespaces=inkex.NSS)
			for element in elements:
				element.attrib.pop("{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}docname", None)

if __name__ == "__main__":
	RemoveObsoleteAttributes().run()
#!/usr/bin/env python3
'''
Grid Strip Creator  v1.0 (30/11/2014)


Copyright (C) 2014 Thomas Gebert - tsgebert **AT** web.de

## This basic extension allows you to automatically draw guides in inkscape for hexagons.

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
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

import inkex
from xml.etree import ElementTree as ET
from lxml import etree

def printDebug(string):
	inkex.errormsg(string)
	
class GridStripCreator(inkex.EffectExtension):
	
	def add_arguments(self, pars):
		pars.add_argument('--length', type = float, default = 230.0, help = 'Length of strip')
		pars.add_argument('--width', type = float, default = 20.0, help = 'Width of strip')
		pars.add_argument('--cellheight', type = float, default = 12.5, help = 'height of cell')
		pars.add_argument('--cellwidth', type = float, default = 12.5, help = 'Width of cell')
		pars.add_argument('--scalecells', type = inkex.Boolean, default = False, help = 'Scale cells over length')
		pars.add_argument('--cellnumx', type = int, default = 11, help = 'Number of cells x')
		pars.add_argument('--cellnumy', type = int, default = 10, help = 'Number of cells y')
		pars.add_argument('--notchdepth', type = float, default = 1.0, help = 'Depth of notch')
		pars.add_argument('--notchwidth', type = float, default = 10.0, help = 'Width of notch')
		pars.add_argument('--notchhorizontal', type = inkex.Boolean, default = False, help = 'Make notches on horizontal strip')
		pars.add_argument('--notchvertical', type = inkex.Boolean, default = False, help = 'Make notches on vertical strip')
		pars.add_argument('--notch2width', type = float, default = 3.0, help = 'Width of notch')
		pars.add_argument('--notchxcorner', type = inkex.Boolean, default = False, help = 'Make notches on corner of horizontal strip')
		pars.add_argument('--notchycorner', type = inkex.Boolean, default = False, help = 'Make notches on corner of vertical strip')

	def effect(self):
		# Get access to main SVG document element and get its dimensions.
		svg = self.document.getroot()
		# getting the parent tag of the guide
		nv = self.document.xpath('/svg:svg/sodipodi:namedview',namespaces=inkex.NSS)[0]
		
		documentUnits = inkex.addNS('document-units', 'inkscape')
		# inkex.utils.debug(nv.get(documentUnits))
		uunits = nv.get(documentUnits)
		message="Units="+uunits
		# inkex.utils.debug(message)

		# Get script's options value.
		stripwidth=self.svg.unittouu(str(self.options.width)+uunits)
		striplength=self.svg.unittouu(str(self.options.length)+uunits)

		cellheight=self.svg.unittouu(str(self.options.cellheight)+uunits)
		cellwidth=self.svg.unittouu(str(self.options.cellwidth)+uunits)

		scalecells=(self.options.scalecells)
		
		cellnumx=(self.options.cellnumx)
		cellnumy=(self.options.cellnumy)
		
		notchdepth=self.svg.unittouu(str(self.options.notchdepth)+uunits)
		notchwidth=self.svg.unittouu(str(self.options.notchwidth)+uunits)
		
		notchhorizontal=(self.options.notchhorizontal)
		notchvertical=(self.options.notchvertical)
				
#		notch2depth=self.svg.unittouu(str(self.options.notch2depth)+uunits)
		notch2width=self.svg.unittouu(str(self.options.notch2width)+uunits)
		
		notch2depth= stripwidth/2
		
		notchxcorner=(self.options.notchxcorner)
		notchycorner=(self.options.notchycorner)

		if scalecells:
			cellwidth=(striplength-4*notch2width)/cellnumx
			cellheight=(striplength-4*notch2width)/cellnumy
			notchxcorner=False
			notchycorner=False
		
		linewidth=self.svg.unittouu(str(0.2)+uunits)

		distx=(striplength-cellnumx*cellwidth)/2	
		disty=(striplength-cellnumy*cellheight)/2
		
		celldistx=(cellwidth-notchwidth)/2
		celldisty=(cellheight-notch2width)/2

		# getting the width and height attributes of the canvas
		width  = float(self.svg.unittouu(svg.attrib['width']))
		height = float(self.svg.unittouu(svg.attrib['height']))

		parent = self.svg.get_current_layer()
		layername=''
		if notchhorizontal:
			layername=layername+'VLED '
		if notchvertical:
			layername=layername+'HLED '
		
		# Create a new layer
		layer = etree.SubElement(svg,'g')
		layer.set(inkex.addNS('label', 'inkscape'),layername+'Long strips')
		layer.set(inkex.addNS('groupmode','inkscape'), 'layer')
		
		
		grp_name = 'group_horizontal_strip_long'
		grp_attribs = {inkex.addNS('label','inkscape'):grp_name}
		grp = etree.SubElement(layer, 'g', grp_attribs) #the group to put everything in

		style = { 'stroke': '#000000', 'stroke-width':str(linewidth), 'fill': 'none' }

		for num in range(0,2):		
			pathstring='M '+str(1)+','+str(1)+' L '
			if notchxcorner:
				pathstring+=str(stripwidth-2*notchdepth)+','+str(1)		# Obere Querkante
				pathstring+=' L '+str(stripwidth-2*notchdepth)+','+str(notchwidth)		# Erste Kerbe aussen
				pathstring+=' L '+str(stripwidth)+','+str(notchwidth)		# Ausrueckung
			else:
				pathstring+=str(stripwidth)+','+str(1)
			if notchhorizontal:
				pathstring+=' L '+str(stripwidth)+','+str(distx)					# Distance to corner
				y=distx
				for i in range(0,cellnumx):
					pathstring+=' L '+str(stripwidth)+','+str(y+celldistx)					# Abstand
					pathstring+=' L '+str(stripwidth-notchdepth)+','+str(y+celldistx)		# Einrueckung
					pathstring+=' L '+str(stripwidth-notchdepth)+','+str(y+celldistx+notchwidth)	# Kerbe
					pathstring+=' L '+str(stripwidth)+','+str(y+celldistx+notchwidth)				# Ausrueckung
					pathstring+=' L '+str(stripwidth)+','+str(y+2*celldistx+notchwidth)				# Abstand
					y=y+2*celldistx+notchwidth
			if notchxcorner:
				pathstring+=' L '+str(stripwidth)+','+str(striplength-notchwidth)					# Untere rechte Ecke
				pathstring+=' L '+str(stripwidth-2*notchdepth)+','+str(striplength-notchwidth)					# Untere rechte Ecke
				pathstring+=' L '+str(stripwidth-2*notchdepth)+','+str(striplength)					# Untere rechte Ecke
			else:
				pathstring+=' L '+str(stripwidth)+','+str(striplength)
			pathstring+=' L '+str(1)+','+str(striplength)							# Linke untere Ecke
							

							
			y=striplength-distx+notch2width/2
			
			pathstring+=' L '+str(1)+','+str(y)					# Distance to corner
			pathstring+=' L '+str(notch2depth)+','+str(y)		# Einrueckung

			
			for i in range(0,cellnumx):
				pathstring+=' L '+str(notch2depth)+','+str(y-notch2width)					# Kerbe
				pathstring+=' L '+str(1)+','+str(y-notch2width)		# Ausrueckung
				pathstring+=' L '+str(1)+','+str(y-notch2width-cellwidth+notch2width)	# Abstand
				pathstring+=' L '+str(notch2depth)+','+str(y-notch2width-cellwidth+notch2width)				# Einrueckung
				y=y-notch2width-cellwidth+notch2width
			
			pathstring+=' L '+str(notch2depth)+','+str(y-notch2width)					# Kerbe 
			pathstring+=' L '+str(1)+','+str(y-notch2width)		# Ausrueckung
			
			pathstring+=' L '+str(1)+','+str(1)+' z'

			strip_transform= 'rotate(' + str(90)+')'
			strip_transform+=' translate('+str(stripwidth*num)+','+str(1)+')'
			strip_attribs = {'style':str(inkex.Style(style)),
								inkex.addNS('label','inkscape'):"strip horizontal long",
								'transform': strip_transform,
								'd':pathstring}
			etree.SubElement(grp, inkex.addNS('path','svg'), strip_attribs )
		
		
		celldisty=(cellheight-notch2width-notchwidth)/2

		grp_name = 'group_vertical_strip_long'
		grp_attribs = {inkex.addNS('label','inkscape'):grp_name}
		grp = etree.SubElement(layer, 'g', grp_attribs) #the group to put everything in
		

		for num in range(0,2):
			y=disty-notch2width/2
			pathstring='M '+str(1)+','+str(1)
			if notchycorner:
				pathstring+=' L '+str(stripwidth-2*notchdepth)+','+str(1)		# Obere Querkante
				pathstring+=' L '+str(stripwidth-2*notchdepth)+','+str(notchwidth)
				pathstring+=' L '+str(stripwidth)+','+str(notchwidth)
			else:
				pathstring+=' L '+str(stripwidth)+','+str(1)
			pathstring+=' L '+str(stripwidth)+','+str(y)					# Distance to corner

			for i in range(0,cellnumy):
				pathstring+=' L '+str(stripwidth-notch2depth)+','+str(y)		# Einrueckung
				pathstring+=' L '+str(stripwidth-notch2depth)+','+str(y+notch2width)	# Kerbe
				pathstring+=' L '+str(stripwidth)+','+str(y+notch2width)				# Ausrueckung
				if notchvertical:
					pathstring+=' L '+str(stripwidth)+','+str(y+notch2width+celldisty)					# Abstand
					pathstring+=' L '+str(stripwidth-notchdepth)+','+str(y+notch2width+celldisty)		# Einrueckung
					pathstring+=' L '+str(stripwidth-notchdepth)+','+str(y+notch2width+celldisty+notchwidth)	# Kerbe
					pathstring+=' L '+str(stripwidth)+','+str(y+notch2width+celldisty+notchwidth)				# Ausrueckung
				pathstring+=' L '+str(stripwidth)+','+str(y+notch2width+2*celldisty+notchwidth)				# Abstand
				y=y+notch2width+2*celldisty+notchwidth

					
			pathstring+=' L '+str(stripwidth-notch2depth)+','+str(y)		# Einrueckung
			pathstring+=' L '+str(stripwidth-notch2depth)+','+str(y+notch2width)	# Kerbe
			pathstring+=' L '+str(stripwidth)+','+str(y+notch2width)				# Ausrueckung

			if notchycorner:
				pathstring+=' L '+str(stripwidth)+','+str(striplength-notchwidth)					# Untere rechte Ecke
				pathstring+=' L '+str(stripwidth-2*notchdepth)+','+str(striplength-notchwidth)					# Untere rechte Ecke
				pathstring+=' L '+str(stripwidth-2*notchdepth)+','+str(striplength)					# Untere rechte Ecke
			else:
				pathstring+=' L '+str(stripwidth)+','+str(striplength)
			pathstring+=' L '+str(1)+','+str(striplength)							# Linke untere Ecke
			pathstring+=' L '+str(1)+','+str(1)+' z'
			
			strip_transform= 'translate('+str(num*stripwidth)+','+str(1)+')'
			strip_attribs = {'style':str(inkex.Style(style)),
								inkex.addNS('label','inkscape'):"strip vertical long",
								'transform': strip_transform,
								'd':pathstring}
			etree.SubElement(grp, inkex.addNS('path','svg'), strip_attribs )
		
		# Create a new layer
		layer = etree.SubElement(svg,'g')
		layer.set(inkex.addNS('label', 'inkscape'), layername+'Horizontal strips short')
		layer.set(inkex.addNS('groupmode','inkscape'), 'layer')

		grp_name = 'group horizontal_strip_short'
		grp_attribs = {inkex.addNS('label','inkscape'):grp_name}
		grp = etree.SubElement(layer, 'g', grp_attribs) #the group to put everything in
		striplength=cellnumx*cellwidth+4*notch2width
		distx=(striplength-cellnumx*cellwidth)/2	
		disty=(striplength-cellnumy*cellheight)/2

		style = { 'stroke': '#000000', 'stroke-width':str(linewidth), 'fill': 'none' }
		
		for num in range(1,cellnumy):
		
			pathstring='M '+str(1)+','+str(1)+' L '
			pathstring+=str(stripwidth)+','+str(1)
			if notchhorizontal:
				pathstring+=' L '+str(stripwidth)+','+str(distx)					# Distance to corner
				y=distx
				for i in range(0,cellnumx):
					pathstring+=' L '+str(stripwidth)+','+str(y+celldistx)					# Abstand
					pathstring+=' L '+str(stripwidth-notchdepth)+','+str(y+celldistx)		# Einrueckung
					pathstring+=' L '+str(stripwidth-notchdepth)+','+str(y+celldistx+notchwidth)	# Kerbe
					pathstring+=' L '+str(stripwidth)+','+str(y+celldistx+notchwidth)				# Ausrueckung
					pathstring+=' L '+str(stripwidth)+','+str(y+2*celldistx+notchwidth)				# Abstand
					y=y+2*celldistx+notchwidth
			pathstring+=' L '+str(stripwidth)+','+str(striplength)
			pathstring+=' L '+str(1)+','+str(striplength)							# Linke untere Ecke
							
			y=striplength-distx+notch2width/2
			
			pathstring+=' L '+str(1)+','+str(y)					# Distance to corner
			pathstring+=' L '+str(notch2depth)+','+str(y)		# Einrueckung
			
			for i in range(0,cellnumx):
				pathstring+=' L '+str(notch2depth)+','+str(y-notch2width)					# Kerbe
				pathstring+=' L '+str(1)+','+str(y-notch2width)		# Ausrueckung
				pathstring+=' L '+str(1)+','+str(y-notch2width-cellwidth+notch2width)	# Abstand
				pathstring+=' L '+str(notch2depth)+','+str(y-notch2width-cellwidth+notch2width)				# Einrueckung
				y=y-notch2width-cellwidth+notch2width
			
			pathstring+=' L '+str(notch2depth)+','+str(y-notch2width)					# Kerbe 
			pathstring+=' L '+str(1)+','+str(y-notch2width)		# Ausrueckung
			
			pathstring+=' L '+str(1)+','+str(1)+' z'

			strip_transform='rotate(' + str(90)+')'
			strip_transform+=' translate('+str((num+1)*stripwidth+2)+','+str(1)+')'
			stripname="strip horizontal short"+str(num)
			strip_attribs = {'style':str(inkex.Style(style)),
								inkex.addNS('label','inkscape'):stripname,
								'transform': strip_transform,
								'd':pathstring}
			etree.SubElement(grp, inkex.addNS('path','svg'), strip_attribs )

			
		# Create a new layer
		layer = etree.SubElement(svg,'g')
		layer.set(inkex.addNS('label', 'inkscape'), layername+'Vertical strips short')
		layer.set(inkex.addNS('groupmode','inkscape'), 'layer')

		grp_name = 'group vertical_strip_short'
		grp_attribs = {inkex.addNS('label','inkscape'):grp_name}
		grp = etree.SubElement(layer, 'g', grp_attribs) #the group to put everything in
		
		striplength=cellnumx*cellwidth+4*notch2width
		distx=(striplength-cellnumx*cellwidth)/2	
		disty=(striplength-cellnumy*cellheight)/2

		striplength=cellnumy*cellheight+4*notch2width
		distx=(striplength-cellnumx*cellwidth)/2	
		disty=(striplength-cellnumy*cellheight)/2

		celldisty=(cellheight-notch2width-notchwidth)/2
		
		for num in range(1,cellnumx):
			y=disty-notch2width/2
			pathstring='M '+str(1)+','+str(1)
			pathstring+=' L '+str(stripwidth)+','+str(1)
			pathstring+=' L '+str(stripwidth)+','+str(y)					# Distance to corner

			for i in range(0,cellnumy):
				pathstring+=' L '+str(stripwidth-notch2depth)+','+str(y)		# Einrueckung
				pathstring+=' L '+str(stripwidth-notch2depth)+','+str(y+notch2width)	# Kerbe
				pathstring+=' L '+str(stripwidth)+','+str(y+notch2width)				# Ausrueckung
				if notchvertical:
					pathstring+=' L '+str(stripwidth)+','+str(y+notch2width+celldisty)					# Abstand
					pathstring+=' L '+str(stripwidth-notchdepth)+','+str(y+notch2width+celldisty)		# Einrueckung
					pathstring+=' L '+str(stripwidth-notchdepth)+','+str(y+notch2width+celldisty+notchwidth)	# Kerbe
					pathstring+=' L '+str(stripwidth)+','+str(y+notch2width+celldisty+notchwidth)				# Ausrueckung
				pathstring+=' L '+str(stripwidth)+','+str(y+notch2width+2*celldisty+notchwidth)				# Abstand
				y=y+notch2width+2*celldisty+notchwidth

					
			pathstring+=' L '+str(stripwidth-notch2depth)+','+str(y)		# Einrueckung
			pathstring+=' L '+str(stripwidth-notch2depth)+','+str(y+notch2width)	# Kerbe
			pathstring+=' L '+str(stripwidth)+','+str(y+notch2width)				# Ausrueckung

			pathstring+=' L '+str(stripwidth)+','+str(striplength)
			pathstring+=' L '+str(1)+','+str(striplength)							# Linke untere Ecke
			pathstring+=' L '+str(1)+','+str(1)+' z'
			
			
			strip_transform= 'translate('+str((num+1)*stripwidth+10)+','+str(1)+')'
			stripname="strip vertical short"+str(num)
			strip_attribs = {'style':str(inkex.Style(style)),
								inkex.addNS('label','inkscape'):stripname,
								'transform': strip_transform,
								'd':pathstring}
			etree.SubElement(grp, inkex.addNS('path','svg'), strip_attribs )
				
if __name__ == '__main__':
    GridStripCreator().run()
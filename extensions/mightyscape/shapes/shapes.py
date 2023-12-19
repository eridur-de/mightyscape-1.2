#!/usr/bin/env python3
'''
shapes.py

Copyright (C) 2015 - 2022 Paco Garcia, www.arakne.es

2017_07_30: added crossed corners
			copy class of original object if exists
2017_08_09: rombus moved to From corners tab
2017_08_17: join circles not need boolen operations now
			join circles added Oval
2017_08_25: fixed error in objects without style
2021_04_05: added envelope card	
			replaced arcs created by beziers by svg arcs
			added crosscorners inverse
2021_04_13: Renamed pillow shape to deflate
			Added deflate to the From nodes tab
2021_10_24: bounding_box no devolvía valores correctos para ellipse, circle y rect
2022_01_10: added tabs, added reverse direction to path
            new option in Join circles for inside tangents, and checkbox for
			only create the join shape 
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
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
-----------------------
# TODO: text bounding box  https://stackoverflow.com/questions/24337531/how-to-determine-text-width-and-height-when-using-svgwrite-for-python

'''
import locale, math
from lxml import etree

import inkex
# from inkex.transforms import BoundingBox

from arakne_xy import *

defStyle = [['stroke-width','0.5'],['fill','#f0ff00'],['stroke','#ff0000']]

locale.setlocale(locale.LC_ALL, '')

# ####################################################3

def calcCircle(pt1, pt2, pt3):
	D_a = XY(pt2)-pt1
	D_b = XY(pt3)-pt2
	m_C = XY()
	Min = 0.000000001

	if (abs(D_a.x) <= Min and abs(D_b.y) <= Min):
		m_C= XY(0.5*(pt2.x + pt3.x), 0.5*(pt1.y + pt2.y))

	aSlope = D_a.y / D_a.x

	if D_b.x == 0:
		bSlope = D_b.y
	else:
		bSlope = D_b.y / D_b.x
	if (abs(aSlope-bSlope) <= Min): # colinear points?
		return [-1,-1,-1]
	# calc center
	m_Cx= (aSlope * bSlope * (pt1.y - pt3.y) + bSlope * (pt1.x + pt2.x) - aSlope * (pt2.x + pt3.x))/(2 * (bSlope - aSlope))
	m_Cy = -1 * (m_Cx - (pt1.x + pt2.x) / 2) / aSlope +  (pt1.y + pt2.y)/2
	v1 = XY(m_Cx,m_Cy).VDist(pt2)
	return {'c':XY(m_Cx,m_Cy),'r':v1}

# ####################################################3

class Shapes(inkex.Effect):
	def addOpt(self, name, Type=str, Default=""):
		self.arg_parser.add_argument("--" + name, action="store", type=Type, dest=name, default=Default, help="")

	def __init__(self):
		inkex.Effect.__init__(self)
		sOP = self.arg_parser
		for n in ["tab","chamfertype","midtype","objid","tab_from_bb","crosscornersshape","envelopetype"] : self.addOpt(n)
		for n in ["size","midsize","incdec","spikesep","spikeheight","joinradius","objsize","reducey","tabsize"] : self.addOpt(n, float, 0.0)
		for n in ["arrowWidth","fntsize","archmax","archmin"] : self.addOpt(n, float, 10.0)
		for n in ["tritype", "spikestype","spikesdir","spikesdirt","spikesdirr","spikesdirb","spikesdirl","unit","arch"] : self.addOpt(n)
		self.addOpt("spikesize", float, "2.0")
		self.addOpt("arrowtype")
		self.addOpt("headWidth",float,"20.0")
		self.addOpt("headHeight",float,"40.0")
		for n in ["squareselection", "trihside","trivside","copyfill", "fromCornersInv", "deleteorigin","helpbuild","reverse","joincircleonlyrect"] : self.addOpt(n, inkex.Boolean, "false")
		sOP.add_argument("--joincirctype", action="store", type=str, dest="joincirctype", default="", help="" )
		# para from nodes
		for n in ["obj","posh","posv"] : self.addOpt(n)
		sOP.add_argument("--maxdecimals", action="store", type=int, dest="maxdecimals", default="6", help="" )
		sOP.add_argument("--archfoils", action="store", type=int, dest="archfoils", default="3", help="" )

		for n in ["ordery", "rotpath"] : self.addOpt(n, inkex.Boolean, "false")

	def _getU(self, val, unit):
		return self.svg.unittouu(str(val) + unit)

	def getU(self, val):
		return self.svg.unittouu(str(val) + self.options.unit)

	def addEle(self, ele, parent, props):
		elem = etree.SubElement(parent, ele)
		for n in props: elem.set(n,props[n])
		return elem

	def addPath(self, parent, props):
		return self.addEle('path', parent, props)

	def chStyles(self,node,sty):
		style = dict(inkex.Style.parse_str(node.get('style')))
		for n in sty:
			if n[0] in style: style.pop(n[0], None)
			if n[1]!="": style[n[0]]=n[1]
		node.set('style',inkex.Style(style))

	def limits(self, node):
		s = node.bounding_box()
		incdec = self.getU(self.options.incdec)
		l, r, t, b, an, al = (s.left, s.right, s.top, s.bottom, s.width, s.height)
		# info(str(node.TAG))
		if (node.TAG=="rect"):
			(l, an,t,al) =[self._getU(node.get(i),"mm") for i in ["x","width","y","height"]]
			r = l + an
			b = t + al
		if (node.TAG=="ellipse"):
			(ry, rx, cy, cx) =[self._getU(node.get(i),"mm") for i in ["ry","rx","cy","cx"]]
			an, al, t, r, b, l = (rx * 2.0, ry * 2.0,  cy - ry, cx + rx, cy + ry, cx - rx)
		if (node.TAG=="circle"):
			(r, cy, cx) =[self._getU(node.get(i),"mm") for i in ["r","cy","cx"]]
			l = cx - r
			an = al = r * 2.0
			t = cy - r
			r = cx + r
			b = cy + r 
		#for n in dir(node): info(n)
		# trbl
		return (t - incdec, r + incdec, b + incdec, l - incdec, an + incdec * 2, al + incdec * 2)

	def copyProp(self, orig, dest, prop):
		if orig.get(prop):
			dest.set(prop, orig.get(prop))

	def estilo(self, nn, orig, style=defStyle):
		if self.options.copyfill:
			self.copyProp(orig, nn, 'style')
			self.copyProp(orig, nn, 'class')
		else:
			self.chStyles(nn,style)

	def deflate(self, cnrs, a, node):
		pts = []
		aa = a
		for n in range(0,len(cnrs)-1):
			pts.append(cnrs[n])
			pts.append(XY(cnrs[n]).atMid(cnrs[n+1]) + XY(0,aa).rot(cnrs[n].getAngle(cnrs[n+1])))

		n = len(cnrs)-1
		pts.append(cnrs[n])

		pM = XY(cnrs[n]).atMid(cnrs[0]) + XY(0,aa).rot(cnrs[n].getAngle(cnrs[0]))
		pts.append(pM)

		s = ''

		for n in range(0,int(len(pts)/2)):
			if n==(int(len(pts)/2)-1):
				n1,n2,n3 =(len(pts)-2, len(pts)-1, 0)
			else:
				n1,n2,n3 =(n*2, n*2+1, n*2+2)
			nnA = calcCircle(pts[n1], pts[n2], pts[n3])
			ang1 = math.degrees(nnA['c'].getAngle(pts[n1]))
			ang2 = math.degrees(nnA['c'].getAngle(pts[n3]))
			if ang1<0 and ang2>0:
				ang2 = ang2 - 360
			dif = ang2 - ang1
			if dif > 0:
				if ang1<ang2:
					a1 = (360 - (ang2 -ang1))/2
					s += svgArcXY(nnA['c'], nnA['r'], ang1, ang1-a1, 0, "M" if n==0 else "L", 0 if n==0 else 1)#+"l10,10"
					s += svgArcXY(nnA['c'], nnA['r'], ang1-a1, ang2-360, 0,  "L", 1)
			else:
				s = s + ' ' + svgArcXY(nnA['c'], nnA['r'], ang1, ang2, 0, "M" if n==0 else "L", 0 if n==0 else 1)
		return s
		#shp = addChild(node.getparent(), 'path',{'d': s})
		#self.estilo(shp,node)

	def crossCorners(self, node, a, l, r, t, b, w, h, sO):
		ccshape = sO.crosscornersshape
		inv = sO.fromCornersInv
		a2=a*2
		if ccshape=="quads":
			if inv:
				pnts=[[l,t+a],[a2,0],[0,a], [-a,0],[0,-a2],[w-a2,0],[0,a2],[-a,0],[0,-a],[a2,0],[0,h-a2],[-a2,0],[0,-a],
				[a,0],[0,a2],[-w+a2,0],[0,-a2],[a,0],[0,a],[-a2,0]]
			else:
				pnts=[[l-a,t],[0,-a],[a,0],[0,h+a*2],[-a,0],[0,-a],[w+a*2,0],[0,a],[-a,0],[0,-h-a*2],[a,0],[0,a]]
		if ccshape=="tris":
			if inv:
				pnts=[[l,t+a],[a2,0],[-a,a],[0,-a2],[w-a2,0],[0,a2],[-a,-a],[a2,0],[0,h-a2],[-a2,0],[a,-a],[0,a2],[-w+a2,0],
					[0,-a2],[a,a],[-a2,0]]
			else:
				pnts=[[l-a,t], [a,-a], [0,h+a*2], [-a,-a], [w+a*2,0], [-a,a], [0,-h-a*2],[a,a]]
		if ccshape=="round":
			dS = "M %sZ"
			if inv:
				sss=svgArc(l+a2,t+a2, a, a, 270, 270, 0) + " " + XY(0,-a2,"l") + " " + XY(w-a2,0) + svgArc(l+w-a2,t+a2, a, a, 0, 270, 0,"L")
				sss += XY(a2,0,"l") + " " + XY(0,h-a2) + " " + svgArc(l+w-a2,t+h-a2, a, a, 90, 270, 0,"L") + XY(0,a2,"l") + XY(-w+a2,0,"l")
				sss += svgArc(l+a2,t+h-a2, a, a, 180, 270, 0,"L") + XY(-a2,0,"l") + XY(0,-h+a2,"l") +"z"
			else:
				sss = svgArc(l-a,t-a, a, a, 0, 270, 90) + " " + svgArc(l-a,t+h+a, a, a, 0, 270, 0,"L") + " " + svgArc(l+w+a,t+h+a, a, a, 0, 270, -90,"L") + " " + svgArc(l+w+a,t-a, a, a, 0, 270, 180,"L")
			self.estilo(self.addPath(node.getparent(),{"d":sss+"Z"}),node)
			if sO.deleteorigin: node.getparent().remove(node)
			pnts=[]
		return pnts

	def envelope(self, node, a, l, r, t, b, w, h):
		sO = self.options
		etype = sO.envelopetype
		pp = node.getparent()
		w2, h2=(w/2.0, h/2.0)
		ll = min(h2,w2)
		dif = max(w,h) - ll*2
		if a==0:
			spts = XYarr2str([XY(l,t,"m"), [w2,-h2], [w2,h2], [w2,h2], [-w2,h2], [-w2,h2], [-w2,-h2], [-w2,-h2],"z"])
		else:
			if etype=="rect":
				spts = XYarr2str(["m",[l,t], "v", -a, "l", [w2,-h2], [w2,h2], "v",a,"h",a, "l", [w2,h2], [-w2,h2],"h", -a,"v", a,
					"l",[-w2,h2], [-w2,-h2], "v", -a, "h", -a,"l", [-w2,-h2], [w2,-h2],"z"])
			if etype=="rectreg":
				if w2==ll:
					spts=XYarr2str(["m",[l,t],"v",-a,"l",[ll,-ll],[ll,ll],"v", a,"h", a,"l", [ll,ll],"v",dif,"l",[-ll,ll],"h", -a,"v",
					 a,"l",[-ll,ll],[-ll,-ll],"v",-a,"h",-a,"l",[-ll,-ll],"v",-dif,"l",[ll,-ll],"z"])
				else:
					spts="m%s v%s l%s h%s l%s v%s h%s l%s l%s h%s v%s l%s h%s l%s v%s h%s l%s %sz" % (XY(l,t), -a, XY(ll,-ll), 
					dif, XY(ll,ll), a, a, XY(ll,ll), XY(-ll,ll), -a, a, XY(-ll,ll), -dif,XY(-ll,-ll),-a,-a, XY(-ll,-ll), XY(ll,-ll))
			if etype=="roundedreg" and w==h: etype = "rounded"
			if etype=="rounded":
				Hy1, Hy2 = (h2/w2 * a, w2/h2 * a)
				rot = XY(0,0).getAngleD(XY(h2,w2))
				rot2 = 90-rot

				sss = svgArc(l+a,t-Hy1, a, a, 180, rot, 0,"L") + " " + svgArc(l+w2,t-h2, a, a, 270-rot2, rot2*2, 0,"L") 
				sss = sss + " " + svgArc(l-a+w,t-Hy1, a, a, 270+rot2, rot, 0,"L") + XY(l+w,t," L").st()
				sss = sss + XY(l+w+Hy2,t,"L").st() + svgArc(l+w+Hy2,t+a, a, a, 270, rot2, 0,"L")
				sss = sss + svgArc(l+w+w2,t+h2, a, a, 360-rot, rot*2, 0,"L") + svgArc(l+w+Hy2,t+h-a, a, a, rot, rot2, 0,"L")
				sss = sss + XY(l+w,t+h,"L").st() + XY(l+w,t+h+Hy1,"L").st() + " " + svgArc(l-a+w,t+h+Hy1, a, a, 0, rot, 0,"L")
				sss = sss+ " " + svgArc(l+w2,t+h+h2, a, a, rot, rot2*2, 0,"L") + " " + svgArc(l+a,t+h+Hy1, a, a, 90+rot2, rot, 0,"L")
				sss = sss + XY(l,t+h,"L").st() + XY(l-Hy2,t+h,"L").st() + " " + svgArc(l-Hy2,t+h-a, a, a, 90, rot2, 0,"L")
				sss = sss+ " " + svgArc(l-w2,t+h2, a, a, 90+rot2, rot*2, 0,"L")
				sss = sss+ " " + svgArc(l-Hy2,t+a, a, a, 180+rot, rot2, 0,"L")
				spts = "M%s %s %s" % (XY(l,t), sss,"Z")
			if etype=="roundedreg":
				if w2==ll:
					sss = svgArc(l+a,t-a, a, a, 180, 45, 0,"L") + " " + svgArc(l+w2,t-ll, a, a, 225, 90, 0,"L") + " "
					sss = sss + svgArc(l-a+w,t-a, a, a, 315, 45, 0,"L") + XY(l+w,t," L").st()
					sss = sss + svgArc(l+w+a,t+a, a, a, 270, 45, 0,"L") + svgArc(l+w+ll,t+ll, a, a, 315, 45, 0,"L")
					sss = sss + svgArc(l+w+ll,t+h-ll, a, a, 0, 45, 0,"L")
					sss = sss + svgArc(l+w+a,t+h-a, a, a, 45, 45, 0,"L") + XY(l+w,t+h," L").st() + XY(l+w,t+h+a," L").st()
					sss = sss + svgArc(l+w-a,t+h+a, a, a, 0, 45, 0,"L") + svgArc(l+ll,t+h+ll, a, a, 45, 90, 0,"L")
					sss = sss + svgArc(l+a,t+h+a, a, a, 135, 45, 0,"L") + XY(l,t+h," L").st() + XY(l-a,t+h," L").st()
					sss = sss + svgArc(l-a,t+h-a, a, a, 90, 45, 0,"L") + svgArc(l-ll,t+h-ll, a, a, 135, 45, 0,"L")
					sss = sss + svgArc(l-ll,t+ll, a, a, 180, 45, 0,"L") + svgArc(l-a,t+a, a, a, 225, 45, 0,"L")
				else:
					sss = svgArc(l+a,t-a, a, a, 180, 45, 0,"L") + " " + svgArc(l+ll,t-ll, a, a, 225, 45, 0,"L") 
					sss = sss + " " + svgArc(l+w-ll,t-ll, a, a, 270, 45, 0,"L") + " " + svgArc(l+w-a,t-a, a, a, 315, 45, 0,"L")
					sss = sss + XY(l+w,t,"L").st() + svgArc(l+w+a,t+a, a, a, 270, 45, 0,"L")
					sss = sss + svgArc(l+w+ll,t+ll, a, a, 270+45, 90, 0,"L") + svgArc(l+w+a,t+h-a, a, a, 45, 45, 0,"L")
					sss = sss + XY(l+w,t+h,"L").st() + XY(l+w,t+h+a,"L").st() + " " + svgArc(l-a+w,t+h+a, a, a, 0, 45, 0,"L")
					sss = sss+ " " + svgArc(l+w-ll,t+h+ll, a, a, 45, 45, 0,"L") + " " + svgArc(l+ll,t+h+ll, a, a, 90, 45, 0,"L")
					sss = sss+ " " + svgArc(l+a,t+h+a, a, a, 135, 45, 0,"L") + XY(l,t+h,"L").st()
					sss = sss+ " " + svgArc(l-a,t+h-a, a, a, 90, 45, 0,"L") + " " + svgArc(l-ll,t+ll, a, a, 135, 90, 0,"L")
					sss = sss+ " " + svgArc(l-a,t+a, a, a, 180+45, 45, 0,"L")
				spts = "M%s %s %s" % (XY(l,t), sss,"Z")
		self.estilo(self.addPath(pp,{'d':spts}),node)
		if sO.deleteorigin: node.getparent().remove(node)

	def draw(self, node, sh='rombus'):
		# ignoramos objetos de texto, no podemos obtener el tamaño del bbox
		if (node.tag == inkex.addNS('text','svg')):
			return
		sO = self.options
		t, r, b, l, an, al = self.limits(node)
		sqSel = sO.squareselection
		tInv = sO.fromCornersInv
		deleteorigin = sO.deleteorigin

		side = min(al,an)
		if sqSel:
			incx=(an-side)/2.0
			l,r,an =(l+incx,r-incx,side)
			incy=(al-side)/2.0
			t +=incy
			b -=incy
			al = side
		cX, cY = (an/2.0,al/2.0)
		sub_bb = sO.tab_from_bb
		pp = node.getparent()
		varBez = 0.551915024494

		a = self.getU(sO.size) if sub_bb=="chamfer" else self.getU(sO.midsize)

		a_2, a2 = (a / 2.0,a * 2.0)
		dS = "m %sz"
		pnts = [[l+cX,t],[cX,cY],[-cX,cY],[-cX,-cY]]
		aa = a * varBez
		chtype = sO.chamfertype
		midtype = sO.midtype

		an2, al2 = ((an-a)/2.0,(al-a)/2.0)
		tritype = sO.tritype
		if sh == 'bbox':
			if midtype=="rombus" and a>0: pnts=[[l+cX - a_2,t],[a,0],[an2,al2],[0,a],[-an2,al2],[-a,0],[-an2,-al2],[0,-a]]
			if (sub_bb=='mid'):
				if midtype=="chamfer":
					if tInv==False:
						pnts=[[l+a,t],[an - a2,0],[a,a],[0,al-a2],[-a,a],[-(an - a2),0],[-a,-a],[0,-(al-a2)]]
					else:
						pnts=[[l,t],[a,0],[-a,a],[an-a,0," z m"],[a,0],[0,a],[a,al," z m"],[0,-a],[-a,a],[-an+a,0," z m"],[-a,-a],[0,a]]
				if midtype=="cross":
					pnts=[[l+an2,t],[a,0],[0,al2],[an2,0],[0,a],[-an2,0],[0,al2],[-a,0],[0,-al2],[-an2,0],[0,-a],[an2,0]]
				if midtype=="starcenter":
					pnts=[[l+cX,t],[a_2,al2], [an2,a_2], [-an2,a_2],[-a_2,al2],[-a_2,-al2],[-an2,-a_2],[an2,-a_2]]

				if midtype=="deflaterombus":
					#self.deflates(midtype, a, node, l, t, r, b, cX, cY)
					sPth = self.deflate([XY(l,t+cY), XY(l+cX,t), XY(r,t+cY), XY(r-cX,b)], a, node)
					pnts  = []
					shp = addChild(node.getparent(), 'path',{'d': sPth})
					self.estilo(shp,node)
					if deleteorigin: node.getparent().remove(node)

			if (sub_bb=='chamfer'):
				if chtype=="chamfer":
					if tInv==False:
						pnts=[[l+a,t],[an - a2,0],[a,a],[0,al-a2],[-a,a],[-(an - a2),0],[-a,-a],[0,-(al-a2)]]
					else:
						pnts=[[l,t],[a,0],[-a,a],[an-a,0," z m"],[a,0],[0,a],[a,al," z m"],[0,-a],[-a,a],[-an+a,0," z m"],[-a,-a],[0,a]]
				if chtype=="round":
					if tInv==False:
						sss = svgArcXY(XY(l,t),a,90,0,0) + svgArcXY(XY(l+an,t),a,90,0,90, "L") +  svgArcXY(XY(l+an,t+al),a,90,0,180, "L")
						sss +=  svgArcXY(XY(l,t+al),a,90,0,270, "L")
						self.estilo(self.addPath(node.getparent(),{"d":sss + "z"}),node)
						if sO.deleteorigin: node.getparent().remove(node)
						pnts=[]
					else:
						pnts=[[l,t],[a,0],[0,aa,"c "],[-aa,a],[-a,a],[an-a,0,"z m "],[a,0],[0,a],[-aa,0," c"],[-a,-aa],[-a,-a],
							[a,al-a,"z m "],[0,a],[-a,0],[0,-aa,"c "],[aa,-a],[a,-a],[-an,0,"z m "],[0,a],[a,0],[0,-aa,"c "],[-aa,-a],[-a,-a]]
				if chtype=="roundinv":
					pnts=[[l,t],[a,0],[0,aa,"c "],[-aa,a],[-a,a],[an-a,0,"z m "],[a,0],[0,a],[-aa,0," c"],[-a,-aa],[-a,-a],
						[a,al-a,"z m "],[0,a],[-a,0],[0,-aa,"c "],[aa,-a],[a,-a],[-an,0,"z m "],[0,a],[a,0],[0,-aa,"c "],[-aa,-a],[-a,-a]]
				if chtype=="rect":
					pnts=[[l+a,t],[an - a2,0],[0,a],[a,0],[0,al-a2],[-a,0],[0,a],[-(an-a2),0],[0,-a],[-a,0],[0,-(al-a2)],[a,0]]
				if chtype=="starcorners": pnts=[[l,t],[cX,al2],[cX,-al2],[-an2,cY],[an2,cY],[-cX,-al2],[-cX,al2],[an2,-cY]]
				if chtype=="crosscorners": pnts = self.crossCorners(node, a, l, r, t, b, an, al, sO)
				if chtype=="letterenvelope":
					self.envelope(node, a, l, r, t, b, an, al)
					pnts=[]

				if chtype=="deflaterect":
					#self.deflates(chtype, a, node, l, t, r, b, cX, cY)
					cnrs=[XY(l,t), XY(r,t), XY(r,b), XY(l,b)]
					sPth = self.deflate(cnrs, a, node)
					pts = []
					pnts  = []
					dS = "M %sZ"
					shp = addChild(node.getparent(), 'path',{'d': sPth})
					self.estilo(shp,node)
					if deleteorigin: node.getparent().remove(node)
				if chtype == "spiralrect":
					An, Al = (an, al)
					pnts = [[l,t], [An,0], [0,Al], [-An,0], [0,-Al+a]]
					An, Al = (An - a, Al - a*2)
					tot = min(An//a,Al//a) // 2 + 1

					for n in range(0,int(tot)):
						pnts.append([An,0])
						An = An-a
						if Al>a:
							pnts.append([0,Al])
							Al = Al-a
						else:
							break
						if An>a:
							pnts.extend([[-An,0]])
							An = An-a
						else:
							break
						if Al>0:
							pnts.extend([[0, -Al]])
							Al=Al-a
						else:
							break

					#   ________________
					#   ______________  |
					#  |  __________  | |
					#  | |____________| |
					#  |________________|

					defStyle = [['stroke-width','2.5'],['fill','none'],['stroke','#ff0000']]
					dS = "m %s"

			if (sub_bb=='spikes'): pnts = self.triSpikes(sO, an, al, l, t)

			if sub_bb=='arrow':
				pnts = self.drawArrow(sO, an, al, l, t)
				if sO.arrowtype=="arrowstick":
					dS = "m %s"

			if sub_bb=='triangles':
				trihside, trivside=(sO.trihside, sO.trivside)
				if tritype=="isosceles": pnts=[[l+cX,t],[cX,al],[-an,0]]
				if tritype=="equi":
					sqrt3 = 1.7320508075
					height = sqrt3/2 * side
					tcx, tcy = ((an - side)/2.0, (al - height)/2.0)
					pnts=[[cX+l,t+tcy],[an/2.0-tcx,height],[-side,0]]
				if tritype=="rect":
					x1 = l + tern(not trivside and trihside,an,0)
					x2 = tern(not trivside and trihside,0,an)
					x3 = tern(trivside and trihside,0,-an)
					pnts=[[x1,t], [x2,tern(not trivside,al,0)], [x3,tern(not trivside,0,al)]]
				# #######################################
				if tritype=="circi" or tritype=="circe" or tritype=="trii":
					# get verts
					pnts = []
					if node.get('d'):
						p = node.path.to_superpath().to_path().to_arrays()
						vs=[]
						for cmd, params in p:
							if cmd != 'Z' and cmd != 'z':
								vs.append(XY(params[-2],params[-1]))
						if len(vs)>2:
							if tritype == "trii":
								p1 = XY(vs[0]) + (XY(vs[1])-vs[0]).div(2)
								p2 = XY(vs[1]) + (XY(vs[2])-vs[1]).div(2)
								p3 = XY(vs[2]) + (XY(vs[0])-vs[2]).div(2)
								pnts = [p3.co,(p1-p3).co,((p2-p1)-p3).co]
							if tritype == "circi" or tritype == "circe":
								if tritype == "circi":
									rad, px, py = circleInscribedInTri(vs[0], vs[1], vs[2])
								if tritype == "circe":
									rad, px, py = TriInscribedInCircle(vs[0], vs[1], vs[2])
								nn = svgCircle(node.getparent(), rad, px, py)
								self.estilo(nn,node)
								pnts=[]
								if deleteorigin: node.getparent().remove(node)
		if sh=="arches":
			self.arches(sO, node)
			pnts = []
		if sh=='nodes':
			# get verts
			obj, posh, posv, objS, oY, reducey =(sO.obj, int(sO.posh), int(sO.posv), sO.objsize, sO.ordery, sO.reducey)
			o2 = objS / 2.0
			pnts = []
			vs = self.parsePath(node,obj in ["def","tabs"])
			if len(vs)==0: return
			#----------------------------------------------
			grp = addChild(node.getparent(), 'g',{})
			self.copyProp(node, grp, 'transform')
			self.estilo(grp, node)
			if obj=="def" or obj=="tabs":
				dS = ""
				if obj=="def":
					for vsA in vs:
						vs = [XY(p[0],p[1]) for p in vsA]
						if (sO.reverse): vs.reverse()
						dS = dS + self.deflate(vs,objS,grp)
				#	addChild(grp, 'path',{'d': dS,'id':obj})
				if obj=="tabs":
					tH, tW = (self.getU(sO.objsize), self.getU(sO.tabsize))
					for vsA in vs:
						dSA = ""
						vs = [XY(p[0],p[1]) for p in vsA]
						if (sO.reverse): vs.reverse()
						for n in range(0,len(vs)):
							nxt = 0 if (n==len(vs) - 1) else n + 1
							p1, p2 = (vs[n], vs[nxt])
							if (p1!=p2):
								n4 = XY(p1).normal(p2).mul(tH)
								p1b = XY(p1.x - n4.y, p1.y + n4.x)
								p2b = XY(p2.x - n4.y, p2.y + n4.x)
								d1u = XY(p1b).unitVec(p2b).mul(tW)
								d2u = XY(p2b).unitVec(p1b).mul(tW)
								dSA = dSA + p1.st() + " " + (p1b+d1u).st() + " " + (p2b+d2u).st() + " "
						dS = dS + "M" + dSA + "z "
				if deleteorigin: node.getparent().remove(node)
				addChild(grp,'path',{'d':dS, 'id':obj})
				return

			vsY = [item[1] for item in vs]
			vsY.sort()
			minY, maxY = (vsY[0], vsY[-1])
			vs = [XY(p[0],p[1]) for p in vs]
			if (sO.reverse): vs.reverse()
			dist = maxY - minY

			if obj == "obj":
				oi = sO.objid
				este = self.svg.getElementById('%s' % oi)
				if este == None:
					obj='c'
				else:
					t1, r1, b1, l1, an1, al1 = self.limits(este)
					w2, h2 = (an1/2 , al1/2)

			orderY = []
			for n in range(0,len(vs)):
				if obj=="obj":
					if este != None:
						reduce = (100 - (reducey * ((maxY - vs[n].y) / dist)))/100
						px = str(vs[n].x / reduce - l1 - w2 + w2 * posh)
						py = str(vs[n].y / reduce - t1 - h2 + h2 * posv)
						nn = addChild(grp,'use',{inkex.addNS('href',"xlink"):"#"+oi,'x':px,'y':py, "transform":"scale(%f)" % (reduce)})
					else:
						obj='c'
				reduce = (o2 / 100 * reducey) * (maxY - vs[n].y) / dist
				O2 = o2 - reduce
				if obj=="c":
					pxy = vs[n] + XY(posh, posv).mul(O2)
					nn = svgCircle(grp, O2, pxy.x, pxy.y)
				if obj=="s":
					pxy = vs[n] - XY(O2) + XY(O2 * posh, O2 * posv)
					nn = addChild(grp,'rect',{'height':str(O2*2), 'width':str(O2*2), 'x':str(pxy.x), 'y':str(pxy.y)})
				if obj=="number":
					nn = self.addTxt(grp, str(vs[n].x), str(vs[n].y), str(n+1))
				if obj=="coords":
					maxDec=sO.maxdecimals
					nn = self.addTxt(grp, str(vs[n].x), str(vs[n].y), str(round(vs[n].x, maxDec)) + "," + str(round(vs[n].y, maxDec)))			
				if obj!="def" and obj!="tabs": orderY.append([vs[n].y,nn])
				#self.estilo(nn,node)
			if oY:
				def myFunc(e):
					return e[0]
				orderY.sort(key=myFunc)
				for item in orderY:
					grp.append( item[1])
			#---------------------------------
			if deleteorigin: node.getparent().remove(node)
			# ##############################3

		d = ""
		if len(pnts)>0:
			for n in pnts:
				if len(n)==1:
					d+=n[0]
				else:
					ss = "" if len(n)<3 else n[2]
					d += "%s%s,%s " % (ss, str(n[0]),str(n[1]))
			nn = self.addEle('path',pp, {'d':dS % (d)})
			self.estilo(nn,node)
			if deleteorigin: node.getparent().remove(node)

	def arches(self, sO, node):
		rMay, rMin, type, helpbuild, archfoils =(self.getU(float(sO.archmax)), self.getU(float(sO.archmin)), sO.arch, sO.helpbuild,int(sO.archfoils) )
		t, r, b, l, an, al = self.limits(node)
		an2 = an / 2.0
		rSub, rAdd = (rMay - rMin, rMay + rMin)
		pp = node.getparent()
		spts=""
		
		grp = addChild(node.getparent(), 'g',{"style":"stroke-dasharray:1, 1;fill:none;stroke:#000;stroke-width:0.1"})
		#grp = addChild(node.getparent(), 'g',{})
		if type=="3c":
			if rSub < 0:
				info("archmax (%f) must be greater than the object width (%f)" % (rMay,an2))
				return
			catA = an2 - rMin
			if catA > rSub:
				# info("math.asin(%f/%f)" % (catA, rSub))
				return
			rot = math.degrees(math.asin(catA/rSub))
			cat = triCat(rSub, catA)

			if helpbuild:
				svgCircle(grp,rMay, an2 + l,t + rMay)
				svgCircle(grp,rMin, l + rMin,t + rMay - cat)
				svgCircle(grp,rMin, l + an - rMin,t + rMay - cat)
			sss = svgArc(l + rMin,t + rMay - cat, rMin, rMin, 0, 90 - rot, 180,"L") #arco peq izda
			sss += svgArc(l + an2,t+rMay, rMay, rMay, 0, rot*2, 270 - rot,"L",1) # arco grande centro
			sss += svgArc(l + an - rMin,t + rMay - cat, rMin, rMin, 0, 90 - rot, -(90 - rot),"L",1) #arco peq der
			spts = "M%s %s %s %s" % (XY(r,b), XY(l,b), sss,"Z")
		if type == "rnd":
			if helpbuild: svgCircle(grp,an2, an2 + l,t + an2)
			spts = "M%s %s %s %s" % (XY(r,b), XY(l,b), svgArc(l + an2,t + an2, an2, an2, 0, 180, 180,"L"),"Z")
		if type=="segmental":
			if helpbuild: svgCircle(grp, rMay, l + an2, t + rMay)
			if (rMay < an2):
				info("Major radius (%f) must be greater than the half of the object width (%f)" % (rMay,an2))
			else:
				rot = math.degrees(math.asin(an2/rMay))
				sss = svgArc( l + an2, t + rMay, rMay, rMay, 270 - rot, rot * 2, 0, "L") #arco peq izda		
				spts = "M%s %s %s %s" % (XY(r,b), XY(l,b), sss,"Z")

		if type == "horseshoe":
			if helpbuild: svgCircle(grp, an2, l + an2, t +an2)
			h = al - an2
			rot = 90 - math.degrees(math.acos(rMin/h))
			spts = "M%s %s %s %s" % (XY(r-rMin,b), XY(l+rMin,b), svgArc(l + an2, t + an2, an2, an2, 180 - rot, 180 + rot * 2, 0,"L"),"Z")
			if (rMay < an2):
				info("archmax must be greater than the object width "+str(rMay)+"_"+str( an2 ) )
		if type=="roundedhorseshoe":
			cat = an2-rMin
			rot = math.degrees(math.asin(cat/an2))
			sss = svgArc(l + an2, t + an2, an2, an2, rot, 90 - rot, 90,"L") 
			sss += svgArc(l + an2, t + an2, an2, an2, 0, 180 + 90 - rot, 180,"L",1)
			spts = "M%s %s %s %s" % (XY(r-rMin,b), XY(l+rMin,b), sss,"Z")
			if (rMay < an2):
				info("archmax must be greater than the object width "+str(rMay)+"_"+str( an2 ) )  		
		if type=="roundrampant":
			r2 = an-rMay
			sss = svgArc(l + rMay, t + rMay, rMay, rMay, 0,90, 180,"L") 
			sss += svgArc(l + rMay, t + r2, r2, r2, 0, 90, 270,"L",1)
			spts = "M%s %s %s %s" % (XY(r,b), XY(l,b), sss,"Z")
			if (rMay < an2):
				info("archmax must be greater than the object width "+str(rMay)+"_"+str( an2 ) )
		if type=="trefoil":
			r4 = an / 4.0
			sss = svgArc(l + r4, t + an2, r4, r4, 180, 90, 0,"L") 
			sss += svgArc(l + an2, t + r4, r4, r4, 180, 180, 0,"L",1)
			sss += svgArc(r - r4, t + an2, r4, r4, 270, 90, 0,"L",1)
			spts = "M%s %s %s %s" % (XY(r,b), XY(l,b), sss,"Z")

		if type=="reverseogee":
			if (rMay+rMin < an2):
				rMay = an2 - rMin
				rAdd = an2
				info("Radius major changed to "+str(rMay))
			cat = triCat(rAdd, an2)
			rot = math.degrees(math.asin(cat/rAdd))
			addChild(grp, 'path',{"d":"M" + XY(l, t -(cat-rMay)).st()+"L"+ XY(l + an2, t + rMay).st()+" "  + XY(r, t -(cat-rMay)).st()})
			sss = svgArc(l, t -(cat-rMay), rMin, rMin, 0, rot-90, -270,"L")
			sss += svgArc(l + an2, t + rMay, rMay, rMay, 270 - rot ,90, 0,"L",1) 
			sss += svgArc(r, t -(cat-rMay), rMin, rMin, 90,0, 0,"L",1)
			spts = "M%s %s %s %s" % (XY(r,b), XY(l,b), sss,"Z")
				#     270
				# 180     0
				#      90 	

		if type=="threepointed":
			cat = math.sqrt(an*an- an2*an2)
			sss = svgArc(r, t +cat , an, an, 180, 60, 0,"L")
			sss += svgArc(l, t + cat, an, an, 270 +30,60, 0,"L",1) 
			spts = "M%s %s %s %s" % (XY(r,b), XY(l,b), sss,"Z")

		if type == "multifoil":
			foils = archfoils
			sss = ""
			rRot = 180 / ((foils-1) * 2)
			p1 = XY(an2,0).rotateD(rRot)
			pp1 = p1.y * ((an2 * an2) / (an2 * p1.x + an2 * p1.y))
			for i in range(foils):
				rot =  rRot * 2 * i
				tP = XY(an2 - pp1,0).rotateD( rot + 180) + XY(l, t) + an2 #+ XY( l + an2, t + an2)
				if i==0:
					sss += svgArcXY(tP, pp1, 180, 270, 0, "L")
				elif i==foils-1:
					sss += svgArcXY(tP, pp1, 270, 360, 0, "L", 1)
				else:
					sss += svgArcXY(tP, pp1, 180 + rot, 270 + rot, 0, "L", 1) 
			spts = "M%s %s %s %s" % (XY(r,b), XY(l,b), sss,"Z")
		if type == "ogee":
			hipo = an2+rMin
			cat = math.sqrt(hipo*hipo - rMin*rMin)
			rot = math.degrees(math.asin(rMin/hipo))
			sss = ""
			cx, cy, trY = (l+an2, t+an2, cat - an2)
			sss += svgArcXY(XY(cx, cy + trY), an2, 180, 270-rot , 0, "L")
			sss += svgArcXY(XY(cx-rMin, cy  - cat + trY), rMin, 180+rot, 180,180, "M", 1)
			sss += svgArcXY(XY(cx+rMin, cy  - cat + trY), rMin, 270, 180-(90-rot), 0, "L", 1)
			sss += svgArcXY(XY(cx, cy + trY), an2, 270+rot ,360, 0, "L")												

			spts = "M%s %s %s %s" % (XY(r,b), XY(l,b), sss,"Z")

		if spts!="":
			self.estilo(self.addPath(pp,{'d':spts}),node)
		if sO.deleteorigin: node.getparent().remove(node)

	def makeRel(self,arr):
		b = arr[:]
		for n in range(1,len(arr)):
			s = b[n]
			for i in range(0,n):
				s = s - arr[i]
			b[n] = s
		return b

	def circle(self,p,r):
		varBez = 0.551915024494
		aa = r * varBez
		d=""
		pnts=[[p.x - r,p.y],[0,aa,"c "],[r - aa,r],[r,r],[aa,0,"c "],[r,-r+aa],[r,-r],[0,-aa,"c "],[-r+aa,-r],[-r,-r],[-aa,0,"c "],[-r,r-aa],[-r,  r]]
		for n in pnts:
			ss = "" if len(n)<3 else n[2]
			d += "%s%s,%s " % (ss, str(n[0]),str(n[1]))
		return d

	def addTxt(self, node, x, y, text, dy = 0):
		new2 = self.addEle(inkex.addNS('text','svg'), node,{'x':str(x),'y':str(y)})
		new = etree.SubElement(new2, inkex.addNS('tspan','svg'), {inkex.addNS('role','sodipodi'): 'line'})
		new.text = str(text)
		new2.set('style','text-align:center; vertical-align:bottom; font-size:%s; fill-opacity:1.0; stroke:none; font-weight:normal; font-style:normal; fill:#000000' % self.options.fntsize)
		new.set('dy', str(dy))
		return new2

	def joinCircles(self, sels, sh='rombus'):
		sO = self.options
		deleteorigin, joincirctype, r2, onlyrect= (sO.deleteorigin, sO.joincirctype, sO.joinradius, sO.joincircleonlyrect)

		for nodos in range(len(sels)-1):
			node = sels[nodos]
			node2 = sels[nodos+1]
			tA, rA, bA, lA, anA, alA = self.limits(node)
			tB, rB, bB, lB, anB, alB = self.limits(node2)
			rA, cY = (anA/2.0,alA/2.0)
			rB, cY2 = (anB/2.0,alB/2.0)

			PtA = XY(lA + rA, tA + cY)
			PtB = XY(lB + rB, tB + cY2)
			idBase = "joincircles_"
			if (circleInCircle(PtA,rA,PtB,rB) or circleInCircle(PtB,rB,PtA,rA)):
				pass
			else:
				pp = node.getparent()
				rotAB = XY(PtB).getAngle(PtA)
				rAB = math.degrees(rotAB)
				dist = PtA.hipo(PtB)
				if joincirctype=='tangentinside':
					cat = rA + rB
					hipo = dist
					catH =cat/hipo
					if (catH>1): catH = catH-1
					rot = 90 - math.degrees(math.asin(catH))
					if onlyrect:
						pnts = "M" + (XY(rA, 0).rotateD(360-rot+180+rAB)+XY(PtA)) + " " + (XY(rA, 0).rotateD(rot+180+rAB)+XY(PtA)) + " "
						pnts += (XY(rB, 0).rotateD(-360+rot+rAB)+XY(PtB)) + " " + (XY(rB, 0).rotateD(-rot+rAB)+XY(PtB)) + " "
					else:
						pnts = svgArcXY(PtA, rA, rot, 360-rot, 180+rAB) + svgArcXY(PtB, rB, -rot, -180, rAB,"L")  + svgArcXY(PtB, rB, -180, -360+rot, rAB,"",1) 		
					self.estilo(self.addEle('path',pp, {'d':"%sZ" % (pnts),"id":idBase + "tangentinside"}),node)
				if joincirctype=='tangent':
					# alineamos las esferas en Y
					# tangentes externas
					rDif = rA - rB
					Axis = XY(-rDif,0)
					D2 = triCat(dist, rDif) / dist
					P1 = XY(Axis).mul(rA / dist)
					P2 = XY(-dist,0) + XY(Axis).mul(rB / dist)
					r = P1.VDist(P2)
					Rot1 = XY(P2.x,rB * D2).getAngleD(XY(P2.x + r, rA * D2))
					if onlyrect:
						ppp = "M"+ (XY(rA, 0).rotateD(rAB -90-Rot1)+XY(PtA)) +" "+ (XY(rA, 0).rotateD(rAB +90+Rot1)+XY(PtA)) + " "
						ppp += (XY(rB, 0).rotateD(rAB +90+Rot1)+XY(PtB)) +" "+ (XY(rB, 0).rotateD(rAB +270-Rot1)+XY(PtB))
					else:
						ppp = svgArcXY(PtA, rA, rAB -90 -Rot1, rAB+90 + Rot1, 0) + svgArcXY(PtB, rB, rAB+90+Rot1, rAB+270-Rot1, 0,"L")
					self.estilo(self.addEle('path',pp, {'d':"%sZ" % (ppp)}),node)
				# ################## B L O B ##############
				if joincirctype=='blob':
					if ((r2==0) and (dist<(rA+rB))):
						r2 = dist - rB
					if (r2 > 0):
						rad1 = rA + r2
						rad2 = rB + r2
						a = ( pow2(dist) - pow2(rB+r2) + pow2(rA+r2))/(dist*2)
					else:
						r2 = dist - rA - rB
						rad1 = dist - rB
						rad2 = dist - rA
						a = (pow2(dist-rB) - pow2(dist-rA) + pow2(dist))/(dist*2)
					# alineamos las esferas en Y
					rt = math.atan2(PtB.y - PtA.y, PtB.x - PtA.x)
					# # distancia del centro 1 a la interseccion de los circulos
					x = (dist * dist - rad2 * rad2 + rad1 * rad1) / (dist*2)
					if (rad1 * rad1 - x * x) > 0 :
						catB = triCat(rad1, x)
						rt = XY().getAngleD(XY(-x, -catB))
						rt2 = XY().getAngleD(XY(-(dist - x), -catB))
						c1 = XY(-x,catB).rotateD(rAB)+PtA
						c4 = XY(-x,-catB).rotateD(rAB) + PtA
						if onlyrect:
							arcs = svgArcXY(c1,r2,180 - rt + rAB, rt2 + rAB,0)
							arcs += svgArcXY(c4,r2,-rt2 + rAB,180 + rt +rAB,0,"L")
						else:
							arcs = svgArcXY(PtA,rA,rAB+rt,rAB+rt-rt*2,0) + svgArcXY(c1,r2,180 - rt + rAB, rt2 + rAB,0,"L",1)
							arcs += svgArcXY(PtB,rB,rt2 + 180 + rAB,180 - rt2 + rAB,0,"L",1) + svgArcXY(c4,r2,-rt2 + rAB,180 + rt +rAB,0,"L",1)
						self.estilo(self.addEle('path',pp,{'d':"%sZ" % (arcs)}),node)
				# ################## O V A L #####################
				if joincirctype=='oval':
					minR2 = dist + min(rA,rB)
					if r2 < minR2:
						r2 = minR2
						info('Changed radius to '+str(minR2))
					rad1 = r2 - rA
					rad2 = r2 - rB
					a = ( pow2(dist) - pow2(rB+r2) + pow2(rA+r2))/(dist*2)

					rt = math.atan2(PtB.y - PtA.y, PtB.x - PtA.x)
					D = dist # distancia entre los centros
					# distancia del centro 1 a la interseccion de los circulos
					x = (dist*dist - rad2*rad2 + rad1*rad1) / (dist*2)
					catB = triCat(rad1, x)

					rotAB = XY(PtB).getAngle(PtA)
					rot1 = XY().getAngleD(XY(-x,-catB)) + 180.0
					rot2 = XY(-dist,0).getAngleD(XY(-x,-catB)) + 180.0

					rot3 = - XY(-dist,0).getAngleD(XY(-x,-catB))
					if onlyrect:
						#arcs = svgArcXY(PtA,rA,rAB-rot1,rot1+rAB,0) 
						arcs = svgArcXY(XY(-x,-catB).rotateD(rAB)+PtA,r2,rAB+rot1,rAB+rot2,0)#,"L",1)
						#arcs += svgArcXY(XY(-dist,0).rotateD(rAB)+PtA, rB, -rot3, rot3, 180+rAB,"L",1)
						arcs += svgArcXY(XY(-x,catB).rotateD(rAB)+PtA,r2,rAB-rot2,rAB-rot1,0,"L")
						arcs+="Z"
					else:
						arcs = svgArcXY(PtA,rA,rAB-rot1,rot1+rAB,0) 
						arcs += svgArcXY(XY(-x,-catB).rotateD(rAB)+PtA,r2,rAB+rot1,rAB+rot2,0,"L",1)
						arcs += svgArcXY(XY(-dist,0).rotateD(rAB)+PtA, rB, -rot3, rot3, 180+rAB,"L",1)
						arcs += svgArcXY(XY(-x,catB).rotateD(rAB)+PtA,r2,rAB-rot2,rAB-rot1,0,"L",1)
					nn = self.addEle('path',pp,{'d':arcs,"style":"fill:#c0f;stroke:#00f"})
					self.estilo(nn,node)

				if deleteorigin: node.getparent().remove(node)

	def drawArrow(self, sO, an, al, l, t):
		arrowType = sO.arrowtype
		headH, headW, arrowW = (self.getU(sO.headHeight), self.getU(sO.headWidth), self.getU(sO.arrowWidth))
		hw2=headW/2.0
		cX = an/2.0
		if arrowType=="arrowfilled":
			pnts=[[l+cX,t],[hw2,headH],[-(headW-arrowW)/2.0,0],[0,al-headH],[-arrowW,0],[0,-(al-headH)],[-(headW-arrowW)/2.0,0]]
		else:
			#dS = "m %s"
			pnts=[[l+cX,t],[0,al],[-hw2,-al+headH,"m "],[hw2,-headH],[hw2,headH]]
		return pnts

	def spikesLinear(self, spktype, spikesdir, sDir, an, ss, sh, ssep, rot = 0):
		anX = int( (an + ssep) / (ss * 2 + ssep))
		iniX = ((an+ssep) - (anX * (ss * 2 + ssep))) / 2.0
		if spktype=="trirect" or spktype=="squ":
			anX = int((an + ssep) / (ss + ssep))
			iniX = ((an + ssep) - (anX * (ss + ssep))) / 2.0

		pnts = [[iniX,0]]
		if sDir=='pre': sDir = spikesdir
		if sDir=='non' or sDir=="void":
			if sDir=='non':
				pnts = [[an,0]]
			else:
				pnts = [[an,0,'m']]
		else :
			dirT = 1
			if sDir=='ins': dirT = -1.0
			if spktype=="tab":
				pnts = [[ss,-sh*dirT],[an - ss*2,0],[ss, sh*dirT]]
			else:
				for n in range(anX):
					if sDir=='alt' : dirT = 1 if n % 2 == 1 else -1
					if spktype=="tri":     pnts.extend([[ss,-sh*dirT],[ss,sh*dirT]])
					if spktype=="trirect": pnts.extend([[0,-sh*dirT],[ss,sh*dirT]])
					if spktype=="squ":     pnts.extend([[0,-sh*dirT],[ss,0],[0,sh*dirT]])
					if ssep != 0 and n < (anX-1): pnts.append([ssep,0])
				pnts.append([iniX,0])
		if rot != 0 :
			pnts = rotList(pnts, rot)
		return pnts

	def spikesRound(self, spktype, spikesdir, sDir, an, ss, sh, ssep, rot = 0):
		anX = int( (an + ssep) / (ss * 2 + ssep))
		iniX = ((an+ssep) - (anX * (ss * 2 + ssep))) / 2.0
		varBez = 0.551915024494
		pnts = [[iniX,0]]
		dif, difh, dBez, dBezh = (ss-(ss*varBez), sh-(sh*varBez), ss*varBez, sh*varBez)
		if sDir=='pre': sDir = spikesdir
		if sDir=='non' or sDir=="void":
			if sDir=='non':
				pnts = [[an,0]]
			else:
				pnts = [[an,0,'m']]
		else :
			dirT = -1.0 if sDir=='ins' else 1.0
			for n in range(anX):
				if sDir=='alt' : dirT = 1 if n % 2 == 1 else -1
				if spktype == "rnd": pnts.extend([[0,-dBezh*dirT," c"],[dif,-sh*dirT],[ss,-sh*dirT],[dBez,0],      [ss,difh*dirT],[ss,sh*dirT]]) #fijo
				if spktype == "wav": pnts.extend([[0,-dBezh*dirT," c"],[dif,-sh*dirT],[ss,-sh*dirT],[0,dBezh*dirT],[dBez,sh*dirT],[ss,sh*dirT]]) #fijo
				if ssep!=0 and n < (anX-1): pnts.append([ssep,0,' l'])
			pnts.extend([[iniX,0,' l']])

		if rot != 0 :
			pnts = rotList(pnts, rot)
		return pnts

	def triSpikes(self, sO, an, al, l, t):
		spktype, spikesdir, sh, ssep = (sO.spikestype, sO.spikesdir, sO.spikeheight, self.getU(sO.spikesep))
		ss = self.getU(sO.spikesize)
		anX, anY = (int( (an + ssep) / (ss * 2 + ssep)), int( (al+ssep) / (ss * 2 + ssep)))
		iniX, iniY = (((an+ssep) - (anX * (ss * 2 + ssep))) / 2.0, ((al+ssep) - (anY * (ss * 2 + ssep))) / 2.0)
		if spktype=="trirect" or spktype=="squ":
			anX, anY = ( int((an + ssep) / (ss + ssep)), int((al + ssep) / (ss + ssep)) )
			iniX, iniY = (((an + ssep) - (anX * (ss + ssep))) / 2.0, ((al + ssep) - (anY * (ss + ssep))) / 2.0)
		dir = 1
		pnts = [[l,t],[iniX,0]]

		if spikesdir=='ins': dir = -1.0
		# 2020_12_29 - New: tab
		dirs = [sO.spikesdirt, sO.spikesdirr, sO.spikesdirb, sO.spikesdirl] # -- TOP    --# -- RIGHT  --# -- BOTTOM --# -- LEFT   --
		sizes = [an, al, an, al]
		pnts = [[l,t]]
		if spktype in ["tab", "tri", "trirect", "squ"]:
			for n in range(4):
				pnts.extend(self.spikesLinear(spktype, spikesdir, dirs[n], sizes[n], ss, sh, ssep, n*90))
		if spktype in ["rnd", "wav"]:
			for n in range(4): pnts.extend(self.spikesRound(spktype, spikesdir, dirs[n], sizes[n], ss, sh, ssep, n*90))
		return pnts # 805

	def draw_shapes(self):
		sels = []
		for id, node in self.svg.selected.items(): sels.append(node)
		tab = str(self.options.tab)
		if tab != 'extra':
			for node in sels:
				self.draw(node, tab)
		else:
			Type = str(self.options.joincirctype)
			if len(sels)<2:
				inkex.errormsg('Select at least two objects')
			else:
				self.joinCircles(sels, Type)

	def parsePath(self, node, separate=False):
		vs = []
		part = []
		if node.get('d'):
			p = node.path.to_arrays()
			prev = [0, 0]
			for cmd, params in p:
				if cmd != 'Z' and cmd != 'z':
					#posY = prev[1]
					posX = prev[0]
					posY = params[-1]
					if cmd in ['h','H']:
						posY = prev[1]
						posX = params[-1]
					elif cmd not in ['v','V','h','H']:
						posX = params[-2]
					if not [posX, posY] in part:
						part.append([posX, posY])
					prev = [posX, posY]
				else:
					if separate:
						vs.append(part)
						part = []
			if separate:
				if len(part)>0:
					vs.append(part)
			else:
				vs=part
		return vs

	def loc_str(self, str):
		return locale.format("%.f", float(str), 0)

	def effect(self):
		self.draw_shapes()

if __name__ == "__main__":
	e = Shapes()
	e.run()
# 576, 545, 537, 507 790, 30.174, 925, 962
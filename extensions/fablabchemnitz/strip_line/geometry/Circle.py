#!/usr/bin/env python3

import math
import inkex
from lxml import etree

class Circle():
	def __init__(self,_c,_r):
		self.radius=_r
		self.center=_c
        
	def __str__(self):
		return "Circle: center:"+str(self.center)+" radius:"+str(self.radius)+"\n"
        
	def __repr__(self):
		return "Circle: center"+str(self.center)+" radius:"+str(self.radius)+"\n"
        
	def isHit(p):
		distance=(center-p).length()
		if(distance<radius):
			return True
		return False

	@classmethod
	def toSVGObject(cls,x,y,r,color,strokewidth):
		att={"cx":str(x),"cy":str(y),"r":str(r),"fill":color,"stroke-width":str(strokewidth)}
		return etree.Element("circle",att)

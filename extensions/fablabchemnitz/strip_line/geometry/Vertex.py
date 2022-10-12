#!/usr/bin/env python3

import math

class Vertex():
	post=None
	pre=None
	def __init__(self,_x,_y):
		self.x=_x
		self.y=_y
        
	def __sub__(self,r):
		return Vertex(self.x-r.x,self.y-r.y)
        
	def __str__(self):
		return "("+str(self.x)+","+str(self.y)+")"
        
	def __repr__(self):
		return "("+str(self.x)+","+str(self.y)+")"
        
	def __eq__(self,p):
		return (self.x==p.x) and (self.y==p.y)
        
	def __add__(self,p):
		return Vertex(self.x+p.x,self.y+p.y)
        
	#inner product
	def dot(self,p):
		return self.x*p.x+self.y*p.y
        
	def cross(self,p):
		return self.x*p.y-self.y*p.x
        
	def length(self):
		return math.hypot(self.x,self.y)
        
	def rotate(self,radian):
		originalX=self.x
		self.x=self.x*math.cos(radian)-self.y*math.sin(radian)
		self.y=originalX*math.sin(radian)+self.y*math.cos(radian)
        
	def set(self,_x,_y):
		self.x=_x
		self.y=_y
        
	def set(self,p):
		self.x=p.x
		self.y=p.y
        
		#SVG for output
	def toSVG(self):
		return str(self.x)+","+str(self.y)

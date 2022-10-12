#!/usr/bin/env python3

class Triangle():
	#given segment
	def __init__(self,_a,_b,_c):
		self.a=_a
		self.b=_b
		self.c=_c
        
	def __repr__(self):
		return "Triangle:("+str(self.a)+","+str(self.b)+","+str(self.c)+")"
        # Center of gravity centered on #a
        # @return u how much to b
        # @return v how much in the c direction
    
	def barycentric(self,p):
		#How to use barycentric coordinates
		#http://www.blackpawn.com/texts/pointinpoly/default.html
		ca = self.c-self.a
		ba = self.b-self.a
		pa = p-self.a

		#Calculate dot product
		dotca = ca.dot(ca)
		dotcba = ca.dot(ba)
		dotcpa = ca.dot(pa)
		dotba = ba.dot(ba)
		dotbpa = ba.dot(pa)

		#Calculation of barycentric coordinates
		invDenom = 1 / (dotca * dotba - dotcba * dotcba);

		u = (dotba * dotcpa-dotcba*dotbpa)*invDenom
		v = (dotca * dotbpa - dotcba * dotcpa) * invDenom
		return u,v
        
	# Whether there is a point inside the triangle
	def isContain(self,p):
		u,v=self.barycentric(p)
		inkex.errormsg("\n u="+str(u)+" v="+str(v))
		If #u=v=0, the same point as the triangle point
		#Check if there is a point in the triangle
		return (u > 0) and (v > 0) and (u + v < 1)
        
	def toSVG(self):
		return str(self.a.x)+","+str(self.a.y)+","+str(self.b.x)+","+str(self.b.y)+","+str(self.c.x)+","+str(self.c.y)
	# Is the arrangement of vertices a, b, c clockwise?
    
	def isClockWise(self):
		circle=self.circumcircle()
		center=circle.center
		aTob=self.b-self.a
		aToc=self.c-self.a
		#Let's find the cross product
		cross=aTob.cross(aToc)

		inkex.errormsg(" cross"+str(cross))
		if(cross>0):
			return True
		return False#Counterclockwise
        
	def circumcircle(self):
		#Find the length of each side
		ab=(self.a-self.b).length()
		bc=(self.b-self.c).length()
		ca=(self.c-self.a).length()
		s=(ab+bc+ca)/2.0;
		area=math.sqrt(s*(s-ab)*(s-bc)*(s-ca));
		maxlength=0
		if(maxlength<ab):
			maxlength=ab;longestEdge=2
		if(maxlength<bc):
			maxlength=bc;longestEdge=0;
		if(maxlength<ca):
			maxlength=ca;longestEdge=1

		if longestEdge==0:
				ha=2*area/bc;
				angleB=math.asin(ha/ab);
				angleC=math.asin(ha/ca);
				angleA=math.pi-angleB-angleC;
		if longestEdge== 1:
				hb=2*area/ca;
				angleA=math.asin(hb/ab);
				angleC=math.asin(hb/bc);
				angleB=math.pi-angleC-angleA;
		if longestEdge== 2:
				hc=2*area/ab;
				angleB=math.asin(hc/bc);
				angleA=math.asin(hc/ca);
				angleC=math.pi-angleA-angleB;

		A = math.sin(2.0*angleA);
		B = math.sin(2.0*angleB);
		C = math.sin(2.0*angleC);
		center=Vertex((self.a.x * A + self.b.x * B + self.c.x * C) / (A+B+C),
			(self.a.y * A + self.b.y * B + self.c.y * C) / (A+B+C));
		rad=bc / math.sin(angleA) / 2.0
		return Circle(center,rad);

#!/usr/bin/env python
'''
shapes_1.py

Copyright (C) 2015-2021 Paco Garcia, www.arakne.es

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

updated for inkscape 1.0
'''
import os, sys, tempfile, webbrowser, math, inkex, simplestyle, simpletransform
from lxml import etree

def info(s, newLine="\n"):
    sys.stderr.write(s)
    sys.stderr.write(newLine)

def tern(condition,val1,val2):
    return val1 if condition else val2

def _rads(n):
    return math.radians(n)

def pow2(n):
    return math.pow(n, 2)

# calcula la hipotenusa dados los catetos
def triHipo(catA, catB):
    return math.sqrt(pow2(catA) + pow2(catB))

# calcula el cateto dada la hipotenusa y el otro cateto
def triCat(Hipo, catA):
    return math.sqrt(pow2(Hipo) - pow2(catA))

class XY:
    """A class for work with 2d points"""
    def __init__(self, *args, **kwargs):
        self.co = [0.0,0.0]
        self.s = ""
        lArgs=len(args)
        Args = list(args)
        if lArgs>0:
            for n in Args:
                if type(n)==str:
                    self.s = n
                    Args.remove(n)
            if lArgs==1:
                if type(Args[0])==XY:
                    self.co = Args[0].co
                else:
                    self.co = [Args[0],Args[0]]
            if lArgs>1:
                self.co = [Args[0],Args[1]]

    def __add__(self,xy):
        if type(xy)==str:
            return str(self) + xy
        if type(xy)==float or type(xy)==int:
            self.co = [self.co[0] + xy,self.co[1] + xy]
        else:
            self.co = [self.co[0] + xy.co[0],self.co[1] + xy.co[1]]
        return self

    def __radd__(self, xy):
        if type(xy)==str:
            return xy + str(self)

    def __sub__(self,xy):
        self.co=[self.co[0] - xy.co[0], self.co[1] - xy.co[1]]
        return self
    def __eq__(self, xy):
        return (self.co[0] == xy.x and self.co[1] == xy.y)
    def __str__(self):
        return self.s + str(self.co[0])+','+str(self.co[1])

    def sub(self,xy):
        self.__sub__(xy)
        return self
    def mul(self,xy):
        if type(xy)==XY:
            co=[self.co[0] * xy.co[0],self.co[1] * xy.co[1]]
        else:
            co=[self.co[0] * xy,self.co[1] * xy]
        self.co = co
        return self

    def div(self,xy):
        if type(xy)==XY:
            co=[self.co[0] / xy.co[0], self.co[1] / xy.co[1]]
        else:
            co=[self.co[0] / xy, self.co[1] / xy]
        self.co = co
        return self

    def vlength(self):
        return triHipo(self.co[0], self.co[1])

    def normal(self,p2):
        co=[self.co[0] - p2.co[0], self.co[1] - p2.co[1]]
        self.co = co
        vlen = self.vlength()
        return self.div(vlen)

    def unitVec(self, p2):
        dif1 = [p2.x - self.x, p2.y - self.y] 
        self.co = dif1
        return self.div(self.vlength())

    def rot(self,ang):
        x,y,sa,ca= (self.co[0], self.co[1], math.sin(ang), math.cos(ang))
        self.co=[ca * x  - sa * y, sa * x + ca * y]
        return self

    def Rot(self,p,r):
        self.co=[math.cos(r)*p, math.sin(r)*p]
        return self

    def rotate(self,rot,cX=0.0,cY=0.0):
        """ Rotate XY in radians about center cX and cY"""
        cosRot = math.cos(rot)
        px = cX + (self.x-cX) * cosRot - (self.y-cY) * math.sin(rot)
        py = cY + (self.x-cX) * math.sin(rot) + (self.y-cY) * cosRot
        self.co = [px,py]
        return self

    def rotateD(self,rot,cX=0.0,cY=0.0):
        self.rotate(_rads(rot),cX,cY)
        return self

    def VDist(self,V2):
        tmp = XY(self.co[0],self.co[1])
        tmp = tmp.sub(V2)
        return tmp.vlength()

    def st(self):
        return self.s+str(self.co[0])+','+str(self.co[1])

    @property
    def x(self):
        return self.co[0]

    @property
    def sx(self):
        return str(self.co[0])

    @property
    def y(self):
        return self.co[1]

    @property
    def sy(self):
        return str(self.co[1])

    def hipo(self,xy):
        #return math.sqrt(math.pow(self.x-xy.x,2) + math.pow(self.y-xy.y,2) )
        return triHipo(self.x-xy.x, self.y-xy.y)
    def angBetween2Lines(self,p1,p2): # pC punto comun
        return math.atan2(self.y - p1.y, self.x - p1.x) - math.atan2(self.y - p2.y, self.x - p2.x)
    def getAngle(self,b):
        return math.atan2(b.y - self.y, b.x - self.x)
    def getAngleD(self,b):
        return math.degrees(math.atan2(b.y - self.y, b.x - self.x))
    # translada un punto hacia otro 
    def atPercent(self, p2, percent):
        self.co = [(p2.x - self.x) * percent + self.x,(p2.y-self.y) * percent + self.y]
        return self

    def atMid(self, p2):
        return self.atPercent(p2,0.5)

# ________________________________________________________________
# ________________________________________________________________
# ________________________________________________________________
class bezpnt(object):
    def __init__(self,pfixed=None,pprev=None,pnext=None):
        if isinstance(pfixed, list):
            self.fixed = XY(pfixed[0],pfixed[1])
        else:
            self.fixed = pfixed
        if isinstance(pprev, list):
            self.prev = XY(pprev[0],pprev[1])
        else:
            self.prev = pprev
        if isinstance(pnext, list):
            self.next = XY(pnext[0],pnext[1])
        else:
            self.next = pnext
        return

    def translate(self,x,y):
        self.fixed + XY(x,y)
        if self.prev!=None:self.prev + XY(x,y)
        if self.next!=None:self.next + XY(x,y)
        return self

    def scale(self,x=1.0,y=1.0):
        self.fixed.scale(x,y)
        if self.prev!=None:self.prev.scale(x,y)
        if self.next!=None:self.next.scale(x,y)
        return self

    def rotate(self,rot,cX=0.0,cY=0.0):
        self.fixed.rotate(rot,cX,cY)
        if self.prev!=None:self.prev.rotate(rot,cX,cY)
        if self.next!=None:self.next.rotate(rot,cX,cY)
        return sel

    def skew(self,rotx,roty,cX=0.0,cY=0.0):
        self.fixed.skew(rotx,roty,cX,cY)
        if self.prev!=None:self.prev.skew(rotx,roty,cX,cY)
        if self.next!=None:self.next.skew(rotx,roty,cX,cY)
        return self
    def copy(self,bez2):
        try:
            self.fixed=XY().copy(bez2.fixed)
            self.prev = None if bez2.prev == None else XY().copy(bez2.prev)
            self.next = None if bez2.next == None else XY().copy(bez2.next)
        except Exception:
            gimp.message(str(Exception))
        return self
    def arrXY(self):
        pts=[]
        if self.prev == None:
            pts+=self.fixed.arrXY(1)
        else:
            pts+=self.prev.arrXY(1)
        pts+=self.fixed.arrXY(1)
        if self.next==None:
            pts+=self.fixed.arrXY(1)
        else:
            pts+=self.next.arrXY(1)
        return pts
    def Prev(self):
        p = self.prev
        if p==None: p=self.fixed
        return p
    def Next(self):
        p = self.next
        if p==None: p=self.fixed
        return p
    def Fixed(self):
        return self.fixed
    def flip(self):
        p=self.prev
        n=self.next
        self.prev=n
        self.next=p

def bezs2XYList(arc1, transform = None):
    pnts=[]
    bezs=[]
    for aa in arc1:
        if aa.prev is not None: bezs.append(XY(aa.prev))
        bezs.append(XY(aa.fixed))
        if aa.next is not None: bezs.append(XY(aa.next))
    for i in range(len(bezs)):
        v = bezs[i]
        if transform: v = v + transform
        if i == 0:
            pnts.append(v)
        else:
            v2=pnts[-1]
            if (v2.x != v.x or v2.y != v.y): pnts.append(XY(v))
    return pnts

def rotList(lst, rot):
    lst2 = []
    rrot = _rads(rot)
    cosRot = math.cos(rrot)
    sinRot = math.sin(rrot)
    for n in range(len(lst)):
        x = lst[n][0]
        y = lst[n][1]
        if len(lst[n])==3:
            lst2.append([x * cosRot - y * sinRot,x * sinRot + y * cosRot, lst[n][2]])
        else:
            lst2.append([x * cosRot - y * sinRot,x * sinRot + y * cosRot])
    return lst2

def bezs2XYList_rev(arc1, transform = None):
    pnts = bezs2XYList(arc1, transform)
    pnts.reverse()
    return pnts

def XYList(lst, rot = 0.0, add = None):
    verts=[]
    for nn in range(len(lst)):
        v = lst[nn]
        if rot != 0.0: v = v.rotate(rot)
        if add: v = v + add
        verts.append([v.x,v.y])
    return verts

def XYListSt(lst, rot = 0.0, add = None):
    """ returns a list of XY as string """
    D2 = ""
    for nn in range(len(lst)):
        v = lst[nn]
        if rot != 0.0: v = v.rotate(rot)
        if add: v = v + add
        D2 += "%s%s " % (tern(nn==1,"C",""), v.st())
    return D2

def circleInCircle(c1,r1,c2,r2):
    return tern((r1 > (c1.hipo(c2) + r2)),True,False)

def svgArc_fMatrixTimes(a, b):
    return XY(a[0][0] * b[0] + a[0][1] * b[1], a[1][0] * b[0] + a[1][1] * b[1])

def svgArcRad(cX,cY, rx, ry, sweepStart, sweepDelta, rot,firstCmd="M",skipFirst=0):
    cosx = math.cos(rot)
    sinx = math.sin(rot)
    rotMatrix = [[cosx, -sinx], [sinx, cosx]]
    delta = sweepDelta % (2 * math.pi)
    sss = svgArc_fMatrixTimes(rotMatrix, [rx * math.cos(sweepStart), ry * math.sin(sweepStart)])+ XY(cX, cY)
    eee = svgArc_fMatrixTimes(rotMatrix, [rx * math.cos(sweepStart + sweepDelta), ry * math.sin(sweepStart + sweepDelta)]) + XY(cX, cY)
    fA = "1" if (sweepDelta > math.pi) else "0"
    fS = "1" if sweepDelta > 0 else "0"
    ini = firstCmd + sss.st() if skipFirst==0 else ""
    return ini + "A%s %s %s %s %s %s" % (rx, ry, rot / math.pi * 180.0, fA, fS, eee.st())

def svgArc(cX,cY, rx, ry, sweepStart, sweepDelta, rot,firstCmd="M",skipFirst=0):
    return svgArcRad(cX,cY, rx, ry, _rads(sweepStart), _rads(sweepDelta), _rads(rot),firstCmd,skipFirst)

def svgArcXY(cXY, r, sweepStart, sweepDelta, rot,firstCmd="M",skipFirst=0):
    return svgArc(cXY.x,cXY.y, r, r, sweepStart, sweepDelta - sweepStart, rot,firstCmd,skipFirst)

def svgArcXYRad(cXY, r, sweepStart, sweepDelta, rot,firstCmd="M",skipFirst=0):
    return svgArcRad(cXY.x,cXY.y, r, r, sweepStart, sweepDelta - sweepStart, rot,firstCmd,skipFirst)

def polar2cartesian(cXY, rad, ang):
    return XY(cXY) + XY(rad * math.cos(ang), rad * math.sin(ang))

def setArc(xy, rad, ang1, ang2, first, direct="0"):
    start = polar2cartesian(xy, rad, ang2)
    end   = polar2cartesian(xy, rad, ang1)
    arcSweep = "0" if ((ang2 - ang1) <= 180) else "1"
    # rX,rY rotation, arc, sweep, eX,eY
    d = " A%f,%f 0 %s %s %s" % (rad, rad, arcSweep, direct, end.st())
    if first == 1:
        d = "M" + start.st() + " " + d
    return d

def addChild(padre, type, props):
    hijo = etree.SubElement(padre, inkex.addNS(type,'svg'))
    for n in props:
        hijo.set(n,props[n])
    return hijo

def svgCircle(padre, r, cx, cy):
    return addChild(padre,'circle' ,{'r':str(r), 'cx': str(cx), 'cy': str(cy)})

def circleInscribedInTri(p1,p2,p3):
    d1, d2, d3 = [n.vlength() for n in [XY(p3)-p2, XY(p1)-p3, XY(p2)-p1]]
    p = d1 + d2 + d3
    centro = XY( (p1.x*d1 + p2.x*d2 + p3.x*d3) / p, (p1.y*d1 + p2.y*d2 + p3.y*d3) / p)
    p = p / 2.0
    radius = math.sqrt(p * (p - d1) * (p - d2) * (p - d3))/p
    return (radius, centro.x, centro.y)

def TriInscribedInCircle(p1,p2,p3):
    x12, x13, x31, x21 = (p1.x - p2.x, p1.x - p3.x, p3.x - p1.x, p2.x - p1.x)
    y12, y13, y31, y21 = (p1.y - p2.y, p1.y - p3.y, p3.y - p1.y, p2.y - p1.y)
    sx13 = pow2(p1.x) - pow2(p3.x)
    sy13 = pow2(p1.y) - pow2(p3.y)
    sx21 = pow2(p2.x) - pow2(p1.x)
    sy21 = pow2(p2.y) - pow2(p1.y)
    f = (sx13*x12 + sy13*x12 + sx21*x13 + sy21*x13) / (2 * (y31*x12 - y21*x13))
    g = (sx13*y12 + sy13*y12 + sx21*y13 + sy21*y13) / (2 * (x31*y12 - x21*y13))
    c = - pow2(p1.x) - pow2(p1.y) - 2*g*p1.x - 2*f*p1.y
    r = math.sqrt(pow2(-g) + pow2(-f) - c)
    return (r, -g, -f)

def XYarr2str(arr):
    s=""
    for n in arr:
        tt = type(n)
        if tt==XY: s += n.st() + " "
        if tt==list: s += str(n[0])+","+str(n[1]) + " "
        if tt==str: s += n
        if (tt==int or tt==float): s += str(n) + " "
    return s

# 243
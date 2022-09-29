#!/usr/bin/env python3
__version__ = "1.0" 
import inkex, math
from lxml import etree

class Mehr_plate():
  def __init__(self,size,tabs,starts,thickness,kerf):
    #general note svg pos x is right, pos y is down
    self.size=size#(X,Y) inner size
    self.tabs=tabs#number of tabs (top,right,bottom,left)
    self.starts=starts#4 elements array of boolean if true start=high (top,right,bottom,left)
    self.kerf=kerf#number, beam radius
    self.thickness=thickness#number
    self.holes=[]#list of SVG Strings
    self.offset=[0.0 if self.starts[3] or self.tabs[3]==0 else self.thickness,0.0 if self.starts[0] or self.tabs[0]==0 else self.thickness]#set global offset so that AABB is at position (0,0)
    self.corner_offset=[0.0 if (self.tabs[3]==0 and not self.starts[3]) else self.thickness,0.0 if (self.tabs[0]==0 and not self.starts[0]) else self.thickness]
    self.AABB=[self.size[0]+(0.0 if (self.tabs[1]==0 and not self.starts[1]) else self.thickness)+self.corner_offset[0]+2*self.kerf,
    self.size[1]+(0.0 if (self.tabs[2]==0 and not self.starts[2]) else self.thickness)+self.corner_offset[1]+2*self.kerf]

    points=[]
    for i in range(4):
        points+=self.rotate(self.side(i),i*math.pi/2)#creating the points of the four sides and rotate them in the radiant system
    self.SVG_String=self.to_SVG_String(points)
    #self.AABB=[self.size[0]+2*self.thickness,0]
    
  def side(self,index): #creating a side as a list of relative points. total lenght should be side lenght+2*kerf.
    points=[[2*self.kerf,0.0]] if not self.starts[index] else [] #if this one starts low add two kerf
    if (self.starts[(index-1)%4]):#if the privious one ended high add a thickness
      points+=[[self.thickness,0.0]]
    if self.tabs[index]>0:
      parts=self.tabs[index]*2+1#number of parts= number of tabs+number of spaces between tabs +1
      tab_state=self.starts[index]#makes a high part if true, low else
      for i in range(parts):#creates the side
        points+=[[(self.size[(index%2)]/parts)+2*self.kerf,0.0]] if (tab_state) else [[(self.size[index%2]/parts)-2*self.kerf,0.0]]#a longer part for tabs and a shorter one for the spaces in between
        if not (i==parts-1):
          points+=[[0.0,self.thickness]] if (tab_state) else [[0.0,-self.thickness]]# if high go down else go up
          tab_state=not tab_state #invert tab_state
    else:
      points+=[[self.size[index%2]+2*self.kerf,0.0]] if (self.starts[index]) else [[self.size[index%2]-2*self.kerf,0.0]]#single line if there are no tabs
    if(self.starts[(index+1)%len(self.starts)]):#if the next one starts high add a thickness
      points+=[[self.thickness,0.0]]
    if not self.starts[index]:#if this one starts and so also ends low add 2 kerf
      points+=[[2*self.kerf,0.0]]
    return points
  
  def to_SVG_String(self,PointList):#creates a SVG_String as connected points from list so that AABB upper left corner is at 0,0
    s="M"+str(self.offset[0])+','+str(self.offset[1])
    for i in range(len(PointList)):
      s+="l"+str(PointList[i][0])+","+str(PointList[i][1])
    return s
  
  def rotate(self,pointlist,angle):#rotate all points by angle in 2*pi system
    matrix=[[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]]
    ret=[]
    for i in range(len(pointlist)):
      ret+=[[pointlist[i][0]*matrix[0][0]+pointlist[i][1]*matrix[0][1],pointlist[i][0]*matrix[1][0]+pointlist[i][1]*matrix[1][1]]]
    return ret
  
  def rect(self,pos,size,center=[False,False]):#SVG_String for a rectangle
    SVG_String="M"+str(pos[0]-((size[0]/2)if center[0]else 0))+','+str(pos[1]-((size[1]/2)if center[1]else 0))
    SVG_String+='h'+str(size[0])+'v'+str(size[1])+'h'+str(-size[0])+'z'
    return SVG_String
  
  def add_holes(self,direction,position,number_of,center=False):
    SVG_String=""
    side=self.size[0] if direction=='X' else self.size[1]#geting size of the relevant side
    hole_offset=(side/(2*number_of+1))#offset each hole
    holesize=[hole_offset-2*self.kerf,self.thickness-2*self.kerf]#size of the holes
    for i in range(number_of):#d=(2*i+1)*hole_offset+self.kerf
      if direction=='X':
        SVG_String+=self.rect([self.corner_offset[0]+self.kerf+(2*i+1)*hole_offset+self.kerf,self.corner_offset[1]+self.kerf+position],holesize,[False,center])
      else:
        SVG_String+=self.rect([self.corner_offset[0]+self.kerf+position,(2*i+1)*hole_offset+self.kerf+self.corner_offset[1]+self.kerf],holesize[::-1],[center,False])#reversed axis
#    inkex.errormsg(SVG_String)
    self.holes+=[SVG_String]
  
  def draw(self,position,colors,parent):
    if len(self.holes)>0:#creating a new group if there are any holes to be drawn
      grp_name = 'Group'
      grp_attribs = {inkex.addNS('label','inkscape'):grp_name}
      parent = etree.SubElement(parent, 'g', grp_attribs)#the group to put everything in
      for s in self.holes:
        self.draw_SVG_String(s,colors[1],parent,position)#drawing the holes if there are any
    self.draw_SVG_String(self.SVG_String,colors[0],parent,position)#drawing the plate    

  def draw_SVG_String(self,SVG_String,color,parent,position=(0,0)):# Adding an SVG_String to the drawing
    name='part'
    transform='translate('+str(position[0])+','+str(position[1])+')'
    style = { 'stroke': color, 'fill': 'none','stroke-width':str(max(self.kerf*2,0.2))}
    drw = {'style':str(inkex.Style(style)),'transform':transform, inkex.addNS('label','inkscape'):name,'d':SVG_String}
    etree.SubElement(parent, inkex.addNS('path','svg'), drw )
    return
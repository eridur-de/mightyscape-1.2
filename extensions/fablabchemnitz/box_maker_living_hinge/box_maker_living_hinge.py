#!/usr/bin/env python3
'''
Generates Inkscape SVG file containing box components needed to 
laser cut a tabbed construction box taking kerf and clearance into account

Original Author -- 2011 elliot white   elliot@twot.eu
Forked --          2013 Reid Borsuk    reid.borsuk@live.com
Updated for 0.91   2016 Maren Hachmann marenhachmann@yahoo.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
__version__ = "0.8rb" 

import inkex
import math
from lxml import etree
import math

def drawS(XYstring):         # Draw lines from a list
  name='part'
  style = { 'stroke': '#000000', 'fill': 'none' }
  drw = {'style': str(inkex.Style(style)),inkex.addNS('label','inkscape'):name,'d':XYstring}
  etree.SubElement(parent, inkex.addNS('path','svg'), drw )
  return

def draw_SVG_ellipse(centerx, centery, radiusx, radiusy, start_end):

    style = {   'stroke'        : '#000000',
                'fill'          : 'none'            }
    ell_attribs = {'style': str(inkex.Style(style)),
        inkex.addNS('cx','sodipodi')        :str(centerx),
        inkex.addNS('cy','sodipodi')        :str(centery),
        inkex.addNS('rx','sodipodi')        :str(radiusx),
        inkex.addNS('ry','sodipodi')        :str(radiusy),
        inkex.addNS('start','sodipodi')     :str(start_end[0]),
        inkex.addNS('end','sodipodi')       :str(start_end[1]),
        inkex.addNS('open','sodipodi')      :'true',    #all ellipse sectors we will draw are open
        inkex.addNS('type','sodipodi')      :'arc',
        'transform'                         :''
            }

    ell = etree.SubElement(parent, inkex.addNS('path','svg'), ell_attribs )

#draw an SVG line segment between the given (raw) points
def draw_SVG_line( x1, y1, x2, y2, parent):
    style = { 'stroke': '#000000', 'fill': 'none' }

    line_attribs = {'style' :  str(inkex.Style(style)),
                    'd' : 'M '+str(x1)+','+str(y1)+' L '+str(x2)+','+str(y2)}

    line = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )

def EllipseCircumference(a, b):
   """
   Compute the circumference of an ellipse with semi-axes a and b.
   Require a >= 0 and b >= 0.  Relative accuracy is about 0.5^53.
   """
   import math
   x, y = max(a, b), min(a, b)
   digits = 53; tol = math.sqrt(math.pow(0.5, digits))
   if digits * y < tol * x: return 4 * x
   s = 0; m = 1
   while x - y > tol * y:
      x, y = 0.5 * (x + y), math.sqrt(x * y)
      m *= 2; s += m * math.pow(x - y, 2)
   return math.pi * (math.pow(a + b, 2) - s) / (x + y)

"""
Gives you a list of points that make up a box.

Returns string suitable for input to drawS
"""
def box(sx, sy,ex, ey, leaveLeftSideOpen = False):
  s=[]
  s='M '+str(sx)+','+str(sy)+' '
  s+='L '+str(ex)+','+str(sy)+' '
  s+='L '+str(ex)+','+str(ey)+' '
  s+='L '+str(sx)+','+str(ey)+' '
  if not leaveLeftSideOpen:
    s+='L '+str(sx)+','+str(sy)+' '
  return s

"""
Side function is used to render any of the sides so needs all this functionality:
 isLongSide -- long sides without tabs (for cover),
 truncate -- partial sides for the elipse
 gap -- extend the tabs on the curved side for ease of movement
 thumbTab -- Render individual boxes for slots instead of one continuous line

isTab is used to specify the male/female designation for a side so they mesh properly. Otherwise the tabs
would be in the same spot for opposing sides, instead of interleaved.

Returns a list of lines to draw.
"""
def side(rx,ry,sox,soy,eox,eoy,tabVec,length, dirx, diry, isTab, isLongSide, truncate = False, gap = False, thumbTab = False):
  #       root startOffset endOffset tabVec length  direction  isTab

  #Long side length= length+((math.pi*(length/2))/4
  tmpLength = 0
  correctionLocal = correction
  if gap:
      correctionLocal = (correction)
  if isLongSide > 0:
      tmpLength = length
      length = isLongSide

  divs=int(length/nomTab)  # divisions
  if not divs%2: divs-=1   # make divs odd
  if isLongSide < 0: 
      divs = 1
      
  divs=float(divs)
  tabs=(divs-1)/2          # tabs for side
  
  if isLongSide < 0:
      divs = 1
      tabWidth = length
      gapWidth = 0
  elif equalTabs:
      gapWidth=tabWidth=length/divs
  else:
      tabWidth=nomTab
      gapWidth=(length-tabs*nomTab)/(divs-tabs)
    
  if isTab:                 # kerf correction
      gapWidth-=correctionLocal 
      tabWidth+=correctionLocal 
      first=correctionLocal/2
  else:
      gapWidth+=correctionLocal 
      tabWidth-=correctionLocal 
      first=-correctionLocal/2

  s=[] 
  firstVec=0; secondVec=tabVec
  if gap:
      secondVec *= 2
  dirxN=0 if dirx else 1 # used to select operation on x or y
  diryN=0 if diry else 1
  (Vx,Vy)=(rx+sox*thickness,ry+soy*thickness)
  s='M '+str(Vx)+','+str(Vy)+' '

  if dirxN: Vy=ry # set correct line start
  if diryN: Vx=rx

  if isLongSide > 0: #LongSide is a side without tabs for a portion.
      length = tmpLength
      divs=int((Z/2)/nomTab)
      if not divs%2: divs-=1
      divs = float(divs)

  # generate line as tab or hole using:
  #   last co-ord:Vx,Vy ; tab dir:tabVec  ; direction:dirx,diry ; thickness:thickness
  #   divisions:divs ; gap width:gapWidth ; tab width:tabWidth
  for n in range(1,int(divs)):
    if n%2:
      Vx=Vx+dirx*gapWidth+dirxN*firstVec+first*dirx
      Vy=Vy+diry*gapWidth+diryN*firstVec+first*diry
      s+='L '+str(Vx)+','+str(Vy)+' '
      Vx=Vx+dirxN*secondVec
      Vy=Vy+diryN*secondVec
      s+='L '+str(Vx)+','+str(Vy)+' '
    else:
      Vxs = Vx
      Vys = Vy
      Vx=Vx+dirx*tabWidth+dirxN*firstVec
      Vy=Vy+diry*tabWidth+diryN*firstVec
      s+='L '+str(Vx)+','+str(Vy)+' '
      Vx=Vx+dirxN*secondVec
      Vy=Vy+diryN*secondVec
      s+='L '+str(Vx)+','+str(Vy)+' '
      if thumbTab:
          drawS(box(Vxs,Vys,Vx,Vy))
    (secondVec,firstVec)=(-secondVec,-firstVec) # swap tab direction
    first=0
  if not truncate: 
    s+='L '+str(rx+eox*thickness+dirx*length)+','+str(ry+eoy*thickness+diry*length)+' '
  else: #Truncate specifies that a side is incomplete in preperation for a curve
    s+='L '+str(rx+eox*thickness+dirx*(length/2))+','+str(ry+eoy*thickness+diry*(length/2))+' '
  return s

#God class. Makes poor design, but not much object oriented in this guy...
class BoxMakerLivingHinge(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--unit',default='mm',help='Measure Units')
        pars.add_argument('--inside',type=int,default=0,help='Int/Ext Dimension')
        pars.add_argument('--length',type=float,default=100,help='Length of Box')
        pars.add_argument('--width',type=float,default=100,help='Width of Box')
        pars.add_argument('--height',type=float,default=100,help='Height of Box')
        pars.add_argument('--tab',type=float,default=25,help='Nominal Tab Width')
        pars.add_argument('--equal',type=int,default=0,help='Equal/Prop Tabs')
        pars.add_argument('--thickness',type=float,default=10,help='Thickness of Material')
        pars.add_argument('--kerf',type=float,default=0.5,help='Kerf (width) of cut')
        pars.add_argument('--clearance',type=float,default=0.01,help='Clearance of joints')
        pars.add_argument('--style',type=int,default=25,help='Layout/Style')
        pars.add_argument('--spacing',type=float,default=25,help='Part Spacing')
        pars.add_argument('--hingeOpt',type=int,default=0,help='Hinge type')
        pars.add_argument('--hingeThick',type=float,default=0,help='Hinge thickness')
        pars.add_argument('--thumbTab',default=0,help='Add a thumb tab')
        		
    """
    Traditional multi-slit design.
    Sx, Sy : Start X, Y (pixels, not user units)
    Ex, Ey : End X, Y (pixels, not user units)
    space : gap between slots in the X direction, in user specified units (IE: wood between two rows of slots)
    solidGap : gap between slots in the Y direction, in user specified units (IE: how much wood is left between 2 or 3 cuts)
    """
    def livingHinge2(self, Sx, Sy, Ex, Ey, space = 2, solidGap = 4):

        space = self.svg.unittouu( str(space)  + unit )
        solidGap = self.svg.unittouu( str(solidGap)  + unit )
        Sy += thickness
        Ey -= thickness

        height = Ey - Sy

        width = Ex - Sx
        # inkex.utils.debug(width)
        horizontalSlots = int(round(width / space))
        # inkex.utils.debug(horizontalSlots)
        if horizontalSlots % 2 and horizontalSlots != 1: 
            horizontalSlots-=1   # make it even so you end with an interior slot
        # inkex.utils.debug(horizontalSlots)
        space = width / horizontalSlots

        grp_name = 'Living Hinge'
        grp_attribs = {inkex.addNS('label','inkscape'):grp_name }
        grp = etree.SubElement(parent, 'g', grp_attribs)#the group to put everything in

        for n in range(0,horizontalSlots+1):
            if n%2:  #odd, exterior slot (slot should go all the way to the part edge)
                draw_SVG_line(Sx + (space * n), Sy, Sx + (space * n), Sy+(height/4)-(solidGap/2), grp)
                draw_SVG_line(Sx + (space * n), Sy+(height/4)+(solidGap/2), Sx + (space * n), Ey-(height/4)-(solidGap/2), grp)
                draw_SVG_line(Sx + (space * n), Ey-(height/4)+(solidGap/2), Sx + (space * n), Ey, grp)

            else:
                #even, interior slot (slot shoud not touch edge of part)
                draw_SVG_line(Sx + (space * n), Sy+solidGap, Sx + (space * n), Sy+(height/2)-(solidGap/2), grp)
                draw_SVG_line(Sx + (space * n), Ey-(height/2)+(solidGap/2), Sx + (space * n), Ey-solidGap, grp)

    """
    The sprial based designs are built from multiple calls of this function. 
    Sx, Sy : Start X, Y (pixels, not user units)
    Ex, Ey : End X, Y (pixels, not user units)
    reverse : specifies the spin of the spiral (1 = outer spiral is counterclockwise, -1 otherwise)
    space : gap between slots, in user specified units (IE: how thick the wood remainder is)
    """
    def livingHinge3(self, Sx, Sy, Ex, Ey, reverse = 1, space = 2):
        space = self.svg.unittouu( str(space)  + unit )

        height = (Ey - Sy)

        width = (Ex - Sx)

        horizontalSlots = int(math.floor(height / (space)))
        if not horizontalSlots%2: horizontalSlots-=1   # make it odd otherwise the below division will result in an outer cut too thin

        space = (height / horizontalSlots)

        horizontalSlots = int(round(horizontalSlots * 1/2)) #We do 2 passes per render, so divide slots requirement in half

        grp_name = 'Living Hinge'
        grp_attribs = {inkex.addNS('label','inkscape'):grp_name }
        grp = etree.SubElement(parent, 'g', grp_attribs)#the group to put everything in

        centerX = Sx + (width/2)
        centerY = Sy + (height/2)

        for n in range(0,horizontalSlots):
            newX = (((space/2) + (space*n)) * reverse)
            draw_SVG_line((centerX -  newX), centerY + (space/2) + (space * n), (centerX - newX ), centerY - (space * 1.5) - (space * n), grp)
            if horizontalSlots - 1 != n: #Last line in center should be omited
                draw_SVG_line((centerX - (space + (space/2 * -reverse)) - (space*n) ), centerY - (space * 1.5) - (space * n), (centerX + (space + (space/2 * reverse)) + (space*n) ), centerY - (space * 1.5) - (space * n), grp)

            draw_SVG_line((centerX + newX ), centerY - (space/2) - (space * n), (centerX + newX ), centerY + (space * 1.5) + (space * n), grp)
            if horizontalSlots - 1 != n: #Last line in center should be omited
                draw_SVG_line((centerX + (space + (space/2 * -reverse)) + (space*n) ), centerY + (space * 1.5) + (space * n), (centerX - (space + (space/2 * reverse)) - (space*n) ), centerY + (space * 1.5) + (space * n), grp)

    """
    The snake based designs are built from multiple calls of this function. 
    Sx, Sy : Start X, Y (pixels, not user units)
    Ex, Ey : End X, Y (pixels, not user units)
    rotate : False means the traditional flexable design (cuts are prependuclar to long sides). True rotates 90 degrees.
    mirror : mirror inverts the left and right slots, used for inverting during double design
    space : gap between adjecent slots, in user specified units (IE: wood between two rows of slots, X if rotate is false, Y if true)
    solidGap : gap between slot and edge, in user specified units (IE: how much wood is left between cut and edge, Y if rotate is false, X if true)
    """
    def livingHinge4(self, Sx, Sy, Ex, Ey, rotate = False, mirror = 0, space = 2, solidGap = 5):

        space = self.svg.unittouu( str(space)  + unit )
        solidGap = self.svg.unittouu( str(solidGap)  + unit )
        Sy += thickness
        Ey -= thickness

        height = Ey - Sy
        width = Ex - Sx

        if not rotate:
            horizontalSlots = int(round(width / space)) 
            space = width / horizontalSlots
            skew = 1 #Paint extra lines at the start and end because in this direction there are no existing lines already
        else:
            horizontalSlots = int(round(height / space))
            if not horizontalSlots%2: horizontalSlots-=1 #make sure we always end on the same side, otherwise we'll cut off the last tooh 
            space = height / horizontalSlots
            skew = 0 #Don't paint the first and last lines, as they're on the cut already, and double cuts on a laser are messy

        grp_name = 'Living Hinge'
        grp_attribs = {inkex.addNS('label','inkscape'):grp_name }
        grp = etree.SubElement(parent, 'g', grp_attribs)#the group to put everything in

        for n in range(1 - skew,horizontalSlots + skew):
            if not rotate:
                if (n+mirror)%2:
                    draw_SVG_line(Sx + (space * n), Sy + solidGap, Sx + (space * n), Ey, grp)
                else:
                    draw_SVG_line(Sx + (space * n), Sy, Sx + (space * n), Ey - solidGap, grp)
            else:
                if (n+mirror)%2:
                    draw_SVG_line(Sx + solidGap, Sy + (space * n), Ex, Sy + (space * n), grp)
                else:
                    draw_SVG_line(Sx, Sy + (space * n), Ex - solidGap, Sy + (space * n), grp)
        if rotate and not mirror:
            draw_SVG_line(Sx, Sy, Sx, Ey - space, grp)
            draw_SVG_line(Ex, Sy + space, Ex, Ey, grp)
        elif mirror:
            draw_SVG_line(Sx, Sy + space, Sx, Ey, grp)
            draw_SVG_line(Ex, Sy, Ex, Ey - space, grp)

    def effect(self):
        global parent,nomTab,equalTabs,thickness,correction, Z, unit 
        
            # Get access to main SVG document element and get its dimensions.
        svg = self.document.getroot()
        
            # Get the attibutes:
        widthDoc  = self.svg.unittouu(svg.get('width'))
        heightDoc = self.svg.unittouu(svg.get('height'))

            # Create a new layer.
        layer = etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), 'newlayer')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        
        parent=self.svg.get_current_layer()
        
            # Get script's option values.
        unit=self.options.unit
        inside=self.options.inside
        X = self.svg.unittouu( str(self.options.length)  + unit )
        Y = self.svg.unittouu( str(self.options.width) + unit )
        Z = self.svg.unittouu( str(self.options.height)  + unit )
        thickness = self.svg.unittouu( str(self.options.thickness)  + unit )
        nomTab = self.svg.unittouu( str(self.options.tab) + unit )
        equalTabs=self.options.equal
        kerf = self.svg.unittouu( str(self.options.kerf)  + unit )
        clearance = self.svg.unittouu( str(self.options.clearance)  + unit )
        layout=self.options.style
        spacing = self.svg.unittouu( str(self.options.spacing)  + unit )
        ring = 1
        hingeOpt = self.options.hingeOpt
        hingeThick = self.options.hingeThick
        thumbTab = self.options.thumbTab 
            
        if inside: # if inside dimension selected correct values to outside dimension
            X+=thickness*2
            Y+=thickness*2
            Z+=thickness*2

        correction=kerf-clearance

        # check input values mainly to avoid python errors
        # TODO restrict values to *correct* solutions
        # TODO -- Do what the origial author suggested I do. QUALITY!
        error=0
        
        if min(X,Y,Z)==0:
            inkex.errormsg('Error: Dimensions must be non zero')
            error=1
        if max(X,Y,Z)>max(widthDoc,heightDoc)*10: # crude test
            inkex.errormsg('Error: Dimensions Too Large')
            error=1
        if min(X,Y,Z)<3*nomTab:
            inkex.errormsg('Error: Tab size too large')
            error=1
        if nomTab<thickness:
            inkex.errormsg('Error: Tab size too small')
            error=1
        if thickness==0:
            inkex.errormsg('Error: Thickness is zero')
            error=1
        if thickness>min(X,Y,Z)/3: # crude test
            inkex.errormsg('Error: Material too thick')
            error=1
        if correction>min(X,Y,Z)/3: # crude test
            inkex.errormsg('Error: Kerf/Clearence too large')
            error=1
        if spacing>max(X,Y,Z)*10: # crude test
            inkex.errormsg('Error: Spacing too large')
            error=1
        if spacing<kerf: #if spacing is less then kerf, the laser cuts will overlap and blast meaningful material.
            inkex.errormsg('Error: Spacing too small')
            error=1

        if error: exit()
    
        # layout format:(rootx),(rooty),Xlength,Ylength,tabInfo
        # root= (spacing,X,Y,Z) * values in tuple
        # tabInfo= <abcd> 0=holes 1=tabs
        if layout==0: # Diagramatic Layout TRBL
            pieces=[         #center low row
                    [(2,0,0,1),(3,0,1,1),X,Z,0b1000,-2],
                            #left middle row
                    [(1,0,0,0),(2,0,0,1),Z,Y,0b1111,0],
                            #center middle row
                    [(2,0,0,1),(2,0,0,1),X,Y,0b0000,0],
                            #right middle row
                    [(3,1,0,1),(2,0,0,1),Z+(EllipseCircumference(X/2, Z/2)/4)+thickness,Y,0b1011,1],
                            #center top row
                    [(2,0,0,1),(1,0,0,0),X,Z,0b0010,-1]]
        elif layout==1: # Inline(compact) Layout
            pieces=[#Base
                    [(1,0,0,0),(1,0,0,0),X,Y,0b0000,0],
                    #Front panel
                    [(2,1,0,0),(1,0,0,0),Z,Y,0b1111,0],
                    #Sides with curves
                    [(3,1,0,1),(1,0,0,0),X,Z,0b1000,-2],
                    [(4,2,0,1),(1,0,0,0),X,Z,0b0010,-1],
                    #Long piece w/ hinge  
                    [(5,3,0,1),(1,0,0,0),Z+(EllipseCircumference(X/2, Z/2)/4)+thickness,Y,0b1011,1]
                    ]

        for piece in pieces: # generate and draw each piece of the box
            (xs,xx,xy,xz)=piece[0]
            (ys,yx,yy,yz)=piece[1]
            x=xs*spacing+xx*X+xy*Y+xz*Z  # root x co-ord for piece
            y=ys*spacing+yx*X+yy*Y+yz*Z  # root y co-ord for piece
            dx=piece[2]
            dy=piece[3]
            tabs=piece[4]
            a=tabs>>3&1; b=tabs>>2&1; c=tabs>>1&1; d=tabs&1 # extract tab status for each side. It's a nasty packed binary flag format, but I'm not fixing it now.
            longSide = 0
            shortSide = 0
            skew = 0

            if piece[5] == 1:
                longSide = Z
            elif piece[5] < 0:
                shortSide = Z   
            
            # generate and draw the sides of each piece
            if piece[5] != -1:
                drawS(side(x,y,d,a,-b,a,-thickness if a else thickness,dx,1,0,a,longSide))          # side a (top)
            else:
                drawS(side(x,y,d,a,-b,a,-thickness if a else thickness,dx/2,1,0,a,-1))          # side a (top) when the top participates in a curve

            if piece[5] != -1 and piece[5] != 1:
                drawS(side(x+dx+skew,y,-b,a,-b,-c,thickness if b else -thickness,dy,0,1,b,shortSide, False if piece[5] != -2 else True, False if piece[5] != 1 else True))     # side b (right) except for side with living hinge or curves
            elif piece[5] == -1:
                drawS(side(x+dx+skew,y+dy,-b,-c,-b,a,thickness if b else -thickness,dy,0,-1,b,shortSide, True))     # side b (right) when the right side participates in a curve
            else: 
                #It is a cardnal sin to compare floats, so assume <0.0005 is 0 since the front end only gives you 3 digits of precision
                if float(0.0005) <= float(self.options.thumbTab):
                    side(x+dx+skew,y,-b,a,-b,-c,thickness if b else -thickness,dy,0,1,b,shortSide, False, True, True) #The one call to side that doesn't actually draw. Instead, side draws boxes on its own
                    drawS(box(x+dx+skew,y+thickness,x+dx+skew+self.svg.unittouu( thumbTab + unit ),y+dy-thickness, True))
                else:
                    drawS(side(x+dx+skew,y,-b,a,-b,-c,thickness if b else -thickness,dy,0,1,b,shortSide, False, True)) #side b (right) on the right side of a living hinge


            if piece[5] != -2:
                drawS(side(x,y+dy,d,-c,-b,-c,thickness if c else -thickness,dx,1,0,c,longSide)) # side c (bottom)
            else:
                drawS(side(x,y+dy,d,-c,-b,-c,thickness if c else -thickness,dx/2,1,0,c,-1)) # side c (bottom) when the bottom participates in a curve

            drawS(side(x,y+dy,d,-c,d,a,-thickness if d else thickness,dy,0,-1,d,0))      # side d (left)

            if piece[5] < 0:
                draw_SVG_ellipse(x+(dx/2), y+(dy/2), (dx/2), (dy/2), [(1.5*math.pi), 0] if piece[5] == -1 else [0, 0.5*math.pi]) #draw the curve

            if piece[5] == 1: #Piece should contain a living hinge
                if hingeOpt == 0: #Traditional parallel slit
                    self.livingHinge2(x+(Z/2), y, x+(Z/2)+(EllipseCircumference(X/2, Z/2)/4), y + (dy), hingeThick)
                elif hingeOpt == 1: #Single spiral
                    if not inside:
                        self.livingHinge3(x+(Z/2), y+thickness, x+(Z/2)+(EllipseCircumference(X/2, Z/2)/4), y + dy - thickness, 1, hingeThick)
                    else:
                        self.livingHinge3(x+(Z/2), y + 2*thickness, x+(Z/2)+(EllipseCircumference(X/2, Z/2)/4), y + dy - 2*thickness, 1, hingeThick)

                elif hingeOpt == 2: #Double spiral
                    self.livingHinge3(x+(Z/2), y+thickness, x+(Z/2)+(EllipseCircumference(X/2, Z/2)/4), y + (dy/2), 1, hingeThick)
                    self.livingHinge3(x+(Z/2), y+(dy/2), x+(Z/2)+(EllipseCircumference(X/2, Z/2)/4), y + dy - thickness, -1, hingeThick)
                elif hingeOpt == 3 or hingeOpt == 4: #Both snake-based designs
                    self.livingHinge4(x+(Z/2), y, x+(Z/2)+(EllipseCircumference(X/2, Z/2)/4), y + (dy), False if hingeOpt == 3 else True, 0, hingeThick)
                elif hingeOpt == 5: #Double snake design
                    self.livingHinge4(x+(Z/2), y, x+(Z/2)+EllipseCircumference(X/2, Z/2)/4, y + (dy/2) + thickness, True, 0, hingeThick) #Add thickness as a cheat so design 4 doesn't have to know if it's a short or long variant
                    self.livingHinge4(x+(Z/2), y + (dy/2) - thickness, (x+(Z/2)+(EllipseCircumference(X/2, Z/2)/4)), y + dy, True, 1, hingeThick) 
           
if __name__ == '__main__':
    BoxMakerLivingHinge().run()
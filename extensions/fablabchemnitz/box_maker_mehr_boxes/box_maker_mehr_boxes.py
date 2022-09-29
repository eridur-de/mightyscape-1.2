#!/usr/bin/env python3
'''
Generates Inkscape SVG file containing box components needed to 
laser cut a tabbed construction box taking kerf into account

Copyright (C) 2018 Thore Mehr thore.mehr@gmail.com
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
__version__ = "1.0" ### please report bugs, suggestions etc to bugs@twot.eu ###

import math
import inkex
import mehr_plate

class mehr_box_maker(inkex.EffectExtension):

  def add_arguments(self, pars):
    pars.add_argument('--page',default='page_1')
    pars.add_argument('--unit',default='mm')
    pars.add_argument('--inside')
    pars.add_argument('--X_size',type=float,default='0.0')
    pars.add_argument('--Y_size',type=float,default='0.0')
    pars.add_argument('--Z_size',type=float,default='0.0')
    pars.add_argument('--tab_mode',default='number')
    pars.add_argument('--tab_size',type=float,default='0.0')
    pars.add_argument('--X_tabs',type=int,default='0')
    pars.add_argument('--Y_tabs',type=int,default='0')
    pars.add_argument('--Z_tabs',type=int,default='0')   
    pars.add_argument('--d_top',type=inkex.Boolean,default=True)
    pars.add_argument('--d_bottom',type=inkex.Boolean,default=True)
    pars.add_argument('--d_left',type=inkex.Boolean,default=True)
    pars.add_argument('--d_right',type=inkex.Boolean,default=True)
    pars.add_argument('--d_front',type=inkex.Boolean,default=True)
    pars.add_argument('--d_back',type=inkex.Boolean,default=True)
    pars.add_argument('--thickness',type=float,default=4,help='Thickness of Material')
    pars.add_argument('--kerf',type=float,default=0.2)
    pars.add_argument('--spaceing',type=float,default=1) 
    pars.add_argument('--X_compartments',type=int,default=1)
    pars.add_argument('--X_divisions')
    pars.add_argument('--X_mode')
    pars.add_argument('--X_fit',type=inkex.Boolean)
    pars.add_argument('--Y_compartments',type=int,default=1)
    pars.add_argument('--Y_divisions')
    pars.add_argument('--Y_mode')
    pars.add_argument('--Y_fit',type=inkex.Boolean)

  def effect(self):
    thickness=self.svg.unittouu(str(self.options.thickness)+self.options.unit)
    kerf=self.svg.unittouu(str(self.options.kerf)+self.options.unit)/2#kerf is diameter in UI and radius in lib
    
    spaceing=self.svg.unittouu(str(self.options.spaceing)+self.options.unit)
    XYZ=[self.svg.unittouu(str(self.options.X_size)+self.options.unit),self.svg.unittouu(str(self.options.Y_size)+self.options.unit),self.svg.unittouu(str(self.options.Z_size)+self.options.unit)]

    if(self.options.inside=='0'):#if the sizes are outside sizes reduce the size by thickness if the side gets drawn
      draw=(self.options.d_left,self.options.d_front,self.options.d_top,self.options.d_right,self.options.d_back,self.options.d_bottom)#order in XYZXYZ
      for i in range(6):
        XYZ[i%3]-=(thickness if draw[i] else 0)#remove a thickness if drawn

#compartments on the X axis, devisons in Y direction
    X_divisions_distances=[]
    if (self.options.X_compartments>1):
      if (self.options.X_mode=='even'):#spliting in even compartments
        X_divisions_distances=[((XYZ[0])-(self.options.X_compartments-1)*(thickness))/self.options.X_compartments]
      else:
        for dist in self.options.X_divisions.replace(",",".").split(";"):#fixing seperator, spliting string
          X_divisions_distances+=[float(self.svg.unittouu(dist+self.options.unit))]#translate into universal units
      X_divisions_distances[0]+=kerf#fixing for kerf
      if self.options.X_mode!='absolut':#for even and relative fix list lenght and offset compartments to absolut distances
        while (len(X_divisions_distances)<self.options.X_compartments+1):#making the list long enought for relative offsets
          X_divisions_distances+=X_divisions_distances
        for i in range(1,self.options.X_compartments):#offset to absolut distances
          X_divisions_distances[i]+=X_divisions_distances[i-1]+thickness-kerf
      X_divisions_distances=X_divisions_distances[0:self.options.X_compartments]#cutting excesive lenght off
      
      if(X_divisions_distances[-2]+thickness>XYZ[0])and not self.options.X_fit:
        inkex.errormsg("X Axis compartments outside of plate")
      if self.options.X_fit:
        XYZ[0]=X_divisions_distances[-1]-kerf
      X_divisions_distances=X_divisions_distances[0:-1]#cutting the last of

    Y_divisions_distances=[]
    if (self.options.Y_compartments>1):
      if (self.options.Y_mode=='even'):#spliting in even compartments
        Y_divisions_distances=[((XYZ[1])-(self.options.Y_compartments-1)*(thickness))/self.options.Y_compartments]
      else:
        for dist in self.options.Y_divisions.replace(",",".").split(";"):#fixing seperator, spliting string
          Y_divisions_distances+=[float(self.svg.unittouu(dist+self.options.unit))]#translate into universal units
      Y_divisions_distances[0]+=kerf#fixing for kerf
      if self.options.Y_mode!='absolut':#for even and relative fix list lenght and offset compartments to absolut distances
        while (len(Y_divisions_distances)<self.options.Y_compartments+1):#making the list long enought for relative offsets
          Y_divisions_distances+=Y_divisions_distances
        for i in range(1,self.options.Y_compartments):#offset to absolut distances
          Y_divisions_distances[i]+=Y_divisions_distances[i-1]+thickness-kerf
      Y_divisions_distances=Y_divisions_distances[0:self.options.Y_compartments]#cutting excesive lenght off
      
      if(Y_divisions_distances[-2]+thickness>XYZ[1])and not self.options.X_fit:
        inkex.errormsg("Y Axis compartments outside of plate")
      if self.options.Y_fit:
        XYZ[1]=Y_divisions_distances[-1]-kerf
      Y_divisions_distances=Y_divisions_distances[0:-1]#cutting the last of

    if (self.options.tab_mode=='number'):#fixed number of tabs
      Tabs_XYZ=[self.options.X_tabs,self.options.Y_tabs,self.options.Z_tabs]
    else:#compute apropriate number of tabs for the edges
      tab_size=float(self.svg.unittouu(str(self.options.tab_size)+self.options.unit))
      Tabs_XYZ=[max(1,int(XYZ[0]/(tab_size))/2),max(1,int(XYZ[1]/(tab_size))/2),max(1,int(XYZ[2]/(tab_size))/2)]

#top and bottom plate
    tabs_tb=(Tabs_XYZ[0] if self.options.d_back else 0,Tabs_XYZ[1] if self.options.d_right else 0,Tabs_XYZ[0] if self.options.d_front else 0,Tabs_XYZ[1] if self.options.d_left else 0)
    start_tb=(True  if self.options.d_back else False,True  if self.options.d_right else False,True  if self.options.d_front else False,True  if self.options.d_left else False)
    Plate_tb=mehr_plate.Mehr_plate((XYZ[0],XYZ[1]),tabs_tb,start_tb,thickness,kerf)#top and bottom plate
    for d in X_divisions_distances:
      Plate_tb.add_holes('Y',d,Tabs_XYZ[1])
    for d in Y_divisions_distances:
      Plate_tb.add_holes('X',d,Tabs_XYZ[0])
#left and right plate
    tabs_lr=(Tabs_XYZ[2] if self.options.d_back else 0,Tabs_XYZ[1] if self.options.d_top else 0,Tabs_XYZ[2] if self.options.d_front else 0,Tabs_XYZ[1] if self.options.d_bottom else 0) 
    start_lr=(True  if self.options.d_back else False,False,True  if self.options.d_front else False,False)
    Plate_lr=mehr_plate.Mehr_plate((XYZ[2],XYZ[1]),tabs_lr,start_lr,thickness,kerf)#left and right plate
    for d in Y_divisions_distances:
      Plate_lr.add_holes('X',d,Tabs_XYZ[2])
#front and back plate
    tabs_fb=(Tabs_XYZ[0] if self.options.d_top else 0,Tabs_XYZ[2] if self.options.d_right else 0,Tabs_XYZ[0] if self.options.d_bottom else 0,Tabs_XYZ[2] if self.options.d_left else 0)#
    start_fb=(False,False,False,False)
    Plate_fb=mehr_plate.Mehr_plate((XYZ[0],XYZ[2]),tabs_fb,start_fb,thickness,kerf)#font and back plate
    for d in X_divisions_distances:
      Plate_fb.add_holes('Y',d,Tabs_XYZ[2])

    Plate_xc=mehr_plate.Mehr_plate((XYZ[2],XYZ[1]),tabs_lr,(False,False,False,False),thickness,kerf)
    for d in Y_divisions_distances:
      Plate_xc.holes+=[Plate_xc.rect([0,Plate_xc.corner_offset[1]+d+kerf],[Plate_xc.AABB[0]/2-kerf,thickness-2*kerf])]
     
    Plate_yc=mehr_plate.Mehr_plate((XYZ[0],XYZ[2]),tabs_fb,(False,False,False,False),thickness,kerf)
    for d in X_divisions_distances:
      Plate_yc.holes+=[Plate_yc.rect([Plate_yc.corner_offset[0]+d+kerf,0],[thickness-2*kerf,Plate_yc.AABB[1]/2-kerf])]

     
    X_offset=0
    Y_offset=0
    if(self.options.d_top):
      Plate_tb.draw([X_offset+spaceing,spaceing],["#000000","#ff0000"],self.svg.get_current_layer())#drawing a plate using black for the outline and red for holes
      X_offset+=Plate_tb.AABB[0]+spaceing
      Y_offset=max(Y_offset,Plate_tb.AABB[1])
    if(self.options.d_bottom):
      Plate_tb.draw([X_offset+spaceing,spaceing],["#000000","#ff0000"],self.svg.get_current_layer())
      X_offset+=Plate_tb.AABB[0]+spaceing
      Y_offset=max(Y_offset,Plate_tb.AABB[1])
      
    if(self.options.d_left):
      Plate_lr.draw([X_offset+spaceing,spaceing],["#000000","#ff0000"],self.svg.get_current_layer())
      X_offset+=Plate_lr.AABB[0]+spaceing
      Y_offset=max(Y_offset,Plate_lr.AABB[1])
    if(self.options.d_right):
      Plate_lr.draw([X_offset+spaceing,spaceing],["#000000","#ff0000"],self.svg.get_current_layer())
      X_offset+=Plate_lr.AABB[0]+spaceing
      Y_offset=max(Y_offset,Plate_lr.AABB[1])
      
    if(self.options.d_front):
      Plate_fb.draw([X_offset+spaceing,spaceing],["#000000","#ff0000"],self.svg.get_current_layer())
      X_offset+=Plate_fb.AABB[0]+spaceing
      Y_offset=max(Y_offset,Plate_fb.AABB[1])
    if(self.options.d_back):
      Plate_fb.draw([X_offset+spaceing,spaceing],["#000000","#ff0000"],self.svg.get_current_layer())
      X_offset+=Plate_fb.AABB[0]+spaceing
      Y_offset=max(Y_offset,Plate_fb.AABB[1])
    X_offset=0
    for i in range(self.options.X_compartments-1):
      Plate_xc.draw([X_offset+spaceing,spaceing+Y_offset],["#000000","#ff0000"],self.svg.get_current_layer())
      X_offset+=Plate_xc.AABB[0]+spaceing
    X_offset=0
    Y_offset+=spaceing+Plate_xc.AABB[1]
    for i in range(self.options.Y_compartments-1):
      Plate_yc.draw([X_offset+spaceing,spaceing+Y_offset],["#000000","#ff0000"],self.svg.get_current_layer())
      X_offset+=Plate_yc.AABB[0]+spaceing
    
if __name__ == '__main__':
    mehr_box_maker().run()
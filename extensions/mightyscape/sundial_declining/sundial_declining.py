#!/usr/bin/python3

# --------------------------------------------------------------------------------------
#http://astrodinamica.altervista.org/ESU/sundial/Condensed-vector-theory.pdf
#https://www.helios-sonnenuhren.de/sites/default/files/upload/the_calculation_of_declining_and_inclining_sundials_an_unusual_approach.pdf
# --------------------------------------------------------------------------------------

from __future__ import division
import inkex 
from datetime import datetime, time, timedelta
from math import * 
from lxml import etree
 
class sundialDeclining(inkex.EffectExtension):
    
    def add_arguments(self, pars):     
        pars.add_argument("--latitude", type=float, dest="latitude", default="50.3515")
        pars.add_argument("--longitude", type=float, dest="longitude", default="15.7512")
        pars.add_argument("--timezone", type=int, dest="timezone", default="0")
        pars.add_argument("--summer_time", type=inkex.Boolean, dest="summer_time", default='False')
        pars.add_argument("--gnom", type=float, dest="gnom", default="30")
        pars.add_argument("--decl", type=float, dest="decl", default="0")
        pars.add_argument("--incl", type=float, dest="incl", default="0")
        pars.add_argument("--DL", type=float, dest="DL", default="0")
        pars.add_argument("--tab")

    def effect(self):
        def draw_SVG_line(x1, y1, x2, y2, width, stroke, name, parent):
            style = { 'stroke': stroke, 'stroke-width':str(width), 'fill': 'none' }
            line_attribs = {'style':str(inkex.Style(style)),
                            inkex.addNS('label','inkscape'):name,
                            'd':'M '+str(x1)+','+str(y1)+' L '+str(x2)+','+str(y2)}
            etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )
        
        def draw_SVG_circle(cx, cy, r, width, stroke, fill, name, parent):
            style = { 'stroke': stroke, 'stroke-width':str(width), 'fill':fill}
            circle_attribs = {'style':str(inkex.Style(style)),
                            inkex.addNS('label','inkscape'):name,
                            'cx':str(cx), 'cy':str(cy), 'r':str(r)}
            etree.SubElement(parent, inkex.addNS('circle','svg'), circle_attribs )
        
        def draw_SVG_tri(x1, y1, x2, y2, x3, y3, width, stroke, name, parent):
            style = { 'stroke': stroke, 'stroke-width':str(width), 'fill': 'none' }
            tri_attribs = {'style':str(inkex.Style(style)),
                            inkex.addNS('label','inkscape'):name,
                            'd':'M '+str(x1)+','+str(y1)+
                               ' L '+str(x2)+','+str(y2)+
                               ' L '+str(x3)+','+str(y3)+
                               ' L '+str(x1)+','+str(y1)+' z'}
            etree.SubElement(parent, inkex.addNS('path','svg'), tri_attribs )
            
        def draw_SVG_rect(x, y, w, h, width, fill, name, parent):
            style = { 'stroke': '#000000', 'stroke-width':str(width), 'fill':fill}
            rect_attribs = {'style':str(inkex.Style(style)),
                            inkex.addNS('label','inkscape'):name,
                            'x':str(x), 'y':str(y), 'width':str(w), 'height':str(h)}
            etree.SubElement(parent, inkex.addNS('rect','svg'), rect_attribs )    
        
        def draw_SVG_polyline(DP, width, colour, fill, name, parent):
            style = { 'stroke': colour, 'stroke-width': str(width), 'fill':fill}
            polyline_attribs = {'style':str(inkex.Style(style)),
                                 inkex.addNS('label','inkscape'):name,
                                 'd':'M' +str(DP)}
            etree.SubElement(parent, inkex.addNS('path','svg'), polyline_attribs )
            
        def draw_SVG_text(x, y, textvalue, font, text_size, parent):
            text = etree.Element(inkex.addNS('text','svg'))
            text.set('x', str(x)) 
            text.set('y', str(y))
            style = {'text-align' : 'center', 'font-family': str(font) ,'text-anchor': 'middle', 'alignment-baseline' : 'central', 'font-size' : str(text_size)}
            text.set('style', str(inkex.Style(style)))
            text.text = textvalue
            parent.append(text)
	
        so = self.options
        parent = self.svg.get_current_layer()

        border=5
        widthgrid = 200
        heightgrid = 150
         
        # Grid
        Gx=15
        Gy=9
                 
        # Get SVG document dimensions
        svg = self.document.getroot()
        width  = self.svg.unittouu(svg.get('width'))
        height = self.svg.unittouu(svg.attrib['height'])

        # Embed grid in group
        #Put in in the centre of the current view
        #t = 'translate(' + str( self.view_center[0]- width/2.0) + ',' + str( self.view_center[1]- height/2.0) + ')'
        #t = 'translate(0,' + str(height) + ') rotate(-180,0,0)'
        t = 'translate(' + str(width/2) + ',' + str(border) + ')'
        #t = 'translate(0 ,0)'
        
        g_attribs = {inkex.addNS('label','inkscape'):'SunDial_Lat:' + str( so.latitude )+';Long:'+str( so.longitude ),'transform':t}
        grid = etree.SubElement(self.svg.get_current_layer(), 'g', g_attribs)
        
        #Group for x gridlines
        g_attribs = {inkex.addNS('label','inkscape'):'XGridlines'}
        glx = etree.SubElement(grid, 'g', g_attribs)
        
        #Group for y gridlines
        g_attribs = {inkex.addNS('label','inkscape'):'YGridlines'}
        gly = etree.SubElement(grid, 'g', g_attribs)

        #Group for Hour lines vertical SunDial
        g_attribs = {inkex.addNS('label','inkscape'):'VerticalHourLines'}
        vhl = etree.SubElement(grid, 'g', g_attribs)

        #Group for Nodus vertical SunDial
        g_attribs = {inkex.addNS('label','inkscape'):'Nodus'}
        nod = etree.SubElement(grid, 'g', g_attribs)
        
        #Group for zodiac line
        g_attribs = {inkex.addNS('label','inkscape'):'Line of zodiac'}
        loz = etree.SubElement(grid, 'g', g_attribs)

# ----------Grid and border------------------------------------------------------------------
        # Border
        draw_SVG_rect(-width/2+border, -0, width-2*border, heightgrid, 0.8, 'none', 'Border', grid) #border rectangle                
        
        # XGridLine
        for i in range(Gx): #x divisons
          distX=widthgrid/(Gx-1)
          draw_SVG_line(distX*i-width/2+border, heightgrid, distX*i-width/2+border, 0, 0.1, '#0000FF', 'X'+str(i), glx)
        
        # YGridLine
        for i in range(Gy): #y divisons
          distY=heightgrid/(Gy-1)
          draw_SVG_line(-width/2+border, distY*i, width/2-border, distY*i, 0.1, '#0000FF', 'Y'+str(i), gly)
          
# ---------------------------------------------------------------------------- 
        Time = [4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
        T = {}                  #
        T_rad = {}              #
        
        # Line of zodiac
        if so.DL == 0: 
          D = []     
        if so.DL == 3: 
          D = [-23.44, 0.0001, 23.44]     
        if so.DL == 7:
          D = [-23.44, -20.15, -11.47, 0.0001, 11.47, 20.15, 23.44]    #https://www.mysundial.ca/tsp/the_zodiac.html
        
        D_rad = {}
        
        W = so.decl*pi/180      # Declination of wall in radian  https://www.mysundial.ca/tsp/vertical_declining_sundial.html
        R = so.incl*pi/180      # Inclination of wall in radian
        L = so.latitude*pi/180  # Latitude in radian

        #Text
        textvalue='Sundials for Latitude: %s; Wall azimuth: %s; Wall inclination: %s --- (c)2019 Tomas Urban ' % (so.latitude, round(W*180/pi,2), round(R*180/pi,2))
        draw_SVG_text(0, heightgrid+4, textvalue, 'san-serif', 4, gly)            

# ----------Gnomon ----------------------------------------------------------------------------
        Xf =-so.gnom*(sin(W)*cos(L))/(cos(R)*cos(W)*cos(L)-sin(R)*sin(L))
        Zf = so.gnom*((sin(R)*cos(W)*cos(L))+(cos(R)*sin(L)))/(cos(R)*cos(W)*cos(L)-sin(R)*sin(L))
        g = asin(cos(R)*cos(W)*cos(L)-sin(R)*sin(L))
        f = atan(-sin(W)*cos(L)/(sin(R)*cos(W)*cos(L)+cos(R)*sin(L)))
        P = -so.gnom/(cos(R)*cos(W)*cos(L)-sin(R)*sin(L))
        
        #Text
        #textvalue='Xf: %s; Zf: %s; g: %s; P: %s; f: %s' % (round(Xf,2), round(Zf,2), round(g*180/pi,2), round(P,2), round(f*180/pi,2))
        #draw_SVG_text(0, 120, textvalue, 'san-serif', 4, gly) 
        #textvalue='G*cos(f): %s; G*sin(f): %s; g: %s; P: %s; f: %s' % (round(so.gnom*cos(f),2), round(so.gnom*sin(f),2), round(so.gnom*180/pi,2), round(P,2), round(f*180/pi,2))
        #draw_SVG_text(0, 125, textvalue, 'san-serif', 4, gly) 
        
        # Horizont line
        draw_SVG_line(-width/2+border, Zf, width/2-border, Zf, 0.5, '#000000', 'Horizont line', nod)
        
        # Nodus
        a = (0,0)    
        b = (-Xf, Zf) 
        c = (-Xf+so.gnom*cos(f),Zf+so.gnom*sin(f)) 
        draw_SVG_tri(a[0], a[1], b[0], b[1], c[0], c[1], 0.35, '#FF00FF', 'Nodus', nod)
        draw_SVG_circle(-Xf,Zf, 2, 0.3, '#000000', '#0000FF', 'Nodus', nod)  
                     
# --------- Line of zodiac ----------------------------------------------------------------------        
        A = -cos(R)*sin(W) 
        B = -cos(R)*cos(W) 
        C = sin(R)
        #textvalue='A: %s; B: %s; C: %s' % (A, B, C)
        #draw_SVG_text(0, 125, textvalue, 'san-serif', 4, gly) 
        
        for i in range(len(D)):
          D_rad[i]= D[i]*pi/180
          DP=''
          for ii in range(len(Time)):
             T[ii]=(Time[ii]-12)*15  
             T_rad[ii]=T[ii]*pi/180
             AzSun = atan(sin(T_rad[ii])/(sin(L)*cos(T_rad[ii]) - tan(D_rad[i])*cos(L)))
             AltSun = asin(sin(D_rad[i])*sin(L) + cos(D_rad[i])*cos(L)*cos(T_rad[ii]))
             
             if T[ii] < 0:
               if AzSun > 0:
                  AzSun=AzSun+pi
               else:
                  AzSun = AzSun+2*pi 
             else:
               if AzSun >= 0:
                  AzSun=AzSun
               else:
                  AzSun = AzSun+pi                 
             
             #Text
             #textvalue='AzSun: %s; AltSun: %s; T: %s' % (round(AzSun*180/pi,2), round(AltSun*180/pi,2), Time[ii])
             #draw_SVG_text(200, 220+5*ii+100*i, textvalue, 'san-serif', 4, gly)  
             
             X0= -cos(AltSun)*sin(AzSun)
             Y0= -cos(AltSun)*cos(AzSun)
             Z0= sin(AltSun)
             
             X1=X0*cos(W)-Y0*sin(W)
             Y1=X0*sin(W)+Y0*cos(W)
             Z1=Z0
             
             X2=X1
             Y2=Y1*cos(R)-Z1*sin(R)
             Z2=Y1*sin(R)+Z1*cos(R)
             
             X3=so.gnom*X2/Y2
             Z3=-so.gnom*Z2/Y2
             p1= X0*A+Y0*B+Z0*C 
             
             Xe = X3 - Xf
             Ze = Z3 + Zf
             
             if p1 >0:
              DP = DP +' '+str(Xe)+', '+str(Ze)
          
          # draw polyline
          draw_SVG_polyline(DP, 0.5,'#FF0000', 'none', 'Zodiac line '+str(i+1), loz)
   
# --------- Time Line ----------------------------------------------------------------------   
        ALFA= atan(widthgrid/(2*heightgrid))  # Line for help
        
        for i in range(len(Time)): 
          T[i]=(Time[i]-12)*15  
          T_rad[i]=T[i]*pi/180
          TL=''
          
          D = [-23.44, -20.15, -11.47, 0.0001, 11.47, 20.15, 23.44]
          for ii in range(len(D)):
             D_rad[ii]= D[ii]*pi/180
             TL= '0, 0'
              
             AzSun = atan(sin(T_rad[i])/(sin(L)*cos(T_rad[i]) - tan(D_rad[ii])*cos(L)))
             AltSun = asin(sin(D_rad[ii])*sin(L) + cos(D_rad[ii])*cos(L)*cos(T_rad[i]))
             
             if T[i] < 0:
               if AzSun > 0:
                  AzSun=AzSun+pi
               else:
                  AzSun = AzSun+2*pi 
             else:
               if AzSun >= 0:
                  AzSun=AzSun
               else:
                  AzSun = AzSun+pi                     
             
             X0= -cos(AltSun)*sin(AzSun)
             Y0= -cos(AltSun)*cos(AzSun)
             Z0= sin(AltSun)
             
             X1=X0*cos(W)-Y0*sin(W)
             Y1=X0*sin(W)+Y0*cos(W)
             Z1=Z0
             
             X2=X1
             Y2=Y1*cos(R)-Z1*sin(R)
             Z2=Y1*sin(R)+Z1*cos(R)
             
             X3=so.gnom*X2/Y2
             Z3=so.gnom*Z2/Y2
             
             Xe = X3 - Xf
             Ze = -Z3 + Zf
             
             if Ze == 0:
               Ze = 0.0001
               
             SG = atan(Xe/Ze)
             #Xe = so.gnom /((cos(R)/tan(AzSun-W))+(sin(R)*tan(AltSun)/sin(AzSun-W))) - Xf
             #Ze = -so.gnom *((tan(R)-(tan(AltSun)/cos(AzSun-W)))/(1+(tan(R)*tan(AltSun))/cos(AzSun-W))) + Zf 
             p1= X0*A+Y0*B+Z0*C 
             
             if p1 >=0:
             #if SG <= pi and SG >=-pi:
               TL = TL +' '+str(Xe)+', '+str(Ze)
             else:
               Xe=-Xe
               Ze=-Ze
               TL = TL +' '+str(Xe)+', '+str(Ze)
               
          if T[i] < 0:
            if SG >= 0:
              SG = SG-pi
            else:
              SG = SG 
          else:
            if SG >= 0:
              SG = SG
            else:
              SG = SG+pi 
             
          if SG >= (-pi) and SG < -ALFA:
            draw_SVG_text(-widthgrid/2+5, -widthgrid/(2*tan(SG)), str(Time[i]), 'Algerian', 8, vhl)
          
          if SG > (-ALFA) and SG < ALFA:
            draw_SVG_text(heightgrid*tan(SG), heightgrid-5, str(Time[i]), 'Algerian',8, vhl)
          
          if SG > ALFA  and SG <= (pi):
            if Time[i] == 12: #workaround because y coordinate gets extreme values like "-816561967659768448.0000"
               draw_SVG_text(0, heightgrid-5, str(Time[i]), 'Algerian',8, vhl)
            else:
               draw_SVG_text(widthgrid/2-8, widthgrid/(2*tan(SG)), str(Time[i]), 'Algerian',8, vhl)
          #Text
          #textvalue='Xe: %s; Ze: %s; T: %s; SG: %s' % (round(Xe,2), round(Ze,2), Time[i], SG*180/pi)
          #draw_SVG_text(0, 220+5*i, textvalue, 'san-serif', 4, gly)
          
          # draw polyline
          draw_SVG_polyline(TL, 0.5,'#008000', 'none', 'Time line '+str(Time[i]), loz)
              
if __name__ == '__main__':
    sundialDeclining().run()
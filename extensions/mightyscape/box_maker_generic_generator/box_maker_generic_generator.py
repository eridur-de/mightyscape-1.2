#!/usr/bin/env python3
# coding: utf8

from enum import Flag
import math
from numbers import Real
from operator import pos
import os.path
from typing import List
from more_itertools import last

from numpy import False_
import inkex
import re
from lxml import etree
from inkex import paths
from inkex import bezier
from th_inkscape_path import *


#Constants defined here
WoodHingeSize = 3               #To be multiplied by thickness 
WoodHingeInternalCircle = 2     #To be multiplied by thickness  
WoodHingeRect = 1.5             #To be multiplied by thickness

SteelHingeSpacing = 0.3
RadiusSteelHingeAxis = 1.3          #Use axis about 2.6mm diameter, I use nails 2.3mmx70mm. The actual hole will be larger
RadiusSteelHingeAxisChange = 0.25   #Factor the the larger hole, multiplied by thickness
MinMove = 1e-2                  #Minimum distance betwwen two points (0.01 mm !)

SlidingLidSpaceZ = 1.3          #Space to allow easy move of the sliding lid (z or thickness). To be multiplied by thickness
SlidingLidSpaceX = 1.0          #Space to allow easy move in X direction/


#Global variables used for the whole program
thickness = 0
burn = 0
fDebug = None

def distance2Points(x0, y0, x1, y1):
    return math.sqrt((x1-x0)**2 + (y1-y0)**2)

def DebugMsg(s):
    '''
    Print a debug message into debug file if debug file is defined
    '''
    if fDebug:
        fDebug.write(s)

def OpenDebugFile():
    global fDebug
    try:
        fDebug = open( 'DebugGenericBox.txt', 'w')
    except IOError:
        pass
    DebugMsg("Start processing\n")

def CloseDebugFile():
    global fDebug
    if fDebug:
        fDebug.close()
        fDebug = None

def drawHole(path, x0, y0, dx, dy, burn):
    ''' 
    Add a rectangle starting at x0,y0 and with a length dx and width dy to the current path
    burn is the burn factor, so actual coordinates are modified by burn/2
    '''
    path.MoveTo(x0+burn/2, y0+burn/2)
    path.LineToVRel(dy-burn)
    path.LineToHRel(dx-burn)
    path.LineToVRel(-dy+burn)
    path.LineToHRel(-dx+burn)

#   Generate vertical lines for flex
#   Parameters : StartX, StartY, size, nunmber of lines and +1 if lines goes up and -1 down
def GenLinesFlex(StartX, StartY, Size, nLine, UpDown, path):
    DebugMsg("Enter GenLinesFlex, Pos="+str((StartX, StartY))+" nSegment="+str(nLine)+" Size Segment="+str(Size)+" UpDown="+str(UpDown)+" End="+str((StartX, StartY+nLine*(Size+2)-2))+'\n')
    for i in range(nLine):
        path.Line(StartX, StartY, StartX, StartY + UpDown*Size)
        DebugMsg("GenLinesFlex from "+str((StartX, StartY))+" to "+str((StartX, StartY + UpDown*Size))+'\n')
        StartY += UpDown*(Size+2)


class Ellipse:
    '''
    This class defines some functions that will be used with the coffin style lid
    '''
    def __init__(self, a, b):
        '''
        a and b are the ellipse parameters
        '''
        self.a = a
        self.b = b
        self.Start = 0
    
    def length(self):
        '''
        Compute a rather good approwimation of the ellipse length.
        Use the formula Ramanujan 2
        '''
        h = (self.a - self.b)*(self.a - self.b)/((self.a + self.b)*(self.a + self.b))
        
        l = math.pi*(self.a+self.b)*(1.0 + 3*h/(10.0+math.sqrt(4.0-3*h)))
        return l
    
    def length2Angle(self, l):
        '''
        Compute the angle which gives the given length on the ellipse.
        The ellipse perimeter couldn't be computed from known functions, so we use a discrete integral computation
        In order to save time, this function should be called with increasing value of l, i.e. it doesn't recompute values less than previous parameter l
        '''
        CurDistance = PrevDistance = self.LastDistance
        index = self.CurPoint
        while CurDistance < l and index < self.nPoints:
            PrevDistance = CurDistance
            Alpha = (index +0.5)* self.StepAngle + self.Start
            CurDistance += self.StepAngle*math.sqrt((self.a*math.sin(Alpha))**2 + (self.b*math.cos(Alpha))**2)
            index += 1
        #Will stop here, record values
        self.LastDistance = CurDistance
        self.CurPoint = index
        #Interpolate between the last points to increase precision
        if CurDistance > PrevDistance:
            Delta = (l - PrevDistance)/(CurDistance - PrevDistance)*self.StepAngle
            return (index-1)*self.StepAngle + Delta + self.Start
        else:
            return index*self.StepAngle + self.Start

    def Compute_Ellipse_Params(self, Start, End):
        self.length_ellipse = self.length() * (End - Start)/math.pi/2.0
        self.Start = Start
        self.End = End
        #Compute length between notches, each notch is about 2mm wide, total length is 2*( l_between_notches + 1)
        if self.length_ellipse < 80:
            self.l_between_notches = 1
        elif self.length_ellipse < 150:
            self.l_between_notches = 2
        elif self.length_ellipse < 250:
            self.l_between_notches = 3
        else:
            self.l_between_notches = 4
        self.nb_Ellipse_Notch = int(round(self.length_ellipse / (2*( self.l_between_notches + 1) + 2),0)) #Add a notch at the end
        self.size_Ellipse_Notch = self.length_ellipse / (self.nb_Ellipse_Notch *( self.l_between_notches + 1) + 1)
        self.Size_betweenNotches = self.l_between_notches*self.size_Ellipse_Notch
        self.nb_point_between_notches = int(round(self.Size_betweenNotches))
        self.SizeBetweenPoints = self.Size_betweenNotches / self.nb_point_between_notches
        DebugMsg("Ellipse length ="+str(self.length_ellipse)+" nb_Ellipse_Notch="+str(self.nb_Ellipse_Notch)
                 +" size_Ellipse_Notch="+str(self.size_Ellipse_Notch)+" Distance between notches="+str((self.l_between_notches+1)*self.size_Ellipse_Notch)
                 +"mm, Nb point_between nocthes="+str(self.nb_point_between_notches)
                 +" Total Size Notch ="+str(self.size_Ellipse_Notch*self.nb_Ellipse_Notch*(self.l_between_notches+1)+self.size_Ellipse_Notch)+'\n')
        #Compute the number of points used to compute the integration, and init values to be used by length2Angle
        if self.length_ellipse < 500:
            self.nPoints = 20000     #Error will be less than 0.01mm
        elif self.length_ellipse < 2000:
            self.nPoints = 100000
        else:
            self.nPoints = 500000    #Beware compute time will be higher.

    def drawNotchedEllipse(self, path, Start, End, Offset):
        '''
        draw the notched ellipse from Start Angle to End Angle using path path
        '''
        self.Compute_Ellipse_Params(Start, End)
        #Compute offset to be added to coordinates such as the start point matches with start angle
        xOffset = -self.a*math.cos(Start) + Offset[0]
        yOffset = -self.a*math.sin(Start) + Offset[1]
        self.StepAngle = (End - Start)/self.nPoints
        self.CurPoint = 0
        self.LastDistance = 0.0     #At the start point
        DebugMsg("nPoints ="+str(self.nPoints)+" StepAngle="+str(self.StepAngle)+"\n")
        DebugMsg("Offset Ellipse="+str((xOffset, yOffset))+'\n')
        '''
        #TEST
        a1 = self.length2Angle(1.0)
        DebugMsg("length2Angle(1.0) --> "+str(a1*180/math.pi)+'\n')
        a2 = self.length2Angle(2.0)
        DebugMsg("length2Angle(2.0) --> "+str(a2*180/math.pi)+'\n')
        a3 = self.length2Angle(5.0)
        DebugMsg("length2Angle(5.0) --> "+str(a3*180/math.pi)+'\n')
        a4 = self.length2Angle(10.0)
        DebugMsg("length2Angle(10.0) --> "+str(a4*180/math.pi)+'\n')
        a5 = self.length2Angle(self.length_ellipse/2.0)
        DebugMsg("length2Angle(length/2) --> "+str(a5*180/math.pi)+'\n')
        a6 = self.length2Angle(3*self.length_ellipse/4.0)
        DebugMsg("length2Angle(length*0.75) --> "+str(a6*180/math.pi)+'\n')
        a7 = self.length2Angle(self.length_ellipse-2.0)
        DebugMsg("length2Angle(length-2) --> "+str(a7*180/math.pi)+'\n')
        a8 = self.length2Angle(self.length_ellipse-1.0)
        DebugMsg("length2Angle(length-1) --> "+str(a8*180/math.pi)+'\n')
        a9 = self.length2Angle(self.length_ellipse)
        DebugMsg("length2Angle(length) --> "+str(a9*180/math.pi)+'\n')
        self.StepAngle = (End - Start)/self.nPoints
        self.CurPoint = 0
        self.LastDistance = 0.0     #At the start point
        a9 = self.length2Angle(self.length_ellipse)
        DebugMsg("length2Angle(length), fresh start --> "+str(a9*180/math.pi)+'\n')
        self.CurPoint = 0
        self.LastDistance = 0.0     #At the start point
        #End TEST
        '''
        #The side face is "internal", that is the notches are towards the exterior.
        DeltaAngleNotches = -math.pi/2      #Angle from the tangeant
        CurAngle = Start                    #Starting point
        CurDistance = 0                     #Distance on ellipse
        #Now for all notches but the last one
        for i in range(self.nb_Ellipse_Notch):
            #Start with the notch itself, but first compute the tangeant at the current point
            theta = math.atan2(self.b*math.cos(CurAngle), -self.a*math.sin(CurAngle))
            AngleNotch = theta + DeltaAngleNotches
            #Draw notch , start position on ellipse + Notch itself
            x = self.a * math.cos(CurAngle) + thickness * math.cos(AngleNotch) + xOffset
            y = self.b * math.sin(CurAngle) + thickness * math.sin(AngleNotch) + yOffset
            DebugMsg("Notch, Pos without offset="+str((self.a * math.cos(CurAngle) + thickness * math.cos(AngleNotch), self.b * math.sin(CurAngle) + thickness * math.sin(AngleNotch) ))+" WithOffset"+str((x,y))+'\n')
            path.LineTo(x, y)
            #Now the side parralel to the ellipse
            x += self.size_Ellipse_Notch * math.cos(theta)
            y += self.size_Ellipse_Notch * math.sin(theta)
            path.LineTo(x, y)
            #Now back to the ellipse, do not use the angle to come back to the ellipse but compute the position on ellipse. 
            #This will give a better approximation of the ellipse. As ellipse is convex, the interior of the notch will be shorter than the exterior
            CurDistance += self.size_Ellipse_Notch
            CurAngle = self.length2Angle(CurDistance)
            x = self.a * math.cos(CurAngle) + xOffset
            y = self.b * math.sin(CurAngle) + yOffset
            path.LineTo(x, y)
            #Now draw the interior line, but mm by mm to have a good approximation of the ellipse 
            for j in range(self.nb_point_between_notches):
                CurDistance += self.SizeBetweenPoints
                CurAngle = self.length2Angle(CurDistance)
                x = self.a * math.cos(CurAngle) + xOffset
                y = self.b * math.sin(CurAngle) + yOffset
                path.LineTo(x, y)
            #We are now ready to draw the next notch
        #Now draw the last notch, but draw it "backward" to have a symetric view.
        theta = math.atan2(self.b*math.cos(End), -self.a*math.sin(End))
        AngleNotch = theta + DeltaAngleNotches
        #Draw notch , start position on ellipse + Notch itself
        x_end_notch = self.a * math.cos(End) + thickness * math.cos(AngleNotch) + xOffset
        y_end_notch = self.b * math.sin(End) + thickness * math.sin(AngleNotch) + yOffset
        #Now the side parralel to the ellipse
        x_start_notch = x_end_notch - self.size_Ellipse_Notch * math.cos(theta)
        y_start_notch = y_end_notch - self.size_Ellipse_Notch * math.sin(theta)
        path.LineTo(x_start_notch, y_start_notch)
        path.LineTo(x_end_notch, y_end_notch)
        #For the last point, we will use the End Parameter
        x = self.a * math.cos(End) + xOffset
        y = self.b * math.sin(End) + yOffset
        path.LineTo(x,y)
        #We should be arrived at the last point now !
    
    
    def drawFlexEllipse(self, path, height, SkipFlex, Position):
        '''
        draw the flex lines for the ellipse
        After this path will be at the right/bottom corner of the flex line.
        '''
        xpos = Position[0]
        ypos = Position[1]
        #First compute angles of each notch in order to skip unnecessary flex lines
        
        self.StepAngle = (self.End - self.Start)/self.nPoints
        self.CurPoint = 0
        self.LastDistance = 0.0     #At the start point
        CurAngle = self.Start                    #Starting point
        CurDistance = 0                     #Distance on ellipse
        DeltaNotch = (self.l_between_notches+1)*self.size_Ellipse_Notch
        ListDistance = []
        #Now for all notches but the last one
        for i in range(self.nb_Ellipse_Notch):
            #Start with the notch itself, but first compute the tangeant at the current point (x0,y0)
            LastAngle = CurAngle
            # with the line equation in the form alpha*x + beta*y + gamma = 0
            alpha = self.b * math.cos(CurAngle)
            beta = self.a * math.sin(CurAngle)
            gamma = -(self.a*self.b)
            CurDistance += DeltaNotch
            CurAngle = self.length2Angle(CurDistance)
            #Now compute distance between tangeant and next point.
            x1 = self.a * math.cos(CurAngle)    
            y1 = self.b * math.sin(CurAngle)    
            #Distance betwwen line and point is (alpha * pt.x + beta * pt.y + gamma)*(alpha * pt.x + beta * pt.y + gamme)/sqrt(alpha*alpha + beta*beta)
            distance = abs(alpha * x1 + beta * y1 + gamma)/math.sqrt(alpha*alpha + beta*beta)
            ListDistance.append(distance)
            DebugMsg("LastAngle ="+str(round(180*LastAngle/math.pi,2))+" CurAngle="+str(round(180*CurAngle/math.pi,2))+" NewPoint="+str((x1,y1))+" distance="+str(distance)+'\n')
        #and for the last one, repeat the previous
        ListDistance.append(distance)
        
        '''
        Now, this is the real flex line drawing
        '''
        #Compute number of vertical lines. Each long mark should be at most 50mm long to avoid failures
        TotalHeight = height+2*thickness
        nMark = int( TotalHeight / 50) + 1       #Compute number of lines
        nMark = max(nMark, 2)   # At least 2 marks
        #Sizes of short and long lines to make flex
        LongMark = (TotalHeight / nMark) - 2.0          #Long Mark equally divide the height
        ShortMark = LongMark/2                          # And short mark should lay at center of long marks
        DebugMsg("\ndrawFlexEllipse, Pos="+str(Position)+" TotalHeight="+str(TotalHeight)+" nMark="+str(nMark)+" LongMark="+str(LongMark)+" ShortMark="+str(ShortMark)+'\n')
        for i in range(self.nb_Ellipse_Notch):
            '''
            For each set notch + interval between notches, always start with a notch, and we are external in this case
            The path is designed as it will lead to "optimal" move of the laser beam.
            
            First draw the nocth and the line inside the notch
            First edge of the notch, start with a short line, then nMark-1 long lines then a short one. This will cover the entire height+2*thickness
            The the second edge of the notch, the same but drawn backwards (bottom to top)
            and at last the line inside the notch, drawn from top to bottom
            '''
            DebugMsg("Notch("+str(i)+"), SkipFlex="+str(SkipFlex)+" ListDistance[i]="+str(ListDistance[i])+'\n')
            #Draw the edge line from Top to Bottom
            GenLinesFlex(xpos, ypos, ShortMark, 1, 1, path)
            #Then nMark-1 long Lines
            GenLinesFlex(xpos, ypos+ShortMark+2, LongMark, nMark-1, 1, path)
            #And the last short line
            GenLinesFlex(xpos, ypos+TotalHeight-ShortMark, ShortMark, 1, 1, path)
            #Now we are at the bottom of the Flex face, draw the bottom notch
            path.Line(xpos, ypos+height+thickness, xpos+self.size_Ellipse_Notch, ypos+height+thickness)
            #Then draw the same pattern for the other side of the notch, but bottom to top
            GenLinesFlex(xpos+self.size_Ellipse_Notch, ypos+TotalHeight, ShortMark, 1, -1, path)
            #Then nMark-1 long Lines
            GenLinesFlex(xpos+self.size_Ellipse_Notch, ypos+TotalHeight-ShortMark-2, LongMark, nMark-1, -1, path)
            #And the last short line that will reach the top external edge
            GenLinesFlex(xpos+self.size_Ellipse_Notch, ypos+ShortMark, ShortMark, 1, -1, path)
            #then the top notch
            path.Line(xpos+self.size_Ellipse_Notch, ypos + thickness, xpos, ypos+thickness)
            #Then draw the long lines inside the notch, first and last will be shorter by thickness
            #This line is drawn from top to bottom, and start at 1mm from the interior of the notch 
            GenLinesFlex(xpos+self.size_Ellipse_Notch/2, ypos+thickness+1, LongMark-thickness, 1, 1, path)
            #Then the remaining inside if any
            if nMark > 2:
                GenLinesFlex(xpos+self.size_Ellipse_Notch/2, ypos+3+LongMark, LongMark, nMark-2, 1, path)
            #Then the last one, shorter also, will reach internal bottom + 1mm
            GenLinesFlex(xpos+self.size_Ellipse_Notch/2, ypos+TotalHeight-LongMark-1, LongMark-thickness, 1, 1, path)
            '''
            At this point we are near the bottom line.
            First draw the external line up to the next notch
            '''
            xpos += self.size_Ellipse_Notch     #xpos is the other side of the notch
            path.Line(xpos, ypos+TotalHeight, xpos+self.Size_betweenNotches, ypos+TotalHeight)
            
            ''' 
            Then draw the lines between external top and bottom, but only if needed when SkipFlex is true
            They are 2*l_between_notches - 1 lines, so the number is always odd
            Even indexes are made of long lines only and drawn Bottom to Top.
            Odd indexes are made of one short line, nMark-2 long lines then a short line and rawn top to bottom
            As total number is odd, wa always end with long lines drawn from bottom to top, so the last position will be near the top line
            '''
            #If the ellipse is not very round at this point, in order to save laser time, draw only lines inside the notch and the line just before the notch
            drawAllLines = False
            if SkipFlex == False or ListDistance[i] > 0.5:
                drawAllLines = True
            for j in range(2*self.l_between_notches-1):
                if j == 2*self.l_between_notches-2 or drawAllLines:
                    if (j % 2)==0:
                        #even, draw long lines bottom to top
                        GenLinesFlex(xpos+(j+1)*self.size_Ellipse_Notch/2, ypos+TotalHeight-1, LongMark, nMark, -1, path)
                    else:
                        #Odd, draw short line, nMark-2 long lines then a short line, top to bottom
                        GenLinesFlex(xpos+(j+1)*self.size_Ellipse_Notch/2, ypos+1, ShortMark-1, 1, 1, path)
                        #Then nMark-1 long Lines
                        GenLinesFlex(xpos+(j+1)*self.size_Ellipse_Notch/2, ypos+ShortMark+2, LongMark, nMark-1, 1, path)
                        #And the last short line
                        GenLinesFlex(xpos+(j+1)*self.size_Ellipse_Notch/2, ypos+TotalHeight-ShortMark, ShortMark-1, 1, 1, path)
            #Now we are near the top line, draw the line up to the next notch
            path.Line(xpos, ypos, xpos+self.Size_betweenNotches, ypos)
            #And we are ready to draw the next flex pattern
            xpos += self.Size_betweenNotches
         
        '''
        Now draw the pattern for the last notch
        '''
        #Draw the edge line from Top to Bottom
        GenLinesFlex(xpos, ypos, ShortMark, 1, 1, path)
        #Then nMark-1 long Lines
        GenLinesFlex(xpos, ypos+ShortMark+2, LongMark, nMark-1, 1, path)
        #And the last short line
        GenLinesFlex(xpos, ypos+TotalHeight-ShortMark, ShortMark, 1, 1, path)
        #Now we are at the bottom of the Flex face, draw the bottom notch
        path.Line(xpos, ypos+height+thickness, xpos+self.size_Ellipse_Notch, ypos+height+thickness)
        #Then draw the same pattern for the other side of the notch, but bottom to top
        GenLinesFlex(xpos+self.size_Ellipse_Notch, ypos+TotalHeight, ShortMark, 1, -1, path)
        #Then nMark-1 long Lines
        GenLinesFlex(xpos+self.size_Ellipse_Notch, ypos+TotalHeight-ShortMark-2, LongMark, nMark-1, -1, path)
        #And the last short line that will reach the top external edge
        GenLinesFlex(xpos+self.size_Ellipse_Notch, ypos+ShortMark, ShortMark, 1, -1, path)
        #then the top notch
        path.Line(xpos+self.size_Ellipse_Notch, ypos + thickness, xpos, ypos+thickness)
        #Then draw the long lines inside the notch, first and last will be shorter by thickness
        #This line is drawn from top to bottom, and start at 1mm from the interior of the notch 
        GenLinesFlex(xpos+self.size_Ellipse_Notch/2, ypos+thickness+1, LongMark-thickness, 1, 1, path)
        #Then the remaining inside if any
        if nMark > 2:
            GenLinesFlex(xpos+self.size_Ellipse_Notch/2, ypos+3+LongMark, LongMark, nMark-2, 1, path)
        #Then the last one, shorter also, will reach internal bottom + 1mm
        GenLinesFlex(xpos+self.size_Ellipse_Notch/2, ypos+TotalHeight-LongMark-1, LongMark-thickness, 1, 1, path)
        xpos += self.size_Ellipse_Notch     #xpos is the other side of the notch
        path.MoveTo(xpos, ypos+TotalHeight)      #Path will be at the end of flex line on the BOTTOM edge. 
        DebugMsg("Path pos ="+str((xpos, ypos+TotalHeight))+'\n')

class CornerPoint:
    '''
    This class stores data about corners, to be used later to draw the faces of the box
    position is a tuple giving the position of the corner
    '''
    def __init__(self, position, radius, x_internal, y_internal, WoodHingeCorner = False):
        self.x_internal = x_internal
        self.y_internal = y_internal
        self.WoodHingeCorner = WoodHingeCorner
        if radius > 0:
            self.radius = radius
        else:
            self.radius = 0
        #Compute position of circle center and corner according to corner quadrant and internal / external flags
        if  position[0]  <= thickness:
            #Left corner        
            if x_internal:
                self.xc = position[0] + self.radius
                self.x_corner = position[0]
            else:
                self.xc = position[0] + self.radius - thickness
                self.x_corner = position[0] - thickness
        else:
            #Right corner        
            if x_internal:
                self.xc = position[0] - self.radius
                self.x_corner = position[0]
            else:
                self.xc = position[0] - self.radius + thickness
                self.x_corner = position[0] + thickness
        if  position[1]  <= thickness:
            #Top corner        
            if y_internal:
                self.yc = position[1] + self.radius
                self.y_corner = position[1] 
            else:
                self.yc = position[1] + self.radius - thickness
                self.y_corner = position[1] - thickness
        else:
            #Bottom corner        
            if y_internal:
                self.yc = position[1] - self.radius
                self.y_corner = position[1] 
            else:
                self.yc = position[1] - self.radius + thickness
                self.y_corner = position[1] + thickness

        #Compute position of line of finger joints
        if position[0]  <= thickness and position[1]  <= thickness:
            #Top left corner, compute positions of start/end of corners
            self.quadrant = 0
            self.x_start_joint = position[0] + self.radius      #X direction, do not take into account Internal/External
            self.y_start_joint = self.y_corner
            self.x_end_joint = self.x_corner
            self.y_end_joint = position[1] + self.radius        #Y Direction, do not take into account Internal/External
        elif position[1]  <= thickness:
            #Top right corner
            self.quadrant = 1
            self.x_start_joint = self.x_corner
            self.y_start_joint = position[1] + self.radius
            self.x_end_joint = position[0] - self.radius
            self.y_end_joint = self.y_corner
        elif position[0]  <= thickness:
            #Bottom left corner
            self.quadrant = 3
            self.x_start_joint = self.x_corner
            self.y_start_joint = position[1] - self.radius
            self.x_end_joint = position[0] + self.radius
            self.y_end_joint = self.y_corner
        else:
            #Bottom right corner
            self.quadrant = 2
            self.x_start_joint = position[0] - self.radius
            self.y_start_joint = self.y_corner
            self.x_end_joint = self.x_corner
            self.y_end_joint = position[1] - self.radius
        #Specific case for WoodHingeCorner, "corner" is 3/4 of the circle out of the corner
        if WoodHingeCorner:
            if self.quadrant == 0:
                self.y_end_joint = self.y_corner + WoodHingeSize*thickness
                self.x_start_joint = self.x_corner + WoodHingeSize*thickness                
            elif self.quadrant == 1:
                self.x_end_joint = self.x_corner - WoodHingeSize*thickness
                self.y_start_joint = self.y_corner + WoodHingeSize*thickness
        DebugMsg("End CornerPoint init. Corner="+str((self.x_corner, self.y_corner))+" Circle="+str((self.xc, self.yc, self.radius))+" StartJoint="+str((self.x_start_joint, self.y_start_joint))+" EndJoint="+str((self.x_end_joint, self.y_end_joint))+" WoodHingeCorner="+str(self.WoodHingeCorner)+'\n')
    
    def drawCorner(self, path):
        '''
        Draw the lines around the corner using path
        Start position of the path should be (x_end_joint, y_end_joint), not checked nor enforced
        End Position is (x_start_joint, y_start_joint)
        '''
        DebugMsg("Start drawCorner PathPos ="+str((path.x_noff, path.y_noff))+'\n')
        if self.WoodHingeCorner:
            #Specific case, draw 3/4 of a circle of radius WoodHingeSize*thickness + plus a small segment of size thickness
            if self.quadrant == 0:      #Left corner
                DebugMsg("drawCorner_WoodHinge Left: StartPoint="+str((self.x_end_joint, self.y_end_joint))+" Circle="+str((self.xc, self.yc))+ " EndPoint="+str((self.x_start_joint, self.y_start_joint))+'\n')
                path.LineToHRel(-thickness)
                path.drawQuarterCircle(self.x_corner-thickness, self.y_corner, WoodHingeSize*thickness, 3)        #Start Lower Left
                path.drawQuarterCircle(self.x_corner-thickness, self.y_corner, WoodHingeSize*thickness, 0)        #Start Upper Left
                path.drawQuarterCircle(self.x_corner-thickness, self.y_corner, WoodHingeSize*thickness, 1)        #Start Upper Right
            elif self.quadrant == 1:      #Right corner
                DebugMsg("drawCorner_WoodHinge Right: StartPoint="+str((self.x_end_joint, self.y_end_joint))+" Circle="+str((self.xc, self.yc))+ " EndPoint="+str((self.x_start_joint, self.y_start_joint))+'\n')
                path.LineToHRel(thickness)
                path.drawQuarterCircle(self.x_corner+thickness, self.y_corner, WoodHingeSize*thickness, 0)        #Start Upper Left
                path.drawQuarterCircle(self.x_corner+thickness, self.y_corner, WoodHingeSize*thickness, 1)        #Start Upper Right
                path.drawQuarterCircle(self.x_corner+thickness, self.y_corner, WoodHingeSize*thickness, 2)        #Start Lower Right
                path.LineToHRel(-thickness)
        elif self.radius > 0:
            nxc = self.xc
            nyc = self.yc
            if self.quadrant == 0:
                #if needed, draw vertical line to cope with external corner
                if self.y_internal == 0:
                    path.LineToVRel(-thickness)
                    DebugMsg("drawCorner, move dY="+str(-thickness)+"\n")
            elif self.quadrant == 1:
                #if needed, draw horizontal line to cope with external corner
                if self.x_internal == 0:
                    path.LineToHRel(thickness)
                    DebugMsg("drawCorner, move dX="+str(thickness)+"\n")
            elif self.quadrant == 2:
                #if needed, draw vertical line to cope with external corner
                if self.y_internal == 0:
                    path.LineToVRel(thickness)
                    DebugMsg("drawCorner, move dY="+str(thickness)+"\n")
            elif self.quadrant == 3:
                #if needed, draw horizontal line to cope with external corner
                if self.x_internal == 0:
                    path.LineToHRel(-thickness)
                    DebugMsg("drawCorner, move dX="+str(-thickness)+"\n")
            DebugMsg("drawCorner before circle PathPos ="+str((path.x_noff, path.y_noff))+'\n')
            DebugMsg("drawCorner radius Center"+str((nxc, nyc))+" Radius="+str(self.radius)+ " quadrant="+str(self.quadrant)+'\n')
            path.drawQuarterCircle(nxc, nyc, self.radius, self.quadrant)
            DebugMsg("drawCorner after circle PathPos ="+str((path.x_noff, path.y_noff))+'\n')
            if self.quadrant == 0:
                #if needed, draw H line to cope with external corner
                if self.x_internal == 0:
                    path.LineToHRel(thickness)
                    DebugMsg("drawCorner, move dX="+str(thickness)+"\n")
            elif self.quadrant == 1:
                #if needed, draw V line to cope with external corner
                if self.y_internal == 0:
                    path.LineToVRel(thickness)
                    DebugMsg("drawCorner, move dY="+str(thickness)+"\n")
            elif self.quadrant == 2:
                #if needed, draw H line to cope with external corner
                if self.x_internal == 0:
                    path.LineToHRel(-thickness)
                    DebugMsg("drawCorner, move dX="+str(-thickness)+"\n")
            elif self.quadrant == 3:
                #if needed, draw V line to cope with external corner
                if self.y_internal == 0:
                    path.LineToVRel(-thickness)
                    DebugMsg("drawCorner, move dY="+str(-thickness)+"\n")
        else:
            DebugMsg("drawCorner: StartPoint="+str((self.x_end_joint, self.y_end_joint))+" Corner="+str((self.x_corner, self.y_corner))+ " EndPoint="+str((self.x_start_joint, self.y_start_joint))+'\n')
            if distance2Points(self.x_end_joint, self.y_end_joint, self.x_corner, self.y_corner) > MinMove:
                #Draw line up to real corner
                path.LineTo(self.x_corner, self.y_corner)
            if distance2Points(self.x_start_joint, self.y_start_joint, self.x_corner, self.y_corner) > MinMove:
                #Draw line between corner and start of joints
                path.LineTo(self.x_start_joint, self.y_start_joint)
        DebugMsg("End drawCorner PathPos ="+str((path.x_noff, path.y_noff))+'\n')



class NotchLine:
    '''
    This class deals with straight lines with or without finger joints
    start and end parameters are actually tuples giving position (x,y) and internal/external status of each point
    The angle give the direction, it couldn't be easily computed from start and ending point because of internal/external status
    If parameter DrawHalf is < 0, only first half of line will be drawn, if > 0 only second half.
    When DrawHalf is null both parts will be drawn
    Beware, DrawHalf could be < 0 or > 0 only when Status (Internal/External) are indentical.
    '''
    def __init__(self, start, end, angle, finger_joint_size, DrawHalf=0):
        self.StartX = start[0]
        self.StartY = start[1]
        self.EndX = end[0]
        self.EndY = end[1]
        self.StartStatus = start[2]
        self.EndStatus = end[2]
        self.JointSize = finger_joint_size
        self.Angle = angle
        self.size_line_joint = 0
        self.start_line_joint_x = self.StartX
        self.start_line_joint_y = self.StartY
        self.end_line_joint_x = self.EndX
        self.end_line_joint_y = self.EndY
        self.DrawHalf = DrawHalf
        DebugMsg("NotchLine_init, StartPoint="+str(start)+" EndPoint="+str(end)+" Joint_size="+str(finger_joint_size)+" DrawHalf="+str(DrawHalf)+'\n')
        # Compute size of all finger joints
        # Compute size as a distance to deal with every direction.
        size = math.sqrt((self.EndX - self.StartX)*(self.EndX - self.StartX) + (self.EndY - self.StartY)*(self.EndY - self.StartY))
        # Round size to avoid float errors
        size = round(size, 3)
        # Compute number of joints
        if finger_joint_size == 0:          #  No finger joint
            self.nb_finger_joint = 0
            if DrawHalf != 0:               #Draw only half of line (specific case for rounded flex)
                self.EndX = (self.StartX + self.EndX) / 2
                self.EndY = (self.StartY + self.EndY) / 2
                self.end_line_joint_x = self.EndX
                self.end_line_joint_y = self.EndY
        elif start[2] == end[2]:
            # Same status, internal/external, the number of notches should be odd (at least 3)
            if size < 3 * finger_joint_size:
                self.nb_finger_joint = 0
            else:
                self.nb_finger_joint = 2*int((size-finger_joint_size) / (2*finger_joint_size)) + 1
            self.size_line_joint = self.nb_finger_joint * finger_joint_size
            # compute start and stop of finger joint line, centered on edge
            delta_pos = (size - self.size_line_joint)/2
            self.start_line_joint_x = self.StartX + delta_pos*math.cos(angle)
            self.start_line_joint_y = self.StartY + delta_pos*math.sin(angle)
            self.end_line_joint_x = self.EndX - delta_pos*math.cos(angle)
            self.end_line_joint_y = self.EndY - delta_pos*math.sin(angle)
            if DrawHalf < 0:
                #Draw only first half of notch line,i.e. end will be at the middle of segment
                self.EndX = (self.StartX + self.EndX) / 2
                self.EndY = (self.StartY + self.EndY) / 2
                self.nb_finger_joint = int(self.nb_finger_joint // 2 ) + 1     #Previous number was odd (2n+1), new notch count = n + 1, as last one will be half notch
                self.end_line_joint_x =   self.start_line_joint_x +  ((self.nb_finger_joint-0.5)*finger_joint_size)*math.cos(angle)         #Quit line at end of last notch
                self.end_line_joint_y =   self.start_line_joint_y +  ((self.nb_finger_joint-0.5)*finger_joint_size)*math.sin(angle)         #Quit line at end of last notch
                if (self.nb_finger_joint%2) == 0 and self.StartStatus:
                    #Now nb joint is even, so Internal/External status is changed so end is external
                    self.end_line_joint_x += thickness * math.cos(angle-math.pi/2)
                    self.end_line_joint_y += thickness * math.sin(angle-math.pi/2)
                    self.EndX = self.end_line_joint_x
                    self.EndY = self.end_line_joint_y
                elif (self.nb_finger_joint%2) == 0 and self.StartStatus == 0:
                    #Now nb joint is even, so Internal/External status is changed so end is internal
                    self.end_line_joint_x += thickness * math.cos(angle+math.pi/2)
                    self.end_line_joint_y += thickness * math.sin(angle+math.pi/2)
                    self.EndX = self.end_line_joint_x
                    self.EndY = self.end_line_joint_y
            elif DrawHalf > 0:
                #Draw only second half of notch line,i.e. Start will be at the middle of segment
                self.StartX = (self.StartX + self.EndX) / 2
                self.StartY = (self.StartY + self.EndY) / 2
                self.nb_finger_joint = int(self.nb_finger_joint // 2 ) + 1    #Previous number was odd (2n+1), new notch count = n+1 , as first one with half notch for the first one
                #Draw the first half notch as a shift from start position
                self.start_line_joint_x = self.StartX - 0.5*finger_joint_size*math.cos(angle)
                self.start_line_joint_y = self.StartY - 0.5*finger_joint_size*math.sin(angle)
                DebugMsg("NotchLine Init, DrawHalf=1, start_line_joint = "+str((self.start_line_joint_x, self.start_line_joint_y))+" nb_joint="+str(self.nb_finger_joint)+" EndStatus="+str(self.EndStatus)+'\n')
                if (self.nb_finger_joint%2) == 0:
                    if self.EndStatus:
                        #Now number of joints is even, so switch StartStatus to have different status (Start and End), and keep End Status
                        #In this case, Start is now External
                        self.StartStatus = 0
                        #Move Start point
                        self.start_line_joint_x += thickness * math.cos(angle-math.pi/2)
                        self.start_line_joint_y += thickness * math.sin(angle-math.pi/2)
                    else:
                        #Now number of joints is even, so switch StartStatus to have different status (Start and End), and keep End Status
                        #In this case, Start is now Internal
                        self.StartStatus = 1
                        #Move Start point
                        self.start_line_joint_x += thickness * math.cos(angle+math.pi/2)
                        self.start_line_joint_y += thickness * math.sin(angle+math.pi/2)
        else:      #Start and end have different internal/external status. Number of notches should be even
            if size < 2 * finger_joint_size:
                self.nb_finger_joint = 0
            else:
                self.nb_finger_joint = 2*int(size / (2*finger_joint_size))
            self.size_line_joint = self.nb_finger_joint * finger_joint_size
            # compute start and stop of finger joint line, centered on edge
            delta_pos = (size - self.size_line_joint)/2
            self.start_line_joint_x = self.StartX + delta_pos*math.cos(angle)
            self.start_line_joint_y = self.StartY + delta_pos*math.sin(angle)
            self.end_line_joint_x = self.EndX - delta_pos*math.cos(angle)
            self.end_line_joint_y = self.EndY - delta_pos*math.sin(angle)
        DebugMsg("NotchLine_init, size of line joints = "+str(size)+" Nb_Joint="+str(self.nb_finger_joint)+" size_line_joint="+str(self.size_line_joint)+" start_line_joint"+str(( self.start_line_joint_x, self.start_line_joint_y))+" end_line_joint="+str((self.end_line_joint_x, self.end_line_joint_y))+'\n')

    def ModifyNotchLine(self, SizeCut, CutOnStart):
        '''
        This function modify a vertical notch line to take into account cuts needed by WoodHinge
        Beware, only safe to call with vertical lines, unexpected results in other cases
        SizeCut is the Size of cut, last notch will be at last 1.5 thickness far from this cut
        CutOnStart is True when the cut is at the start of the line. Beware could be top or bottom if angle is 90 or 270°
        '''
        DebugMsg("Enter ModifyNotchLine, CutOnStart="+str(CutOnStart)+" angle="+str(self.Angle)+" Start ="+str(self.StartY)+" End="+str(self.EndY)+" nb_finger_joint="+str(self.nb_finger_joint)+" SizeJoint="+str(self.JointSize)+" start_line_joint_y="+str(self.start_line_joint_y)+" end_line_joint_y="+str(self.end_line_joint_y)+'\n')
        Dir = 0     #Bottom to Top if Dir = 0
        SizeCut -= thickness    #In all cases, reduce sizecut because top and bottom lines are always external in Y

        if abs(self.Angle - math.pi/2) < 1e-6:
            Dir = 1     # Top to Bottom
        if Dir == 1 and CutOnStart:
            #Change line, shorten of SizeCut at the start, in this case start at end of line
            nbNotch = 1
            ypos =  self.end_line_joint_y 
            Limit = SizeCut + self.StartY + 1.5*thickness
            DebugMsg("WHC_init_1 : ypos ="+str(ypos)+" nbNotch ="+str(nbNotch)+"  Limit="+str(Limit)+" NewSizeCut="+str(SizeCut)+"\n")
            while ypos > Limit:
                ypos -= 2*self.JointSize
                nbNotch += 2
                DebugMsg("WHC : ypos ="+str(ypos)+" nbNotch ="+str(nbNotch)+"\n")
            #Now change the line
            if nbNotch > 3:
                nbNotch -= 2    #Sub last step which was too far
                self.start_line_joint_y = self.end_line_joint_y - nbNotch*self.JointSize
                self.nb_finger_joint = nbNotch
                self.StartY += SizeCut
            else:
                self.nb_finger_joint = 0        #No more notch
                self.StartY += SizeCut
        elif Dir==1 and CutOnStart == False:
            #Change line, shorten of SizeCut at the end, in this case start at start of line
            nbNotch = 1
            ypos =  self.start_line_joint_y 
            Limit = self.EndY - SizeCut - 1.5*thickness
            DebugMsg("WHC_init_2 : ypos ="+str(ypos)+" nbNotch ="+str(nbNotch)+"  Limit="+str(Limit)+" NewSizeCut="+str(SizeCut)+"\n")
            while ypos < Limit:
                ypos += 2*self.JointSize
                nbNotch += 2
                DebugMsg("WHC : ypos ="+str(ypos)+" nbNotch ="+str(nbNotch)+"\n")
            #Now change the line
            if nbNotch > 3:
                nbNotch -= 2    #Sub last step which was too far
                #Cut on end, so change EndY and end_line_joint_y
                self.end_line_joint_y = self.start_line_joint_y + nbNotch*self.JointSize
                self.nb_finger_joint = nbNotch
                self.EndY -= SizeCut
            else:
                self.nb_finger_joint = 0        #No more notch
                self.EndY -= SizeCut
            if self.EndY < self.end_line_joint_y:           #Limit send_line_joint_y to be lower or equal than EndY
                self.end_line_joint_y = self.EndY
        elif Dir==0 and CutOnStart:
            #Change line, shorten of SizeCut at the start, in this case this the bottom of line because Angle is 270°
            nbNotch = 1
            ypos =  self.end_line_joint_y 
            Limit = self.StartY - SizeCut - 1.5*thickness
            DebugMsg("WHC_init_3 : ypos ="+str(ypos)+" nbNotch ="+str(nbNotch)+"  Limit="+str(Limit)+" NewSizeCut="+str(SizeCut)+"\n")
            while ypos < Limit:
                ypos += 2*self.JointSize
                nbNotch += 2
                DebugMsg("WHC : ypos ="+str(ypos)+" nbNotch ="+str(nbNotch)+"\n")
            #Now change the line
            if nbNotch > 3:
                nbNotch -= 2    #Sub last step which was too far
                #Change at start of line
                self.start_line_joint_y = self.end_line_joint_y + nbNotch*self.JointSize
                self.nb_finger_joint = nbNotch
                self.StartY -= SizeCut
            else:
                self.nb_finger_joint = 0        #No more notch
                self.StartY -= SizeCut
        elif Dir==0 and CutOnStart == 0:
            #Change line, shorten of SizeCut at the end, in this case this the top of line because Angle is 270°
            nbNotch = 1
            ypos =  self.start_line_joint_y 
            Limit = self.EndY + SizeCut + 1.5*thickness
            DebugMsg("WHC_init_4 : ypos ="+str(ypos)+" nbNotch ="+str(nbNotch)+"  Limit="+str(Limit)+" NewSizeCut="+str(SizeCut)+"\n")
            while ypos > Limit:
                ypos -= 2*self.JointSize
                nbNotch += 2
                DebugMsg("WHC : ypos ="+str(ypos)+" nbNotch ="+str(nbNotch)+"\n")
            #Now change the line
            if nbNotch > 3:
                nbNotch -= 2    #Sub last step which was too far
                self.end_line_joint_y = self.start_line_joint_y - nbNotch*self.JointSize
                self.nb_finger_joint = nbNotch
                self.EndY += SizeCut            #New EndY is below the previous one
            else:
                self.nb_finger_joint = 0        #No more notch
                self.EndY += SizeCut
            if self.EndY < self.end_line_joint_y:
                self.end_line_joint_y = self.EndY
        DebugMsg("Exit ModifyNotchLine, angle="+str(self.Angle)+" Start ="+str(self.StartY)+" End="+str(self.EndY)+" nb_finger_joint="+str(self.nb_finger_joint)+" SizeJoint="+str(self.JointSize)+" start_line_joint_y="+str(self.start_line_joint_y)+" end_line_joint_y="+str(self.end_line_joint_y)+'\n')
        
    def drawNotchLine(self, path):
        '''
        Draw the actual line, starting at current position of path.
        The position should be StartX, StartY, this is not checked or enforced to avoid unwanted moves
        Each finger joint is JointSize long but there is a correction to take into account the burn factor (thickness of the cutting line).
        So each external joint is actually JointSize+2*burn long and Internal joints are JointSize-2*burn
        '''
        if self.nb_finger_joint == 0:
            #Easy case, no finger joint, draw a straight line
            path.LineTo(self.EndX, self.EndY)
            return
        #Normal case, there are finger joint(s)
        #First compute angles. 
        #AngleJoint is the angle for drawing the first part of the finger joint
        #If start point is internal, AngleJoint should be Angle - pi/2, else it should be Angle + pi/2
        if self.StartStatus:        #internal
            AngleJoint = self.Angle - math.pi/2
            DeltaBurn = -burn
        else:
            AngleJoint = self.Angle + math.pi/2
            DeltaBurn = burn
        DebugMsg("drawNotchLine, Angle ="+str(round(self.Angle*180/math.pi))+" AngleJoint="+str(round(AngleJoint*180/math.pi))+'\n')
        DebugMsg("start_line_joint="+str((self.start_line_joint_x, self.start_line_joint_y))+"  JointSize="+str(self.JointSize)+" DeltaBurn="+str(DeltaBurn)+'\n')
        #First go up to start of notch line + first joint + burn correction
        DebugMsg("Position before drawNotchLine : "+str((path.x_noff, path.y_noff))+'\n')
        xcur = self.start_line_joint_x + (self.JointSize+DeltaBurn)*math.cos(self.Angle)
        ycur = self.start_line_joint_y + (self.JointSize+DeltaBurn)*math.sin(self.Angle)
        path.LineTo(xcur, ycur)
        DebugMsg("First Point="+str((xcur, ycur))+'\n')
        i = self.nb_finger_joint - 1
        while i > 0:
            #The start drawing finger joint
            path.LineToRel(thickness*math.cos(AngleJoint), thickness*math.sin(AngleJoint))
            #Compute next AngleJoint for return move if necessary
            AngleJoint = AngleJoint + math.pi
            if AngleJoint > 2*math.pi:
                AngleJoint -= 2*math.pi         #Keep angle between 0 and 2*pi
            #idem for burn factor
            DeltaBurn = -DeltaBurn
            #Then line which is JointSize long and take into account the burn factor, draw half finger joint when last of first half
            if self.DrawHalf < 0 and i == 1:
                path.LineToRel((self.JointSize/2+DeltaBurn)*math.cos(self.Angle), (self.JointSize/2+DeltaBurn)*math.sin(self.Angle))
            elif i > 1:     #Do not draw last segment, not necessary, will be completed by next path.LIneTo
                path.LineToRel((self.JointSize+DeltaBurn)*math.cos(self.Angle), (self.JointSize+DeltaBurn)*math.sin(self.Angle))
            i -= 1
        #Then draw last part, up to end point
        #Do not check if necessary because of burn factor, last position is not the real end of notch line.
        path.LineTo(self.EndX, self.EndY)
        DebugMsg("Last LineTo End ="+str((self.EndX, self.EndY))+'\n')

class FlexLines:
    '''
    This class deals and draw set of flex lines to round a corner
    '''
    def drawFlexLines(self, Position, Height, Radius, path):
        '''
        First compute how many segment per line. Segment length should be kept short, < 50mm or so, so high boxes means number of lines
        Also compute distance between lines, which depend on radius. Shorter radius means smaller distance between lines
        But keep min distance at about 1mm minimum and 1.5mm max, after this value flex is quite hard to bend !
        '''
        if Height+2*thickness < 30:
            nSegmentFlex = 1
        elif Height+2*thickness < 80:
            nSegmentFlex = 2
        elif Height+2*thickness < 150:
            nSegmentFlex = 3
        else:
            nSegmentFlex = int((Height+2*thickness) // 50)
        #Then compute distance between flex lines. The basic idea is to have a minimum of 15 lines per corner, with lines distant at least of 1mm
        #But also ensure that distance between lines is at most at 2mm 
        round_distance = Radius*math.pi/2
        flex_line_spacing = round_distance / 14
        flex_line_spacing = max(flex_line_spacing, 1.0)
        flex_line_spacing = min(flex_line_spacing, 1.5)
        nb_flex_lines =  int(round(round_distance / flex_line_spacing,0))
        DebugMsg("sizeround ="+str(round_distance)+" flex_line_spacing="+str(flex_line_spacing)+" nb_flex_lines="+str(nb_flex_lines)+" size="+str(nb_flex_lines*flex_line_spacing)+"\n")        
        #nb_flex_lines should be odd
        nb_flex_lines |= 1 
        flex_line_spacing = round_distance / (nb_flex_lines-1)  #Real distance between lines 
        length_flex_segment_case1 = (Height+2*thickness - 2*nSegmentFlex) / nSegmentFlex      #Case 1, 1/2 segment starting at top, n-1 segments and 1/2 segment up to bottom
        length_flex_segment_case2 = (Height+2*thickness - 2*(nSegmentFlex+1)) / nSegmentFlex  #Case 2, n segments equally spaced (2mm) from top to bottom
        DebugMsg("nSegmentFlex="+str(nSegmentFlex)+" sizeround ="+str(round_distance)+" flex_line_spacing="+str(flex_line_spacing)+" nb_flex_lines="+str(nb_flex_lines)+" size="+str(nb_flex_lines*flex_line_spacing)+"\n")
        #Now draw set of flex lines
        for i in range(nb_flex_lines):
            if i % 2:
                #In this case draw nSegmentFlex segments which are identical. First segment start at 2 mm above bottom line, segments are 2mm spaced
                for j in range(nSegmentFlex):
                    path.MoveTo(Position + i * flex_line_spacing, Height+thickness-2-j * (length_flex_segment_case2+2) )
                    path.LineToVRel(-length_flex_segment_case2)
            else:
                #In this case draw a first segment starting at -thickness (top), segment is length_flex_segment_even/2 long
                path.MoveTo(Position + i * flex_line_spacing, -thickness )
                path.LineToVRel(length_flex_segment_case1/2)        #One half segment
                #Then nSegmentFlex-1 which are 
                for j in range(nSegmentFlex-1):
                    path.MoveTo(Position + i * flex_line_spacing, j*(length_flex_segment_case1+2) + length_flex_segment_case1/2 + 2 - thickness )
                    path.LineToVRel(length_flex_segment_case1)
                path.MoveTo(Position + i * flex_line_spacing, Height+thickness - length_flex_segment_case1/2)
                path.LineTo(Position + i * flex_line_spacing, Height+thickness )

        
class FlexFace:
    '''
    This class deal with flex faces, which are used as vertical faces when rounded corners are used.
    '''
    def __init__(self, FlexBandList, isLid, zbox, z_joint, InkscapeGroup, PositionInPage):
        '''
        The list FlexBandList contains all elements to be used on top and bottom line of the flex face. 
        Each element is in a tuple 
            item 0 is the path id
            item 1 is Start_Internal
            item 2 is End Internal
            item 3..n are tuple with ( size, size_joints top, radius rounded corner, size_joints bottom, [hasCircle])
            Last item is always with radius = 0
        '''
        self.FlexBandList = FlexBandList
        self.z_joint = z_joint
        self.height = zbox
        self.isLid = isLid
        #Update PositionInPage to take into account finger joints (only OK if it is a simple shape with finger joints).
        PositionInPage[0] -= thickness
        PositionInPage[1] -= thickness
        
        FlexElt = FlexBandList[3]
        if len(FlexElt) == 5 and FlexElt[4] and self.isLid == False:
            #Change path offset to take into account the circle...
            PositionInPage[0] -= WoodHingeSize*thickness
            PositionInPage[1] -= WoodHingeSize*thickness
        elif len(FlexBandList) > 4:
            FlexElt = FlexBandList[len(FlexBandList)-1]
            if len(FlexElt) == 5 and FlexElt[4] and self.isLid == False:
                #Change path offset to take into account the circle... but only on y here
                PositionInPage[1] -= WoodHingeSize*thickness
          
            
        self.BoundingBox = (-PositionInPage[0], -PositionInPage[1], -PositionInPage[0], -PositionInPage[1])
        
        #If needed, create path which will be used to draw the face
        #The path will be in the group InkscapeGroup
        name = FlexBandList[0]
        if isLid:
            name = 'Lid_'+name
        self.path = th_inkscape_path(PositionInPage, InkscapeGroup, name)
        #Remember these 2 parameters for Side Notch lines
        self.InkscapeGroup = InkscapeGroup
        self.BaseName = FlexBandList[0]
        
    def Close(self):
        '''
        Close and write the path after drawing is done
        '''
        self.path.Close()
        self.path.GenPath()

    def drawClip(self, size_clip, UpDown):
        ''' Draw a single clip pattern
            The clip is vertical, with length size_clip and width size_clip/4
            Add clip to current path, use LineTo
            New path position will be end of clip
            If draw up, UpDown should be 1
        '''
        if UpDown != 1:
            UpDown=-1       #Will draw negative
        #First draw vertical line which is .31*size
        self.path.LineToVRel(size_clip*0.3075*UpDown)
        #Then small bezier curve
        self.path.BezierRel(0, size_clip*0.036241333*UpDown, size_clip*0.045356111, size_clip*0.052734333*UpDown, size_clip*0.0685556, size_clip*0.025*UpDown)
        #then line 
        self.path.LineToRel(size_clip*0.132166667, size_clip*-0.157555556*UpDown)
        #then bezier
        self.path.BezierRel(size_clip*0.016710556, size_clip*-0.02*UpDown, size_clip*0.05, size_clip*-0.008*UpDown, size_clip*0.05, size_clip*0.017795167*UpDown)
        #Then vertical line
        self.path.LineToVRel(size_clip*0.615*UpDown)
        #then bezier
        self.path.BezierRel(0, size_clip*0.026*UpDown, size_clip*-0.032335, size_clip*0.037760389*UpDown, size_clip*-0.05, size_clip*0.017795167*UpDown)
        #Then line
        self.path.LineToRel(size_clip*-0.132166667, size_clip*-0.157555556*UpDown)
        #then last bezier
        #c -0.42188,0.5 -1.23438,0.203125 -1.23438,-0.449219
        self.path.BezierRel(size_clip*-0.023437778, size_clip*-0.027777778*UpDown, size_clip*-0.068576667, size_clip*-0.011284722*UpDown, size_clip*-0.068576667, size_clip*0.025*UpDown)
        #then last line
        self.path.LineToVRel(size_clip*0.3075*UpDown)

    def drawFlexFace(self, ClosePath):
        '''
        Draw the flex face into its path, close path if argument is true after drawing
        This method is only valid when the corners are straight.
        When all corners are rounded, drawRoundedFlexFace should be used.
        '''
        ListFlexLines = []
        #Build Top line
        xpos = 0
        if self.isLid: 
            TopJointOff = 3
            BotJointOff = 1
        else:
            TopJointOff = 1
            BotJointOff = 3
        leftCircle = False
        leftCircleCut = False
        leftCirclePos = 0
        rightCircle = False
        rightCircleCut = False
        rightCirclePos = 0
        LastRadius = 0      #Always start with straight corner
        DebugMsg("\nEnter drawFlexFace, isLid="+str(self.isLid)+" Number of elements in list="+str(len(self.FlexBandList))+"Height="+str(self.height)+"\n")
        #Now read all elements (3..N)
        for i in range(3, len(self.FlexBandList)):
            FlexElement = self.FlexBandList[i]
            DebugMsg("Top line, i="+str(i)+" FlexElement="+str(FlexElement)+'\n')
            if i == 3 and len(FlexElement) == 5 and FlexElement[4] and self.isLid == False:
                #Specific case of left wood hinge face, draw circle on top
                leftCircle = True
                leftCirclePos = -thickness        #Remember circle position
                #In this case start position is 0, (WoodHingeSize-1)*thickness
                self.path.MoveTo(0, (WoodHingeSize-1)*thickness)
                self.path.LineToHRel(-thickness)
                self.path.drawQuarterCircle(-thickness, -thickness, WoodHingeSize*thickness, 3)        #Start Lower Left
                self.path.drawQuarterCircle(-thickness, -thickness, WoodHingeSize*thickness, 0)        #Start Upper Left
                self.path.drawQuarterCircle(-thickness, -thickness, WoodHingeSize*thickness, 1)        #Start Upper Right
                #After this position should be WoodHingeSize*thickness-thickness, -thickness
                self.path.LineTo(FlexElement[0] - FlexElement[2], -thickness)
                xpos += FlexElement[0] - LastRadius - FlexElement[2]
            elif i == 3 and len(FlexElement) == 5 and FlexElement[4] and self.isLid == True:
                leftCircleCut = True
                if i == 3:
                    #Draw path start 
                    if self.FlexBandList[1]:                       #First item : Start point if internal
                        self.path.MoveTo(0, -thickness)            # Start position (0, -thickness) because flex band is always external in Y direction
                    else:
                        self.path.MoveTo(-thickness, -thickness)  # Start position (-thickness, -thickness) because x external and flex band is always external in Y direction
                        self.path.LineTo(0, -thickness)
                DebugMsg("Element "+str(i)+": xpos="+str(xpos)+' Size ='+str(FlexElement[0])+' radius ='+str(FlexElement[2])+' --> '+str(FlexElement[2]*math.pi/2)+'\n')
                #First Notch Line, with length SizeEdge - SizeOfRoundedCorners
                hLine = NotchLine((xpos, -thickness, 0), (xpos+FlexElement[0]-(LastRadius+FlexElement[2]), -thickness, 0), 0.0, FlexElement[TopJointOff])
                hLine.drawNotchLine(self.path)
                xpos += FlexElement[0] - LastRadius - FlexElement[2]
            elif i == len(self.FlexBandList) - 1 and  len(FlexElement) == 5 and FlexElement[4] and self.isLid == False:
                #Specific case of right wood hinge face, draw circle on top
                rightCircle = True
                rightCirclePos = xpos        #Remember circle position
                #In this case start position is 0, (WoodHingeSize-1)*thickness
                self.path.LineTo( xpos + FlexElement[0] - LastRadius - (WoodHingeSize-1)*thickness, -thickness)
                xpos += FlexElement[0] - LastRadius
                rightCirclePos = xpos + thickness       #Remember circle position
                self.path.drawQuarterCircle(rightCirclePos, -thickness, WoodHingeSize*thickness, 0)        #Start Upper Left
                self.path.drawQuarterCircle(rightCirclePos, -thickness, WoodHingeSize*thickness, 1)        #Start Upper Right
                self.path.drawQuarterCircle(rightCirclePos, -thickness, WoodHingeSize*thickness, 2)        #Start Lower Right
                self.path.LineToHRel(-thickness)
            elif i == len(self.FlexBandList) - 1 and  len(FlexElement) == 5 and FlexElement[4] and self.isLid == True:
                rightCircleCut = True
                DebugMsg("Element "+str(i)+": xpos="+str(xpos)+' Size ='+str(FlexElement[0])+' radius ='+str(FlexElement[2])+' --> '+str(FlexElement[2]*math.pi/2)+'\n')
                #First Notch Line, with length SizeEdge - SizeOfRoundedCorners
                hLine = NotchLine((xpos, -thickness, 0), (xpos+FlexElement[0]-(LastRadius+FlexElement[2]), -thickness, 0), 0.0, FlexElement[TopJointOff])
                hLine.drawNotchLine(self.path)
                xpos += FlexElement[0] - LastRadius - FlexElement[2]
            else:
                if i == 3:
                    #Draw path start 
                    if self.FlexBandList[1]:                       #First item : Start point if internal
                        self.path.MoveTo(0, -thickness)            # Start position (0, -thickness) because flex band is always external in Y direction
                    else:
                        self.path.MoveTo(-thickness, -thickness)  # Start position (-thickness, -thickness) because x external and flex band is always external in Y direction
                        self.path.LineTo(0, -thickness)
                DebugMsg("Element "+str(i)+": xpos="+str(xpos)+' Size ='+str(FlexElement[0])+' radius ='+str(FlexElement[2])+' --> '+str(FlexElement[2]*math.pi/2)+'\n')
                #First Notch Line, with length SizeEdge - SizeOfRoundedCorners
                hLine = NotchLine((xpos, -thickness, 0), (xpos+FlexElement[0]-(LastRadius+FlexElement[2]), -thickness, 0), 0.0, FlexElement[TopJointOff])
                hLine.drawNotchLine(self.path)
                xpos += FlexElement[0] - LastRadius - FlexElement[2]
            #Then the line corresponding to rounded corner, also add coordinates for Flex lines
            if FlexElement[2] > 0:
                self.path.LineTo(xpos + FlexElement[2]*math.pi/2, -thickness)
                ListFlexLines.append((xpos, FlexElement[2]))
            xpos += FlexElement[2]*math.pi/2
            LastRadius = FlexElement[2]         #For the next edge
        if rightCircle == 0:
            if self.FlexBandList[2] == 0:           #External end ?
                self.path.LineTo(xpos + thickness, -thickness)
                xpos += thickness
            self.path.LineTo(xpos, 0)
        DebugMsg('Vertical Line 1, xpos='+str(xpos)+'\n')
        #Then Vertical notch line, 
        vLine = NotchLine((xpos, 0, self.FlexBandList[2]), (xpos, self.height, self.FlexBandList[2]), math.pi/2, self.z_joint)
        if rightCircle:
            #In this case modify the line just created
            #Specific case, shorten Right line of notches to take into account the wood hinge circle. Delete some notches on top
            SizeCut = WoodHingeSize*thickness
            vLine.ModifyNotchLine(SizeCut, True)        #Last parameter, CutOnStart = True
        elif rightCircleCut:
            #In this case modify the line just created
            #Specific case, shorten Right line of notches to take into account the wood hinge circle cut. Delete some notches on bottom
            SizeCut = WoodHingeSize*thickness
            vLine.ModifyNotchLine(SizeCut, False)        #Last parameter, CutOnStart = False
        vLine.drawNotchLine(self.path)      #Draw the line of notches
        if rightCircleCut:
            #Then the cut. Choose 0.95*SizeCut because the actual circle is NOT centered of this vertical edge but shifted by thickness
            self.path.LineTo(xpos, self.height+thickness-SizeCut*0.95)
            #Then the rounded cut, almost a quarter of circle, radius SizeCut
            self.path.Bezier(xpos-SizeCut*0.23, self.height+thickness-SizeCut*0.90, 
                        xpos-SizeCut+thickness, self.height+thickness-SizeCut*0.551916, 
                        xpos-SizeCut+thickness, self.height+thickness)
        else:
            self.path.LineTo(xpos, self.height+thickness)
        DebugMsg("Start bottom line, reverse\n")
        #Then Bottom line (reverse from top line)
        if self.FlexBandList[2] == 0:           #External end ?
            self.path.LineTo(xpos - thickness, self.height+thickness)
            xpos -= thickness
        for i in range(len(self.FlexBandList)-1, 2, -1):        #Start at end up to third element
            #For reverse drawing, should have the radius of the next corner
            if i > 3:
                NextRadius = self.FlexBandList[i-1][2]
            else:
                NextRadius = 0
            FlexElement = self.FlexBandList[i]
            DebugMsg("Element "+str(i)+": xpos="+str(xpos)+' Size ='+str(FlexElement[0])+' radius ='+str(FlexElement[2])+' --> '+str(FlexElement[2]*math.pi/2)+' Next Radius='+str(NextRadius)+'\n')
            #First the line corresponding to rounded corner (reverse from previous)
            DebugMsg("Draw line for rounded corner, size ="+str(FlexElement[2]*math.pi/2)+" New xpos="+str(xpos - FlexElement[2]*math.pi/2)+'\n')
            if FlexElement[2] > 0:
                self.path.LineTo(xpos - FlexElement[2]*math.pi/2, self.height+thickness)
                xpos -= FlexElement[2]*math.pi/2
            #Then Notch Line
            if i == 3 and leftCircleCut:
                #specific case, draw up to start of cut
                self.path.LineTo(SizeCut - thickness , self.height+thickness)
                xpos = 0    #Not true yet, but needed to place the vertical line at the right position
                DebugMsg("leftCircleCut True, pathto "+str((SizeCut - thickness , self.height+thickness))+" xpos ="+str(xpos)+"\n")
            else:
                hLine = NotchLine((xpos, self.height+thickness, 0), (xpos-(FlexElement[0]-FlexElement[2]-NextRadius), self.height+thickness, 0), math.pi, FlexElement[BotJointOff])
                hLine.drawNotchLine(self.path)
                xpos -= FlexElement[0] - NextRadius - FlexElement[2]
        if leftCircleCut == False:
            if self.FlexBandList[1] == 0:           #External Start ?
                self.path.LineTo(xpos - thickness, self.height+thickness)
                xpos -= thickness
            self.path.LineTo(xpos, self.height)
        #Then Vertical notch line for left edge
        vLine = NotchLine((xpos, self.height, self.FlexBandList[1]), (xpos, 0, self.FlexBandList[1]), -math.pi/2, self.z_joint)
        if leftCircle:
            SizeCut = WoodHingeSize*thickness
            vLine.ModifyNotchLine(SizeCut, False)        #Last parameter, CutOnStart = False, because we start at bottom
        elif  leftCircleCut:    
            #In this case, shorten the notch line on bottom because of the circle cut
            SizeCut = WoodHingeSize*thickness
            vLine.ModifyNotchLine(SizeCut, True)        #Last parameter, CutOnStart = True, because we start at bottom
            #Draw the rounded cut, almost a quarter of circle, radius ExtRadius
            self.path.Bezier(SizeCut-thickness, self.height+thickness-SizeCut*0.551916
                             , SizeCut*0.23, self.height+thickness-SizeCut*0.90
                             , 0, self.height+thickness-SizeCut*0.95)


        vLine.drawNotchLine(self.path)
        DebugMsg('Vertical Line 2, xpos='+str(xpos)+'\n')
        
        #Draw up to -thickness because external in Y direction
        if leftCircle:
            self.path.LineTo(xpos, SizeCut - thickness)
        else:
            self.path.LineTo(xpos, -thickness)

        # If circle, draw interior and rectangles
        #Case with WoodHingeCorner, draw circle and rectangle
        if leftCircle:        
            #Draw the circle internal to the hinge, radius is 2*thickness mm
            CircleRadius = WoodHingeInternalCircle*thickness
            self.path.drawCircle(leftCirclePos, -thickness, CircleRadius)
            #Then the internal rectangle, rectangle height is 1.5*thickness
            RectHeight = WoodHingeRect*thickness
            self.path.MoveTo(leftCirclePos, -thickness)     #Starting point Ext/Bottom
            self.path.LineToVRel(-RectHeight)            #Ext/Top
            self.path.LineToHRel(thickness)              #Int/Top
            self.path.LineToVRel(RectHeight)             #Int Bottom 
            self.path.LineToHRel(-thickness)             #Return to start
        if rightCircle:        
            #Draw the circle internal to the hinge, radius is 2*thickness mm
            CircleRadius = WoodHingeInternalCircle*thickness
            self.path.drawCircle(rightCirclePos, -thickness, CircleRadius)
            #Then the internal rectangle, rectangle height is 1.5*thickness
            RectHeight = WoodHingeRect*thickness
            self.path.MoveTo(rightCirclePos, -thickness)     #Starting point Ext/Bottom
            self.path.LineToVRel(-RectHeight)             #Ext/Top
            self.path.LineToHRel(-thickness)             #Int/Top
            self.path.LineToVRel(RectHeight)            #Int Bottom 
            self.path.LineToHRel(thickness)              #Return to start


        #Now draw flex lines
        
        for FlexLinePos in ListFlexLines:
            Flex = FlexLines()
            Flex.drawFlexLines(FlexLinePos[0], self.height, FlexLinePos[1], self.path)
        #Get bounding box of path
        self.BoundingBox = (self.path.xmin, self.path.ymin, self.path.xmax, self.path.ymax)

        if ClosePath:
            self.path.Close()
            self.path.GenPath()

    def drawRoundedFlexFace(self, ClosePath):
        '''
        Draw a Flex band when all corners are rounded. This is a specific case because there are clips at the center of back face
        Back face should be the first in list
        '''
        
        #Compute clips number and position, zone with clips will be between thickness and zbox - thickness 
        zoneclips = self.height - 2*thickness
        #Size of clips is dependant to size of zoneclips
        if zoneclips < 50:
            sizeclips = 10
        else:
            sizeclips = 18
        nbclips = int(zoneclips // sizeclips)
        if nbclips == 0:
            inkex.errormsg('Box is not high enough, no room for clips')
            CloseDebugFile()
            return
        DebugMsg("\ndrawRoundedFlexFace, sizeclips="+str(sizeclips)+" nbclips="+str(nbclips)+'\n')
        ListFlexLines = []
        LastRadius = self.FlexBandList[6][2]       # Radius of left back corner
        xpos = 0
        FlexElement = self.FlexBandList[3]
        DebugMsg("First Half notch line, size ="+str(FlexElement[0])+" Size Round BackLeft="+str(LastRadius)+" Size Round BackRight="+str(FlexElement[2])+'\n')
        #The notch line will be centered on xpos (0), so should start at -(SizeNotchLine-SizeRadius_BackLeft-SizeRadius_BackRight)/2
        First_hLine = NotchLine((-(FlexElement[0]-FlexElement[2] - LastRadius)/2, -thickness, 0), ((FlexElement[0]-FlexElement[2] - LastRadius)/2, -thickness, 0), 0.0, FlexElement[1], 1)      #Draw only second half
        if First_hLine.StartStatus == 0:
            self.path.MoveTo(0, -thickness)   # Start position (0, -thickness) because flex band is external in Y direction, and this side start internal in X
            DebugMsg("Start Point is "+str((self.path.x_noff, self.path.y_noff))+'\n')
        else:
            self.path.MoveTo(0, 0)   # Start position (0, 0) because flex band is internal in Y direction, and this side start internal in X
            DebugMsg("Start Point is "+str((self.path.x_noff, self.path.y_noff))+'\n')
        First_hLine.drawNotchLine(self.path)
        xpos = (FlexElement[0]-FlexElement[2]-LastRadius)/2
        DebugMsg("After drawing first half of notch line, pos ="+str((self.path.x_noff, self.path.y_noff))+'\n')
        ListFlexLines.append((xpos, FlexElement[2]))            #Add this position to draw flex lines.
        #Then the line corresponding to rounded corner
        if FlexElement[2] > 0:
            self.path.LineTo(xpos + FlexElement[2]*math.pi/2, -thickness)
        xpos += FlexElement[2]*math.pi/2
        DebugMsg("Line corresponding to back right corner, l="+str(FlexElement[2]*math.pi/2)+" xpos="+str(xpos)+'\n')
        LastRadius = FlexElement[2]
        #Now read all elements (4..N-1) --> 4..6 here
        for i in range(4, 7):
            FlexElement = self.FlexBandList[i]
            DebugMsg("Element "+str(i)+": xpos="+str(xpos)+' Size ='+str(FlexElement[0])+' radius ='+str(FlexElement[2])+" LastRadius="+str(LastRadius)+"--> "+str(FlexElement[0] - LastRadius - FlexElement[2]) +'\n')
            #First Notch Line
            hLine = NotchLine((xpos, -thickness, 0), (xpos+FlexElement[0] - LastRadius - FlexElement[2] , -thickness, 0), 0.0, FlexElement[1], 0)
            hLine.drawNotchLine(self.path)
            xpos += FlexElement[0] - LastRadius - FlexElement[2]
            #Then the line corresponding to rounded corner
            if FlexElement[2] > 0:
                self.path.LineTo(xpos + FlexElement[2]*math.pi/2, -thickness)
                ListFlexLines.append((xpos, FlexElement[2]))
            xpos += FlexElement[2]*math.pi/2
            LastRadius = FlexElement[2]
            DebugMsg("After drawing line for rounded corner, xpos="+str(xpos)+'\n')

        #Last element 
        FlexElement = self.FlexBandList[7]
        DebugMsg("Last Element (7): xpos="+str(xpos)+' Size ='+str(FlexElement[0])+' radius ='+str(FlexElement[2])+" LastRadius="+str(LastRadius)+"--> "+str(FlexElement[0] - LastRadius - FlexElement[2]) +'\n')
        #Last Notch Line, at last half of it ! First half indeed.
        hLine = NotchLine((xpos, -thickness, 0), (xpos+FlexElement[0] - LastRadius - FlexElement[2], -thickness, 0), 0.0, FlexElement[1], -1)
        hLine.drawNotchLine(self.path)
        xpos += (FlexElement[0] - LastRadius - FlexElement[2])/2
        
        self.path.LineTo(xpos, thickness)
        DebugMsg('Clip Line 1, xpos='+str(xpos)+'\n')
        #Then Vertical clip line
        self.path.LineToVRel((zoneclips - nbclips*sizeclips)/2)
        for i in range(nbclips):
            self.drawClip(sizeclips, 1)
        
        DebugMsg("Bottom line, reverse, start at xpos="+str((xpos, self.height+thickness))+'\n')
        #Then Bottom line (reverse from top line)
        FlexElement = self.FlexBandList[7]
        #Element 7 is the last one, with radius of Back Right corner
        NextRadius = self.FlexBandList[6][2]        #This is the radius of the left right corner
        DebugMsg("Element 7: xpos="+str(xpos)+' Size ='+str(FlexElement[0])+' radius ='+str(FlexElement[2])+' --> '+str(FlexElement[0]-FlexElement[2]-NextRadius)+'\n')
        #Last Notch Line, half line. Center line on xpos
        hLine = NotchLine((xpos + (FlexElement[0] - NextRadius - FlexElement[2])/2, self.height+thickness, 0), (xpos-(FlexElement[0] - NextRadius - FlexElement[2])/2, self.height+thickness, 0), math.pi, FlexElement[3], 1)
        if hLine.StartStatus == 0:
            self.path.LineTo(xpos, self.height+thickness)
        else:
            self.path.LineTo(xpos, self.height)
        hLine.drawNotchLine(self.path)
        xpos -= (FlexElement[0] - NextRadius - FlexElement[2])/2
        for i in range(6, 3, -1):        #Start at end up to third element
            FlexElement = self.FlexBandList[i]
            NextRadius = self.FlexBandList[i-1][2]
            DebugMsg("Element "+str(i)+": xpos="+str(xpos)+' Size ='+str(FlexElement[0])+" radius ="+str(FlexElement[2])+" NextRadius="+str(NextRadius)+' --> '+str(FlexElement[0] - FlexElement[2] - NextRadius)+'\n')
            #First the line corresponding to rounded corner (reverse from previous)
            if FlexElement[2] > 0:
                self.path.LineTo(xpos - FlexElement[2]*math.pi/2, self.height+thickness)
                xpos -= FlexElement[2]*math.pi/2
            DebugMsg("After line for rounded corner, l="+str(FlexElement[2]*math.pi/2)+" Pos="+str((xpos, self.height+thickness))+'\n')
            #Then Notch Line
            hLine = NotchLine((xpos, self.height+thickness, 0), (xpos-(FlexElement[0] - FlexElement[2] - NextRadius), self.height+thickness, 0), math.pi, FlexElement[3], 0)
            hLine.drawNotchLine(self.path)
            xpos -= FlexElement[0] - FlexElement[2] - NextRadius

        NextRadius = self.FlexBandList[7][2]
        FlexElement = self.FlexBandList[3]
        DebugMsg("First Element (3): xpos="+str(xpos)+' Size ='+str(FlexElement[0])+" radius ="+str(FlexElement[2])+" NextRadius="+str(NextRadius)+' --> '+str(FlexElement[0] - FlexElement[2] - NextRadius)+'\n')
        #Then Last round corner
        self.path.LineTo(xpos - FlexElement[2]*math.pi/2, self.height+thickness)
        xpos -= FlexElement[2]*math.pi/2
        DebugMsg("Last Round corner, l="+str(FlexElement[2]*math.pi/2)+" new pos="+str((xpos, self.height+thickness))+'\n')
        #Then Notch Line, half of it
        hLine = NotchLine((xpos, self.height+thickness, 0), (xpos-(FlexElement[0]-FlexElement[2]-LastRadius), self.height+thickness, 0), math.pi, FlexElement[3], -1)      #Draw only first half
        hLine.drawNotchLine(self.path)
        xpos -= (FlexElement[0]-FlexElement[2] - LastRadius)/2
        self.path.LineTo(xpos, self.height)
        #Then Vertical clip line
        DebugMsg('Vertical Clip 2, pos='+str((xpos, self.height))+'\n')
        #and vertical trip (reverse)
        self.path.LineToVRel(-1.0*((zoneclips - nbclips*sizeclips)/2) - thickness)
        for i in range(nbclips):
            self.drawClip(sizeclips, -1)
        if First_hLine.StartStatus == 0:    #If StartStatus is external, move to (0,-Thickness)
            self.path.LineTo(0, -thickness)
        else:
            self.path.LineTo(0, 0)

        #Now draw flex lines
        
        for FlexLinePos in ListFlexLines:
            Flex = FlexLines()
            Flex.drawFlexLines(FlexLinePos[0], self.height, FlexLinePos[1], self.path)
        #Get bounding box of path
        self.BoundingBox = (self.path.xmin, self.path.ymin, self.path.xmax, self.path.ymax)

        if ClosePath:
            self.path.Close()
            self.path.GenPath()

    def drawSideLineNotches(self):
        '''
        Draw the side line notches used with sliding lid. These lines are on left and right (if flex) lines
        These lines are created whenever the top notches are not null
        '''
        n_side_line = 0
        ypos = -self.BoundingBox[1]
        LastRadius = 0
        for i in range(3, len(self.FlexBandList)):
            FlexElement = self.FlexBandList[i]
            if FlexElement[1] > 0:          #Notches are present, draw SideLine with notches
                n_side_line += 1
                DebugMsg("\nDraw "+self.BaseName+'LidJoint'+str(n_side_line)+" Radius="+str(FlexElement[2])+" LastRadius="+str(LastRadius)+" Size ="+str(FlexElement[0] - FlexElement[2] - LastRadius)+'\n')
                Line = BoxFace(self.BaseName+'LidJoint'+str(n_side_line), 
                               CornerPoint((0,0), 0, 1, 1), 0,                                  #Start point, no notch
                               CornerPoint((FlexElement[0] - FlexElement[2] - LastRadius,0), 0, 1, 1), 0,    #Size is up to rounded corner, no notch for the small side 
                               CornerPoint((FlexElement[0] - FlexElement[2] - LastRadius,thickness), 0, 1, 1), FlexElement[1],    #Same x, height = 2*thickness, joints up to next
                               CornerPoint((0, thickness), 0, 1, 1), 0,
                               self.InkscapeGroup, [-self.BoundingBox[2]-2, ypos])
                ypos -= 2*thickness + 2
                Line.drawSimpleFace(True)
            LastRadius = FlexElement[2]


class BoxFace:
    '''
    This class deals with faces
    Each face is defined with 4 corners and the size of the finger joints between the corners
    finger joint size = 0 means no finger joints (straight line)
    The InkscapeGroup parameter is used to bind the path in this group
    The PositionInPage parameter is used to fix the path within the inkscape document
    '''
    def __init__(self, name, top_left, top_finger_joint, top_right, right_finger_joint, bottom_right, bottom_finger_joint, bottom_left, left_finger_joint, InkscapeGroup, PositionInPage, Path=None):
        #First set up the corners
        self.top_left_corner = top_left
        self.top_right_corner = top_right
        self.bottom_right_corner = bottom_right
        self.bottom_left_corner = bottom_left
        #then the lines between the corners
        self.TopLine = NotchLine((top_left.x_start_joint, top_left.y_start_joint, top_left.y_internal), (top_right.x_end_joint, top_right.y_end_joint, top_right.y_internal), 0, top_finger_joint) 

        self.RightLine = NotchLine((top_right.x_start_joint, top_right.y_start_joint, top_right.x_internal), (bottom_right.x_end_joint, bottom_right.y_end_joint, bottom_right.x_internal), math.pi/2, right_finger_joint) 
        
        self.BottomLine = NotchLine((bottom_right.x_start_joint, bottom_right.y_start_joint, bottom_right.y_internal), (bottom_left.x_end_joint, bottom_left.y_end_joint, bottom_left.y_internal), math.pi, bottom_finger_joint) 
        
        self.LeftLine = NotchLine((bottom_left.x_start_joint, bottom_left.y_start_joint, bottom_left.x_internal), (top_left.x_end_joint, top_left.y_end_joint, top_left.x_internal), -math.pi/2, left_finger_joint) 

        #Update PositionInPage to take into account external corners or notches
        if self.top_left_corner.WoodHingeCorner:
            PositionInPage[0] -= (WoodHingeSize+1)*thickness
            PositionInPage[1] -= WoodHingeSize*thickness
        elif self.top_right_corner.WoodHingeCorner:
            PositionInPage[1] -= WoodHingeSize*thickness
            PositionInPage[0] -= thickness
        elif self.top_left_corner.x_internal == 0 or self.bottom_left_corner.x_internal == 0 or self.LeftLine.nb_finger_joint > 0:
            PositionInPage[0] -= thickness
        if self.top_left_corner.y_internal == 0 or self.top_right_corner.y_internal == 0 or self.TopLine.nb_finger_joint > 0:
            PositionInPage[1] -= thickness
        self.BoundingBox = (-PositionInPage[0], -PositionInPage[1], -PositionInPage[0], -PositionInPage[1])
        self.name = name
        self.InkscapeGroup = InkscapeGroup
        #If needed, create path which will be used to draw the face
        #The path will be in the group InkscapeGroup
        if Path == None:
            self.path = th_inkscape_path(PositionInPage, InkscapeGroup, name)
            DebugMsg("Creating path("+name+") Position ="+str(PositionInPage)+'\n')
        else:
            self.path = Path
        #DebugMsg("Create path "+str(name)+ " PositionInPage="+str(PositionInPage)+'\n')

    def Close(self):
        '''
        Close and write the path after drawing is done
        '''
        self.path.Close()
        self.path.GenPath()
        

    def drawSimpleFace(self, ClosePath):
        '''
        Draw the face, when there are no other elements in the perimeter 
        If ClosePath is true the path is closed
        '''
        if self.top_left_corner.WoodHingeCorner:
            #Specific case, shorten Left line of notches to take into account the wood hinge circle
            #But first copy values from right edge, because WoodHingeCorner has modified the notch line
            self.LeftLine.start_line_joint_y = self.RightLine.end_line_joint_y
            self.LeftLine.JointSize = self.RightLine.JointSize
            self.LeftLine.nb_finger_joint = self.RightLine.nb_finger_joint
            self.LeftLine.EndY = self.RightLine.StartY
            SizeCut = WoodHingeSize * thickness
            #Start from bottom (because reverse on left line) up to sizecut
            self.LeftLine.ModifyNotchLine(SizeCut, False)        #Last parameter, CutOnStart = False, because we start at bottom
        if self.top_right_corner.WoodHingeCorner:
            #Specific case, shorten Right line of notches to take into account the wood hinge circle
            #But first copy values from Left edge, because WoodHingeCorner has modified the notch line
            self.RightLine.start_line_joint_y = self.LeftLine.end_line_joint_y
            self.RightLine.end_line_joint_y = self.LeftLine.start_line_joint_y
            self.RightLine.JointSize = self.LeftLine.JointSize
            self.RightLine.nb_finger_joint = self.LeftLine.nb_finger_joint
            self.RightLine.StartY = self.LeftLine.EndY
            SizeCut = WoodHingeSize * thickness
            self.RightLine.ModifyNotchLine(SizeCut, True)        #Last parameter, CutOnStart = False, because we start at Top
        # Go To starting point
        self.path.MoveTo(self.top_left_corner.x_end_joint, self.top_left_corner.y_end_joint)
        #DebugMsg("StartPoint, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #first (top left) corner
        self.top_left_corner.drawCorner(self.path)
        #DebugMsg("TopLeft, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #then top edge
        self.TopLine.drawNotchLine(self.path)
        #DebugMsg("Top Edge, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Top right corner
        self.top_right_corner.drawCorner(self.path)
        #DebugMsg("Top Right corner, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Right edge
        self.RightLine.drawNotchLine(self.path)
        #DebugMsg("Right Edge, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Bottom right corner
        self.bottom_right_corner.drawCorner(self.path)
        #DebugMsg("Bottom Right corner, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Bottom edge
        self.BottomLine.drawNotchLine(self.path)
        #DebugMsg("Bottom Edge, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Bottom left corner
        self.bottom_left_corner.drawCorner(self.path)
        DebugMsg("Bottom Left corner, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Left edge
        self.LeftLine.drawNotchLine(self.path)
        #DebugMsg("Left Edge, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #The position is now (top_left_corner.x_end_joint, top_left_corner.y_end_joint), it is the starting point

        #Case with WoodHingeCorner, draw circle and rectangle
        if self.top_left_corner.WoodHingeCorner:        
            #Draw the circle internal to the hinge, radius is 2*thickness mm
            CircleRadius = WoodHingeInternalCircle*thickness
            self.path.drawCircle(-thickness, -thickness, CircleRadius)
            #Then the internal rectangle, rectangle height is 1.5*thickness
            RectHeight = WoodHingeRect*thickness
            self.path.MoveTo(-thickness, -thickness)     #Starting point Ext/Bottom
            self.path.LineToVRel(-RectHeight)            #Ext/Top
            self.path.LineToHRel(thickness)              #Int/Top
            self.path.LineToVRel(RectHeight)             #Int Bottom 
            self.path.LineToHRel(-thickness)             #Return to start
        if self.top_right_corner.WoodHingeCorner:        
            #Draw the circle internal to the hinge, radius is 2*thickness mm
            CircleRadius = WoodHingeInternalCircle*thickness
            self.path.drawCircle(self.top_right_corner.x_corner+thickness, -thickness, CircleRadius)
            #Then the internal rectangle, rectangle height is 1.5*thickness
            RectHeight = WoodHingeRect*thickness
            self.path.MoveTo(self.top_right_corner.x_corner+thickness, -thickness)     #Starting point Ext/Bottom
            self.path.LineToVRel(-RectHeight)             #Ext/Top
            self.path.LineToHRel(-thickness)             #Int/Top
            self.path.LineToVRel(RectHeight)            #Int Bottom 
            self.path.LineToHRel(thickness)              #Return to start

        #Get bounding box of path
        self.BoundingBox = (self.path.xmin, self.path.ymin, self.path.xmax, self.path.ymax)

        #Close the path if asked
        if ClosePath:
            self.path.Close()
            self.path.GenPath()

    def drawSimpleFaceHinge(self, HingeList, ClosePath):
        '''
        Draw the face, and the cut for the hinge
        If ClosePath is true the path is closed
        '''
        # Go To starting point
        self.path.MoveTo(self.top_left_corner.x_end_joint, self.top_left_corner.y_end_joint)
        #DebugMsg("StartPoint, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #first (top left) corner
        self.top_left_corner.drawCorner(self.path)
        #DebugMsg("TopLeft, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #then top edge, no notch in this case, but cut for the hinge(s)
        for Hinge in HingeList:
            HingePos = Hinge[2] - 1
            self.path.LineTo(HingePos, 0)
            #Then cut for the Hinge
            self.path.LineToVRel(4.5*thickness+1) 
            self.path.LineToHRel(5*thickness + 2.5*SteelHingeSpacing + 2)
            self.path.LineToVRel(-4.5*thickness-1)
        #Then line up to length
        self.path.LineTo(self.top_right_corner.x_corner, 0)  #Up to end of top line
        #Top right corner
        self.top_right_corner.drawCorner(self.path)
        #DebugMsg("Top Right corner, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Right edge
        self.RightLine.drawNotchLine(self.path)
        #DebugMsg("Right Edge, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Bottom right corner
        self.bottom_right_corner.drawCorner(self.path)
        #DebugMsg("Bottom Right corner, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Bottom edge
        self.BottomLine.drawNotchLine(self.path)
        #DebugMsg("Bottom Edge, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Bottom left corner
        self.bottom_left_corner.drawCorner(self.path)
        #DebugMsg("Bottom Left corner, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Left edge
        self.LeftLine.drawNotchLine(self.path)
        #DebugMsg("Left Edge, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #The position is now (top_left_corner.x_end_joint, top_left_corner.y_end_joint), it is the starting point

        #Get bounding box of path
        self.BoundingBox = (self.path.xmin, self.path.ymin, self.path.xmax, self.path.ymax)

        #Close the path if asked
        if ClosePath:
            self.path.Close()
            self.path.GenPath()
        #DebugMsg("Closing path, BoundingBox="+str(self.BoundingBox)+'\n')

    def drawFaceWithHoles(self, n_slot, slot_size, DeltaHolePosition, z_joint_size, Height_percentage, ClosePath, HingeList = None):
        '''
        Draw a face with holes (for internal walls)
        The holes positions are given in a list (see CalcNotchPos), and an offset will be added if necessary (shorten face)
        n_slot : number of slots
        slot_size
        DeltaHolePosition : Offset for holes
        z_joint_size
        Height_percentage : Actual interior will be height*percentage, so dig holes only for useful part
        ClosePath :
        HingeList : 
        '''
        if HingeList == None:
            #No cut for hinge, call regular function to draw face
            self.drawSimpleFace(False)           #First draw the face itself, without closing path
        else:
            self.drawSimpleFaceHinge(HingeList, False)           #First draw the face itself, without closing path
        #now the holes used to fix the walls
        #This line  will be used to draw the holes
        InteriorHeight = self.bottom_right_corner.y_end_joint * Height_percentage / 100.0
        l_NotchLine = NotchLine((0, 0, 1), (InteriorHeight, 0, 1), math.pi/2, z_joint_size) 

        StartHole = l_NotchLine.start_line_joint_y + l_NotchLine.JointSize
        Spacing = 2*l_NotchLine.JointSize
        DebugMsg("drawFaceWithHoles, Hole Start ="+str(StartHole)+" Spacing="+str(Spacing)+" n_holes"+str(l_NotchLine.nb_finger_joint//2)
                 +' n_slot='+str(n_slot)+'  slot_size='+str(slot_size)+" Delta_Pos="+str(DeltaHolePosition)+'\n')
        for i in range(1, n_slot):
            #For each wall, draw holes corresponding at each notch on zbox
            for j in range(int(l_NotchLine.nb_finger_joint//2)):
                drawHole(self.path, i*(slot_size+thickness) - DeltaHolePosition -thickness, StartHole + j*Spacing, thickness, l_NotchLine.JointSize, burn)

        #Close the path if asked
        if ClosePath:
            self.path.Close()
            self.path.GenPath()  
    
    def drawFaceInternalSlidingLeft(self, ClosePath):
        '''
        Draw specific pattern helping the sliding of the lid inside the box
        '''
        radius_back = self.top_left_corner.radius
        # Go To starting point (top left)
        self.path.MoveTo(self.top_left_corner.x_corner, self.top_left_corner.y_corner+thickness)
        DebugMsg("drawFaceInternalSlidingLeft, top left start in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Then draw the small quarter of circle
        self.path.LineToVRel(radius_back)
        DebugMsg("drawFaceInternalSlidingLeft, now in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        self.path.drawQuarterCircle(self.top_left_corner.x_corner+radius_back, self.top_left_corner.y_corner+radius_back+thickness, radius_back, 0)
        DebugMsg("drawFaceInternalSlidingLeft, after circle in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        self.path.LineToHRel(-radius_back)
        DebugMsg("drawFaceInternalSlidingLeft, End of top left circle in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        

        #Then restart path at bottom right
        self.path.MoveTo(self.bottom_right_corner.x_end_joint, self.bottom_right_corner.y_end_joint)
        DebugMsg("drawFaceInternalSlidingLeft, start in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Draw the horizontal line towards left corner
        self.path.LineTo(self.bottom_left_corner.x_end_joint+SlidingLidSpaceZ*thickness, self.bottom_left_corner.y_end_joint)
        DebugMsg("drawFaceInternalSlidingLeft, now in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Draw the vertical left line towards rounded back
        #Change left line 
        x = self.path.x_noff
        self.LeftLine = NotchLine((x, self.bottom_left_corner.y_start_joint, 0), (x, self.top_left_corner.y_end_joint+SlidingLidSpaceZ*thickness, 0), -math.pi/2, self.LeftLine.JointSize) 
        self.LeftLine.drawNotchLine(self.path)
        x = self.top_left_corner.x_end_joint+SlidingLidSpaceZ*thickness
        y = self.top_left_corner.y_end_joint+SlidingLidSpaceZ*thickness
        DebugMsg("drawFaceInternalSlidingLeft, after notches in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        self.path.LineTo(x, y)
        DebugMsg("drawFaceInternalSlidingLeft, now in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Draw the quarter circle (quadrant 0)
        self.path.drawQuarterCircle(x+radius_back, y, radius_back, 0)
        DebugMsg("drawFaceInternalSlidingLeft, after first circle in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Then the horizontal line towards the large circle
        x = self.top_right_corner.x_end_joint - (SlidingLidSpaceZ+1)*thickness
        y = self.path.y_noff
        self.path.LineTo(x, y)
        DebugMsg("drawFaceInternalSlidingLeft, now in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #then large circle (Quadrant 1)
        radius = self.top_right_corner.radius
        y_end = min(self.top_right_corner.y_start_joint, self.bottom_right_corner.y_end_joint - thickness)
        self.path.Bezier(x+radius*0.551916, y, x + radius, y+radius*(1-0.551916), x+radius, y_end)  
        DebugMsg("drawFaceInternalSlidingLeft, now in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Then V Line up to bottom
        self.path.LineTo(self.bottom_right_corner.x_end_joint- (SlidingLidSpaceZ+1)*thickness, self.bottom_right_corner.y_end_joint - thickness)
        DebugMsg("drawFaceInternalSlidingLeft, After V Line now in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Then H line 
        x = self.bottom_right_corner.x_end_joint -  thickness
        y = self.bottom_right_corner.y_end_joint -  thickness     
        self.path.LineTo(x, y)
        DebugMsg("drawFaceInternalSlidingLeft, now in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Then V Line
        self.path.LineTo(x, y_end)
        #Then large circle, first quadrant but reverse drawing
        self.path.Bezier(x, y_end - radius*0.551916, x - radius*0.551916, y_end-radius, x-radius+thickness, y_end-radius)  # upper right quarter
        DebugMsg("drawFaceInternalSlidingLeft, After circle 2 in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Then V line
        self.path.LineToVRel(-thickness)
        DebugMsg("drawFaceInternalSlidingLeft, now in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #And last large circle
        x = self.path.x_noff
        y = self.path.y_noff
        self.path.Bezier(x+radius*0.551916, y, self.bottom_right_corner.x_end_joint, y+radius*(1-0.551916), self.bottom_right_corner.x_end_joint, self.top_right_corner.y_start_joint-thickness)  
        DebugMsg("drawFaceInternalSlidingLeft, now in "+str((self.path.x_noff, self.path.y_noff))+'\n')

        #Get bounding box of path
        self.BoundingBox = (self.path.xmin, self.path.ymin, self.path.xmax, self.path.ymax)

        #Close the path if asked
        if ClosePath:
            self.path.Close()
            self.path.GenPath()  
        
    def drawFaceInternalSlidingRight(self, ClosePath):
        '''
        Draw specific pattern helping the sliding of the lid inside the box
        '''
        radius_back = self.top_right_corner.radius
        # Go To starting point (top Right)
        self.path.MoveTo(self.top_right_corner.x_corner, self.top_right_corner.y_corner+thickness)
        DebugMsg("drawFaceInternalSlidingRight, top right start in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Then draw the small quarter of circle
        self.path.LineToHRel(-radius_back)
        DebugMsg("drawFaceInternalSlidingRight, now in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        self.path.drawQuarterCircle(self.top_right_corner.x_corner-radius_back, self.top_right_corner.y_corner+radius_back+thickness, radius_back, 1)
        DebugMsg("drawFaceInternalSlidingRight, after circle in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        self.path.LineToVRel(-radius_back)
        DebugMsg("drawFaceInternalSlidingRight, End of top right circle in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        

        #Then restart path at bottom left
        self.path.MoveTo(self.bottom_left_corner.x_end_joint, self.bottom_left_corner.y_end_joint)
        DebugMsg("drawFaceInternalSlidingRight, start in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Draw the horizontal line towards right corner
        self.path.LineTo(self.bottom_right_corner.x_end_joint-SlidingLidSpaceZ*thickness, self.bottom_right_corner.y_end_joint)
        DebugMsg("drawFaceInternalSlidingRight, now in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Draw the vertical Right line towards rounded back
        #Change right line 
        x = self.path.x_noff   
        self.RightLine = NotchLine((x, self.bottom_right_corner.y_start_joint, 1), (x, self.top_right_corner.y_start_joint+SlidingLidSpaceZ*thickness, 1), -math.pi/2, self.RightLine.JointSize) 
        self.RightLine.drawNotchLine(self.path)
        DebugMsg("drawFaceInternalSlidingRight, after notches in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        y = self.top_right_corner.y_start_joint+SlidingLidSpaceZ*thickness
        self.path.LineTo(x, y)
        DebugMsg("drawFaceInternalSlidingRight, now in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Draw the quarter circle, use bezier instead of drawCircle because reverse draw
        self.path.Bezier(x, y - radius_back*0.551916, x - radius_back*(1-0.551916), y-radius_back, x-radius_back, y-radius_back)
        DebugMsg("drawFaceInternalSlidingRight, after first circle in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Then the horizontal line towards the large circle
        x = self.top_left_corner.x_start_joint + (SlidingLidSpaceZ+1)*thickness
        y = self.path.y_noff
        self.path.LineTo(x, y)
        DebugMsg("drawFaceInternalSlidingRight, now in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #then large circle (Quadrant 0)
        radius = self.top_left_corner.radius
        y_end = min(self.top_left_corner.y_end_joint, self.bottom_left_corner.y_end_joint -  thickness)
        self.path.Bezier(x-radius*0.551916, y, x - radius, y+radius*(1-0.551916), x-radius, y_end) 
        x = x-radius
        DebugMsg("drawFaceInternalSlidingRight, after circle 1 in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Then V Line up to bottom
        self.path.LineTo(x, self.bottom_left_corner.y_end_joint - thickness)
        DebugMsg("drawFaceInternalSlidingLeft, After V Line now in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Then H line 
        x = self.bottom_left_corner.x_end_joint +  thickness
        y = self.bottom_left_corner.y_end_joint -  thickness     
        self.path.LineTo(x, y)
        DebugMsg("drawFaceInternalSlidingRight, now in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Then Up yo y_end
        self.path.LineTo(x, y_end)
        #Then large circle, first quadrant
        self.path.Bezier(x, y_end - radius*0.551916, x + radius*0.551916, y_end-radius, x+radius-thickness, y_end-radius)
        DebugMsg("drawFaceInternalSlidingRight, Circle in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Then V line
        self.path.LineToVRel(-thickness)
        DebugMsg("drawFaceInternalSlidingRight, VLine in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #And last large circle
        x = self.path.x_noff
        y = self.path.y_noff
        self.path.Bezier(x-radius*0.551916, y, self.bottom_left_corner.x_end_joint, y+radius*(1-0.551916), self.bottom_left_corner.x_end_joint, self.top_left_corner.y_end_joint-thickness)  
        DebugMsg("drawFaceInternalSlidingRight, Circle in "+str((self.path.x_noff, self.path.y_noff))+'\n')
        #Then Last line
        self.path.LineTo(self.bottom_left_corner.x_end_joint, self.bottom_left_corner.y_end_joint)
        #Get bounding box of path
        self.BoundingBox = (self.path.xmin, self.path.ymin, self.path.xmax, self.path.ymax)

        #Close the path if asked
        if ClosePath:
            self.path.Close()
            self.path.GenPath()  

    def drawSideLineNotches(self, xpos, ypos):
        '''
        Draw the side line notches used with sliding lid. These lines are on left and right lines
        These lines are created whenever the top notches are not null
        '''
        n_side_line = 0
        Line = BoxFace(self.name+'LidJoint', 
                       CornerPoint((0,0), 0, 1, 1), 0,                                  #Start point, no notch
                       CornerPoint((self.top_right_corner.xc - self.top_left_corner.xc,0), 0, 1, 1), 0,    #Size is up to rounded corner, no notch for the small side 
                       CornerPoint((self.top_right_corner.xc - self.top_left_corner.xc,thickness), 0, 1, 1), self.TopLine.JointSize,    #Same x, height = 2*thickness, joints up to next
                       CornerPoint((0, thickness), 0, 1, 1), 0,
                       self.InkscapeGroup, [xpos, ypos])
        Line.drawSimpleFace(True)
        

    def drawExternalBackSlidingLid(self, ClosePath):
        '''
        Draw the face, specific case for sliding lid back face
        If ClosePath is true the path is closed
        '''
        # Go To starting point
        self.path.MoveTo(self.top_left_corner.x_end_joint, self.top_left_corner.y_end_joint)
        #first (top left) corner
        self.top_left_corner.drawCorner(self.path)
        #DebugMsg("TopLeft, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Then draw below thickness
        self.path.LineToVRel(thickness)
        #then top edge, without notches
        self.path.LineToHRel(self.top_right_corner.x_end_joint)
        #Then Up thickness
        self.path.LineToVRel(-thickness)
        #Top right corner
        self.top_right_corner.drawCorner(self.path)
        #DebugMsg("Top Right corner, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Right edge
        self.RightLine.drawNotchLine(self.path)
        #DebugMsg("Right Edge, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Bottom right corner
        self.bottom_right_corner.drawCorner(self.path)
        #DebugMsg("Bottom Right corner, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Bottom edge
        self.BottomLine.drawNotchLine(self.path)
        #DebugMsg("Bottom Edge, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Bottom left corner
        self.bottom_left_corner.drawCorner(self.path)
        #DebugMsg("Bottom Left corner, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Left edge
        self.LeftLine.drawNotchLine(self.path)
        #DebugMsg("Left Edge, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #The position is now (top_left_corner.x_end_joint, top_left_corner.y_end_joint), it is the starting point
        
        #Get bounding box of path
        self.BoundingBox = (self.path.xmin, self.path.ymin, self.path.xmax, self.path.ymax)

        #Close the path if asked
        if ClosePath:
            self.path.Close()
            self.path.GenPath()
        #DebugMsg("Closing path, BoundingBox="+str(self.BoundingBox)+'\n')

    def drawExternalBackWoodHingeLid(self, ClosePath):
        '''
        Draw the face, specific case for wood hinge lid back face
        This face will use a specific vertical notch lines, which are shorter by the circle of the hinge 
        If ClosePath is true the path is closed
        '''
        DebugMsg("\n enter drawExternalBackWoodHingeLid\n")
        #Size of wood hinge cut
        SizeCut = WoodHingeSize*thickness + 2*burn
        #Modify right line to accomodate this cut
        self.RightLine.ModifyNotchLine(SizeCut, True)
        #Do the same for left line, but reverse
        self.LeftLine.ModifyNotchLine(SizeCut, False)
        # Go To starting point
        self.path.MoveTo(0, -thickness)
        self.path.LineTo(self.top_right_corner.x_end_joint, -thickness)  #Space for cut
        #Then go to cut
        self.path.LineToVRel(SizeCut)
        self.path.LineToHRel(thickness)
        #Right edge
        self.RightLine.drawNotchLine(self.path)
        #Bottom right corner
        self.bottom_right_corner.drawCorner(self.path)
        #Bottom edge
        self.BottomLine.drawNotchLine(self.path)
        #Bottom left corner
        self.bottom_left_corner.drawCorner(self.path)
        #Left edge
        self.LeftLine.drawNotchLine(self.path)
        #Then cut
        self.path.LineToHRel(thickness)
        self.path.LineTo(0, -thickness)
        #The position is now (top_left_corner.x_end_joint, top_left_corner.y_end_joint), it is the starting point
        
        #Get bounding box of path
        self.BoundingBox = (self.path.xmin, self.path.ymin, self.path.xmax, self.path.ymax)

        #Close the path if asked
        if ClosePath:
            self.path.Close()
            self.path.GenPath()
        #DebugMsg("Closing path, BoundingBox="+str(self.BoundingBox)+'\n')

    def drawLidBackWoodHinge(self, ClosePath):
        '''
        Draw the lid back when Wood hinge is chosen, specific case for wood hinge lid back face
        This face will use a specific vertical notch lines, which are shorter by the circle of the hinge 
        If ClosePath is true the path is closed
        '''
        #Size of wood hinge cut
        SizeCut = WoodHingeSize*thickness + 2*burn
        DebugMsg("\n enter drawLidBackWoodHinge, SizeCut = "+str(SizeCut)+"\n")
        DebugMsg("Joint size ="+str(self.RightLine.JointSize)+" Top_Right="+str((self.top_right_corner.x_corner, self.top_right_corner.y_corner))+" Bottom Right="+str((self.bottom_right_corner.x_corner, self.bottom_right_corner.y_corner))+"\n")
        #Change right line, from top to bottom RightLine
        self.RightLine.ModifyNotchLine(SizeCut, False)       #Last Parameter false because we start on Top and cut is on bottom
        #The left line will be the same but reverse
        self.LeftLine.ModifyNotchLine(SizeCut, True)       #Last Parameter false because we start on Bottom and cut is on bottom
        # Go To starting point
        self.path.MoveTo(self.top_left_corner.x_end_joint, self.top_left_corner.y_end_joint)
        #DebugMsg("StartPoint, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #first (top left) corner
        self.top_left_corner.drawCorner(self.path)
        #DebugMsg("TopLeft, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #then top edge
        self.TopLine.drawNotchLine(self.path)
        #DebugMsg("Top Edge, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Top right corner
        self.top_right_corner.drawCorner(self.path)
        #Right edge
        self.RightLine.drawNotchLine(self.path)
        #Then the cut with the notch for the circle
        StartNotchCircle = 1.5 * thickness
        self.path.LineToHRel(-thickness)
        self.path.LineTo(self.bottom_right_corner.x_end_joint - thickness, self.bottom_right_corner.y_corner - StartNotchCircle)
        self.path.LineToHRel(thickness)
        self.path.LineToVRel(StartNotchCircle)
        self.path.LineTo(self.bottom_right_corner.x_end_joint - thickness, self.bottom_right_corner.y_corner)
        #Bottom edge
        self.path.LineTo(-thickness, self.bottom_left_corner.y_corner)
        #Then Cut
        self.path.LineToVRel(-StartNotchCircle)
        self.path.LineToHRel(thickness)
        self.path.LineTo(0, self.bottom_left_corner.y_corner - SizeCut)
        self.path.LineToHRel(-thickness)
        #Left edge
        self.LeftLine.drawNotchLine(self.path)
        self.path.LineTo(-thickness, -thickness)
       
        #Get bounding box of path
        self.BoundingBox = (self.path.xmin, self.path.ymin, self.path.xmax, self.path.ymax)

        #Close the path if asked
        if ClosePath:
            self.path.Close()
            self.path.GenPath()
        #DebugMsg("Closing path, BoundingBox="+str(self.BoundingBox)+'\n')

    def drawExternalBackSteelHingeLid(self, HingeList, ClosePath):
        '''
        Draw the face, specific case for lid with 'steel hinge' back face
        This face will have cuts to place the real hinge elements 
        HingeList is a list of Hinge position
        If ClosePath is true the path is closed
        '''
        DebugMsg("\n enter drawExternalBackSteelHingeLid\n")
        # Go To starting point
        self.path.MoveTo(-thickness, -thickness)
        #The top line will have cut for the hinge
        for Hinge in HingeList:
            HingePos = Hinge[2]
            self.path.LineTo(HingePos + thickness, -thickness)       #add thickness in x because hinge pos is internal, and sub thickness in y because always external
            #Then Hinge
            self.path.LineToVRel(2.5*thickness)
            self.path.LineToHRel(thickness)
            self.path.LineToVRel(-thickness + 0.5*SteelHingeSpacing)
            self.path.LineToHRel(thickness + SteelHingeSpacing)
            self.path.LineToVRel(thickness - 0.5*SteelHingeSpacing)
            self.path.LineToHRel(thickness)
            self.path.LineToVRel(-thickness + 0.5*SteelHingeSpacing)
            self.path.LineToHRel(thickness + SteelHingeSpacing)
            self.path.LineToVRel(thickness - 0.5*SteelHingeSpacing)
            self.path.LineToHRel(thickness)
            self.path.LineToVRel(-2.5*thickness)
        #Then line up to length
        self.path.LineTo(self.top_right_corner.x_corner, -thickness)  #Up to end of top line
   
        #Right edge
        self.RightLine.drawNotchLine(self.path)
        #Bottom right corner
        self.bottom_right_corner.drawCorner(self.path)
        #Bottom edge
        self.BottomLine.drawNotchLine(self.path)
        #Bottom left corner
        self.bottom_left_corner.drawCorner(self.path)
        #Left edge
        self.LeftLine.drawNotchLine(self.path)
        #Then return to Start
        self.path.LineTo(-thickness, -thickness)

        #Now draw holes for the hinge(s)
        for Hinge in HingeList:
            self.path.MoveTo(Hinge[2]+thickness, 3.5*thickness)
            self.path.LineToHRel(thickness)
            self.path.LineToVRel(-thickness)
            self.path.LineToHRel(-thickness)
            self.path.LineToVRel(thickness)
            self.path.MoveTo(Hinge[2] + 3*thickness + SteelHingeSpacing, 3.5*thickness)
            self.path.LineToHRel(thickness)
            self.path.LineToVRel(-thickness)
            self.path.LineToHRel(-thickness)
            self.path.LineToVRel(thickness)
            self.path.MoveTo(Hinge[2] + 5*thickness + 2*SteelHingeSpacing, 3.5*thickness)
            self.path.LineToHRel(thickness)
            self.path.LineToVRel(-thickness)
            self.path.LineToHRel(-thickness)
            self.path.LineToVRel(thickness)
        
        #Get bounding box of path
        self.BoundingBox = (self.path.xmin, self.path.ymin, self.path.xmax, self.path.ymax)

        #Close the path if asked
        if ClosePath:
            self.path.Close()
            self.path.GenPath()
        #DebugMsg("Closing path, BoundingBox="+str(self.BoundingBox)+'\n')


    def drawLidBackSteelHinge(self, HingeList, ClosePath):
        '''
        Draw the lid back, specific case for lid with 'steel hinge' back face
        This face will have cuts to place the real hinge elements 
        HingeList is a list of Hinge position
        If ClosePath is true the path is closed
        '''
        DebugMsg("\n enter drawLidBackSteelHinge\n")
        # Go To starting point
        self.path.MoveTo(self.top_left_corner.x_end_joint, self.top_left_corner.y_end_joint)
        #DebugMsg("StartPoint, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #first (top left) corner
        self.top_left_corner.drawCorner(self.path)
        #DebugMsg("TopLeft, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #then top edge
        self.TopLine.drawNotchLine(self.path)
        #DebugMsg("Top Edge, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Top right corner
        self.top_right_corner.drawCorner(self.path)
        #Right edge
        self.RightLine.drawNotchLine(self.path)
        #Bottom right corner
        self.bottom_right_corner.drawCorner(self.path)
        #Bottom edge, this one has cut for the hinge(s).
        z = self.bottom_right_corner.y_corner
        #Now draw holes for the hinge(s), reverse because draw from right to left
        for Hinge in reversed(HingeList):
            HingePos = Hinge[2] + thickness
            #First H line up to end of 2nd hinge
            self.path.LineTo(HingePos + 5*thickness + 2.5*SteelHingeSpacing, z)
            #Then Hinge
            self.path.LineToVRel(-1.5*thickness - 0.5*SteelHingeSpacing)
            self.path.LineToHRel(-thickness - SteelHingeSpacing)
            self.path.LineToVRel(-thickness + 0.5*SteelHingeSpacing)
            self.path.LineToHRel(-thickness)
            self.path.LineToVRel(thickness - 0.5*SteelHingeSpacing)
            self.path.LineToHRel(-thickness - SteelHingeSpacing)
            self.path.LineToVRel(-thickness + 0.5*SteelHingeSpacing)
            self.path.LineToHRel(-thickness)
            self.path.LineToVRel(thickness - 0.5*SteelHingeSpacing)
            self.path.LineToHRel(-thickness - SteelHingeSpacing)
            self.path.LineToVRel(1.5*thickness + 0.5*SteelHingeSpacing)
        #Then draw up to corner            
        self.path.LineTo(self.bottom_left_corner.x_end_joint, self.bottom_left_corner.y_end_joint)
        #Bottom left corner
        self.bottom_left_corner.drawCorner(self.path)
        #Left edge
        self.LeftLine.drawNotchLine(self.path)
        #Then return to Start
        self.path.LineTo(-thickness, -thickness)

        #Then draw holes for the hinge(s)
        for Hinge in HingeList:
            HingePos = Hinge[2] + 2*thickness
            self.path.MoveTo(HingePos + 0.5*SteelHingeSpacing, z - 3.5*thickness)
            self.path.LineToHRel(thickness)
            self.path.LineToVRel(-thickness)
            self.path.LineToHRel(-thickness)
            self.path.LineToVRel(thickness)
            self.path.MoveTo(HingePos + 2*thickness + 1.5*SteelHingeSpacing, z - 3.5*thickness)
            self.path.LineToHRel(thickness)
            self.path.LineToVRel(-thickness)
            self.path.LineToHRel(-thickness)
            self.path.LineToVRel(thickness)
        #Get bounding box of path
        self.BoundingBox = (self.path.xmin, self.path.ymin, self.path.xmax, self.path.ymax)

        #Close the path if asked
        if ClosePath:
            self.path.Close()
            self.path.GenPath()
        #DebugMsg("Closing path, BoundingBox="+str(self.BoundingBox)+'\n')

    def drawLidSideWoodHinge(self, FlagRight, ClosePath):
        '''
        Generate lid side with integrated hinge. This is a rectangle with a rounded cut for the hinge and notches on 3 edges
        No notch on the bottom edge
        '''
        SizeCut = WoodHingeSize*thickness + 2*burn
        DebugMsg("\n enter drawLidSideWoodHinge, SizeCut="+str(SizeCut)+" FlagRight ="+str(FlagRight)+"\n")
        #Because of the cut on the lid, we have to change either the right of left line of notches
        if FlagRight > 0:
            self.RightLine.ModifyNotchLine(SizeCut, False)
        else:
            self.LeftLine.ModifyNotchLine(SizeCut, True)
        # Go To starting point
        self.path.MoveTo(self.top_left_corner.x_end_joint, self.top_left_corner.y_end_joint)
        #DebugMsg("StartPoint, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #first (top left) corner
        self.top_left_corner.drawCorner(self.path)
        #DebugMsg("TopLeft, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #then top edge
        self.TopLine.drawNotchLine(self.path)
        #DebugMsg("Top Edge, PathPos ="+str((self.path.x, self.path.y))+" Bounding Box="+str(self.path.GetBoundingBox())+'\n')
        #Top right corner
        self.top_right_corner.drawCorner(self.path)
        #Right edge, first start with normal notch line
        self.RightLine.drawNotchLine(self.path)
        #If right side, special case. Start with notches, but then switch to a circle
        if FlagRight > 0:
            #Then the cut. Choose 0.95*SizeCut because the actual circle is NOT centered of this vertical edge but shifted by thickness
            self.path.LineTo(self.top_right_corner.x_corner, self.bottom_right_corner.y_corner-SizeCut*0.95)
            #Then the rounded cut, almost a quarter of circle, radius SizeCut
            self.path.Bezier(self.top_right_corner.x_corner-SizeCut*0.23, self.bottom_right_corner.y_corner-SizeCut*0.90, 
                        self.top_right_corner.x_corner-SizeCut+thickness, self.bottom_right_corner.y_corner-SizeCut*0.551916, 
                        self.top_right_corner.x_corner-SizeCut+thickness, self.bottom_right_corner.y_corner)
            #No notches on bottom line, just go to next corner
            self.path.LineTo(0, self.bottom_left_corner.y_corner)
        else:
            self.path.LineTo(self.top_right_corner.x_corner, self.bottom_right_corner.y_corner)     #Up to corner
            self.path.LineTo(SizeCut-thickness, self.bottom_left_corner.y_corner)                   #Bottom line up to circle cut
            #Draw the rounded cut, almost a quarter of circle, radius ExtRadius
            self.path.Bezier(SizeCut-thickness, self.bottom_left_corner.y_corner-SizeCut*0.551916
                             , SizeCut*0.23, self.bottom_left_corner.y_corner-SizeCut*0.90
                             , 0, self.bottom_left_corner.y_corner-SizeCut*0.95)
        #Left edge
        self.LeftLine.drawNotchLine(self.path)
        self.path.LineTo(0, -thickness)         #Up to starting point

        #Get bounding box of path
        self.BoundingBox = (self.path.xmin, self.path.ymin, self.path.xmax, self.path.ymax)

        #Close the path if asked
        if ClosePath:
            self.path.Close()
            self.path.GenPath()
        #DebugMsg("Closing path, BoundingBox="+str(self.BoundingBox)+'\n')



    
class GenericBox(inkex.EffectExtension):
    """
    Creates a new layer with the drawings for a parametrically generated box.
    """
    def add_arguments(self, pars):
        self.knownUnits = ['in', 'pt', 'px', 'mm', 'cm', 'm', 'km', 'pc', 'yd', 'ft']
        pars.add_argument('--as_layer', type=inkex.Boolean, default=False, help='Layer or group')
        pars.add_argument('--unit', default='mm', help='Unit, should be one of ')
        pars.add_argument('--thickness', type=float, default=3.0, help='Material thickness')
        pars.add_argument('--lid_type', default='Simple', help='Box lid style ')
        pars.add_argument('--n_slot_x', type=int, default=2, help='Number of columns of slots')
        pars.add_argument('--n_slot_y', type=int, default=2, help='Number of rows of slots')
        pars.add_argument('--h_slot', type=int, default=100, help='Height of slots (%)')
        pars.add_argument('--z', type=float, default=40.0,help="box height")
        pars.add_argument('--y', type=float, default=60.0, help="box depth")
        pars.add_argument('--x', type=float,  default=40.0, help="box width")
        pars.add_argument('--z_lid', type=float, default=20.0, help='lid height')
        pars.add_argument('--z_dome_lid', type=float, default=20.0, help='dome lid height')
        pars.add_argument('--SkipFlexLines', type=inkex.Boolean, default=True, help='Skip flex lines when possible')
        pars.add_argument('--radius_lid', type=float, default=50.0, help='Radius of rounded lid')
        pars.add_argument('--burn', type=float, dest='burn', default=0.1, help='laser burn size')
        pars.add_argument('--StraigthCorners', type=inkex.Boolean, dest='StraigthCorners', default=True, help='Straight corners')
        pars.add_argument('--back_left_radius', type=float, default=10.0, help='Radius of top left rounded corner')
        pars.add_argument('--back_right_radius', type=float, default=10.0, help='Radius of top right rounded corner')
        pars.add_argument('--front_left_radius', type=float, default=10.0, help='Radius of bottom left rounded corner')
        pars.add_argument('--front_right_radius', type=float, default=10.0, help='Radius of bottom right rounded corner')
        pars.add_argument('--AutoSizeJoints', type=inkex.Boolean, default=True, help='Size of finger joints computed from box dimlensions')
        pars.add_argument('--x_joint', type=float, default=10.0, help='Size of finger joints in X direction')
        pars.add_argument('--y_joint', type=float, default=10.0, help='Size of finger joints in Y direction')
        pars.add_argument('--z_joint', type=float, default=10.0, help='Size of finger joints in Z direction')
        pars.add_argument('--Topic')

        self.BoundingBox = [0, 0, 0, 0]
        self.HingeList = []

    def UpdateBoundingBox(self, Face):
        if Face.BoundingBox[0] < self.BoundingBox[0]:
            self.BoundingBox[0] = Face.BoundingBox[0]
        if Face.BoundingBox[1] < self.BoundingBox[1]:
            self.BoundingBox[1] = Face.BoundingBox[1]
        if Face.BoundingBox[2] > self.BoundingBox[2] - 2:
            self.BoundingBox[2] = Face.BoundingBox[2] + 2
        if Face.BoundingBox[3] > self.BoundingBox[3] - 2:
            self.BoundingBox[3] = Face.BoundingBox[3] + 2
    
    def CalcNotchPos(self, n_slot, size_slot):
        ''' 
        Compute the position of notches for a vertical or horizontal line
        No offset, i.e. position is relative to internal side
        Return a list of positions, each position is a tuple with 3 elements, giving start, size of notch and group number
        These positions are NOT sensitive to burn factor. The burn factor should be added later if needed
        '''
        NPos = []
        if size_slot < 50:
            #Small size, only one notch 
            i_notch_number = 1
            notch_number = 3
            notch_size = size_slot / 3 # Notch is center aligned
        elif size_slot < 120:
            #Medium size, draw 15mm notches
            notch_number = int(size_slot / 15)
            if (notch_number % 2) == 0:
                notch_number -= 1           #should be odd
            notch_size = size_slot / notch_number
            i_notch_number = int(notch_number // 2)
        elif size_slot < 200:
            #Medium high size, draw 25mm notches
            notch_number = int(size_slot / 25)
            if (notch_number % 2) == 0:
                notch_number -= 1           #should be odd
            notch_size = size_slot / notch_number
            i_notch_number = int(notch_number // 2)
        else:
            #Large size, draw 40mm notches
            notch_number = int(size_slot / 40)
            if (notch_number % 2) == 0:
                notch_number -= 1           #should be odd
            notch_size = size_slot / notch_number
            i_notch_number = int(notch_number // 2)
        #Compute initial shift. Add this shift to reach symetrical notches within each slot
        Shift = (size_slot - notch_size * notch_number) / 2
        DebugMsg("CalcNotchPos: Size_slot="+str(size_slot)+", notch_number="+str(notch_number)+", notch_size="+str(notch_size)+", Shift="+str(Shift)+'\n')
        for j in range(n_slot):
            #For each slot
            for i in range(i_notch_number):
                NPos.append((j*(size_slot+thickness)+notch_size+2*i*notch_size + Shift, notch_size, j))        #Add a tuple with 3 elements for start, size of notch and group number
        return NPos

    def ComputeJointSize(self, xbox, ybox, zbox, back_left_radius, back_right_radius, front_right_radius, front_left_radius):
        '''
        This function compute finger joint size
        It will try to have identical finger joint, but if not possible we will have different joint sizes
        Basic joint size : if l < 100, size = 5mm, when l > 100 --> size = 0.5*sqrt(l)
        '''
        #First take into account radius
        x = min(xbox - back_left_radius - back_right_radius, xbox - front_right_radius - front_left_radius)
        if x < 18:
            inkex.errormsg('Error: box length too small, should be at least 18mm + round radius')
            CloseDebugFile()
            exit()
        y = min(ybox - back_left_radius - front_left_radius, ybox - front_right_radius - back_right_radius)
        if y < 18:
            inkex.errormsg('Error: box depth too small, should be at least 18mm + round radius')
            CloseDebugFile()
            exit()
        if x  <= 100:
            basic_size_x = 5.0
        else:
            basic_size_x = 5.0*math.pow(x/100,0.8)
        if y <= 100:
            basic_size_y = 5.0
        else:
            basic_size_y = 5.0*math.pow(y/100,0.8)
        if zbox <= 100:
            basic_size_z = 5.0
        else:
            basic_size_z = 5.0*math.pow(zbox/100,0.8)
        #DebugMsg("Basic joint sizes (1) :"+str((basic_size_x, basic_size_y, basic_size_z))+' \n')
        #Now try to converge towards a single size
        # First with x and y
        if basic_size_x > basic_size_y and y >= 3.0*basic_size_x + 1:
            #x is greater, but at least 3 joints in y direction (one notch)
            basic_size_y = basic_size_x
        if basic_size_y > basic_size_x and x >= 3.0*basic_size_y + 1:
            #y is greater, but at least 3 joints in x direction (one notch)
            basic_size_x = basic_size_y
        # For z direction, should have at least 3 joint size (one notch)
        if basic_size_x > basic_size_y:
            if zbox > 3*basic_size_x + 1:
                basic_size_z = basic_size_x
            else:
                basic_size_z = (zbox-1) / 3         #If not possible, set max finger size
        else:
            if zbox > 3*basic_size_y + 1:
                basic_size_z = basic_size_y
            else:
                basic_size_z = (zbox-1) / 3         #If not possible, set max finger size
        return(basic_size_x, basic_size_y, basic_size_z)

    def drawSteelHingeElement(self, idx, thickness, xOffset, yOffset, parent):
        StartOffset = (xOffset, yOffset)
        xOffset -= 2*thickness

        path = th_inkscape_path((xOffset, yOffset), parent, 'HingeElt_'+str(idx))
        path.MoveTo(0, 0)
        #Start at upper right
        path.LineToVRel(thickness)
        path.LineToHRel(-thickness)
        path.LineToVRel(thickness)
        path.LineToHRel(thickness)
        path.LineToVRel(thickness)
        #Now draw half circle (radius is 1.5*thickness)
        #Position is now 0,3*thickness
        path.Bezier(1.5*thickness*0.551916, 3*thickness, 1.5*thickness, 3*thickness+1.5*thickness*0.551916, 1.5*thickness, 4.5*thickness) 
        path.Bezier(1.5*thickness, 4.5*thickness+1.5*thickness*0.551916, 1.5*thickness*(1-0.551916), 6*thickness, 0, 6*thickness) 
        #Second part of circle has a radius of 2*thickness
        path.Bezier(-2*thickness*0.551916, 6*thickness, -2*thickness, 6*thickness-2*thickness*0.551916, -2*thickness, 4*thickness) 
        path.LineTo(-2*thickness, thickness)
        path.Bezier(-2*thickness, thickness*(1-0.551916), thickness*-1.551916, 0, -thickness, 0)
        path.LineTo(0,0)
        #and last the circle at center for this axis, radius is RadiusSteelHingeAxis mm 
        #Change the diameter to allow some space
        locRadiusSteelHingeAxis = RadiusSteelHingeAxis + thickness * RadiusSteelHingeAxisChange
        path.drawCircle(0, 4.5*thickness, locRadiusSteelHingeAxis)
        path.Close()
        path.GenPath()
        if path.xmin < self.BoundingBox[0]:
            self.BoundingBox[0] = path.xmin
        if path.ymin < self.BoundingBox[1]:
            self.BoundingBox[1] = path.ymin
        if path.xmax > self.BoundingBox[2] - 2:
            self.BoundingBox[2] = path.xmax + 2
        if  path.ymax > self.BoundingBox[3] - 2:
            self.BoundingBox[3] =  path.ymax + 2

    def BuildTop(self, xbox, ybox, back_left_radius, back_right_radius, front_right_radius, front_left_radius):
        '''
        Draw the top of the box. It depends on the lid style
        '''
        if self.options.lid_type == 'Without' or self.options.lid_type == 'Coffin':
            return      # Nothing in this case
        if self.options.lid_type == 'Sliding':
            #Specific case, top is a rectangle which is xbox long and ybox  wide with finger joints on top
            #Not compatible with rounded corners on back, so radius is set to 0
            #On top, corner are internal on x and external on y
            #Position is set at 0,0 (first element)
            #There is also a line of finger joints which is xbox long and thickness wide, begin with this one
            TopLineBottomRight = CornerPoint((xbox+2*thickness,thickness), 0, 1, 1)
            TopLineBottomLeft = CornerPoint((0,thickness), 0, 1, 1)
            #Modify Bottom right corner to change start of line
            TopLineBottomRight.x_start_joint -= thickness
            #idem for bottom left
            TopLineBottomLeft.x_end_joint += thickness
            TopLine = BoxFace('Lid_Joints', CornerPoint((0,0), 0, 1, 1), 
                          0, CornerPoint((xbox+2*thickness,0), 0, 1, 1), 
                          0, TopLineBottomRight,
                          self.x_joint, TopLineBottomLeft,
                          0, self.group, [0.0,0.0])
            TopLine.drawSimpleFace(True)
            self.UpdateBoundingBox(TopLine)
            Top = BoxFace('Lid_Top', CornerPoint((0,0), back_left_radius, 1, 0), 
                          self.x_joint, CornerPoint((xbox,0), back_right_radius, 1, 0), 
                          0, CornerPoint((xbox,ybox), front_right_radius, 1, 1),
                          0, CornerPoint((0,ybox), front_left_radius, 1, 1),
                          0, self.group, [-thickness,-self.BoundingBox[3]])
            Top.drawSimpleFace(True)
            self.UpdateBoundingBox(Top)
            return
        if self.options.lid_type == 'SlidingRounded':
            #Specific case, top is a rectangle which is xbox long and ytop_sliding_rounded  wide with finger joints on 3 edges
            #The rectangle is a little bit bigger than thickness to allow easy handling.
            TopLine = BoxFace('Lid_Joints', CornerPoint((thickness,0), 0, 1, 1), 
                          0, CornerPoint((xbox-thickness-SlidingLidSpaceX,0), 0, 1, 1), 
                          0, CornerPoint((xbox-thickness-SlidingLidSpaceX,thickness*1.5), 0, 1, 1),
                          self.x_joint, CornerPoint((thickness,thickness*1.5), 0, 1, 1),
                          0, self.group, [0.0,0.0])
            TopLine.drawSimpleFace(True)
            self.UpdateBoundingBox(TopLine)
            Top = BoxFace('Top', CornerPoint((0,0), 0, 1, 1), 
                          self.x_joint, CornerPoint((xbox,0), 0, 1, 1), 
                          self.y_joint, CornerPoint((xbox, self.ytop_sliding_rounded), 0, 1, 1),
                          0, CornerPoint((0, self.ytop_sliding_rounded), 0, 1, 1),
                          self.y_joint, self.group,  [-thickness,-self.BoundingBox[3]])
            Top.drawSimpleFace(True)
            self.UpdateBoundingBox(Top)
            return
            
        #For all cases except coffin, draw a rounded rectangle with internal corners
        Top = BoxFace('Lid_Top', CornerPoint((0,0), back_left_radius, 1, 1), 
                      self.x_joint, CornerPoint((xbox,0), back_right_radius, 1, 1), 
                      self.y_joint, CornerPoint((xbox,ybox), front_right_radius, 1, 1),
                      self.x_joint, CornerPoint((0,ybox), front_left_radius, 1, 1),
                      self.y_joint, self.group, [0.0, 0.0])
        Top.drawSimpleFace(False)
        if self.options.lid_type == 'Simple':
            #Add a hole in the top, which the same rounded rectangle, but with thickness less in each direction 
            TopHole = BoxFace('Lid_Int', CornerPoint((thickness,thickness), back_left_radius-thickness, 1, 1), 
                          0, CornerPoint((xbox-thickness,thickness), back_right_radius-thickness, 1, 1), 
                          0, CornerPoint((xbox-thickness,ybox-thickness), front_right_radius-thickness, 1, 1),
                          0, CornerPoint((thickness,ybox-thickness), front_left_radius-thickness, 1, 1),
                          0, self.group, [0.0, 0.0], Top.path)
            TopHole.drawSimpleFace(False)
        Top.Close()     #Close and generate path (both if simple lid)
        self.UpdateBoundingBox(Top)
        if self.options.lid_type == 'Simple':
            #In this case, draw a simple face without notches, external at all corners in both directions
            Top = BoxFace('Lid', CornerPoint((0,0), back_left_radius, 0, 0), 
                          0, CornerPoint((xbox,0), back_right_radius, 0, 0), 
                          0, CornerPoint((xbox,ybox), front_right_radius, 0, 0),
                          0, CornerPoint((0,ybox), front_left_radius, 0, 0),
                          0, self.group, [-self.BoundingBox[2]-thickness-2, 0.0])
            Top.drawSimpleFace(True)
            self.UpdateBoundingBox(Top)

        return

    def BuildBottom(self, xbox, ybox, back_left_radius, back_right_radius, front_right_radius, front_left_radius):
        '''
        Draw the bottom of the box. It is a rounded rectangle 
        Also draw the holes used to secure the internal walls
        Should exchange left and right from top to draw the external face
        '''
        if self.options.lid_type == 'SlidingRounded':
            Bottom = BoxFace('Bottom', CornerPoint((0,0), back_right_radius, 1, 1), 
                      self.x_joint, CornerPoint((xbox,0), back_left_radius, 1, 1), 
                      self.y_joint, CornerPoint((xbox,ybox), front_left_radius, 1, 1),
                      0, CornerPoint((0,ybox), front_right_radius, 1, 1),
                      self.y_joint, self.group, [-self.BoundingBox[2], 0.0])            #Draw it right of top, same Y

        else:
            Bottom = BoxFace('Bottom', CornerPoint((0,0), back_right_radius, 1, 1), 
                      self.x_joint, CornerPoint((xbox,0), back_left_radius, 1, 1), 
                      self.y_joint, CornerPoint((xbox,ybox), front_left_radius, 1, 1),
                      self.x_joint, CornerPoint((0,ybox), front_right_radius, 1, 1),
                      self.y_joint, self.group, [-self.BoundingBox[2], 0.0])            #Draw it right of top, same Y
        Bottom.drawSimpleFace(False)
        #now the holes used to fix the walls
        #Start with columns, compute holes position
        self.ListNotchColumns = self.CalcNotchPos(self.n_slot_y, self.y_slot_size)
        DebugMsg("List Column Notches:"+str( self.ListNotchColumns)+'\n')
        for i in range(1, self.n_slot_x):
            #For each wall, draw holes corresponding at each notch_y
            for notch in self.ListNotchColumns:
                drawHole(Bottom.path, i*(self.x_slot_size+thickness), notch[0] + thickness, thickness, notch[1], burn)
            
        #Then rows
        self.ListNotchRows = self.CalcNotchPos(self.n_slot_x, self.x_slot_size)
        DebugMsg("List Row Notches:"+str( self.ListNotchRows)+'\n')
        
        for i in range(1, self.n_slot_y):
            #For each wall, draw holes corresponding at each notch_y
            for notch in self.ListNotchRows:
                drawHole(Bottom.path, notch[0] + thickness, i*(self.y_slot_size+thickness), notch[1], thickness, burn)
        
        Bottom.Close()
        self.UpdateBoundingBox(Bottom)
        return

    def drawColumWall(self, index, n_slot_y, y_slot_size, ListNotchPos, length, zbox, height_percentage, xOffset, yOffset, parent):
        '''
        Draw the face, specific case for columns walls
        This is a specific face with cuts for row walls on top
        '''
        DebugMsg("\nDrawColumWall, index="+str(index)+" n_Slot="+str(n_slot_y)+" Slot_Size="+str(y_slot_size)+" Length="+str(length)+" Height="+str(zbox)+" Percentage="+str(height_percentage)+" Offset="+str((xOffset, yOffset))+'\n')
        path = th_inkscape_path((xOffset-thickness, yOffset), parent, 'COL_WALL_'+str(index+1))
        
        actual_height = zbox * height_percentage / 100.0
        VNotchLine1 = NotchLine((length,0,1), (length, actual_height, 1), math.pi/2, self.z_joint )        #Vertical Notch line
        VNotchLine2 = NotchLine((0,actual_height,1), (0, 0, 1), -math.pi/2, self.z_joint )       #Vertical Notch line, reverse


        path.MoveTo(0,0)
        #first H line with cut to accomodate with row walls
        for i in range(1, n_slot_y):
            path.LineToHRel(y_slot_size)
            path.LineToVRel(actual_height/2)
            path.LineToHRel(thickness)
            path.LineToVRel(-actual_height/2)
        path.LineTo(length, 0)
     
        #Second line (V), this is a notch line
        path.LineTo(length, thickness)
        VNotchLine1.drawNotchLine(path)
        path.LineTo(length, actual_height)
        #Third line (H) with notches, but at specific positions. Use reversed because, draw from right to left
        for Notch in reversed(ListNotchPos):
            path.LineTo(Notch[0]+Notch[1], actual_height)
            path.LineToVRel(thickness)
            path.LineToHRel(-Notch[1])
            path.LineToVRel(-thickness)
        path.LineTo(0, actual_height)
        #and last one
        path.LineTo(0, actual_height-thickness)
        VNotchLine2.drawNotchLine(path)
        path.LineTo(0, 0)
        
        #Apply bounding box of path
        DebugMsg("Path Bounding box="+str(((path.xmin, path.ymin), (path.xmax, path.ymax)))+'\n')
        if path.xmin < self.BoundingBox[0]:
            self.BoundingBox[0] = path.xmin
        if path.ymin < self.BoundingBox[1]:
            self.BoundingBox[1] = path.ymin
        if path.xmax > self.BoundingBox[2] - 2:
            self.BoundingBox[2] = path.xmax + 2
        if  path.ymax > self.BoundingBox[3] - 2:
            self.BoundingBox[3] =  path.ymax + 2

        #Close the path
        path.Close()
        path.GenPath()
        #DebugMsg("Closing path, BoundingBox="+str(self.BoundingBox)+'\n')


    def drawRowWall(self, index, n_slot_x, x_slot_size, ListNotchPos, length, zbox, height_percentage, xOffset, yOffset, parent):
        '''
        Draw the face, specific case for row walls
        This is a specific face with cuts for columns walls on bottom
        index : index of Row wall (0..nSlot-1)
        n_slot_x : number of slots (columns) to draw specific cuts for the column wall
        x_slot_size
        ListNotchPos : Position of notches
        '''
        DebugMsg("\nDrawRowWall, index="+str(index)+" n_Slot="+str(n_slot_x)+" Slot_Size="+str(x_slot_size)+" Length="+str(length)+" Height="+str(zbox)+" Offset="+str((xOffset, yOffset))+'\n')
        path = th_inkscape_path((xOffset-thickness, yOffset), parent, 'ROW_WALL_'+str(index+1))
        actual_height = zbox * height_percentage / 100.0
        
        VNotchLine1 = NotchLine((length,0,1), (length, actual_height, 1), math.pi/2, self.z_joint )        #Vertical Notch line
        VNotchLine2 = NotchLine((0,actual_height,1), (0, 0, 1), -math.pi/2, self.z_joint )       #Vertical Notch line, reverse


        path.MoveTo(0,0)
        
        #first H line (top) without cut, so up to length
        path.LineTo(length, 0)

        #Second line (V), this is a notch line
        path.LineTo(length, thickness)
        VNotchLine1.drawNotchLine(path)
        path.LineTo(length, actual_height)
        #Third line (bottom H) with notches, but at specific positions. Use reversed because, draw from right to left, also cut openings for columns
        # At each change of group, draw a cut
        group_num = n_slot_x - 1
        for Notch in reversed(ListNotchPos):
            if group_num != Notch[2]:           #   Change of group, draw cut (up to half of the piece)
                path.LineTo(group_num * (x_slot_size + thickness) , actual_height)
                path.LineToVRel(-actual_height/2)
                path.LineToHRel(-thickness)
                path.LineToVRel(actual_height/2)
                group_num = Notch[2]            #Change group for next pass
            path.LineTo(Notch[0]+Notch[1], actual_height)
            path.LineToVRel(thickness)
            path.LineToHRel(-Notch[1])
            path.LineToVRel(-thickness)
        path.LineTo(0, actual_height)
        #and last one
        path.LineTo(0, actual_height-thickness)
        VNotchLine2.drawNotchLine(path)
        path.LineTo(0, 0)
        
        #Apply bounding box of path
        DebugMsg("Path Bounding box="+str(((path.xmin, path.ymin), (path.xmax, path.ymax)))+'\n')
        if path.xmin < self.BoundingBox[0]:
            self.BoundingBox[0] = path.xmin
        if path.ymin < self.BoundingBox[1]:
            self.BoundingBox[1] = path.ymin
        if path.xmax > self.BoundingBox[2] - 2:
            self.BoundingBox[2] = path.xmax + 2
        if  path.ymax > self.BoundingBox[3] - 2:
            self.BoundingBox[3] =  path.ymax + 2

        #Close the path
        path.Close()
        path.GenPath()
        #DebugMsg("Closing path, BoundingBox="+str(self.BoundingBox)+'\n')

    def drawCoffinSide(self, FlagRight, ybox, zlid, z_dome_lid, xOffset, yOffset, parent):
        ''' 
        Draw the sides of the coffin style lid.
        This is a rectangle ybox x zlid with an ellipse (ybox, z_dome_lid) on top of the rectangle
        There a "normal notches on the rectangle, then small notches on the ellipse, because the "front/top/Back" part will be flex
        '''
        DebugMsg("\ndrawCoffinSide, FlagRight="+str(FlagRight)+" ybox="+str(ybox)+" zlid="+str(zlid)+" z_dome_lid="+str(z_dome_lid)+'\n')
        name = 'Lid_Left'
        if FlagRight=='Right':
            name = 'Lid_Right'
        #Change offset in y direction because this one will be drawn from bottom left.
        path = th_inkscape_path((xOffset-thickness, yOffset-zlid - z_dome_lid-thickness), parent, name)
        #First build the notch lines for the rectangle
        VNotchLine1 = NotchLine((0,0,1), (0, -zlid, 1), -math.pi/2, self.z_joint )          #Vertical Notch line (left side)
        VNotchLine2 = NotchLine((ybox,-zlid,1), (ybox, 0, 1), math.pi/2, self.z_joint )     #Vertical Notch line, right side
        
        #First point on (0,0) : bottom/left of the lid
        path.MoveTo(0, 0)
        #The draw left notch line
        VNotchLine1.drawNotchLine(path)
        #The draw the notched ellipse, this ellipse has parameters ybox/2 and z_dome_lid       
        TopLid = Ellipse(ybox/2.0, z_dome_lid)
        TopLid.drawNotchedEllipse(path, math.pi, 2*math.pi, (0, -zlid))
        #Now the second Notch line
        VNotchLine2.drawNotchLine(path)
        #And end with bottom line (straight)
        path.LineTo(0,0)
        #Apply bounding box of path
        DebugMsg("Path Bounding box="+str(((path.xmin, path.ymin), (path.xmax, path.ymax)))+'\n')
        if path.xmin < self.BoundingBox[0]:
            self.BoundingBox[0] = path.xmin
        if path.ymin < self.BoundingBox[1]:
            self.BoundingBox[1] = path.ymin
        if path.xmax > self.BoundingBox[2] - 2:
            self.BoundingBox[2] = path.xmax + 2
        if  path.ymax > self.BoundingBox[3] - 2:
            self.BoundingBox[3] =  path.ymax + 2

        path.Close()
        path.GenPath()
        
    def drawCoffinTop(self, xbox, ybox, zlid, z_dome_lid, xOffset, yOffset, parent):
        ''' 
        Draw the top of the coffin style lid.
        This is 2 rectangle xbox x zlid separated by a flex pattern which has the length half of the ellipse (ybox, z_dome_lid), flex height is xbox 
        '''
        DebugMsg("\ndrawCoffinTop, xbox="+str(xbox)+" ybox="+str(ybox)+" zlid="+str(zlid)+" z_dome_lid="+str(z_dome_lid)+'\n')
        #Change offset in y direction because this one will be drawn from bottom left.
        path = th_inkscape_path((xOffset, yOffset - thickness), parent, 'Coffin_Top')
        DebugMsg("Offset ="+str((xOffset, yOffset))+" Path_Offset="+str((path.offsetX, path.offsetY))+'\n')
        #Create the ellipse object used to draw the flex
        FlexBand = Ellipse(ybox/2.0, z_dome_lid)
        FlexBand.Compute_Ellipse_Params(math.pi, 2*math.pi)
        l = FlexBand.length_ellipse
        #First build the notch lines for the rectangle
        HNotchLine1 = NotchLine((zlid, xbox+thickness, 0), (0, xbox+thickness, 0), math.pi, self.z_joint )     #Horizontal Notch line, bottom left
        HNotchLine2 = NotchLine((0,-thickness,0), (zlid, -thickness, 0), 0, self.z_joint )                     #Horizontal Notch line, top left
        HNotchLine3 = NotchLine((zlid+l, xbox+thickness, 1), (2*zlid+l, xbox+thickness, 1), 0, self.z_joint )  #Horizontal Notch line, bottom right        
        HNotchLine4 = NotchLine((2*zlid+l, -thickness, 1), (zlid+l, -thickness, 1), math.pi, self.z_joint )    #Horizontal Notch line, bottom left

        #In order to minimize move effects, draw the holes for the hinge first
        #Draw holes for the hinge(s)
        for Hinge in self.HingeList:
            HingePos = Hinge[2] + 2*thickness
            path.MoveTo(3.5*thickness, HingePos + 0.5*SteelHingeSpacing)
            path.LineToVRel(thickness)
            path.LineToHRel(thickness)
            path.LineToVRel(-thickness)
            path.LineToHRel(-thickness)
            path.MoveTo(3.5*thickness, HingePos + 2*thickness + 1.5*SteelHingeSpacing)
            path.LineToVRel(thickness)
            path.LineToHRel(thickness)
            path.LineToVRel(-thickness)
            path.LineToHRel(-thickness)

        #First point on (zlid,0) : bottom/left of the lid
        path.MoveTo(zlid, xbox+thickness)
        #The draw left notch line
        HNotchLine1.drawNotchLine(path)
        #The draw the bottom line with cuts for the hinge(s)
        #Now draw holes for the hinge(s), reverse because draw from right to left
        for Hinge in reversed(self.HingeList):
            HingePos = Hinge[2] + thickness
            #First H line up to end of 2nd hinge
            path.LineTo(0, HingePos + 5*thickness + 2.5*SteelHingeSpacing)
            #Then Hinge
            path.LineToHRel(1.5*thickness + 0.5*SteelHingeSpacing)
            path.LineToVRel(-thickness - SteelHingeSpacing)
            path.LineToHRel(thickness - 0.5*SteelHingeSpacing)
            path.LineToVRel(-thickness)
            path.LineToHRel(-thickness + 0.5*SteelHingeSpacing)
            path.LineToVRel(-thickness - SteelHingeSpacing)
            path.LineToHRel(thickness - 0.5*SteelHingeSpacing)
            path.LineToVRel(-thickness)
            path.LineToHRel(-thickness + 0.5*SteelHingeSpacing)
            path.LineToVRel(-thickness - SteelHingeSpacing)
            path.LineToHRel(-1.5*thickness - 0.5*SteelHingeSpacing)
        #Then draw up to corner
        path.LineTo(0, -thickness)
        #Now the second Notch line
        HNotchLine2.drawNotchLine(path)
        #Then the flex band
        FlexBand.drawFlexEllipse(path, xbox, self.options.SkipFlexLines, (zlid, -thickness))
        #Then the third notch line
        HNotchLine3.drawNotchLine(path)
        #Then the straight line up to the next corner (top right)
        path.LineTo(2*zlid+l, -thickness)
        #And the last line
        HNotchLine4.drawNotchLine(path)
        #Apply bounding box of path
        DebugMsg("Path Bounding box="+str(((path.xmin, path.ymin), (path.xmax, path.ymax)))+'\n')
        if path.xmin < self.BoundingBox[0]:
            self.BoundingBox[0] = path.xmin
        if path.ymin < self.BoundingBox[1]:
            self.BoundingBox[1] = path.ymin
        if path.xmax > self.BoundingBox[2] - 2:
            self.BoundingBox[2] = path.xmax + 2
        if  path.ymax > self.BoundingBox[3] - 2:
            self.BoundingBox[3] =  path.ymax + 2
        path.GenPath()

    def drawRoundedSlidindLid(self, w_lid, l_lid, xOffset, yOffset, parent):
        ''' 
        Draw the rounded sliding lid.
        This is a rectangle made of flex which is w_lid wide and l_lid long.
        There are notches on one width long edge, but not on the other edges
        '''
        DebugMsg("\ndrawRoundedSlidindLid, w_lid="+str(w_lid)+" l_lid="+str(l_lid)+'\n')
        #Change offset in y direction because this one will be drawn from bottom left.
        path = th_inkscape_path((xOffset, yOffset - thickness), parent, 'Sliding_Top')
        DebugMsg("Offset ="+str((xOffset, yOffset))+" Path_Offset="+str((path.offsetX, path.offsetY))+'\n')

        #First build the notch line for the rectangle
        NotchLine1 = NotchLine((0, w_lid-thickness, 0), (0, thickness, 0), -math.pi/2, self.z_joint )     #Vertical Notch line, left edge, external
        #Then draw the rectangle
        path.MoveTo(0, w_lid-thickness)
        NotchLine1.drawNotchLine(path)
        DebugMsg("After Notches pos="+str((path.x_noff, path.y_noff))+'\n')
        path.LineToHRel(thickness)
        path.LineToVRel(-thickness)
        #Then the top H Line
        path.LineTo(l_lid, 0)
        #Then V Line
        path.LineToVRel(w_lid)
        #Then last H line
        path.LineTo(thickness, w_lid)
        path.LineToVRel(-thickness)
        path.LineTo(0, w_lid-thickness)
        
        #Now draw flex lines, first compute flex parameters
        nLines = int(l_lid - thickness) - 1              #One mm free at each end
        delta_x =  (l_lid - thickness - 1)/nLines
        TotalHeight = w_lid
        nMark = int( TotalHeight / 50) + 1              #Compute number of lines
        nMark = max(nMark, 2)   # At least 2 marks
        #Sizes of short and long lines to make flex
        LongMark = (TotalHeight / nMark) - 2.0          #Long Mark equally divide the height
        ShortMark = LongMark/2                          # And short mark should lay at center of long marks
        DebugMsg("\ndrawRoundedSlidindLid, nLines="+str(nLines)+" TotalHeight="+str(TotalHeight)+" nMark="+str(nMark)+" LongMark="+str(LongMark)+" ShortMark="+str(ShortMark)+'\n')
        xpos = thickness + 1
        ypos = 0
        for i in range(nLines):
            if i % 2 == 0:
                #Even number, start with short mark and draw from top to bottom
                GenLinesFlex(xpos, 0, ShortMark, 1, 1, path)
                #Then nMark-1 long Lines
                GenLinesFlex(xpos, ShortMark+2, LongMark, nMark-1, 1, path)
                #And the last short line
                GenLinesFlex(xpos, TotalHeight-ShortMark, ShortMark, 1, 1, path)
            else:
                #odd number draw long lines only, at 1mm from edge
                GenLinesFlex(xpos, w_lid-1, LongMark, nMark, -1, path)
            xpos += delta_x


        
        #Apply bounding box of path
        DebugMsg("Path Bounding box="+str(((path.xmin, path.ymin), (path.xmax, path.ymax)))+'\n')
        if path.xmin < self.BoundingBox[0]:
            self.BoundingBox[0] = path.xmin
        if path.ymin < self.BoundingBox[1]:
            self.BoundingBox[1] = path.ymin
        if path.xmax > self.BoundingBox[2] - 2:
            self.BoundingBox[2] = path.xmax + 2
        if  path.ymax > self.BoundingBox[3] - 2:
            self.BoundingBox[3] =  path.ymax + 2
        path.GenPath()
        


    def effect(self):
        global burn, thickness
        
        # input sanity check
        error = False
        if self.options.thickness <  1 or self.options.thickness >  10:
            inkex.errormsg('Error: thickness should be at least 1mm and less than 10mm')
            error = True

        if error:
            exit()

        self.n_slot_x = self.options.n_slot_x
        self.n_slot_y = self.options.n_slot_y


        # convert units
        unit = self.options.unit

        xbox = self.svg.unittouu(str(self.options.x) + unit)
        ybox = self.svg.unittouu(str(self.options.y) + unit)
        zbox = self.svg.unittouu(str(self.options.z) + unit)
        zlid = self.svg.unittouu(str(self.options.z_lid) + unit)
        z_dome_lid = self.svg.unittouu(str(self.options.z_dome_lid) + unit)
        radius_lid = self.svg.unittouu(str(self.options.radius_lid) + unit)

        if self.options.StraigthCorners:
            back_left_radius = 0
            back_right_radius = 0
            front_right_radius = 0
            front_left_radius = 0
        else:
            back_left_radius = self.svg.unittouu(str(self.options.back_left_radius) + unit)
            back_right_radius = self.svg.unittouu(str(self.options.back_right_radius) + unit)
            front_right_radius = self.svg.unittouu(str(self.options.front_right_radius) + unit)
            front_left_radius = self.svg.unittouu(str(self.options.front_left_radius) + unit)
        
        max_radius = max(back_left_radius, back_right_radius, front_right_radius, front_left_radius)
        thickness = self.svg.unittouu(str(self.options.thickness) + unit)
        burn = self.svg.unittouu(str(self.options.burn) + unit)

        self.x_joint = self.svg.unittouu(str(self.options.x_joint) + unit) 
        self.y_joint = self.svg.unittouu(str(self.options.y_joint) + unit) 
        self.z_joint = self.svg.unittouu(str(self.options.z_joint) + unit) 

        self.x_slot_size = (xbox  - (1+self.n_slot_x)*thickness)/self.n_slot_x 
        self.y_slot_size = (ybox - (1+self.n_slot_y)*thickness)/self.n_slot_y 


        
        if self.x_slot_size < 18 or self.y_slot_size < 18:
            inkex.errormsg('Error: each slot should be at least 18mm large, here x_slot_size='+str(self.x_slot_size)+ ' y_slot_size='+str(self.y_slot_size))
            CloseDebugFile()
            exit()
        if self.x_slot_size < max_radius or self.y_slot_size < max_radius: 
            inkex.errormsg('Error: slot size should be greater than rounded corner radius, here x_slot_size='+str(self.x_slot_size)+ ' y_slot_size='+str(self.y_slot_size))
            CloseDebugFile()
            exit()

                
        svg = self.document.getroot()
        docWidth = self.svg.unittouu(svg.get('width'))
        docHeigh = self.svg.unittouu(svg.attrib['height'])

        if self.options.as_layer is True:
            layer = etree.SubElement(self.svg.get_current_layer(), 'g')
            layer.set(inkex.addNS('label', 'inkscape'), 'Generic Box')
            layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
            self.group = etree.SubElement(layer, 'g')
        else:
            self.group = etree.SubElement(self.svg.get_current_layer(), 'g')
        OpenDebugFile()
        
        HasLid = False
        HasNormalLid = False
        #Compute joint size if auto is chosen
        if self.options.AutoSizeJoints:
            self.x_joint, self.y_joint, self.z_joint = self.ComputeJointSize(xbox, ybox, zbox, back_left_radius, back_right_radius, front_right_radius, front_left_radius)
        #Default case, for the top lines, front and back joints are x_joint in size, left and right joints are y_joint in size
        self.front_joint = self.x_joint
        self.back_joint = self.x_joint
        self.right_joint = self.y_joint
        self.left_joint = self.y_joint
        
        DebugMsg("Joints size ="+str((self.x_joint, self.y_joint, self.z_joint))+'\n')
        DebugMsg("Slots X N="+str(self.n_slot_x)+" size="+str(self.x_slot_size)+'\n')
        DebugMsg("Slots Y N="+str(self.n_slot_y)+" size="+str(self.y_slot_size)+'\n')
        
        #Now, check if internal walls should be drawn
        self.InternalWalls_LR = False
        self.InternalWalls_FB = False
        zbox_internal_walls = zbox          #Height of internal walls
        
        #If there are slots inside the box, also draw internal walls
        if self.n_slot_x  > 1:
            self.InternalWalls_FB = True
        if self.n_slot_y  > 1:
            self.InternalWalls_LR = True

        # If lid is sliding, there are always internal walls left and right
        if self.options.lid_type == 'Sliding':
            self.InternalWalls_LR = True
            zbox += thickness               #Also increase box height to take into account the sliding top, but NOT internal walls height
            zbox_internal_walls -= 0.2      #Indeed, reduce internal wall height to ease sliding
            if back_left_radius > 0 or back_right_radius > 0:
                inkex.errormsg('Error: Sliding lid is incompatible with rounded corners on back')
                CloseDebugFile()
                exit()
            self.front_joint = 0        #No joint on front top
        
        # If lid is rounded sliding, there are always internal walls left and right
        if self.options.lid_type == 'SlidingRounded':
            if radius_lid > zbox or radius_lid > ybox:
                inkex.errormsg('Error: incorrect radius for sliding lid, should be lower than width and height ')
                CloseDebugFile()
                exit()                
            self.InternalWalls_LR = True
            zbox += thickness               #Also increase box height to take into account the sliding top, but NOT internal walls height
            zbox_internal_walls -= 0.2      #Indeed, reduce internal wall height to ease sliding
            if back_left_radius > 0 or back_right_radius > 0 or front_left_radius > 0 or  front_right_radius:
                inkex.errormsg('Error: Sliding lid is incompatible with rounded corners')
                CloseDebugFile()
                exit()
            self.front_joint = 0        #No joint on front top
            #Check that the dimensions are OK. y_box should be greater than radius_lid*pi/2
            self.radius_back_lid = thickness * 6
            self.ytop_sliding_rounded = ybox - radius_lid
            self.length_sliding_rounded = zbox + radius_lid*(math.pi/2 - 1)
            DebugMsg("Rounded sliding, radius_lid="+str(radius_lid)+", radius_back_lid="+str(self.radius_back_lid)+" ytop_sliding_rounded="+str(self.ytop_sliding_rounded)+" length_sliding_rounded="+str(self.length_sliding_rounded)+"\n")
            if self.length_sliding_rounded > zbox + self.radius_back_lid*(math.pi/2 - 2) +  self.ytop_sliding_rounded - 2 * thickness:
                inkex.errormsg('Error: no room for sliding lid, please increase width, should be at least '+str( (radius_lid - self.radius_back_lid)*(math.pi/2 - 1) + 2 * thickness + radius_lid + self.radius_back_lid ))
                CloseDebugFile()
                exit()                

        # If there is no lid, no notches on top
        if self.options.lid_type == 'Without':
            self.front_joint = 0        #No joint on front top
            self.back_joint = 0         #No joint on back top
            self.right_joint = 0        #No joint on right top
            self.left_joint = 0         #No joint on left top
            #As top edges are external, but without notches, just decrease height by thickness
            zbox -= thickness
        
        # If this is a real lid, no round corners allowed on back
        if self.options.lid_type == 'WoodHinge' or self.options.lid_type == 'SteelHinge' or self.options.lid_type == 'Coffin':
            if back_left_radius > 0 or back_right_radius > 0:
                inkex.errormsg('Error: real lid option is incompatible with rounded corners on back')
                CloseDebugFile()
                exit()
            self.front_joint = 0        #No joint on front top
            self.back_joint = 0         #No joint on back top
            self.right_joint = 0        #No joint on right top
            self.left_joint = 0         #No joint on left top
            #As top edges are external, but without notches, just decrease height by thickness
            zbox -= thickness
            zlid -= thickness
            if self.options.lid_type == 'Coffin':
                if front_left_radius > 0 or front_right_radius > 0:
                    inkex.errormsg('Error: coffin lid option is incompatible with rounded corners')
                    CloseDebugFile()
                    exit()
                HasCoffinlid = True
                HasLid = False
            else:
                HasCoffinlid = False
                HasLid = True

        if self.options.lid_type == 'SteelHinge' or self.options.lid_type == 'Coffin':
            #Compute placement of hinges
            #First compute hinge width. Each hinge has 5 elements with thickness width whiche should be slighly spaced for the main box elements (3)
            hingeWidth = 5*thickness + 3*SteelHingeSpacing
            if ( hingeWidth > self.x_slot_size - 3 ):
                inkex.errormsg('Error: no space for hinge within slots, slots should be at least '+str(hingeWidth+3)+'mm wide')
                CloseDebugFile()
                exit(1)
            #if the box is small with only one slot in x direction try with only one hinge
            if self.n_slot_x == 1 and self.x_slot_size < 2 * hingeWidth + 30:
                HingePos = (self.x_slot_size - hingeWidth)/2.0
                self.HingeList.append((0, HingePos, HingePos))      # One hinge, starting at the middle of slot 0 (the only one)
            elif self.n_slot_x == 1:
                #One slot, but a large one. 2 hinges about 1/4 - 3/4 of the edge
                HingePos = max(self.x_slot_size/4 -  hingeWidth/2, 2)
                if HingePos < 10:
                    HingePos = 10
                self.HingeList.append((0, HingePos, HingePos))
                self.HingeList.append((0, self.x_slot_size - HingePos, (self.x_slot_size - HingePos - hingeWidth) ))
            elif self.n_slot_x == 2:
                #in this case place hinge in first and last slot.
                # Exact position depend on slot width, try to place hinge at about 1/3 of the slot
                HingePos = max(self.x_slot_size/3 -  hingeWidth/2, 2)
                if HingePos < 8:
                    HingePos = max(self.x_slot_size/2.5 -  hingeWidth/2, 2)         #1/3 is very close from start, so change to 1/2.5
                self.HingeList.append((0, HingePos, HingePos))
                self.HingeList.append((self.n_slot_x-1, self.x_slot_size - HingePos, (self.n_slot_x-1)*(self.x_slot_size+thickness) + (self.x_slot_size - HingePos - hingeWidth) ))
            elif self.n_slot_x <= 6:
                #in this case place hinge in first and last slot.
                # Exact position depend on slot width, try to place hinge at about 1/2 of the slot
                HingePos = (self.x_slot_size -  hingeWidth)/2.0
                self.HingeList.append((0, HingePos, HingePos))
                self.HingeList.append((self.n_slot_x-1, self.x_slot_size - HingePos, (self.n_slot_x-1)*(self.x_slot_size+thickness) + (self.x_slot_size - HingePos - hingeWidth) ))
            else:
                #a lot of slots, place hinge in second and before last slot, at center of slots 
                HingePos = (self.x_slot_size -  hingeWidth)/2.0
                self.HingeList.append((1, HingePos, self.x_slot_size + thickness + HingePos ))
                self.HingeList.append((self.n_slot_x-2, HingePos, (self.n_slot_x-2)*(self.x_slot_size+thickness) + (self.x_slot_size - HingePos - hingeWidth)))
            DebugMsg("Lid with steel hinge\n")
            DebugMsg("Hinge width="+str(hingeWidth)+", Number of hinges="+str(len(self.HingeList))+", Hinge pos="+str(self.HingeList)+"\n")


        #Draw external faces which are planes, begin with top (no top for rounded sliding or open or coffin)  
        
        DebugMsg("\n\nBuild TOP\n")
        self.BuildTop(xbox, ybox, back_left_radius, back_right_radius, front_right_radius, front_left_radius)

        DebugMsg("\n\nBuild Bottom\n")
        self.BuildBottom(xbox, ybox, back_left_radius, back_right_radius, front_right_radius, front_left_radius)
        
        ''' Draw sides, which could be rounded (with flex)
            For boxes with lid, draw also the lid, just above the side.
            There are 16 cases
            TL    TR    BR    BL    Flex                            Straight
            0    0    0    0    NO                                ALL                 OK
            0    0    0    1    Left → Front                    Back, Right         OK
            0    0    1    0    Front → Right                    Back, Left          OK
            0    0    1    1    Left → Front → Right            Back                OK
            0    1    0    0    Right → Back                    Front, Left         OK
            0    1    0    1    Right → Back, Left → Front      No                  OK
            0    1    1    0    Front --> Right --> Back        Left                OK
            0    1    1    1    Left → Front → Right → Back        No                  OK
            1    0    0    0    Back → Left                        Right, Front        OK
            1    0    0    1    Back → Left → Front                Right               OK
            1    0    1    0    Back → Left, Front → Right        No                  OK
            1    0    1    1    Back → Left → Front → Right        No                  OK
            1    1    0    0    Right → Back → Left                Front               OK
            1    1    0    1    Right → Back → Left  → Front    No                  OK
            1    1    1    0    Front → Right → Back → Left        No                  OK
            1    1    1    1    All Flex                        No
        '''
        FlexBandList = []        #empty list at init
        RightFace = None
        LeftFace = None
        ypos = -self.BoundingBox[3]
        yposface = ypos
        xpos = 0.0
        LidFace = None
        if front_left_radius == 0 and front_right_radius == 0:
            if HasLid:
                DebugMsg("Draw front lid\n")
                LidFace = BoxFace('Lid_Front', CornerPoint((0,0), 0, 0, 0), 
                              self.x_joint, CornerPoint((xbox,0), 0, 0, 0), 
                              self.z_joint, CornerPoint((xbox,zlid), 0, 0, 0),
                              self.front_joint, CornerPoint((0,zlid), 0, 0, 0),
                              self.z_joint, self.group, [xpos, ypos])        #Draw face just below previous drawings
                LidFace.drawSimpleFace(True)
                self.UpdateBoundingBox(LidFace)    #Now update bounding box, to place back face just below
                yposface = -self.BoundingBox[3]
            if self.options.lid_type != 'SlidingRounded':
                DebugMsg("\nStraight face for front\n")
                #No round, front is straight
                #Front is xbox * zbox, all corners are external in each direction
                Face = BoxFace('Front', CornerPoint((0,0), 0, 0, 0), 
                              self.front_joint, CornerPoint((xbox,0), 0, 0, 0), 
                              self.z_joint, CornerPoint((xbox,zbox), 0, 0, 0),
                              self.x_joint, CornerPoint((0,zbox), 0, 0, 0),
                              self.z_joint, self.group, [xpos, yposface])        #Draw face just below previous drawings
                Face.drawSimpleFace(True)
                xpos = -Face.BoundingBox[2]-2
                self.UpdateBoundingBox(Face)    #Now update bounding box
        elif front_left_radius == 0:
            #Rounded corner on Front right
            #Straight corner on Front/left, there is a flex band starting on front left
            if back_right_radius == 0:
                #Straight corner on Front / right, Flex on front --> right, BL to TR
                DebugMsg("\nFlex on front --> Right\n")
                FlexBand = ('Flex_Front_Right', 0, 1,                           #Draw Front then Right so first element is external and last internal
                            (xbox, self.front_joint, front_right_radius, self.x_joint),       #Then Front Notch Line and round corner r= front_right_radius
                            #Then Right notch line withount rounded corner, the last parameter is used when WoodHinge to draw the top circle
                            (ybox, self.right_joint, 0, self.y_joint, self.options.lid_type == 'WoodHinge')) 
                FlexBandList.append(FlexBand)
            elif back_left_radius == 0:
                #Straight corner on back left, flex band is front + right + back
                DebugMsg("\nFlex on front --> right --> back\n")
                FlexBand = ('Flex_Front_Right_Back', 0, 0,                      #Draw Front then Right and Back so first element is external and last external
                            (xbox, self.front_joint, front_right_radius, self.x_joint),       #Then Front Notch Line and round corner r= front_right_radius
                            (ybox, self.right_joint, back_right_radius, self.y_joint),        #Then Right notch line and Back/Right rounded corner
                            (xbox, self.back_joint, 0, self.x_joint))                         #Then Back notch line withount rounded corner
                FlexBandList.append(FlexBand)
            else:
                #flex band is front + right + back + left
                DebugMsg("\nFlex on front --> right --> back --> left\n")
                FlexBand = ('Flex_Front_Right_Back_Left', 0, 1,                 #Draw Front then Right, Back and left so first element is external and last internal
                            (xbox, self.front_joint, front_right_radius, self.x_joint),       #Then Front Notch Line and round corner r= front_right_radius
                            (ybox, self.right_joint, back_right_radius, self.y_joint),        #Then Right notch line and Back/Right rounded corner
                            (xbox, self.back_joint, back_left_radius, self.x_joint),          #Then Back notch line with Back/Left rounded corner
                            (ybox, self.left_joint, 0))                         #At last, Left line without rounded corner
                FlexBandList.append(FlexBand)
            
        if back_left_radius == 0 and back_right_radius == 0:
            if HasLid:
                DebugMsg("Draw back lid\n")
                LidFace = BoxFace('Lid_Back', CornerPoint((0,0), 0, 0, 0), 
                              self.x_joint, CornerPoint((xbox,0), 0, 0, 0), 
                              self.z_joint, CornerPoint((xbox,zlid), 0, 0, 0),
                              self.back_joint, CornerPoint((0,zlid), 0, 0, 0),
                              self.z_joint, self.group, [xpos, ypos])        #Draw face just right previous drawings
                if self.options.lid_type == 'WoodHinge':
                    LidFace.drawLidBackWoodHinge(True)
                else:       #This is SteelHinge or Coffin
                    LidFace.drawLidBackSteelHinge(self.HingeList, True)
                if yposface == ypos:
                    self.UpdateBoundingBox(LidFace)    #Now update bounding box, if not already done, to place back face just below
                    yposface = -self.BoundingBox[3]

            #Back is xbox * zbox, all corners are external in each direction
            DebugMsg("\nStraight face for Back\n")
            if self.options.lid_type == 'Sliding':
                #In this case, not a simple face, so we use a specific function. Also, top line is internal in y and external in x
                Face = BoxFace('Back', CornerPoint((0,0), 0, 0, 1), 
                              self.back_joint, CornerPoint((xbox,0), 0, 0, 1), 
                              self.z_joint, CornerPoint((xbox,zbox), 0, 0, 0),
                              self.x_joint, CornerPoint((0,zbox), 0, 0, 0),
                              self.z_joint, self.group, [xpos, yposface])        #Draw face just right from previous one 
                Face.drawExternalBackSlidingLid(True)
            elif self.options.lid_type == 'WoodHinge':
                #In this case, not a simple face, so we use a specific function.
                Face = BoxFace('Back', CornerPoint((0,0), 0, 0, 0), 
                              0, CornerPoint((xbox,0), 0, 0, 0),            #No joint here !
                              self.z_joint, CornerPoint((xbox,zbox), 0, 0, 0),
                              self.x_joint, CornerPoint((0,zbox), 0, 0, 0),
                              self.z_joint, self.group, [xpos, yposface])        #Draw face just right from previous one 
                Face.drawExternalBackWoodHingeLid(True)
            elif self.options.lid_type == 'SteelHinge' or self.options.lid_type == 'Coffin':
                #In this case, not a simple face, so we use a specific function.
                Face = BoxFace('Back', CornerPoint((0,0), 0, 0, 0), 
                              0, CornerPoint((xbox,0), 0, 0, 0),            #No joint here !
                              self.z_joint, CornerPoint((xbox,zbox), 0, 0, 0),
                              self.x_joint, CornerPoint((0,zbox), 0, 0, 0),
                              self.z_joint, self.group, [xpos, yposface])        #Draw face just right from previous one 
                Face.drawExternalBackSteelHingeLid(self.HingeList, True)
            else:
                Face = BoxFace('Back', CornerPoint((0,0), 0, 0, 0), 
                              self.back_joint, CornerPoint((xbox,0), 0, 0, 0), 
                              self.z_joint, CornerPoint((xbox,zbox), 0, 0, 0),
                              self.x_joint, CornerPoint((0,zbox), 0, 0, 0),
                              self.z_joint, self.group, [xpos, yposface])        #Draw face just right from previous one 
                Face.drawSimpleFace(True)
            self.UpdateBoundingBox(Face)    #Now update bounding box
            xpos = -Face.BoundingBox[2]-2
        elif back_right_radius == 0:
            #Rounded corner on Back left
            #Straight corner on Back/right, there is a flex band starting on back right
            if front_left_radius == 0:
                #Straight corner on front / left, flex band is back + left
                DebugMsg("\nFlex on back --> left\n")
                FlexBand = ('Flex_Back_Left', 0, 1,                             #Draw Back then Left so first element is external and last internal
                            (xbox, self.back_joint, back_left_radius, self.x_joint),          #Back Notch Line and round corner r= front_right_radius
                            (ybox, self.left_joint, 0, self.y_joint))                         #Then Left notch line without rounded corner
                FlexBandList.append(FlexBand)

            elif front_right_radius == 0:
                #Straight corner on bottom right, flex band is back + left + front
                DebugMsg("\nFlex on back --> left --> front\n")
                FlexBand = ('Flex_Back_Left_Front', 0, 0,                       #Draw Back then Left then Front so first element is external and last External
                            (xbox, self.back_joint, back_left_radius, self.x_joint),          #Back Notch Line and round corner r= front_right_radius
                            (ybox, self.left_joint, front_left_radius, self.y_joint),         #Then Left notch line and Front/Left rounded corner
                            (xbox, self.front_joint, 0, self.x_joint))                        #At last, Front line without rounded corner
                FlexBandList.append(FlexBand)
            else:
                #flex band is back + left + front + right
                DebugMsg("\nFlex on back --> left --> front --> right\n")
                FlexBand = ('Flex_Back_Left_Front_Right', 0, 1,                 #Draw Back then Left then Front Then Right so first element is external and last Inetrnal
                            (xbox, self.back_joint, back_left_radius, self.x_joint),          #Back Notch Line and round corner r= front_right_radius
                            (ybox, self.left_joint, front_left_radius, self.y_joint),         #Then Left notch line and Front/Left rounded corner
                            (xbox, self.front_joint, front_right_radius, self.x_joint),       #Then Front line with Front/Right rounded corner
                            (ybox, self.right_joint, 0, self.y_joint))                        #At last Right line without rounded corner
                FlexBandList.append(FlexBand)


        if back_left_radius == 0 and front_left_radius == 0:
            if HasLid:
                DebugMsg("Draw left lid\n")
                LidFace = BoxFace('Lid_Left', CornerPoint((0,0), 0, 1, 0), 
                              self.y_joint, CornerPoint((ybox,0), 0, 1, 0), 
                              self.z_joint, CornerPoint((ybox,zlid), 0, 1, 0),
                              self.left_joint, CornerPoint((0,zlid), 0, 1, 0),
                              self.z_joint, self.group, [xpos, ypos])        #Draw face just right previous drawings
                if self.options.lid_type == 'WoodHinge':
                    LidFace.drawLidSideWoodHinge(0, True)
                elif self.options.lid_type == 'SteelHinge':       #This is SteelHinge
                    LidFace.drawSimpleFace(True)
            # No round for left face
            # Left is ybox * zbox, corners are external in y but internal in x
            DebugMsg("\nStraight face for Left\n")
            if self.options.lid_type == 'Sliding' or self.options.lid_type == 'SlidingRounded' :
                delta_yposface = 2*thickness + 2
            else:
                delta_yposface = 0
            if self.options.lid_type == 'SlidingRounded':
                LeftFace = BoxFace('Left', CornerPoint((0,0), 0, 1, 0, 0), 
                              self.y_joint, CornerPoint((ybox,0), radius_lid, 1, 0), 
                              0, CornerPoint((ybox,zbox), 0, 1, 0),
                              self.y_joint, CornerPoint((0,zbox), 0, 1, 0),
                              self.z_joint, self.group, [xpos, yposface-delta_yposface])        #Draw face just right from previous drawings
            else:
                LeftFace = BoxFace('Left', CornerPoint((0,0), 0, 1, 0, self.options.lid_type == 'WoodHinge'), 
                              self.left_joint, CornerPoint((ybox,0), 0, 1, 0), 
                              self.z_joint, CornerPoint((ybox,zbox), 0, 1, 0),
                              self.y_joint, CornerPoint((0,zbox), 0, 1, 0),
                              self.z_joint, self.group, [xpos, yposface-delta_yposface])        #Draw face just right from previous drawings
            LeftFace.drawSimpleFace(True)
            self.UpdateBoundingBox(LeftFace)    #Now update bounding box
            if self.options.lid_type == 'Sliding':
                LeftFace.drawSideLineNotches(xpos, yposface)         #Left face is straight
            xpos = -LeftFace.BoundingBox[2]-2
        elif back_left_radius == 0:
            #Rounded corner on Front left
            #Straight corner on Back/left, there is a flex band starting on Back left
            if front_right_radius == 0:
                #Straight corner on Front / Right, flex band is Left + Front
                DebugMsg("\nFlex on Left --> Front\n")
                FlexBand = ('Flex_Left_Front', 1, 0,                            #Draw Left then Front so first element is internal and last external
                             #Left Notch Line and round corner r= front_left_radius, last parameter used when WoodHing to draw top circles
                            (ybox, self.left_joint, front_left_radius, self.y_joint, self.options.lid_type == 'WoodHinge'),       
                            (xbox, self.front_joint, 0, self.x_joint))                        #Then Front notch line without rounded corner
                FlexBandList.append(FlexBand)
            elif back_right_radius == 0:
                #Straight corner on Back right, flex band is Left + Back + Right
                DebugMsg("\nFlex on Left --> Front --> Right\n")
                FlexBand = ('Flex_Left_Front_Right', 1, 1,                      #Draw Left then Front and Right so first element is internal and last internal
                             #Left Notch Line and round corner r= front_left_radius, last parameter used when WoodHing to draw top circles
                            (ybox, self.left_joint, front_left_radius, self.y_joint, self.options.lid_type == 'WoodHinge'),
                            (xbox, self.front_joint, front_right_radius, self.x_joint),       #Then Front notch line with Front/Right rounded corner
                            (ybox, self.right_joint, 0, self.y_joint, self.options.lid_type == 'WoodHinge'))     #And Right notch line without rounded corner                 
                FlexBandList.append(FlexBand)
            else:
                #flex band on Left --> front --> right --> Back
                DebugMsg("\nFlex on Left --> front --> right --> Back\n")
                FlexBand = ('Flex_Left_Front_Right_Back', 1, 0,                 #Draw Left then Front, Right and Back so first element is internal and last external
                            (ybox, self.left_joint, front_left_radius, self.y_joint),         #Left Notch Line and round corner r= front_left_radius
                            (xbox, self.front_joint, front_right_radius, self.x_joint),       #Then Front notch line with Front/Right rounded corner
                            (ybox, self.right_joint, back_right_radius, self.y_joint),        #And Right notch line with Back/Right rounded corner    
                            (xbox, self.back_joint, 0, self.x_joint))
                FlexBandList.append(FlexBand)


        if back_right_radius == 0 and front_right_radius == 0:
            #Right is the same
            if HasLid:
                DebugMsg("Draw Right lid\n")
                LidFace = BoxFace('Lid_Right', CornerPoint((0,0), 0, 1, 0), 
                              self.y_joint, CornerPoint((ybox,0), 0, 1, 0), 
                              self.z_joint, CornerPoint((ybox,zlid), 0, 1, 0),
                              self.right_joint, CornerPoint((0,zlid), 0, 1, 0),
                              self.z_joint, self.group, [xpos, ypos])        #Draw face just right previous drawings
                if self.options.lid_type == 'WoodHinge':
                    LidFace.drawLidSideWoodHinge(1, True)
                elif self.options.lid_type == 'SteelHinge':       #This is SteelHinge
                    LidFace.drawSimpleFace(True)

            # Right is ybox * zbox, corners are external in y but internal in x
            DebugMsg("\nStraight face for Right\n")
            if self.options.lid_type == 'Sliding' or self.options.lid_type == 'SlidingRounded':
                delta_yposface = 2*thickness + 2
            else:
                delta_yposface = 0
            if self.options.lid_type == 'SlidingRounded':
                RightFace = BoxFace('Right', CornerPoint((0,0), radius_lid, 1, 0), 
                              self.y_joint, CornerPoint((ybox,0), 0, 1, 0), 
                              self.z_joint, CornerPoint((ybox,zbox), 0, 1, 0),
                              self.y_joint, CornerPoint((0,zbox), 0, 1, 0),
                              0, self.group, [xpos, yposface-delta_yposface])        #Draw face just right from previous drawings
            else:
                RightFace = BoxFace('Right', CornerPoint((0,0), 0, 1, 0), 
                              self.right_joint, CornerPoint((ybox,0), 0, 1, 0, self.options.lid_type == 'WoodHinge'), 
                              self.z_joint, CornerPoint((ybox,zbox), 0, 1, 0),
                              self.y_joint, CornerPoint((0,zbox), 0, 1, 0),
                              self.z_joint, self.group, [xpos, yposface-delta_yposface])        #Draw face just below previous drawings
            RightFace.drawSimpleFace(True)
            if self.options.lid_type == 'Sliding':
                RightFace.drawSideLineNotches(xpos, yposface)         #Right face is straight
            self.UpdateBoundingBox(RightFace)    #Now update bounding box
            xpos = -RightFace.BoundingBox[2]-2
        elif front_right_radius == 0:
            #Rounded corner on Back right
            #Straight corner on Front right
            if back_left_radius == 0:
                #Straight corner on top / left, flex band is Left + Back
                DebugMsg("\nFlex on Right --> Back\n")
                FlexBand = ( 'Flex_Right_Back', 1, 0,                           #Draw Right then Back so first element is internal and last external
                            (ybox, self.right_joint, back_right_radius, self.y_joint),       #Left Notch Line and round corner r= back_right_radius
                            (xbox, self.back_joint, 0, self.x_joint))                        #Then Back notch line without rounded corner
                FlexBandList.append(FlexBand)
            elif front_left_radius == 0:
                #Straight corner on Front left, flex band is Right --> Back --> Left
                DebugMsg("\nFlex on Right --> Back --> Left\n")
                FlexBand = ('Flex_Right_Back_Left', 1, 1,                       #Draw Right then Back and left so first element is internal and last internal
                            (ybox, self.right_joint, back_right_radius, self.y_joint),        #Left Notch Line and round corner r= back_right_radius
                            (xbox, self.back_joint, back_left_radius, self.x_joint),          #Then Back notch line with Back/Left rounded corner
                            (ybox, self.left_joint, 0, self.y_joint))                         #And left Notch line without rounded corner
                FlexBandList.append(FlexBand)
            else:
                #flex band on Left --> front --> right --> Back --> Front
                DebugMsg("\nFlex on Right --> Back --> Left --> Front\n")
                FlexBand = ('Flex_Right_Back_Left_Front', 1, 1,                 #Draw Right then Back and left so first element is internal and last internal
                            (ybox, self.right_joint, back_right_radius, self.y_joint),        #Left Notch Line and round corner r= back_right_radius
                            (xbox, self.back_joint, back_left_radius, self.x_joint),          #Then Back notch line with Back/Left rounded corner
                            (ybox, self.left_joint, front_left_radius, self.y_joint),         #Then left Notch line with Front/Left rounded corner
                            (xbox, self.front_joint, 0, self.x_joint))                        #And Front notch line without rounded corner
                FlexBandList.append(FlexBand)

        if front_right_radius > 0 and back_right_radius > 0 and back_left_radius > 0 and front_left_radius > 0:
            #Specific case, all corners are rounded
            DebugMsg("\n\nFlex on all faces\n")
            FlexBand = ('Flex_All', 1, 1,                                   #Draw flex all around the box with clips
                        (xbox, self.back_joint, back_right_radius, self.x_joint),         #(Half) Back Notch Line and round corner r= back_right_radius
                        (ybox, self.right_joint, front_right_radius, self.y_joint),       #Then Right notch line with Front/Right rounded corner
                        (xbox, self.front_joint, front_left_radius, self.x_joint),        #Then front notch line with Front/Left rounded corner
                        (ybox, self.left_joint, back_left_radius, self.y_joint),          #Then Laft notch line with Back/Left rounded corner
                        (xbox, self.back_joint, back_right_radius, self.x_joint))         #And another back line, (half)
            Face = FlexFace(FlexBand, 0, zbox, self.z_joint, self.group, [xpos, ypos])
            Face.drawRoundedFlexFace(True)
            self.UpdateBoundingBox(Face)    #Now update bounding box
        else:
            for FlexBand in FlexBandList:
                if HasLid:
                    FaceLid = FlexFace(FlexBand, 1, zlid, self.z_joint, self.group, [xpos, ypos])
                    FaceLid.drawFlexFace(True)
                    if yposface == ypos:
                        yposface = ypos - FaceLid.BoundingBox[3] - 2
                Face = FlexFace(FlexBand, 0, zbox, self.z_joint, self.group, [xpos, yposface])
                Face.drawFlexFace(True)
                xpos -= Face.BoundingBox[2] + 2

        #if sliding top, generate specific elements to let the lid slide
        if self.options.lid_type == 'Sliding':
            if len(FlexBandList) > 0:
                #Case with flex 
                #This code works because with sliding top, there is AT MOST one flex band.
                Face.drawSideLineNotches()
        self.UpdateBoundingBox(Face)    #Now update bounding box
        
        ypos = -self.BoundingBox[3]
        xpos = 0.0

        # If coffin draw the lid here
        if self.options.lid_type == 'Coffin':
            self.drawCoffinSide('Left', ybox, zlid+thickness, z_dome_lid, xpos, ypos, self.group)
            xpos -= ybox + 2*thickness + 2
            self.drawCoffinSide('Right', ybox, zlid+thickness, z_dome_lid, xpos, ypos, self.group)
            xpos -= ybox + 2*thickness + 2
            self.drawCoffinTop(xbox, ybox, zlid+thickness, z_dome_lid, xpos, ypos, self.group)

        ypos = -self.BoundingBox[3]
        xpos = 0.0
        # Then draw internal walls
        # First Back and front
        # Rectangle with joints on sides, not on top and bottom
        # 
        if self.InternalWalls_FB:
            DebugMsg("\nDrawing Internal Back\n")
            if self.InternalWalls_LR:
                left_joint = self.z_joint
            else:
                left_joint = 0          #Only draw joints if there is a left side !                
            #If rounded corner, shorten size by radius, if not by thickness
            if back_left_radius > 0:
                left_joint = 0
                d1 = back_left_radius
            else:
                d1 = thickness
            if self.InternalWalls_LR:
                right_joint = self.z_joint
            else:
                right_joint = 0          #Only draw joints if there is a right side !                
            #If rounded corner, shorten size by radius, if not by thickness
            if back_right_radius > 0:
                right_joint = 0
                d2 = back_right_radius
            else:
                d2 = thickness

            InternalBack = BoxFace('Int_Back', CornerPoint((0,0), 0, 0, 1),         #First corner, external on X, internal on Y sides 
                              0, CornerPoint((xbox-d1-d2,0), 0, 0, 1), 
                              right_joint, CornerPoint((xbox-d1-d2, zbox_internal_walls), 0, 0, 1),
                              0, CornerPoint((0,zbox_internal_walls), 0, 0, 1),
                              left_joint, self.group, [xpos, ypos])        #Draw face just below previous drawings
            if self.options.lid_type == 'SteelHinge' or self.options.lid_type == 'Coffin':
                #Special case, should cut some spce for the hinge in the back, so add the last parameter
                InternalBack.drawFaceWithHoles(self.n_slot_x, self.x_slot_size, d1 - thickness, self.z_joint, self.options.h_slot, True, self.HingeList)
            else:
                InternalBack.drawFaceWithHoles(self.n_slot_x, self.x_slot_size, d1 - thickness, self.z_joint, self.options.h_slot, True)
            xpos = -InternalBack.BoundingBox[2]-2


            if self.InternalWalls_LR:
                left_joint = self.z_joint
            else:
                left_joint = 0          #Only draw joints if there is a left side !                
            if front_left_radius > 0:
                left_joint = 0
                d1 = front_left_radius
            else:
                d1 = thickness
            if self.InternalWalls_LR:
                right_joint = self.z_joint
            else:
                right_joint = 0          #Only draw joints if there is a right side !                
            if front_right_radius > 0:
                right_joint = 0
                d2 = front_right_radius
            else:
                d2 = thickness
            DebugMsg("\nDrawing Internal Front\n")
            InternalFront = BoxFace('Int_Front', CornerPoint((0,0), 0, 0, 1),         #First corner, external on X, internal on Y sides 
                              0, CornerPoint((xbox-d1-d2,0), 0, 0, 1), 
                              right_joint, CornerPoint((xbox-d1-d2, zbox_internal_walls), 0, 0, 1),
                              0, CornerPoint((0,zbox_internal_walls), 0, 0, 1),
                              left_joint, self.group, [xpos, ypos])        #Draw face just below previous drawings
            InternalFront.drawFaceWithHoles(self.n_slot_x, self.x_slot_size, d1 - thickness, self.z_joint, self.options.h_slot, True)
            xpos = -InternalFront.BoundingBox[2]-2

        # Then Left and right internal walls if needed.
        if self.InternalWalls_LR:
            DebugMsg("\nDrawing Internal Left\n")
            if self.InternalWalls_FB:
                left_joint = self.z_joint
            else:
                left_joint = 0          #Only draw joints if there is a left side !                
            if back_left_radius > 0:
                left_joint = 0
                d1 = back_left_radius
            else:
                d1 = thickness
            if self.InternalWalls_FB:
                right_joint = self.z_joint
            else:
                right_joint = 0          #Only draw joints if there is a right side !                
            if front_left_radius > 0:
                right_joint = 0
                d2 = front_left_radius
            else:
                d2 = thickness
            if self.options.lid_type == 'SlidingRounded':
                InternalLeft = BoxFace('Int_Left', CornerPoint((0,0), self.radius_back_lid, 1, 0),         #First corner, internal x, external y
                                  0, CornerPoint((ybox,0), radius_lid, 1, 0), 
                                  0, CornerPoint((ybox, zbox), 0, 1, 1),      #internal both directions
                                  0, CornerPoint((0,zbox), 0, 1, 1),
                                  self.z_joint, self.group, [xpos, ypos])         #Draw face just below previous drawings
                InternalLeft.drawFaceInternalSlidingLeft(True)                   #Left side
            else:
                InternalLeft = BoxFace('Int_Left', CornerPoint((0,0), 0, 1, 1),         #First corner, internal on both sides 
                                  0, CornerPoint((ybox-d1-d2,0), 0, 1, 1), 
                                  right_joint, CornerPoint((ybox-d1-d2, zbox_internal_walls), 0, 1, 1),
                                  0, CornerPoint((0,zbox_internal_walls), 0, 1, 1),
                                  left_joint, self.group, [xpos, ypos])        #Draw face just below previous drawings
                InternalLeft.drawFaceWithHoles(self.n_slot_y, self.y_slot_size, d1 - thickness, self.z_joint, self.options.h_slot, True)
            xpos = -InternalLeft.BoundingBox[2]-2


            if self.InternalWalls_FB:
                left_joint = self.z_joint
            else:
                left_joint = 0          #Only draw joints if there is a left side !                
            if front_right_radius > 0:
                left_joint = 0
                d1 = front_right_radius
            else:
                d1 = thickness
            if self.InternalWalls_FB:
                right_joint = self.z_joint
            else:
                right_joint = 0          #Only draw joints if there is a right side !                
            if back_right_radius > 0:
                right_joint = 0
                d2 = back_right_radius
            else:
                d2 = thickness
            DebugMsg("\nDrawing Internal Right\n")
            if self.options.lid_type == 'SlidingRounded':
                InternalRight = BoxFace('Int_Right', CornerPoint((0,0), radius_lid, 1, 0),         #First corner, internal x, external y
                                  0, CornerPoint((ybox,0), self.radius_back_lid, 1, 0), 
                                  self.z_joint, CornerPoint((ybox, zbox), 0, 1, 1),      #internal both directions
                                  0, CornerPoint((0,zbox), 0, 1, 1),
                                  0, self.group, [xpos, ypos])         #Draw face just below previous drawings
                InternalRight.drawFaceInternalSlidingRight(True)                   #Right side
            else:
                InternalRight = BoxFace('Int_Right', CornerPoint((0,0), 0, 1, 1),         #First corner, internal on both sides 
                              0, CornerPoint((ybox-d1-d2,0), 0, 1, 1), 
                              right_joint, CornerPoint((ybox-d1-d2, zbox_internal_walls), 0, 1, 1),
                              0, CornerPoint((0,zbox_internal_walls), 0, 1, 1),
                              left_joint, self.group, [xpos, ypos])        #Draw face just below previous drawings
                InternalRight.drawFaceWithHoles(self.n_slot_y, self.y_slot_size, d1 - thickness, self.z_joint, self.options.h_slot, True)

            xpos = -InternalRight.BoundingBox[2]-2
            self.UpdateBoundingBox(InternalRight)    #Now update bounding box
        elif self.InternalWalls_FB:
            #Udate bounding box with front and back value
            self.UpdateBoundingBox(InternalFront)    #Now update bounding box
        
        if self.options.lid_type == 'SlidingRounded':
            #Draw the internal wall at the back used to "protect" the sliding lid inside the box
            InternalProtection = BoxFace('Int_Back', CornerPoint((0,0), 0, 1, 1),         #First corner, internal x, internal y
                                  0, CornerPoint((xbox-2*thickness,0), 0, 1, 1), 
                                  self.z_joint, CornerPoint((xbox-2*thickness, zbox-self.radius_back_lid-thickness), 0, 1, 1),      #internal both directions
                                  0, CornerPoint((0,zbox-self.radius_back_lid-thickness), 0, 1, 1),
                                  self.z_joint, self.group, [xpos, ypos])         #Draw face just below previous drawings
            InternalProtection.drawSimpleFace(True)
            self.UpdateBoundingBox(InternalProtection)    #Now update bounding box
            ypos = -self.BoundingBox[3]
            xpos = 0.0
            #And draw the sliding lid
            self.drawRoundedSlidindLid(xbox-SlidingLidSpaceX, self.length_sliding_rounded, xpos, ypos, self.group)
            
        #Then internal walls
        #Columns first
        xpos = 0
        ypos = -self.BoundingBox[3]

        for i in range(self.n_slot_x-1):
            self.drawColumWall(i, self.n_slot_y, self.y_slot_size, self.ListNotchColumns, ybox-2*thickness, zbox_internal_walls, self.options.h_slot, xpos, ypos, self.group) 
            xpos -= ybox + 2                  #Next position for drawing

        #Then rows, nearly the same, but opening at the bottom edge        
        
        xpos = 0
        ypos -= zbox_internal_walls + thickness + 2
        for i in range(self.n_slot_y-1):
            self.drawRowWall(i, self.n_slot_x, self.x_slot_size, self.ListNotchRows, xbox-2*thickness, zbox_internal_walls, self.options.h_slot, xpos, ypos, self.group) 
            xpos -= xbox + 2                  #Next position for drawing
        
        #
        if self.options.lid_type == 'SteelHinge' or self.options.lid_type == 'Coffin':
            #the elements of the hinge
            HingeNum = 0
            ypos = -self.BoundingBox[3] - 2
            xpos = -2
            for Hinge in self.HingeList:
                for i in range(5):
                    self.drawSteelHingeElement(HingeNum*5+i, thickness, xpos, ypos, self.group)
                    xpos -= 3.5*thickness + 2
                HingeNum += 1
                xpos -= 3


        CloseDebugFile()


# Create effect instance and apply it.
effect = GenericBox().run()

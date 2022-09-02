#!/usr/bin/env python3
#
# shirt_waist_allington.py
# Inkscape extension-Effects-Sewing Patterns-Shirt Waist Allington
# Copyright (C) 2010, 2011, 2012 Susan Spencer, Steve Conklin <www.taumeta.org>

'''
Licensing paragraph:

1. CODE LICENSE: GPL 2.0+
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
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

2. PATTERN LICENSE: CC BY-NC 3.0
The output of this code is a pattern and is considered a
visual artwork. The pattern is licensed under
Attribution-NonCommercial 3.0 (CC BY-NC 3.0)
<http://creativecommons.org/licenses/by-nc/3.0/>
Items made from the pattern may be sold;
the pattern may not be sold.

End of Licensing paragraph.
'''

import math, inkex
from sewing_patterns import *

class ShirtWaist(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--m_unit', default = 'Inches', help = 'Centimeters or Inches?')
        pars.add_argument('--m_front_waist_length', type = float, default = '15.0', help = 'Front Waist Length')
        pars.add_argument('--m_back_waist_length', type = float, default = '15.5', help = 'Back Waist Length')
        pars.add_argument('--m_neck_circumference', type = float, default = '13.5', help = 'Neck Circumference')
        pars.add_argument('--m_bust_circumference', type = float, default = '39.0', help = 'Bust Circumference')
        pars.add_argument('--m_waist_circumference', type = float, default = '25.0', help = 'Waist Circumference')
        pars.add_argument('--m_armscye_circumference', type = float, default = '15.0', help = 'Armscye circumference')
        pars.add_argument('--m_across_back', type = float, default = '13.5', help = 'Across Back')
        pars.add_argument('--m_shoulder', type = float, default = '6.5', help = 'Shoulder')
        pars.add_argument('--m_side', type = float, default = '7.75', help = 'Side')
        pars.add_argument('--m_upper_front_height', type = float, default = '10.75', help = 'Upper Front Height')
        pars.add_argument('--m_overarm_length', type = float, default = '20.00', help = 'Overarm Length')
        pars.add_argument('--m_elbow_height', type = float, default = '9.50', help = 'Elbow Height - from wrist to elbow')
        pars.add_argument('--m_elbow_circumference', type = float, default = '12.50', help = 'Elbow Circumference - arm bent')
        pars.add_argument('--m_hand_circumference', type = float, default = '8.00', help = 'Hand Circumference')

    def effect(self):

        def printPoint(pnt):
            debug('  %s  =  %f,  %f')%pnt.id, pnt.x, pnt.y

        INCH_to_PX = 96.0 #inkscape 1.0 uses 96 pixels per 1 inch
        CM_to_INCH = 1/2.54
        CM_to_PX = CM_to_INCH*INCH_to_PX
        CM = CM_to_PX # CM - shorthand when using centimeters
        IN = INCH_to_PX # IN - shorthand when using inches

        #all measurements must be converted to px
        munit = self.options.m_unit
        if munit == 'Centimeters':
            MEASUREMENT_CONVERSION = CM
        else:
            MEASUREMENT_CONVERSION = IN

        #convert measurements
        front_waist_length = self.options.m_front_waist_length * MEASUREMENT_CONVERSION
        neck_circumference = self.options.m_neck_circumference * MEASUREMENT_CONVERSION
        bust_circumference = self.options.m_bust_circumference * MEASUREMENT_CONVERSION
        waist_circumference = self.options.m_waist_circumference * MEASUREMENT_CONVERSION
        armscye_circumference = self.options.m_armscye_circumference * MEASUREMENT_CONVERSION
        across_back = self.options.m_across_back * MEASUREMENT_CONVERSION
        shoulder = self.options.m_shoulder * MEASUREMENT_CONVERSION
        side = self.options.m_side * MEASUREMENT_CONVERSION
        upper_front_height = self.options.m_upper_front_height * MEASUREMENT_CONVERSION
        overarm_length = self.options.m_overarm_length * MEASUREMENT_CONVERSION
        elbow_height = self.options.m_elbow_height * MEASUREMENT_CONVERSION
        elbow_circumference = self.options.m_elbow_circumference * MEASUREMENT_CONVERSION
        hand_circumference = self.options.m_hand_circumference * MEASUREMENT_CONVERSION

        #constants
        ANGLE90 = angleOfDegree(90)
        ANGLE180 = angleOfDegree(180)
        SEAM_ALLOWANCE = (5/8.0)*IN
        BORDER = 1*IN
        NOTE_HEIGHT = 1*IN

        #get the document,  set initial width & height
        doc = self.document.getroot() # self.document is the canvas seen in Inkscape
        #add defs group with markers to document
        addDefs(doc)

        #width_orig  = inkex.unittouu(doc.get('width'))
        #height_orig  = inkex.unittouu(doc.get('height'))
        #doc_width = 4*BORDER+4*SEAM_ALLOWANCE + bust_circumference/2.0
        #doc_height = 2*BORDER+3*SEAM_ALLOWANCE+(upper_front_height+side)
        #doc.set('width', str(doc_width)) #temporary document width,  doc is resized near end of pattern file
        #doc.set('height', str(doc_height)) #temporary document height,  doc is resized near end of pattern file


        #create a base group in the document to hold all patterns
        pattern_base = base(doc, 'pattern_base')
        #create a pattern group for each pattern,  put pattern group in base group - there can be multiple patterns
        bodice = pattern(pattern_base, 'bodice')
        # create a group for each pattern piece,  put pattern piece group in pattern group
        A  =  patternPiece(bodice, 'A', 'bodice_front', fabric = 2, interfacing = 0, lining = 0)
        B  =  patternPiece(bodice, 'B', 'bodice_back', fabric = 2, interfacing = 0, lining = 0)
        C  =  patternPiece(bodice, 'C', 'bodice_sleeve', fabric = 2, interfacing = 0, lining = 0)
        D  =  patternPiece(bodice, 'D', 'bodice_cuff', fabric = 2, interfacing = 0, lining = 0)

        #pattern notes
        notes = []
        notes.append('Define Seam Allowances: Select File/Inkscape Preferences/Steps and set Outset to 56.25px (5/8" seam allowance)')
        notes.append('Create Seam Allowances: Press CTRL-F,  type "cuttingline" in the ID field,  click the Find button,  press CTRL-)')
        notes.append('Remove Points & Gridlines: Press CTRL-F,  type "reference" in the Attribute field,  click Find button,  press DELETE')
        notes.append('Print: Save as a PDF file,  open PDF with PDF viewer (Adobe,  Evince,  Okular,  xPDF),  print from Print Preview option')

        #pattern points
        b1 = patternPointXY(B, 'b1', 0, 0) #B
        b2 = patternPoint(B, 'b2', down(b1,  front_waist_length)) #A
        b3 = patternPoint(B, 'b3', up(b2,  side)) #C
        a1 = patternPoint(A, 'a1', left(b3,  bust_circumference/2.0)) #D
        b4 = patternPoint(B, 'b4', left(b3, across_back/2.0)) #E
        b5 = patternPoint(B, 'b5', up(b4, armscye_circumference/3.0)) #F
        b6 = patternPoint(B, 'b6', up(b1,  0.5*IN)) #G
        b7 = patternPoint(B, 'b7', left(b6, 1.5*IN)) #H
        b8 = patternPoint(B, 'b8',  onLineAtLength(b5, b7,  -0.5*IN)) #I
        a2 = patternPoint(A, 'a2', left(b4,  armscye_circumference/4.0)) #J
        a3 = patternPoint(A, 'a3', midPoint(a2, b4)) #K
        a4 = patternPoint(A, 'a4', up(a2,  2.5*IN)) #L
        a5 = patternPoint(A, 'a5', up(b5, 1.5*IN)) #M
        a6 = patternPoint(A, 'a6', left(a5, 2*IN)) #N
        a7 = patternPoint(A, 'a7', left(a6, distance(b7, b8))) #O
        a8 = patternPointXY(A, 'a8', a7.x,  b3.y - (upper_front_height - distance(b1, b7))) #P
        a9 = patternPoint(A, 'a9', down(a8,  neck_circumference/4.0)) #Q
        a10 = patternPoint(A, 'a10', up(a9,  0.5*IN)) #R
        a11 = patternPoint(A, 'a11', left(a10,  (neck_circumference/6.0)+0.25*IN )) #S
        b9 = patternPoint(B, 'b9', midPoint(a3, b4)) #T on back bodice B
        a12 = patternPoint(A, 'a12', b9) #T on front bodice A
        b10 = patternPoint(B, 'b10', down(b9, side)) #U
        b11 = patternPoint(B , 'b11', right(b10, 1*IN)) #V
        a13 = patternPoint(A, 'a13', left(b10, 1*IN)) #W
        a14 = patternPoint(A, 'a14',  onLineAtLength(a11,  a1,  front_waist_length)) #X
        a15 = patternPoint(A, 'a15', down(a8, distance(a8, a14))) #Y - new point at front waist
        b12 = patternPoint(B, 'b12', up(b4, distance(b5,  b4)/3.0)) #Z - new point at back armscye
        #temporary armscye curve from a3 to b12 to find top point of side seam
        length = distance(a3, b12)/3.0
        temp_b12_c1 = right(a3, length) #don't create an svg controlpoint circle for this point
        temp_b12_c2 = down(b12, length) #or for this point
        #find top point of side seam with intersection of side and armscye curve,  save to two points a16 and b13
        curve1 = pointList(a3, temp_b12_c1, temp_b12_c2, b12)
        intersections  =  intersectLineCurve(b10,  b9,  curve1) #this line is directional from b10 to b9
        b13 = patternPoint(B, 'b13', intersections[0]) # AA on bodice back B -use 1st intersection found,  in this case there's only one intersection
        a16 = patternPoint(A, 'a16', b13) #AA on bodice back A

        #front control points - path runs counterclockwise from front neck center a11
        #front neck control points from a8 to a11
        length = distance(a8, a11)/3.0
        a11.c2 = controlPoint(A, 'a11.c2', right(a11, 1.5*length))
        a11.c1 = controlPoint(A, 'a11.c1', polar(a8, length, angleOfLine(a8, a11.c2)))
        #front waist control points from a14 to a15
        length = distance(a14, a15)/3.0
        a15.c1 = controlPoint(A, 'a15.c1', polar(a14, length, angleOfLine(a14, a11)+ANGLE90)) #control handle line is perpendicular to line a14-a11
        a15.c2 = controlPoint(A, 'a15.c2', left(a15, length))
        #front waist control points from a15 to a13
        length = distance(a15, a13)/3.0
        a13.c1 = controlPoint(A, 'a13.c1', right(a15, 1.5*length))
        a13.c2 = controlPoint(A, 'a13.c2', polar(a13, length, angleOfLine(a13, a13.c1))) #second control aimed at first control point
        #front side control points from a13 to a12
        length = distance(a13, a12)/3.0
        a12.c1 = controlPoint(A, 'a12.c1', up(a13, length))
        a12.c2 = controlPoint(A, 'a12.c2', down(a12, length))
        #front armscye control points from a16 to a3 to a4 to 16
        length1 = distance(a16, a3)/3.0
        length2 = distance(a3, a4)/3.0
        length3 = distance(a4, a6)/3.0
        angle1 = angleOfLine(a16, a3)
        angle2 = ANGLE180
        angle3 = (angle1+angle2)/2.0
        a3.c1 = controlPoint(A, 'a3.c1', polar(a16, length1, angle1))
        a3.c2 = controlPoint(A, 'a3.c2', polar(a3, length1, angle3-ANGLE180))
        a4.c1 = controlPoint(A, 'a4.c1', polar(a3, length2, angle3))
        angle4 = angleOfLine(a3, a6)
        angle5 = angleOfLine(a4, a6)
        angle6 = (angle4+angle5)/2.0
        a4.c2 = controlPoint(A, 'a4.c2', polar(a4, 1.5*length2, angle6-ANGLE180))
        a6.c1 = controlPoint(A, 'a6.c1', polar(a4, length3, angle6))
        a6.c2 = controlPoint(A, 'a6.c2', polar(a6, length3/2.0, angleOfLine(a8, a6)+ANGLE90))

        #back control points - path runs clockwise from back nape b1
        #back neck control points from b7 to b1
        length = distance(b7, b1)/3.0
        b1.c1 = controlPoint(B, 'b1.c1', down(b7, length/2.0)) #short control point handle
        b1.c2 = controlPoint(B, 'b1.c2', left(b1, length*2)) #long control point handle
        #back side control points from b11 to b9
        length = distance(b11, b9)/3.0
        b9.c1 = controlPoint(B, 'b9.c1', up(b11, length))
        b9.c2 = controlPoint(B, 'b9.c2', down(b9, length))
        #back armscye points from b13 to b12 to b8
        length1 = distance(b13, b12)/3.0
        length2 = distance(b12, b8)/3.0
        angle1 = angleOfLine(b13, b8)
        b12.c1 = controlPoint(B, 'b12.c1', polar(b13, length1, angleOfLine(a3.c1, a16)))
        b12.c2 = controlPoint(B, 'b12.c2', polar(b12, length1, angle1-ANGLE180))
        b8.c1 = controlPoint(B, 'b8.c1', polar(b12, length2, angle1))
        b8.c2 = controlPoint(B, 'b8.c2', polar(b8, length2/2.0, angleOfLine(b7, b8)-ANGLE90))

        #sleeve C
        c1 = patternPointXY(C, 'c1', 0.0, 0.0) #A
        c2 = patternPoint(C, 'c2', down(c1, overarm_length)) #B
        c3 = patternPoint(C, 'c3', up(c2, elbow_height)) #C
        c4 = patternPoint(C, 'c4', right(c2, 1*IN)) #D
        c5 = patternPoint(C, 'c5', right(c3, 0.5*IN)) #E
        c6 = patternPoint(C, 'c6', left(c1, 1*IN)) #F
        c7 = patternPoint(C, 'c7', right(c4, 1*IN)) #G
        c8 = patternPoint(C, 'c8', right(c7, hand_circumference+2*IN)) #H
        c9 = patternPoint(C, 'c9', right(c8, 1*IN)) #I
        c10 = patternPoint(C, 'c10', right(c5, 1*IN) )#J
        c11 = patternPoint(C, 'c11', right(c10, elbow_circumference)) #K
        c12 = patternPoint(C, 'c12', right(c11, 0.5*IN)) #L
        c13 = patternPoint(C, 'c13', right(c1, armscye_circumference)) #M
        c14 = patternPoint(C, 'c14', right(c13, 2*IN)) #N
        c15 = patternPoint(C, 'c15', up(c1, 2.5*IN)) #O
        c16 = patternPoint(C, 'c16', right(c1, 1.5*IN)) #P
        c17 = patternPoint(C, 'c17', left(c13, 3*IN)) #Q
        c18 = patternPointXY(C, 'c18', c16.x, c15.y) #R
        c19 = patternPointXY(C, 'c19', c17.x, c15.y) #S
        c20 = patternPoint(C, 'c20', midPoint(c16, c17)) #T
        c21 = patternPoint(C, 'c21', up(c20, distance(c20, c18))) #U - above T
        c22 = patternPoint(C, 'c22', down(midPoint(c7, c8), 0.75*IN)) #V - was U
        c23 = patternPoint(C, 'c23', right(c4, distance(c4, c8)*3/5.0)) #W
        c24 = patternPoint(C, 'c24', up(c23, distance(c4, c3)/3.0)) #X - was V
        c25 = patternPoint(C, 'c25', down(c23, 0.75*IN)) #Y - new point
        # sleeve C control points
        # sleevecap c6 to c18 to c21 to c19 to c13 to c14
        length1 = distance(c6, c18)/3.0
        length2 = distance(c18, c21)/3.0
        c21.c2 = controlPoint(C, 'c21.c2', left(c21, length2))
        c21.c1 = controlPoint(C, 'c21.c1', polar(c18, length2, angleOfLine(c18, c21.c2)))
        angle = angleOfLine(c6, c18)+angleOfVector(c18, c6, c1)/2.0
        c18.c1 = controlPoint(C, 'c18.c1', polar(c6, length1, angle))
        c18.c2 = controlPoint(C, 'c18.c2', polar(c18, length1, angleOfLine(c21.c1, c18)))
        length1 = distance(c21, c19)/3.0
        length2 = distance(c19, c13)/3.0
        length3 = distance(c13, c14)/3.0
        c19.c1 = controlPoint(C, 'c19.c1', right(c21, length1))
        c19.c2 = controlPoint(C, 'c19.c2', polar(c19, length1, angleOfLine(c19, c19.c1)))
        c13.c1 = controlPoint(C, 'c13.c1', polar(c19, length2, angleOfLine(c19.c2, c19)))
        angle1 = angleOfLine(c13.c1, c13)/2.0
        c13.c2 = controlPoint(C, 'c13.c2', polar(c13, length2, angle1+ANGLE180))
        c14.c1 = controlPoint(C, 'c14.c1', polar(c13, length3, angle1))
        c14.c2 = controlPoint(C, 'c14.c2', polar(c14, length3, angleOfLine(c18.c1, c6)))
        # c14 to c12
        length = distance(c14, c12)/3.0
        c12.c2 = controlPoint(C, 'c12.c2', polar(c12, length, angleOfLine(c9, c12)))
        c12.c1 = controlPoint(C, 'c12.c1', polar(c14, length, angleOfLine(c14, c12.c2)))
        # c9 to c25
        length = distance(c9, c25)/3.0
        c25.c2 = controlPoint(C, 'c25.c2', right(c25, length))
        c25.c1 = controlPoint(C, 'c25.c1', polar(c9, length, angleOfLine(c9, c25.c2)))
        #c22 to c4
        length = distance(c22, c4)/3.0
        c4.c1 = controlPoint(C, 'c4.c1', left(c22, length))
        c4.c2 = controlPoint(C, 'c4.c2', polar(c4, length, angleOfLine(c4, c4.c1)))
        #c5 to c6
        length = distance(c5, c6)/3.0
        c6.c1 = controlPoint(C, 'c6.c1', polar(c5, length, angleOfLine(c4, c5)))
        c6.c2 = controlPoint(C, 'c6.c2', polar(c6, length, angleOfLine(c6, c6.c1)))


        #cuff D
        d1 = patternPointXY(D, 'd1', 0, 0)
        d2 = patternPoint(D, 'd2', right(d1, hand_circumference+2*IN))
        d3 = patternPoint(D, 'd3', down(d2, 3*IN))
        d4 = patternPoint(D, 'd4', up(d3, 0.75*IN))
        d5 = patternPoint(D, 'd5', left(d3, 1*IN))
        d6 = patternPoint(D, 'd6', down(d1, 3*IN))
        d7 = patternPoint(D, 'd7', right(d6, 1*IN))
        d8 = patternPoint(D, 'd8', up(d6, 0.75*IN))
        length1 = 0.7*distance(d1, d6)
        length2 = 0.75*IN
        d9 = patternPointXY(D, 'd9', d1.x+0.5*IN, d1.y+length1)
        d10 = patternPoint(D, 'd10', right(d9, length2))
        d11 = patternPointXY(D, 'd11', d2.x-0.5*IN, d2.y+length1)
        d12 = patternPoint(D, 'd12', left(d11, length2))
        #cuff D control points
        length = distance(d4, d5)/3.0
        d5.c1 = controlPoint(D, 'd5.c1', down(d4, length))
        d5.c2 = controlPoint(D, 'd5.c2', right(d5, length))
        d8.c1 = controlPoint(D, 'd8.c1', left(d7, length))
        d8.c2 = controlPoint(D, 'd8.c2', down(d8, length))

        # all points are defined, now create paths with them...
        # pattern marks, labels, grainlines, seamlines, cuttinglines, darts, etc.

        #bodice front A
        #letter
        pnt1 = Point('', a8.x, a6.c1.y)
        addText(A, 'A_letter', pnt1.x, pnt1.y, 'A', fontsize = '72')
        #label
        pnt2 = down(pnt1, 0.5*IN)
        addText(A, 'A_label', pnt2.x, pnt2.y, 'Bodice Front', fontsize = '48')
        #label
        pnt3 = down(pnt2, 0.5*IN)
        addText(A, 'A_fabric', pnt3.x, pnt3.y, 'Cut 2 of fabric', fontsize = '38')
        #grainline points
        aG1  =  down(a11,  front_waist_length/3.0)
        aG2  =  polar(aG1,  front_waist_length/2.0,  angleOfLine(a11,  a14))
        path_str = formatPath('M', aG1, 'L', aG2)
        A_grainline = addPath(A, 'A_grainline', path_str, 'grainline')
        # gridline - helpful for troubleshooting during design phase
        path_str = formatPath('M', a1, 'L', a3, 'M', a4, 'L', a2, 'M', a8, 'L', a15, 'M', a11, 'L', a10, 'M', a7, 'L', a5)
        A_gridline = addPath(A, 'A_gridline', path_str, 'gridline')
        #seamline & cuttingline
        path_str = formatPath('M', a11, 'L', a14, 'C', a15.c1, a15.c2, a15, 'C', a13.c1, a13.c2, a13, 'C', a12.c1, a12.c2, a12)
        path_str = path_str+formatPath('L', a16, 'C', a3.c1, a3.c2, a3, 'C', a4.c1, a4.c2, a4, 'C', a6.c1, a6.c2, a6, 'L', a8, 'C', a11.c1, a11.c2, a11)
        A_seamline = addPath(A, 'A_seamline', path_str, 'seamline')
        A_cuttingline = addPath(A, 'A_cuttingline', path_str, 'cuttingline')

        #bodice back B
        #letter
        pnt1 = Point('', b8.x*2/3.0, b8.c2.y)
        addText(B, 'B_letter', pnt1.x, pnt1.y, 'B', fontsize = '72') #
        #label
        pnt2 = down(pnt1, 0.5*IN)
        addText(B, 'B_name', pnt2.x, pnt2.y, 'Bodice Back', fontsize = '48')
        #label
        pnt3 = down(pnt2, 0.5*IN)
        addText(B, 'B_fabric', pnt3.x, pnt3.y, 'Cut 2 of fabric', fontsize = '38')
        #grainline points
        bG1 = down(b7, front_waist_length/3.0)
        bG2 = down(bG1, front_waist_length/2.0)
        path_str = formatPath('M', bG1, 'L', bG2)
        B_grainline = addPath(B, 'B_grainline', path_str, 'grainline')
        # gridline
        path_str = formatPath('M', b1, 'L', b2, 'M', b11, 'L', b9, 'M', b9, 'L', b10, 'M', b7, 'L', b6, 'L', b1, 'M', b11, 'L', b10)
        B_gridline = addPath(B, 'B_gridline', path_str, 'gridline')
        #seamline & cuttingline
        path_str = formatPath('M', b1, 'L', b2, 'L', b11, 'C', b9.c1, b9.c2, b9, 'L', b13, 'C', b12.c1, b12.c2, b12, 'C', b8.c1, b8.c2, b8, 'L', b7, 'C', b1.c1, b1.c2, b1)
        B_seamline = addPath(B, 'B_seamline', path_str, 'seamline')
        B_cuttingline = addPath(B, 'B_cuttingline', path_str, 'cuttingline')

        #bodice sleeve C
        #letter
        pnt1 = Point('', c19.c1.x, c12.c1.y)
        addText(C, 'C_letter', pnt1.x, pnt1.y, 'C', fontsize = '72') #
        #label
        pnt2 = down(pnt1, 0.5*IN)
        addText(C, 'C_name', pnt2.x, pnt2.y, 'Bodice Sleeve', fontsize = '48')
        #label
        pnt3 = down(pnt2, 0.5*IN)
        addText(C, 'C_fabric', pnt3.x, pnt3.y, 'Cut 2 of fabric', fontsize = '38')
        #grainline points
        cG1 = c20
        cG2 = down(cG1, overarm_length/2.0)
        path_str = formatPath('M', cG1, 'L', cG2)
        C_grainline = addPath(C, 'C_grainline', path_str, 'grainline')
        # gridline
        path_str = formatPath('M', c15, 'L', c2, 'M', c15, 'L', c19, 'M', c2, 'L', c9, 'M', c3, 'L', c12, 'M', c6, 'L', c14, 'M', c18, 'L', c16, 'M', c19, 'L', c17)
        C_gridline = addPath(C, 'C_gridline', path_str, 'gridline')
        # slashline
        path_str = formatPath('M', c24, 'L', c25)
        C_slashline = addPath(C, 'C_slashline', path_str, 'slashline')
        #seamline & cuttingline
        path_str = formatPath('M', c6, 'C', c18.c1, c18.c2, c18, 'C', c21.c1, c21.c2, c21, 'C', c19.c1, c19.c2, c19, 'C', c13.c1, c13.c2, c13, 'C', c14.c1, c14.c2, c14)
        path_str += formatPath('C', c12.c1, c12.c2, c12, 'L', c9, 'C', c25.c1, c25.c2, c25, 'L', c22, 'C', c4.c1, c4.c2, c4, 'L', c5, 'C', c6.c1, c6.c2, c6)
        C_seamline = addPath(C, 'C_seamline', path_str, 'seamline')
        C_cuttingline = addPath(C, 'C_cuttingline', path_str, 'cuttingline')

        #bodice cuff D
        #letter
        pnt1 = Point('', d7.x, d6.y/4.0)
        addText(D, 'D_letter', pnt1.x, pnt1.y, 'D', fontsize = '38') #
        #label
        pnt2 = right(pnt1, 1*IN)
        addText(D, 'C_name', pnt2.x, pnt2.y, 'Bodice Sleeve Cuff', fontsize = '30')
        #label
        pnt3 = right(pnt2, 4*IN)
        addText(D, 'C_fabric', pnt3.x, pnt3.y, 'Cut 2 of fabric', fontsize = '24')
        pnt3 = down(pnt3, 0.3*IN)
        addText(D, 'C_finterfacing', pnt3.x, pnt3.y, 'Cut 2 of interfacing', fontsize = '24')
        #grainline points
        pnt1 = midPoint(d1, d6)
        dG1 = right(pnt1, distance(d1, d2)/4.0)
        dG2 = right(dG1, distance(d1, d2)/2.0)
        path_str = formatPath('M', dG1, 'L', dG2)
        D_grainline = addPath(D, 'D_grainline', path_str, 'grainline')
        # gridline
        path_str = formatPath('M', d1, 'L', d2, 'L', d4, 'L', d5, 'L', d7, 'L', d8, 'L', d1)
        D_gridline = addPath(D, 'D_gridline', path_str, 'gridline')
        # slashline
        path_str = formatPath('M', d9, 'L', d10, 'M', d11, 'L', d12)
        D_slashline = addPath(D, 'D_slashline', path_str, 'slashline')
        #seamline & cuttingline
        path_str = formatPath('M', d1, 'L', d2, 'L', d4, 'C', d5.c1, d5.c2, d5, 'L', d7, 'C', d8.c1, d8.c2, d8, 'L', d1)
        D_seamline = addPath(D, 'D_seamline', path_str, 'seamline')
        D_cuttingline = addPath(D, 'D_cuttingline', path_str, 'cuttingline')

        #layout patterns on document in rows
        dx = BORDER+SEAM_ALLOWANCE #left border,  allow width for seam allowance
        dy = BORDER+NOTE_HEIGHT+2*SEAM_ALLOWANCE # print pattern under the note header,  allow height for seam allowance plus extra space
        pattern_buffer = 3*SEAM_ALLOWANCE #between any two patterns need 2 seam allowances plus additional space
        # first row
        pattern_offset = dx
        row_offset = dy
        #layout bodice front A
        adx = pattern_offset-a14.x #left border offset dx,  translate leftmost A point a14 to this offset
        ady = row_offset-a8.y #upper height offset dy,  translate highest A point a8
        A.set('transform', 'translate('+str(adx)+' '+str(ady)+')')
        pattern_offset = adx+a12.x+pattern_buffer
        #layout bodice front B
        bdx = pattern_offset-b9.x #translate leftmost B point
        bdy = row_offset-b6.y #translate highest B point
        B.set('transform', 'translate('+str(bdx)+' '+str(bdy)+')')

        #2nd row
        pattern_offset = dx
        row_offset = ady+a15.y+pattern_offset # row_offset + lowest point from previous row,  plus pattern_offset
        #layout sleeve C
        cdx = pattern_offset-c6.x
        cdy = row_offset-c21.y
        C.set('transform', 'translate('+str(cdx)+' '+str(cdy)+')')
        pattern_offset = cdx+c14.x+pattern_buffer
        #layout cuff D
        ddx = pattern_offset-d1.x
        ddy = row_offset-d1.y
        D.set('transform', 'translate('+str(ddx)+' '+str(ddy)+')')
        #3rd row,  use this to calculate document height
        row_offset = cdy+c25.y

        #resize document to fit pattern piece layout
        width = ddx+d2.x # use pattern piece that appears farthest to the right in Inkscape canvas
        doc_width = width+2*SEAM_ALLOWANCE+2*BORDER
        doc_height = row_offset+SEAM_ALLOWANCE+BORDER
        root = self.svg.getElement('//svg:svg');
        root.set('viewBox', '%f %f %f %f' % (0,0,doc_width,doc_height))
        root.set('width', str(doc_width))
        root.set('height', str(doc_height))
        
        #Place notes on document after pattern pieces are transformed so that notes are centered on correct width
        x = doc_width/2.0
        y = BORDER
        i = 0
        for item in notes:
            addText(bodice, 'note'+str(i), x, y, item, fontsize = '28', textalign = 'center', textanchor = 'middle', reference = 'false')
            y = y+0.33*IN

if __name__ == '__main__':
    ShirtWaist().run()
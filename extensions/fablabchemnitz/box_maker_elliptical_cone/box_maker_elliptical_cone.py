#!/usr/bin/env python3
import inkex
import math
import numpy as np
from lxml import etree

sizeTab = 10000 #Any value greater than 1000 should give goo results

objStyle = str(inkex.Style(
    {'stroke': '#000000',
    'stroke-width': 0.1,
    'fill': 'none'
    }))


objStyleStart = str(inkex.Style(
    {'stroke': '#FF0000',
    'stroke-width': 0.1,
    'fill': 'none'
    }))

def lengthCurve(Xarray, Yarray, npoints):
    '''
    Give length of a path between point of a curve
    Beware, go from 0 to Index included, so the arrays should have at least npoints+1 elements 
    '''
    x = Xarray[0]
    y = Yarray[0]
    Length = 0.0
    i = 1
    while i <= npoints:
        Length += math.hypot((Xarray[i] - x), (Yarray[i] - y))
        x = Xarray[i]
        y = Yarray[i]
        i += 1
    return Length

class inkcape_polar:
    def __init__(self, Offset, group):
        self.offsetX = Offset[0]
        self.offsetY = Offset[1]
        self.Path = ''
        self.group = group
    
    def MoveTo(self, r, angle):
    #Return string for moving to point given as parameter, with polar coordinates radius, angle
        self.Path += ' M ' + str(round(r*math.cos(angle)-self.offsetX, 3)) + ',' + str(round(r*math.sin(angle)-self.offsetY, 3))

    def MoveTo_cartesian(self, pt):
    #Return string for moving to point given as parameter
        self.Path += ' M ' + str(round(pt[0]-self.offsetX, 3)) + ',' + str(round(pt[1]-self.offsetY, 3))


    def LineTo_cartesian(self, pt):
    #Return string for moving to point given as parameter
        self.Path += ' L ' + str(round(pt[0]-self.offsetX, 3)) + ',' + str(round(pt[1]-self.offsetY, 3))

    def LineTo(self, r, angle):
    #Retourne chaine de caractères donnant la position du point avec des coordonnées polaires
        self.Path += ' L ' + str(round(r*math.cos(angle)-self.offsetX, 3)) + ',' + str(round(r*math.sin(angle)-self.offsetY, 3))

    def Line(self, r1, angle1, r2, angle2):
    #Retourne chaine de caractères donnant la position du point avec des coordonnées polaires
        self.Path += ' M ' + str(round(r1*math.cos(angle1)-self.offsetX, 3)) + ',' + str(round(r1*math.sin(angle1)-self.offsetY, 3)) + ' L ' + str(round(r2*math.cos(angle2)-self.offsetX, 3)) + ',' + str(round(r2*math.sin(angle2)-self.offsetY, 3))
    
    def GenPath(self):
        line_attribs = {'style': objStyle, 'd': self.Path}
        etree.SubElement(self.group, inkex.addNS('path', 'svg'), line_attribs)

class BoxMakerEllipticalCone(inkex.EffectExtension):
    """
    Creates a new layer with the drawings for a parametrically generaded box.
    """
    def __init__(self):
        inkex.Effect.__init__(self)
        self.knownUnits = ['in', 'pt', 'px', 'mm', 'cm', 'm', 'km', 'pc', 'yd', 'ft']
        self.arg_parser.add_argument('--unit', default = 'mm', help = 'Unit, should be one of ')
        self.arg_parser.add_argument('--thickness', type = float, default = '3.0', help = 'Material thickness')
        self.arg_parser.add_argument('--d1', type = float, default = '50.0', help = 'Small ellipse diameter')
        self.arg_parser.add_argument('--d2', type = float, default = '100.0', help = 'Large ellipse diameter')
        self.arg_parser.add_argument('--eccentricity', type = float, default = '1.0', help = 'Ratio minor vs major axis, should be less than 1')
        self.arg_parser.add_argument('--zc', type = float, default = '50.0', help = 'Cone height')
        self.arg_parser.add_argument('--notch_interval', type = int, default = '2', help = 'Interval between notches, should be even')
        self.arg_parser.add_argument('--cut_position', type = int, default = '0', help = 'Cut position angle')
        self.arg_parser.add_argument('--inner_size', type = inkex.Boolean, default = 'true', help = 'Dimensions are internal')
        self.arg_parser.add_argument('--Mode_Debug', type = inkex.Boolean, default = 'false', help = 'Output Debug information in file')

        # Create list of points for the ellipse, will be filled later
        self.xEllipse = np.zeros(sizeTab+1)     #X coordiantes
        self.yEllipse = np.zeros(sizeTab+1)     # Y coordinates
        self.lEllipse = np.zeros(sizeTab+1)     # Length of curve until this point

        def unittouu(self, unit):
            return inkex.unittouu(unit)

    def DebugMsg(self, s):
        if self.fDebug:
            self.fDebug.write(s)

    def length2Angle(self, StartIdx, Position):
        ''' 
        Return the first index which is near the requested position.
        Start search at StartIdx to optimize computation
        '''
        while Position > self.lEllipse[StartIdx]:
            StartIdx += 1
            if StartIdx >= sizeTab:
                return sizeTab
        # Now return value between StartIdx and StartIdx - 1 which is nearer
        if StartIdx == 0:
            return 0
        if abs(Position - self.lEllipse[StartIdx]) > abs(Position - self.lEllipse[StartIdx-1]):
            return StartIdx - 1
        return StartIdx
    
    def ellipse_ext(self, a, b, alpha, e):
        '''
        Compute the point which is on line orthogonal to ellipse (a, b) and angle alpha and on the ellipse of parameters ( a+e, b+e)
        As equations are quite complex, use an approximation method
        '''
        Slope = math.atan2(b*math.cos(alpha), -a*math.sin(alpha))        #Ellipse slope in point at angle alpha
        Ortho = Slope - math.pi/2                                   # Use -pi/2 because e positive means second ellipse larger
        ''' The point is on the line x = a*cos(alpha) + L*cos(Ortho), y= b*sin(alpha) + L*sin(Ortho)
            We have to determine L
            For this, change L and compare with equation of larger ellipse
            Start with L = e
            Result should lie between L/2 and 2L
        '''
        #self.DebugMsg("Enter ellipse_ext"+str((a,b,alpha,e))+"  Slope="+str(Slope*180/math.pi)+"  Ortho="+str(Ortho*180/math.pi)+'\n')
        L = e
        step = e
        ntry = 1
        x = a*math.cos(alpha) + L*math.cos(Ortho)
        y = b*math.sin(alpha) + L*math.sin(Ortho)
        # Compute difference which the error between this point and the large ellipse
        distance =  (x*x)/((a+e)*(a+e)) + (y*y)/((b+e)*(b+e)) - 1
        #self.DebugMsg("ellipse_ext First try with L=e pt="+str((x,y))+"  distance="+str(distance)+'\n')
        while abs(distance) > 0.001 and step >0.001:
            if distance > 0:
                #L is too large, decrease by step/2 
                step /= 2
                L -= step
            else:
                #L is not large enough, increase by step/2 
                step /= 2
                L += step
            ntry += 1
            x = a*math.cos(alpha) + L*math.cos(Ortho)
            y = b*math.sin(alpha) + L*math.sin(Ortho)
            # Compute difference which the error between this point and the large ellipse
            distance =  (x*x)/((a+e)*(a+e)) + (y*y)/((b+e)*(b+e)) - 1
            #self.DebugMsg(" try "+str(ntry)+" with L="+str(L)+" pt="+str((x,y))+"  distance="+str(distance)+'\n')
        if distance > 0.001:
            self.DebugMsg("Problem, solution do not converge. Error is "+str(distance)+" after "+str(ntry)+" tries\n")
            return(x, y)
        #self.DebugMsg("Solution converge after "+str(ntry)+" tries. Error is "+str(distance)+"\n")
        return(x, y)

    def Coordinates_Step_SubStep(self, step, substep):
        '''
        Return the radius and angle on resulting curve for step i, substep j
        '''
        if step == self.num_notches:
            # Specific case for last notch on curve
            if substep == 0:            #Last position on curve
                return (self.ResultingCurve_R[sizeTab], self.ResultingCurve_Theta[sizeTab])
            else:
                AngleEllipse = self.Notches_Angle_ellipse[self.Offset_Notch][1] - self.Offset_Ellipse #To match first step
                if AngleEllipse < 0:
                    AngleEllipse += sizeTab
                return(self.ResultingCurve_R[AngleEllipse], self.ResultingCurve_Theta[AngleEllipse]+self.ResultingCurve_Theta[sizeTab]) 
        new_step = step + self.Offset_Notch
        if new_step >= self.num_notches:
            new_step -= self.num_notches
        AngleEllipse = self.Notches_Angle_ellipse[new_step][substep] - self.Offset_Ellipse
        if AngleEllipse < 0:
            AngleEllipse += sizeTab
        if substep == 0 or step == 0:
            self.DebugMsg("Coordinates_Step_SubStep"+str((step, substep))+" --> AngleEllipse ="+str(self.Notches_Angle_ellipse[new_step][substep])+" --> "+str(AngleEllipse)+" Result="+str((self.ResultingCurve_R[AngleEllipse], self.ResultingCurve_Theta[AngleEllipse]))+'\n')
           
        return (self.ResultingCurve_R[AngleEllipse], self.ResultingCurve_Theta[AngleEllipse])

    def gen_flex_step(self, index_step):
        ''' 
        Draw a flex step. Each step has N + 2 vertical lines where N is the distance between notches.
        The notch itself is 2 mm (roughly) large, the whole notch is N+2 mm large 
        '''
        #Each step is a path for inkscape
        path = inkcape_polar(self.Offset, self.group)
        # first draw the line between next notch and current one
        R, angle = self.Coordinates_Step_SubStep(index_step+1, 0)
        self.DebugMsg("gen_flex_step("+str(index_step)+") : MoveTo("+str((R, 180*angle/math.pi))+'\n')
        path.MoveTo(R, angle)
        R, angle = self.Coordinates_Step_SubStep(index_step, 2)
        path.LineTo(R, angle)
        self.DebugMsg("  From next notch, LineTo("+str((R, 180*angle/math.pi))+'\n')
        # Then the notch, starting internal to external
        # Compute radius to largest ellipse
        R2 = R * self.large_ell_a / self.small_ell_a
        # The short vertical line begins at (R2 - R)/2/NbVerticalLines - 1
        v = (R2-R)/2/self.nbVerticalLines - 1
        path.Line(R+v, angle, R-self.thickness, angle)
        self.DebugMsg("  Int notch, LineFrom("+str((R+v, 180*angle/math.pi))+" to "+str((R-self.thickness, 180*angle/math.pi))+" v="+str(v)+'\n')
        # Then notch (internal side)
        R, angle = self.Coordinates_Step_SubStep(index_step, 0)
        path.LineTo(R-self.thickness, angle)
        self.DebugMsg("  Int notch, LineTo "+str((R-self.thickness, 180*angle/math.pi))+'\n')
        # Compute radius to largest ellipse
        R2 = R * self.large_ell_a / self.small_ell_a
        # The short vertical line ends at (R2 - R)/2/NbVerticalLines - 1
        v = (R2-R)/2/self.nbVerticalLines - 1
        v2 = (R2-R)/self.nbVerticalLines - 2
        path.LineTo(v + R , angle)
        self.DebugMsg("  notch, LineTo "+str((R+v, 180*angle/math.pi))+" v ="+str(v)+" v2="+str(v2)+'\n')
        # Now draw N-1 vertical lines, size v2
        for i in range(self.nbVerticalLines-1):
            path.Line(i*(v2+2)+v+2+R, angle, (i+1)*(v2+2)+v+R, angle)
            self.DebugMsg("  Vertical lines_1 , Line from "+str((i*(v2+2)+v+2+R, 180*angle/math.pi))+" to "+str(((i+1)*(v2+2)+v+R, 180*angle/math.pi))+'\n')
        # Then external notch
        path.Line((i+1)*(v2+2)+v+R+2, angle, R2 + self.thickness, angle)
        self.DebugMsg("  Ext_notch , Line from "+str(((i+1)*(v2+2)+v+R+2, 180*angle/math.pi))+" to "+str((R2 + self.thickness, 180*angle/math.pi))+'\n')
        R, angle = self.Coordinates_Step_SubStep(index_step, 2)
        R21 = R * self.large_ell_a / self.small_ell_a
        path.LineTo(R21+self.thickness, angle)
        self.DebugMsg("  Ext notch, LineTo "+str((R21+self.thickness, 180*angle/math.pi))+'\n')
        R01, angle2 = self.Coordinates_Step_SubStep(index_step+1, 0)
        R21 = R01 * self.large_ell_a / self.small_ell_a
        # Then return
        v = (R2-R)/2/self.nbVerticalLines - 1
        v2 = (R2-R)/self.nbVerticalLines - 2
        path.LineTo(R2-v, angle)
        self.DebugMsg("  Ext notch, LineTo "+str((R2-v, 180*angle/math.pi))+" v="+str(v)+" v2="+str(v2)+'\n')
        #Line to next notch (external)
        path.Line(R2, angle, R21, angle2)
        self.DebugMsg("  To next notch, Line From "+str((R21, 180*angle/math.pi))+" To "+str((R2, 180*angle2/math.pi))+'\n')
        # Now draw N-1 vertical lines
        for i in range(self.nbVerticalLines-2, -1, -1):
            path.Line((i+1)*(v2+2)+v+R, angle, i*(v2+2)+v+2+R, angle)
            self.DebugMsg("  Vertical lines_2 , Line from "+str(((i+1)*v2+R+v+1, 180*angle/math.pi))+" to "+str((i*(v2+2)+v+2+R, 180*angle/math.pi))+'\n')
        # Then draw nbVerticalLines inside notch, "top" to "bottom" 
        R, angle = self.Coordinates_Step_SubStep(index_step, 1)
        v2 = (R2-R)/self.nbVerticalLines - 2
        for i in range(self.nbVerticalLines):
            if i == 0:
                path.Line(R-self.thickness+1, angle, R+v2+1, angle)
                self.DebugMsg("  Vertical lines_3 , Line from "+str((R-self.thickness+1, 180*angle/math.pi))+" to "+str((R+(i+1)*(v2+2)-1, 180*angle/math.pi))+'\n')
            elif i == self.nbVerticalLines - 1:
                path.Line(R+i*(v2+2)+1, angle, R2 + self.thickness - 1, angle)
                self.DebugMsg("  Vertical lines_3 , Line from "+str((R+i*(v2+2)+1, 180*angle/math.pi))+" to "+str((R2 + self.thickness - 1, 180*angle/math.pi))+'\n')
            else:
                path.Line(R+i*(v2+2)+1, angle, R+(i+1)*(v2+2)-1, angle)
                self.DebugMsg("  Vertical lines_3 , Line from "+str((R+i*(v2+2)+1, 180*angle/math.pi))+" to "+str((R+(i+1)*(v2+2)-1, 180*angle/math.pi))+'\n')
        # Then notch_interval set of nbVerticalLines
        # 
        for line in range(1, self.options.notch_interval):
            R, angle = self.Coordinates_Step_SubStep(index_step, line+2)
            v = (R2-R)/2/self.nbVerticalLines - 1
            v2 = (R2-R)/self.nbVerticalLines - 2
            if line % 2 == 0:
                #line is even, draw nbVerticalLines top to bottom
                for i in range(self.nbVerticalLines):
                    path.Line(R+i*(v2+2)+1, angle, R+(i+1)*(v2+2)-1, angle)
                    self.DebugMsg("  Vertical lines_4_0 , Line from "+str((R+i*(v2+2)+1, 180*angle/math.pi))+" to "+str((R+(i+1)*(v2+2)-1, 180*angle/math.pi))+'\n')
            else:
                # line is odd, draw bottom to top, first line half size
                path.Line(R2 - 1, angle, R2 - v, angle)
                # then nbVerticalLines - 1 lines
                for i in range(self.nbVerticalLines-2, -1, -1):
                    path.Line((i+1)*(v2+2)+v+R, angle, i*(v2+2)+v+2+R, angle)
                #and at last, one vertical line half size                    
                path.Line(v+R, angle, R+1, angle)
        path.GenPath()
        
    def gen_flex_first_step(self):
        ''' 
        Draw the first step flex. 
        This specific step has a notch which is only 1mm (roughly) wide, because first and last step shoul lie in same notch
        This has step has N + 2 vertical lines where N is the distance between notches.
        '''
        #Each step is a path for inkscape
        path = inkcape_polar(self.Offset, self.group)
        # first draw the line between next notch and current one
        R, angle = self.Coordinates_Step_SubStep(1, 0)      # Position of next step, which is 1
        self.DebugMsg("gen_first_flex_step : MoveTo("+str((R, 180*angle/math.pi))+'\n')
        path.MoveTo(R, angle)
        R, angle = self.Coordinates_Step_SubStep(0, 2)
        path.LineTo(R, angle)
        self.DebugMsg("  From next notch, LineTo("+str((R, 180*angle/math.pi))+'\n')
        # Then the notch, starting internal to external
        # Compute radius to largest ellipse
        R2 = R * self.large_ell_a / self.small_ell_a
        # The short vertical line begins at (R2 - R)/2/NbVerticalLines - 1
        v = (R2-R)/2/self.nbVerticalLines - 1
        path.Line(R+v, angle, R-self.thickness, angle)
        self.DebugMsg("  Int notch, LineFrom("+str((R+v, 180*angle/math.pi))+" to "+str((R-self.thickness, 180*angle/math.pi))+" v="+str(v)+'\n')
        # Then notch (internal side)
        R, angle = self.Coordinates_Step_SubStep(0, 1)
        path.LineTo(R-self.thickness, angle)
        self.DebugMsg("  Int notch, LineTo "+str((R-self.thickness, 180*angle/math.pi))+'\n')
        # Compute radius to largest ellipse
        R2 = R * self.large_ell_a / self.small_ell_a
        # Then edge, full line towards R2
        path.LineTo(R2+self.thickness , angle)
        self.DebugMsg("  edge, LineTo "+str((R2, 180*angle/math.pi))+'\n')
        R, angle = self.Coordinates_Step_SubStep(0, 2)
        R21 = R * self.large_ell_a / self.small_ell_a
        path.LineTo(R21+self.thickness, angle)
        self.DebugMsg("  Ext notch, LineTo "+str((R21+self.thickness, 180*angle/math.pi))+'\n')
        R01, angle2 = self.Coordinates_Step_SubStep(1, 0)
        R21 = R01 * self.large_ell_a / self.small_ell_a
        # Then return
        v = (R2-R)/2/self.nbVerticalLines - 1
        v2 = (R2-R)/self.nbVerticalLines - 2
        path.LineTo(R2-v, angle)
        self.DebugMsg("  Ext notch, LineTo "+str((R2-v, 180*angle/math.pi))+" v="+str(v)+" v2="+str(v2)+'\n')
        #Line to next notch (external)
        path.Line(R2, angle, R21, angle2)
        self.DebugMsg("  To next notch, Line From "+str((R21, 180*angle/math.pi))+" To "+str((R2, 180*angle2/math.pi))+'\n')
        # Now draw N-1 vertical lines
        for i in range(self.nbVerticalLines-2, -1, -1):
            path.Line((i+1)*(v2+2)+v+R, angle, i*(v2+2)+v+2+R, angle)
            self.DebugMsg("  Vertical lines_2 , Line from "+str(((i+1)*v2+R+v+1, 180*angle/math.pi))+" to "+str((i*(v2+2)+v+2+R, 180*angle/math.pi))+'\n')
        # Then notch_interval -1 or +1 set of nbVerticalLines
        if self.options.notch_interval == 2:
            numstep = 3
        else:
            numstep = self.options.notch_interval - 1
        for line in range(1, numstep):
            R, angle = self.Coordinates_Step_SubStep(0, line+2)
            v = (R2-R)/2/self.nbVerticalLines - 1
            v2 = (R2-R)/self.nbVerticalLines - 2
            if line % 2 == 0:
                #line is even, draw nbVerticalLines top to bottom
                for i in range(self.nbVerticalLines):
                    path.Line(R+i*(v2+2)+1, angle, R+(i+1)*(v2+2)-1, angle)
                    self.DebugMsg("  Vertical lines_4_0 , Line from "+str((R+i*(v2+2)+1, 180*angle/math.pi))+" to "+str((R+(i+1)*(v2+2)-1, 180*angle/math.pi))+'\n')
            else:
                # line is odd, draw bottom to top, first line half size
                path.Line(R2 - 1, angle, R2 - v, angle)
                # then nbVerticalLines - 1 lines
                for i in range(self.nbVerticalLines-2, -1, -1):
                    path.Line((i+1)*(v2+2)+v+R, angle, i*(v2+2)+v+2+R, angle)
                #and at last, one vertical line half size                    
                path.Line(v+R, angle, R+1, angle)
        path.GenPath()
    
    def gen_flex_last_step(self):
        ''' 
        Draw the last step flex. 
        This specific step has a notch which is only 1mm (roughly) wide, because first and last step shoul lie in same notch
        This is a very simple step, with only the narrow notch
        '''
        #Each step is a path for inkscape
        path = inkcape_polar(self.Offset, self.group)
        # Then the notch, starting internal to external
        R, angle = self.Coordinates_Step_SubStep(self.num_notches, 0)
        # Compute radius to largest ellipse
        R2 = R * self.large_ell_a / self.small_ell_a
        # The short vertical line begins at (R2 - R)/2/NbVerticalLines - 1
        v = (R2-R)/2/self.nbVerticalLines - 1
        path.Line(R+v, angle, R-self.thickness, angle)
        self.DebugMsg("GenLast_Step, LineFrom("+str((R+v, 180*angle/math.pi))+" to "+str((R-self.thickness, 180*angle/math.pi))+" v="+str(v)+'\n')
        # Then notch (internal side)
        R, angle = self.Coordinates_Step_SubStep(self.num_notches, 1)
        path.LineTo(R-self.thickness, angle)
        self.DebugMsg("  Last notch, LineTo "+str((R-self.thickness, 180*angle/math.pi))+'\n')
        # Compute radius to largest ellipse
        R2 = R * self.large_ell_a / self.small_ell_a
        # Then edge, full line towards R2
        path.LineTo(R2+self.thickness , angle)
        self.DebugMsg("  edge, LineTo "+str((R2, 180*angle/math.pi))+'\n')
        R, angle = self.Coordinates_Step_SubStep(self.num_notches, 0)
        R21 = R * self.large_ell_a / self.small_ell_a
        path.LineTo(R21+self.thickness, angle)
        self.DebugMsg("  Ext notch, LineTo "+str((R21+self.thickness, 180*angle/math.pi))+'\n')
        # Then return
        v = (R2-R)/2/self.nbVerticalLines - 1
        v2 = (R2-R)/self.nbVerticalLines - 2
        path.LineTo(R2-v, angle)
        self.DebugMsg("  Ext notch, LineTo "+str((R2-v, 180*angle/math.pi))+" v="+str(v)+" v2="+str(v2)+'\n')
        # Now draw N-1 vertical lines
        for i in range(self.nbVerticalLines-2, -1, -1):
            path.Line((i+1)*(v2+2)+v+R, angle, i*(v2+2)+v+2+R, angle)
            self.DebugMsg("  Last Vertical lines_2 , Line from "+str(((i+1)*v2+R+v+1, 180*angle/math.pi))+" to "+str((i*(v2+2)+v+2+R, 180*angle/math.pi))+'\n')
        path.GenPath()

    def compute_notches_angle(self):
        ''' 
        Compute the angles associated with each notch
        Indeed, do not compute angles, but index in the reference ellipse array.
        After this angle could be easily computed by multiplying by 2*pi/sizeTab
        For each notch build a list of n+2 angles, corresponding to each step in the notch
        2 steps for the notch itself and n steps as requested between notches
        Angles are computed to match length of the small ellipse, length of the larger one will be longer accordingly to size ratio 
        return an array which will be used for drawing both ellipses and curved surface
        '''
        self.Notches_Angle_ellipse = []
        LastIdx = 0
        curPos = 0
        #Compute offset, this is the first notch greater or equal to offset
        Delta_i = self.options.cut_position * sizeTab / 360     #expected offset

        self.Offset_Notch = -1
        for iNotch in range(self.num_notches):
            #   First point is same as end of previous one, do not compute
            #   Second and third one are 1mm (roughly) farther to make the notch
            idx1 = self.length2Angle( LastIdx, (curPos + self.notch_size / ( self.options.notch_interval + 2.0))/self.small_ell_a)
            idx2 = self.length2Angle( LastIdx, (curPos + self.notch_size * 2.0 / ( self.options.notch_interval + 2.0))/self.small_ell_a)
            #   Check if this is the "special notch"
            if idx1 >= Delta_i:
                self.Offset_Ellipse = LastIdx
                self.Offset_Notch = iNotch
                Delta_i = sizeTab * 2       # To make sure there is only one match !
            elif self.Offset_Notch < 0 and iNotch >= self.num_notches -1:
                #If not found the special notch, this is the last one
                self.Offset_Ellipse = LastIdx
                self.Offset_Notch = iNotch
            current_notch = [LastIdx, idx1, idx2]
            #self.DebugMsg("Notch "+str(iNotch)+" First points="+str(current_notch)+'\n')
            NumStep = self.options.notch_interval
            if iNotch == self.Offset_Notch:
                self.DebugMsg("Angle offset="+str(self.options.cut_position)+" Delta notch="+str(self.Offset_Notch)+" Real offset="+str(self.Offset_Ellipse)+'\n')
                if NumStep == 2:
                    NumStep = 3     # In this case, special notch is longer
                else:
                    NumStep -= 1    # In this case, it is shorter
            # Now for each remaining steps
            for i in range(NumStep):
                # Even with specific notch, use self.options.notch_interval to keep global notch_size different
                idx = self.length2Angle( LastIdx, (curPos + self.notch_size * (2.0+i+1) / ( self.options.notch_interval + 2.0))/self.small_ell_a)
                current_notch.append(idx)   # add to the list
            LastIdx = idx
            curPos = self.lEllipse[idx] * self.small_ell_a
            self.Notches_Angle_ellipse.append(current_notch)
            if iNotch == self.Offset_Notch:
                self.DebugMsg(" Special Notch "+str(iNotch)+" with Numstep="+str(NumStep)+" ="+str(current_notch)+'\n')

            #self.DebugMsg("  Complete Notch "+str(iNotch)+"="+str(current_notch)+'\n')
        self.DebugMsg("Angles are computed, last position : "+str(curPos)+'\n')
        # Now change position of notch next to Offset to make assembly easier
        # if notch_interval is 2, add one for this 

       
    def gen_Resulting_Curve(self):
        '''
            Each point from the smallest ellipse will be on a curve defined by
            1) The distance from the cone summit will sqrt(h**2 + a**2*cos(alpha)**2 + b**2*sin(alpha)**2) where h is the cone height (full cone up to summit)
               and a and b are the ellipse dimensions.
            2) The distance between two points on the curve should be equal at the distance between two points on the ellipse.
               If when on alpha1 on the ellipse the angle on the resulting curbe is Theta1. 
               When on alpha2 on the ellipse, the angle on the resulting curve will be Theta2, and distance between Point(Theta2), Point(Theta1) will be equal 
               to distance Point(Alpha1), Point(Alpha2) 
            3) Theta=0 on resulting curve should correspond to parameter cut_position on the ellipse. 
                 
        '''
        #First compute the cone summit with the dimensions of the two ellipses
        # When angle is 0, positions are (small_a, 0) and (large_a,0)
        h1 = self.zc*self.small_ell_a/(self.large_ell_a - self.small_ell_a)
        self.DebugMsg("gen_Resulting_Curve: height for small ellipse "+str(h1)+" For large one "+str(h1*self.large_ell_a/self.small_ell_a)+'\n')
        # Now for each angle (index) in Notches_Angle compute the corresponding Theta angle on the resulting curve and the associated distance (polar coordinates)
        # Do the computation with the small ellipse and large ellipse
        self.ResultingCurve_R = np.zeros(sizeTab+1)         # Distance from center for the small ellipse, once projection is applied
        self.ResultingCurve_Theta = np.zeros(sizeTab+1)     # Angle on resulting curve, for each point in initial ellipse
        LengthResultingCurve = 0
        alpha = (math.pi * 2 / sizeTab) * self.Offset_Ellipse
        #Offset to length computation on ellipse
        length_Offset = self.lEllipse[self.Offset_Ellipse]
        #Compute first point
        self.ResultingCurve_R[0] = math.sqrt(h1**2 + self.small_ell_a**2*math.cos(alpha)**2 + self.small_ell_b**2*math.sin(alpha)**2)
        self.ResultingCurve_Theta[0] = 0
        oldR = self.ResultingCurve_R[0]
        oldX = oldR
        oldY = 0
        self.BoundingXmax = oldX
        self.BoundingXmin = oldX
        self.BoundingYmax = oldY
        self.BoundingYmin = oldY
        i = 1
        error = 0
        maxError = 0
        maxErrorPos = 0
        while i <= sizeTab:
            index_ellipse = i + self.Offset_Ellipse
            if index_ellipse > sizeTab:
                index_ellipse -= sizeTab
            # First radius
            alpha = (math.pi * 2 / sizeTab) * index_ellipse
            R = math.sqrt(h1**2 + self.small_ell_a**2*math.cos(alpha)**2 + self.small_ell_b**2*math.sin(alpha)**2)
            self.ResultingCurve_R[i] = R
            # Then angle
            # First get distance on ellipse and delta from distance on result curve
            if i == sizeTab:    #Specific case, whole ellipse
                Distance = self.small_ell_a * self.lEllipse[sizeTab]
            else:
                Distance = self.small_ell_a * (self.lEllipse[index_ellipse] - length_Offset)
                if Distance < 0:
                    Distance += self.lEllipse[sizeTab] * self.small_ell_a
            Delta_Distance = Distance - LengthResultingCurve
            if i == sizeTab:
                self.DebugMsg("gen_Resulting_Curve["+str(i)+"] : oldR="+str(oldR)+" R="+str(R)+" Distance="+str(Distance)+" Delta_Distance="+str(Delta_Distance)+" Compute acos("+str((oldR**2 + R**2 - Delta_Distance**2 ) / (2*oldR*R))+")\n")
            dTheta = math.acos((oldR**2 + R**2 - Delta_Distance**2 ) / (2*oldR*R))
            Theta = self.ResultingCurve_Theta[i-1] + dTheta
            self.ResultingCurve_Theta[i] = Theta
            X = R*math.cos(Theta)
            Y = R*math.sin(Theta)
            LengthResultingCurve += math.sqrt((X - oldX)**2 + (Y - oldY)**2)
            oldR = R
            oldX = X
            oldY = Y
            if self.BoundingXmax < X:
                self.BoundingXmax = X
            if self.BoundingXmin > X:
                self.BoundingXmin = X
            if self.BoundingYmax < Y:
                self.BoundingYmax = Y
            if self.BoundingYmin > Y:
                self.BoundingYmin = Y
            #self.DebugMsg("Index= "+str(i)+" R= "+str(R)+" Theta= "+str(180*Theta/math.pi)+" Longueur= "+str(LengthResultingCurve)+'\n')
            error = abs(Distance - LengthResultingCurve)
            if error > maxError:
                maxError = error
                maxErrorPos = i
                self.DebugMsg("New max error reached at index "+str(i)+" Distance Ellipse="+str(Distance)+" on curve="+str(LengthResultingCurve)+" Error="+str(error)+'\n')
            i += 1
        

    def gen_ellipse(self, axis_a, axis_b, xOffset, yOffset, parent):
        ''' Generate an ellipse with notches as a path.
                Ellipse dimensions' are parameters axis_a and axis_b
                Notches size gives the exact distance between two notches
                Notches number gives the number of notches to be drawed
                xOffset and yOffset gives the offset within the inkscape page
                Parent gives the parent structure of the path which will be created, most often the inkscape page itself
        '''
        group = etree.SubElement(parent, 'g')  # Create a group which will hold the ellipse 
        path = inkcape_polar((xOffset, yOffset), group)
        #   First point is in (major_axis, 0)
        Angle = 0
        idx = 0
        for iNotch in range(self.num_notches):
            #Angle on ellipse
            angle = (math.pi * 2.0 / sizeTab) * self.Notches_Angle_ellipse[iNotch][0]
            # First point is external
            pt1 = self.ellipse_ext(axis_a, axis_b, angle, self.thickness)
            #Second point is on ellipse at angle given by Notches_Angle_ellipse
            pt2 = (axis_a*math.cos(angle), axis_b*math.sin(angle))
            #Third point is on ellipse at angle with substep=2
            angle1 = (math.pi * 2.0 / sizeTab) * self.Notches_Angle_ellipse[iNotch][2]
            pt3 = (axis_a*math.cos(angle1), axis_b*math.sin(angle1))
            #Fourth point is external
            pt4 = self.ellipse_ext(axis_a, axis_b, angle1, self.thickness)
            if iNotch == 0:
                #Specific case, use MoveTo
                path.MoveTo_cartesian(pt1)
            else:
                #Draw line from previous fourth point
                path.LineTo_cartesian(pt1)
            #Then pt1 --> pt2
            path.LineTo_cartesian(pt2)
            #Then pt2 --> pt3
            path.LineTo_cartesian(pt3)
            #And at last pt3 --> pt4
            path.LineTo_cartesian(pt4)
            self.DebugMsg("Draw Ellipse, notch "+str(iNotch)+"  Pts="+str([pt1, pt2, pt3, pt4])+'\n')
            #Last line will be drawed with next notch
        #For the last one
        path.LineTo_cartesian((axis_a+self.thickness, 0))
        path.GenPath()
        
    def gen_flex(self, xOffset, yOffset, parent):
        group = etree.SubElement(parent, 'g')
        self.group = group
        self.Offset = (xOffset, yOffset)
        #Compute number of vertical lines, depends on cone's height
        R = self.ResultingCurve_R[0]
        R2 = self.large_ell_a / self.small_ell_a * self.ResultingCurve_R[0]
        if R2 - R > 60:
            self.nbVerticalLines = int((R2 - R)/25)
        else:
            self.nbVerticalLines = 2
        self.DebugMsg("Starting gen flex with "+str(self.nbVerticalLines)+" vertical lines R1="+str(R)+" R2="+str(R2)+ "R2-R1="+str(R2-R)+"\n")
        # First start step
        self.gen_flex_first_step()
        # Then middle steps
        for step in range(1, self.num_notches):
            self.gen_flex_step(step)
        # and alst one, (very short)
        self.gen_flex_last_step()

    def effect(self):
        """
        Draws an elliptical conic box, based on provided parameters
        """

        # input sanity check
        error = False
        if self.options.zc < 15:
            inkex.errormsg('Error: Cone height should be at least 15mm')
            error = True

        if self.options.d1 < 30:
            inkex.errormsg('Error: d1 should be at least 30mm')
            error = True

        if self.options.d2 < self.options.d1 + 0.009999:
            inkex.errormsg('Error: d2 should be at d1 + 0.01mm')
            error = True

        if self.options.eccentricity > 1.0 or self.options.eccentricity < 0.01:
            inkex.errormsg('Ratio minor axis / major axis should be between 0.01 and 1.0')
            error = True

        if self.options.notch_interval > 10:
            inkex.errormsg('Distance between notches should be less than 10')
            error = True

        if self.options.thickness <  1 or self.options.thickness >  10:
            inkex.errormsg('Error: thickness should be at least 1mm and less than 10mm')
            error = True

        if error:
            exit()

        # convert units
        unit = self.options.unit
        self.small_ell_a  = round(0.5 * self.svg.unittouu(str(self.options.d1) + unit), 2)
        self.large_ell_a  = round(0.5 * self.svg.unittouu(str(self.options.d2) + unit), 2)
        self.zc = self.svg.unittouu(str(self.options.zc) + unit)
        self.thickness = self.svg.unittouu(str(self.options.thickness) + unit)
        if self.options.notch_interval % 2:
            #Should be even !
            self.options.notch_interval += 1
        # If dimensions are external, correct d1, d2 and zc by thickness
        if self.options.inner_size == False:
            self.large_ell_a -= 2*self.thickness
            self.d2 -= 2*self.thickness
            self.zc -= 2*self.thickness
        #Compute minor axes sizes
        self.small_ell_b = round(self.small_ell_a * self.options.eccentricity, 2)
        self.large_ell_b = round(self.large_ell_a * self.options.eccentricity, 2)
        
        svg = self.document.getroot()
        docWidth = self.svg.unittouu(svg.get('width'))
        docHeight = self.svg.unittouu(svg.attrib['height'])

        # Open Debug file if requested
        self.fDebug = None
        if self.options.Mode_Debug:
            try:
                self.fDebug = open( 'DebugEllConicBox.txt', 'w')
            except IOError:
                print ('cannot open debug output file')
            self.DebugMsg("Start processing, doc size="+str((docWidth, docHeight))+"\n")


        layer = etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), 'Conical Box')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        #Create reference ellipse points.
        self.xEllipse[0] = 1
        self.yEllipse[0] = 0
        self.lEllipse[0] = 0
        i = 1
        while i <= sizeTab:
            self.xEllipse[i] = math.cos(2*math.pi*i/sizeTab)                                # Major axis size : 1
            self.yEllipse[i] = self.options.eccentricity*math.sin(2*math.pi*i/sizeTab)      # Minor axis size
            self.lEllipse[i] = self.lEllipse[i-1] + math.hypot( self.xEllipse[i] - self.xEllipse[i-1], self.yEllipse[i] - self.yEllipse[i-1])
            i += 1
            

        # Compute notches size of small ellipse
        Ell_Length = self.small_ell_a * self.lEllipse[sizeTab]
        # One notch is different to make assembly easier, as the notch on flex are NOT evenly spaced
        if self.options.notch_interval == 2:
            self.num_notches = int(round((Ell_Length - self.options.notch_interval - 3) / (2.0 + self.options.notch_interval)+1))
            self.notch_size = Ell_Length / (self.num_notches -1 + (self.options.notch_interval+3.0)/(self.options.notch_interval+2.0))
        else:
            self.num_notches = int(round((Ell_Length - self.options.notch_interval - 1) / (2.0 + self.options.notch_interval)+1))
            self.notch_size = Ell_Length / (self.num_notches -1 + (self.options.notch_interval+1.0)/(self.options.notch_interval+2.0))
        self.DebugMsg("Small ellipse dimensions a ="+str(self.small_ell_a)+" b="+str(self.small_ell_b)+" Length ="+str(Ell_Length)+'\n')
        self.DebugMsg("Number of notches : "+str(self.num_notches)+" Real notch size="+str(self.notch_size)+'\n')
        #Compute angles of all points which be drawed
        self.compute_notches_angle()
        #Then draw small ellipse
        self.gen_ellipse(self.small_ell_a, self.small_ell_b, -self.small_ell_a - self.thickness - 1, -self.small_ell_b - self.thickness - 1, layer)
        # Then large one
        self.gen_ellipse(self.large_ell_a, self.large_ell_b, -self.large_ell_a-2*self.small_ell_a - 3*self.thickness - 5, -self.large_ell_b - self.thickness - 1, layer)
        # Compute points on resulting curve
        self.gen_Resulting_Curve()
        # Then generate flex
        # Bounding box of flex has been computed in gen_Resulting_Curve
        self.DebugMsg("Flex bounding box : "+str((self.BoundingXmin, self.BoundingYmin))+","+str((self.BoundingXmax, self.BoundingYmax))+'\n')
        # yOffset is below large ellipse
        yOffset = -2*(self.large_ell_b+self.thickness) - 5 - self.BoundingYmin
        # xOffset, center on page
        xOffset = 0.5*(self.BoundingXmin + self.BoundingXmax) - 0.5*docWidth
        self.DebugMsg("Offset Flex="+str((xOffset, yOffset))+'\n')
        self.gen_flex(xOffset, yOffset, layer)

        if self.fDebug:
            self.fDebug.close()

if __name__ == '__main__':
    BoxMakerEllipticalCone().run()
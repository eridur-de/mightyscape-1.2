#!/usr/bin/env python3

# Distributed under the terms of the GNU Lesser General Public License v3.0

import math
import inkex
from copy import deepcopy
from lxml import etree
from inkex.transforms import Transform
from inkex import Color

# Helper functions
def calc_angle_between_points(p1, p2):
    xDiff = p2[0] - p1[0]
    yDiff = p2[1] - p1[1]
    return math.degrees(math.atan2(yDiff, xDiff))
	
def calc_dist_between_points(p1, p2):
    xDiff = p2[0] - p1[0]
    yDiff = p2[1] - p1[1]
    return math.sqrt(yDiff*yDiff + xDiff*xDiff)
	
def normalize(p1, p2):
    " p1,p2 defines a vector return normalized "
    xDiff = p2[0] - p1[0]
    yDiff = p2[1] - p1[1]
    magn = calc_dist_between_points(p1,p2)
    return (xDiff/magn, yDiff/magn)
	
def polar_to_cartesian(cx, cy, radius, angle_degrees):
    " So we can make arcs in the 'A' svg syntax. "
    angle_radians = math.radians(angle_degrees)
    return [
	          cx + (radius * math.cos(angle_radians)), 
			  cy + (radius * math.sin(angle_radians))
		    ]
	
def point_on_circle(radius, angle):
    " return xy coord of the point at distance radius from origin at angle "
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    return [x, y]

class SheetMetalConus(inkex.EffectExtension):
    """ Program to unfold a frustum of a cone or a cone 
        (if parameter diaCut=0) and generate a sheet cutting layout
        or flat pattern projection that can be rolled or bend up into a (truncated) cone shape.
    """
    color_marker_dim = '#703cd6'    # purple
    color_marker_chords = '#9d2222' # red
    color_marker_base = '#36ba36'   # green
    # Arrowed lines
    dimline_style = {'stroke'        : '#000000',
                     'stroke-width'  : '0.75px',
                     'fill'          : 'none',
                     'marker-start'  : 'url(#ArrowDIN-start)',
                     'marker-end'    : 'url(#ArrowDIN-end)'    }

    def add_arguments(self, pars):
        pars.add_argument('-b', '--diaBase', type = float, dest = 'diaBase', default = 300.0, help = 'The diameter of the cones base.')
        pars.add_argument('-c', '--diaCut',  type = float, default = 100.0, help = 'The diameter of cones cut (0.0 if cone is not cut.')
        pars.add_argument('-l', '--heightCone',  type = float, default = 200.0, help = 'The height of the (cut) cone.')
        pars.add_argument('-u', '--units', default = 'mm', help = 'The units in which the cone values are given. mm or in for real objects')
        pars.add_argument('-w', '--strokeWidth', type = float, default = 0.3, help = 'The line thickness in given unit. For laser cutting it should be rather small.')
        pars.add_argument('-f', '--strokeColour', type=Color, default = 255, help = 'The line colour.')
        pars.add_argument('-d', '--verbose', type = inkex.Boolean, default = False, help = 'Enable verbose output of calculated parameters. Used for debugging or is someone needs the calculated values.')


    # Marker arrows
    def makeMarkerstyle(self, name, rotate):
        " Markers added to defs for reuse "
        defs = self.svg.getElement('/svg:svg//svg:defs')
        if defs == None:
            defs = etree.SubElement(self.document.getroot(),inkex.addNS('defs','svg'))
        marker = etree.SubElement(defs ,inkex.addNS('marker','svg'))
        marker.set('id', name)
        marker.set('orient', 'auto')
        marker.set('refX', '0.0')
        marker.set('refY', '0.0')
        marker.set('style', 'overflow:visible')
        marker.set(inkex.addNS('stockid','inkscape'), name)

        arrow = etree.Element("path")
        # definition of arrows in beautiful DIN-shapes:
        if name.startswith('ArrowDIN-'):
            if rotate:
                arrow.set('d', 'M 8,0 -8,2.11 -8,-2.11 z')
            else:
                arrow.set('d', 'M -8,0 8,-2.11 8,2.11 z')
        if name.startswith('ArrowDINout-'):
            if rotate:
                arrow.set('d', 'M 0,0 16,2.11 16,0.5 26,0.5 26,-0.5 16,-0.5 16,-2.11 z')
            else:
                arrow.set('d', 'M 0,0 -16,2.11 -16,0.5 -26,0.5 -26,-0.5 -16,-0.5 -16,-2.11 z')
        arrow.set('style', 'fill:#000000;stroke:none')
        marker.append(arrow)

    def set_arrow_dir(self, option, style):
        if option=='inside':
            # inside
            self.arrowlen = 6.0
            style['marker-start'] = 'url(#ArrowDIN-start)'
            style['marker-end'] = 'url(#ArrowDIN-end)'
            self.makeMarkerstyle('ArrowDIN-start', False)
            self.makeMarkerstyle('ArrowDIN-end', True)
        else:
            # outside
            self.arrowlen = 0
            style['marker-start'] = 'url(#ArrowDINout-start)'
            style['marker-end'] = 'url(#ArrowDINout-end)'
            self.makeMarkerstyle('ArrowDINout-start', False)
            self.makeMarkerstyle('ArrowDINout-end', True)

    def drawDimArc(self, start, end, radius, style, parent, gap=0, lowside=True):
        " just the arrowed arc line "
        angle = abs(end-start)
        # inside or outside 
        inside = True
        critical_length = 35
        dist = calc_dist_between_points(point_on_circle(radius, start), point_on_circle(radius, end))
        if angle < 45 and dist > critical_length: inside = False
        # change start and end angles to make room for arrow markers
        arrow_angle = math.degrees(math.sin(self.arrowlen/radius))
        if lowside:
            start += arrow_angle
            angle -= arrow_angle
            anglefac = 1
        else:
            start -= arrow_angle
            angle -= arrow_angle
            anglefac = -1

        if gap == 0:
            line_attribs = {'style' : str(inkex.Style(style)),
                            'd'     : self.build_arc(0, 0, start, angle*anglefac, radius, lowside) }
            ell = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )
        else: # leave a gap for label
            gap_angle = math.degrees(math.sin(gap/radius))
            startstyle = deepcopy(style)
            #startstyle['marker-start'] = None
            line_attribs = {'style' : str(inkex.Style(startstyle)),
                            'd'     : self.build_arc(0, 0, start, angle*anglefac/2-gap_angle/2*anglefac, radius, lowside) }
            ell = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )
            endstyle = deepcopy(style)
            #endstyle['marker-end'] = None
            line_attribs = {'style' : str(inkex.Style(endstyle)),
                            'd'     : self.build_arc(0, 0, angle/2*anglefac+gap_angle/2*anglefac, angle*anglefac, radius, lowside) }
            etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )
        # return pos in center of gap (or arc)
        textposangle = angle/2*anglefac
        return (point_on_circle(radius, math.radians(textposangle)))
        
    def drawDimension(self, a, b, style, parent):
        " draw arrowed dimensions using markers "
        # draw arrows as inside or outside dimension
        critical_length = 35.
        if calc_dist_between_points(a,b) > critical_length:
            self.set_arrow_dir('inside', style)
        else:
            self.set_arrow_dir('outside', style)
        attribs = {'style' : str(inkex.Style(style))}
        # account for length change so arrows fit
        norm = normalize(a, b)
        dim_start_x = a[0] + self.arrowlen*norm[0]
        dim_start_y = a[1] + self.arrowlen*norm[1]
        dim_end_x = b[0] - self.arrowlen*norm[0]
        dim_end_y = b[1] - self.arrowlen*norm[1]
        #
        attribs['d'] = 'M %f,%f %f,%f' % (dim_start_x, dim_start_y, dim_end_x, dim_end_y)
        dimline = etree.SubElement(parent, inkex.addNS('path', 'svg'), attribs)
        return dimline
    
    def calculateCone(self, dictCone):
        """ Calculates all relevant values in order to construct a cone.
            These values are:
            - short radius
            - long radius
            - angle of cone layout
            - chord of base diameter
            - chord of cut diameter
            - coordinates of points A, B, C and D
        """        
        dBase = dictCone['diaBase']
        dCut =  dictCone['diaCut']
        hCone = dictCone['heightCone']
        base = dBase - dCut
        # radius from top of cone to cut
        if dCut > 0:
            shortRadius = math.sqrt( dCut*dCut/4 + (dCut*hCone)/base * (dCut*hCone)/base )
        else:
            shortRadius=0.0
        dictCone['shortRadius'] = shortRadius
        ## radius from top of cone to base of cone
        longRadius=math.sqrt( dBase*dBase/4 + (dBase*hCone)/base * (dBase*hCone)/base )
        dictCone['longRadius'] = longRadius

        ## angle of circle sector
        angle=(math.pi * dBase) / longRadius
        dictCone['angle'] = angle
        # chord is the straight line between the 2 endpoints of an arc. 
        # Not used directly, but available in verbose output.
        chordBase = longRadius * math.sqrt( 2* (1-math.cos(angle)) )
        dictCone['chordBase'] = chordBase
        chordCut = shortRadius * math.sqrt( 2* (1-math.cos(angle)) )
        dictCone['chordCut'] = chordCut

        # calculate coordinates of points A, B, C and D
        # center M is at (0,0) and points A and B are on the x-axis:
        ptA = (shortRadius, 0.0)
        ptB = (longRadius,  0.0)
        # we can calculate points C and D with the given radii and the calculated angle
        ptC=(longRadius * math.cos(angle),  longRadius *  math.sin(angle))
        ptD=(shortRadius * math.cos(angle), shortRadius * math.sin(angle))
        dictCone['ptA'] = ptA
        dictCone['ptB'] = ptB
        dictCone['ptC'] = ptC
        dictCone['ptD'] = ptD

    def effect(self):
        
        if self.options.diaBase == self.options.diaCut:
            inkex.utils.debug("Warning. Cut diameter may not be equal to base diameter.")
            exit(1)
        
        # calc scene scale
        convFactor = self.svg.unittouu("1" + self.options.units)   
        # Store all the relevants values in a dictionary for easy access
        dictCone={'diaBase':    self.options.diaBase,
                  'diaCut':     self.options.diaCut,
                  'heightCone': self.options.heightCone }
        # Get all values needed in order to draw cone layout:
        self.calculateCone(dictCone)
        
        # Draw the cone layout:
        # Make top level group
        t = 'translate(%s,%s)' % (self.svg.namedview.center[0], self.svg.namedview.center[1])
        grp_attribs = {inkex.addNS('label','inkscape'):'Sheet Metal Conus Group', 'transform':t}
        grp = etree.SubElement(self.svg.get_current_layer(), 'g', grp_attribs)

        linestyle = { 'stroke' : self.options.strokeColour, 'fill' : 'none',
                      'stroke-width': str(self.svg.unittouu(str(self.options.strokeWidth) + self.options.units)) }
        line_attribs = {'style' : str(inkex.Style(linestyle)), inkex.addNS('label','inkscape') : 'Cone' }
        
        # Connect the points into a single path of lines and arcs
        zeroCenter=(0.0, 0.0)
        angle = math.degrees(dictCone['angle'])
        path = ""
        path += self.build_line(dictCone['ptA'][0], dictCone['ptA'][1], dictCone['ptB'][0], dictCone['ptB'][1], convFactor) # A,B
        path += " " + self.build_arc(zeroCenter[0], zeroCenter[1], 0.0, angle, dictCone.get('longRadius')*convFactor)
        path += " " + self.build_line(dictCone['ptC'][0], dictCone['ptC'][1],dictCone['ptD'][0], dictCone['ptD'][1], convFactor) # C,D
        path += self.build_arc(zeroCenter[0], zeroCenter[1], 0.0, angle, dictCone['shortRadius']*convFactor)
        line_attribs['d'] = path
        ell = etree.SubElement(grp, inkex.addNS('path','svg'), line_attribs )
        
        # Draw Dimensions Markup
        if self.options.verbose == True:
            grp_attribs = {inkex.addNS('label','inkscape'):'markup'}
            markup_group = etree.SubElement(grp, 'g', grp_attribs)
            self.beVerbose(dictCone, convFactor, markup_group)
                
    def build_arc(self, x, y, start_angle, end_angle, radius, reverse=True, swap=False):
        # Not using internal arc rep - instead construct path A in svg style directly
        # so we can append lines to make single path
        start = polar_to_cartesian(x, y, radius, end_angle)
        end = polar_to_cartesian(x, y, radius, start_angle)
        arc_flag = 0 if reverse else 1
        sweep = 0 if (end_angle-start_angle) <=180 else 1
        if swap: sweep = 1-sweep
        path = 'M %s,%s' % (start[0], start[1])
        path += " A %s,%s 0 %d %d %s %s" % (radius, radius, sweep, arc_flag, end[0], end[1])
        return path
    
    def build_line(self, x1, y1, x2, y2, unitFactor):
        path = 'M %s,%s L %s,%s' % (x1*unitFactor, y1*unitFactor, x2*unitFactor, y2*unitFactor)
        return path

    def beVerbose(self, dictCone, unitFactor, parent):
        """ Verbose output of calculated values. 
            Can be used for debugging purposes or if calculated values needed.
        """
        # unpack
        base_dia = dictCone['diaBase']
        cut_dia = dictCone['diaCut']
        cone_height = dictCone['heightCone']
        shortradius = dictCone['shortRadius']
        longradius = dictCone['longRadius']
        angle = dictCone['angle']
        chord_base = dictCone['chordBase']
        chord_cut = dictCone['chordCut']
        ptA = dictCone['ptA']
        ptB = dictCone['ptB']
        ptC = dictCone['ptC']
        ptD = dictCone['ptD']

        # styles for markup
        stroke_width = max(0.1, self.svg.unittouu(str(self.options.strokeWidth/2) + self.options.units))
        line_style = { 'stroke': self.color_marker_dim, 'stroke-width': str(stroke_width), 'fill':'none' }
        arrow_style = self.dimline_style
        font_height = min(32, max( 8, int(self.svg.unittouu(str(longradius/40) + self.options.units))))
        text_style = { 'font-size': str(font_height),
                       'font-family': 'arial',
                       'text-anchor': 'middle',
                       'text-align': 'center',
                       'fill': self.color_marker_dim }
        # verbose message for debug window
        msg = "Base diameter: " + str(base_dia) + "Cut diameter: " + str(cut_dia) + \
              "\nCone height: " + str(cone_height) + "\nShort radius: " + str(shortradius) + \
              "\nLong radius: " + str(longradius) + "\nAngle of circle sector: " + str(angle) + \
              " radians (= " + str(math.degrees(angle)) + " degrees)" + \
              "\nChord length of base arc: " + str(chord_base) + \
              "\nChord length of cut arc: " + str(chord_cut)
        #inkex.utils.debug( msg)

        # Mark center
        marker_length = max(5, longradius* unitFactor/100)
        line_attribs = {'style' : str(inkex.Style(line_style)),
                        inkex.addNS('label','inkscape') : 'center',
                        'd' : 'M -{0},-{0} L {0},{0}'.format(marker_length)}
        line = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        line_attribs = {'style' : str(inkex.Style(line_style)),
                        inkex.addNS('label','inkscape') : 'center',
                        'd' : 'M -{0},{0} L {0},-{0}'.format(marker_length)}
        line = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        # Draw tick marks
        line_attribs = {'style' : str(inkex.Style(line_style)), 'd' : 'M 0,-3 L 0,-30'}
        line = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        if cut_dia != 0:
            line_attribs = {'style' : str(inkex.Style(line_style)), 'd' : 'M {0},-3 L {0},-30'.format(shortradius * unitFactor)}
            line = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        line_attribs = {'style' : str(inkex.Style(line_style)), 'd' : 'M {0},-3 L {0},-30'.format(longradius * unitFactor)}
        line = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        # span line
        arrow_style['stroke'] = self.color_marker_dim
        self.drawDimension((0,-10), (shortradius * unitFactor, -10), arrow_style, parent)
        self.drawDimension((shortradius * unitFactor,-10), (longradius * unitFactor, -10), arrow_style, parent)
        # labels for short, long radii
        if cut_dia >= 0.001:
            text_atts = {'style':str(inkex.Style(text_style)),
                         'x': str(shortradius*unitFactor/2),
                         'y': str(-15) }
            text = etree.SubElement(parent, 'text', text_atts)
            text.text = "%4.3f" %(shortradius)
        text_atts = {'style':str(inkex.Style(text_style)),
                     'x': str((shortradius + (longradius-shortradius)/2)*unitFactor),
                     'y': str(-15) }
        text = etree.SubElement(parent, 'text', text_atts)
        text.text = "%4.3f" %(longradius)
        # Draw angle
        lowside = math.degrees(angle) < 180
        value = math.degrees(angle) if lowside else 360-math.degrees(angle)
        # radial limit lines
        line_attribs = {'style' : str(inkex.Style(line_style)), 'd' : 'M 3,0 L %4.2f,0' % (ptA[0]*unitFactor*0.8)}
        line = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        line_attribs = {'style' : str(inkex.Style(line_style)), 'd' : 'M %4.2f,%4.2f L %4.2f,%4.2f' % (ptD[0]*unitFactor*0.02, ptD[1]*unitFactor*0.02,ptD[0]*unitFactor*0.8, ptD[1]*unitFactor*0.8)}
        line = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        # arc
        arc_rad = ptA[0]*unitFactor*0.50
        gap = self.svg.unittouu(str(font_height*2)+"pt")
        textpos = self.drawDimArc(0, value, arc_rad, arrow_style, parent, gap, lowside)
        # angle label
        textpos[1] += font_height/4 if lowside else font_height/2
        text_atts = {'style':str(inkex.Style(text_style)),
                     'x': str(textpos[0]),
                     'y': str(textpos[1]) }
        text = etree.SubElement(parent, 'text', text_atts)
        text.text = "%4.2f deg" %(value)
        # chord lines
        dash_style = deepcopy(arrow_style)
        dash_style['stroke'] = self.color_marker_chords
        dash_style['stroke-dasharray'] = '4, 2, 1, 2'
        line = self.drawDimension((ptA[0]*unitFactor, ptA[1]*unitFactor), (ptD[0]*unitFactor, ptD[1]*unitFactor), dash_style, parent)
        line = self.drawDimension((ptB[0]*unitFactor, ptB[1]*unitFactor), (ptC[0]*unitFactor, ptC[1]*unitFactor), dash_style, parent)
        # chord labels
        centerx = ptB[0]*unitFactor + (ptC[0]-ptB[0])*unitFactor/2
        centery = ptB[1]*unitFactor + (ptC[1]-ptB[1])*unitFactor/2
        line_angle = calc_angle_between_points(ptC, ptB)
        ypos = centery+font_height+2 if line_angle<0 else centery-2
        text_style['fill'] = self.color_marker_chords
        text_atts = {'style':str(inkex.Style(text_style)),
                     'transform': 'rotate(%f)' % (line_angle) }
        text = etree.SubElement(parent, 'text', text_atts)
        scale_matrix = [[1, 0.0, centerx], [0.0, 1, ypos]] # needs cos,sin corrections
        text.transform = Transform(scale_matrix) @ text.transform
        text.text = "%4.2f" % (chord_base)
        if cut_dia >= 0.001:
            centerx = ptA[0]*unitFactor + (ptD[0]-ptA[0])*unitFactor/2
            centery = ptA[1]*unitFactor + (ptD[1]-ptA[1])*unitFactor/2
            xpos = centerx - font_height*math.sin(math.radians(abs(line_angle)))
            ypos = centery-2 if line_angle>0 else centery+font_height+2
            text = etree.SubElement(parent, 'text', text_atts)
            scale_matrix = [[1, 0.0, centerx], [0.0, 1, ypos]]
            text.transform = Transform(scale_matrix) @ text.transform
            text.text = "%4.2f" % (chord_cut)
        # frustum lines
        frustrum_repos = [[1, 0.0, 1], [0.0, 1, math.sqrt(pow(shortradius*unitFactor,2)-pow(cut_dia*unitFactor/2,2))]]
        text_style['fill'] = self.color_marker_base
        line_style['stroke'] = self.color_marker_base
        arrow_style['stroke'] = self.color_marker_base
        line_attribs = {'style': str(inkex.Style(line_style)),
                        'd': 'M %f,%f L %f,%f %f,%f %f,%f z' %(-cut_dia/2*unitFactor,0, cut_dia/2*unitFactor,0, base_dia/2*unitFactor,cone_height*unitFactor, -base_dia/2*unitFactor,cone_height*unitFactor)}
        line = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        line.transform = Transform(frustrum_repos) @ line.transform
        # ticks
        line_attribs = {'style': str(inkex.Style(line_style)),
                        'd': 'M %f,%f L %f,%f' %(-(5+cut_dia/2*unitFactor),0, -(5+base_dia/2*unitFactor),0 )}
        line = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        line.transform = Transform(frustrum_repos) @ line.transform
        #
        line = self.drawDimension((-base_dia/2*unitFactor,0), (-base_dia/2*unitFactor,cone_height*unitFactor), arrow_style, parent)
        line.transform = Transform(frustrum_repos) @ line.transform
        # frustum text
        text_atts = {'style':str(inkex.Style(text_style)),
                     'x': str(-(18+base_dia/2*unitFactor)),
                     'y': str(cone_height*unitFactor/2) }
        text = etree.SubElement(parent, 'text', text_atts)
        text.text = "%4.3f" %(cone_height)
        text.transform = Transform(frustrum_repos) @ text.transform
        if cut_dia >= 0.001:
            text_atts = {'style':str(inkex.Style(text_style)),
                         'x': '0',
                         'y': str(font_height) }
            text = etree.SubElement(parent, 'text', text_atts)
            text.text = "%4.3f" %(cut_dia)
            text.transform = Transform(frustrum_repos) @ text.transform
        text_atts = {'style':str(inkex.Style(text_style)),
                     'x': '0',
                     'y': str(cone_height*unitFactor+font_height) }
        text = etree.SubElement(parent, 'text', text_atts)
        text.text = "%4.3f" %(base_dia)
        text.transform = Transform(frustrum_repos) @ text.transform
        
if __name__ == '__main__':
    SheetMetalConus().run()
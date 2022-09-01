#!/usr/bin/env python3
'''
Zoetrope maker.
- prints disk of given diameter and number of images around the outside.
Also includes a pulse trigger ring to trigger a strobe.
- Width and phase of the pulse can be defined.
Prints a distorted and undistorted image reference sizes
-  for use in a paint program to distort the source inages to fit onto the Disk.

Neon22 - github 2016
MIT license
'''

import inkex
from lxml import etree
from math import cos, sin, radians, pi

__version__ = '0.2'

def point_on_circle(radius, angle):
    " return xy coord of the point at distance radius from origin at angle "
    x = radius * cos(angle)
    y = radius * sin(angle)
    return (x, y)

def draw_SVG_circle(parent, r, cx, cy, name, style):
    " structre an SVG circle entity under parent "
    circ_attribs = {'style': str(inkex.Style(style)),
                    'cx': str(cx), 'cy': str(cy), 
                    'r': str(r),
                    inkex.addNS('label','inkscape'): name}
    circle = etree.SubElement(parent, inkex.addNS('circle','svg'), circ_attribs )

Black = '#000000'

class Zoetrope(inkex.EffectExtension): 
    
    def add_arguments(self, pars):
        pars.add_argument("-u", "--units", default='mm', help="Units this dialog is using")
        pars.add_argument("-d", "--diameter", type=float, default=1.0, help="Diameter of disk")
        pars.add_argument("-n", "--divisions", type=int, default=24, help="Number of divisions")
        pars.add_argument("-i", "--height", type=float, default=1.0, help="Image height")
        pars.add_argument("-t", "--trigger", type=inkex.Boolean, default=False, help="Trigger")
        pars.add_argument("-q", "--triggerradius", type=float, default=1.0, help="Height of trigger line")
        pars.add_argument("-e", "--thick", type=float, default=1.0, help="Thickness of trigger line")
        pars.add_argument("-r", "--ratio", type=float, default=0.5, help="Ratio of trigger pulse")
        pars.add_argument("-p", "--phase", type=float, default=0, help="Delay of trigger pulse")
        pars.add_argument("-w", "--stroke_width", type=float, default=0.1, help="Line thickness")
        pars.add_argument("-m", "--template", type=inkex.Boolean,  default=False, help="Show Image Distortion template")
        pars.add_argument("-k", "--dpi", type=int, default=300, help="To calculate useful image size")
        pars.add_argument("--active-tab", default='', help="Active tab. Not used now.")
 
    def calc_unit_factor(self):
        """ return the scale factor for all dimension conversions.
            - Everything in inkscape is expected to be in 90dpi pixel units
        """
        unit_factor = self.svg.unittouu(str(1.0) + self.options.units)
        return unit_factor

    def polar_to_cartesian(self, cx, cy, radius, angle):
        " So we can make arcs in the 'A' svg syntax. "
        angle_radians = radians(angle)
        return (cx + (radius * cos(angle_radians)),
                cy + (radius * sin(angle_radians)))
                
    def build_arc(self, x,y, start_angle, end_angle, radius, reverse=True):
        " Make a filled arc "
        # Not using internal arc rep - instead construct path A in svg style directly
        # so we can append lines to make single path
        start = self.polar_to_cartesian(x, y, radius, end_angle)
        end = self.polar_to_cartesian(x, y, radius, start_angle)
        arc_flag = 0 if reverse else 1
        sweep = 0 if (end_angle-start_angle) <=180 else 1
        path = 'M %s,%s' % (start[0], start[1])
        path += " A %s,%s 0 %d %d %s %s" % (radius, radius, sweep, arc_flag, end[0], end[1])
        return path
    
    def build_trigger_arc(self, angle, radius1, radius2):
        """ return path 
            - using -ve angles to get pulse on CCW side of division line
        """
        path = self.build_arc(0,0, -angle, 0, radius1)
        # shorten and reverse second arc to connect
        path += " L"+self.build_arc(0,0, 0, -angle, radius2, False)[1:]
        path += " Z" # close
        return path
        
        
        
### -------------------------------------------------------------------
### This is the main function and is called when the extension is run.
    
    def effect(self):
        """ Calculate Zoetrope from inputs.
            - Make gropups for each drawn entity type. 
            - add explanatory text
            - Show trigger pulse ring, distortion and image templates
        """
        # convert import options
        unit_factor = self.calc_unit_factor()
        path_stroke_width = self.options.stroke_width * unit_factor
        diameter = self.options.diameter * unit_factor
        divisions = self.options.divisions 
        image_height = self.options.height * unit_factor
        triggerradius = self.options.triggerradius * unit_factor
        thick = self.options.thick * unit_factor
        cross = diameter/50
        
        # This finds center of current view in inkscape
        t = 'translate(%s,%s)' % (self.svg.namedview.center[0], self.svg.namedview.center[1] )
        # Make a nice useful name
        g_attribs = { inkex.addNS('label','inkscape'): 'Zoetrope',
                      'transform': t,
                      'info':'N: '+str(divisions)+';' }
        # add the group to the document's current layer
        topgroup = etree.SubElement(self.svg.get_current_layer(), 'g', g_attribs )
        # Group for pulse triggers
        g_attr = { inkex.addNS('label','inkscape'): 'Pulse track'}
        pulsegroup = etree.SubElement(topgroup, 'g', g_attr )
        # Group for Labels
        t = 'translate(%s,%s)' % (0, diameter/1.9 )
        g_attr = { inkex.addNS('label','inkscape'): 'Label', 'transform': t }
        labelgroup = etree.SubElement(topgroup, 'g', g_attr )

        # Center cross
        line_style = { 'stroke': Black, 'fill': 'none', 'stroke-width': path_stroke_width }
        fill_style = { 'stroke': 'none', 'fill': Black, 'stroke-width': 'none' }
        d = 'M {0},0 L {1},0 M 0,{0} L 0,{1}'.format(-cross,cross)
        cross_attribs = { inkex.addNS('label','inkscape'): 'Center cross',
                          'style': str(inkex.Style(line_style)), 'd': d }
        cross_path = etree.SubElement(topgroup, inkex.addNS('path','svg'), cross_attribs )
        
        # Main Disk
        draw_SVG_circle(topgroup, diameter/2, 0, 0, 'outer_ring', line_style)
        draw_SVG_circle(topgroup, diameter/2-image_height, 0, 0, 'image_ring', line_style)
        # radials
        trigger_angle = (360.0/divisions) * self.options.ratio
        angle = 360.0/divisions
        angle_radians = radians(angle)
        arc_path = self.build_trigger_arc(trigger_angle, triggerradius, triggerradius + thick)
        for i in range(divisions):
            startpt = point_on_circle(cross*2, angle_radians*i)
            if self.options.trigger:
                endpt = point_on_circle(triggerradius, angle_radians*i)
            else:
                endpt = point_on_circle(diameter/2, angle_radians*i)
            path = "M%s,%s L%s,%s"%(startpt[0], startpt[1], endpt[0], endpt[1])
            radial_attr = {inkex.addNS('label','inkscape'): 'radial',
                           'style': str(inkex.Style(line_style)), 'd': path  }
            etree.SubElement(topgroup, inkex.addNS('path','svg'), radial_attr )
            # second part of radial line (and trigger ring) if needed
            if self.options.trigger:
                # radial lines
                startpt = point_on_circle(triggerradius + thick, angle_radians*i)
                endpt = point_on_circle(diameter/2, angle_radians*i)
                path = "M%s,%s L%s,%s"%(startpt[0], startpt[1], endpt[0], endpt[1])
                radial_attr = {inkex.addNS('label','inkscape'): 'radial',
                               'style': str(inkex.Style(line_style)), 'd': path  }
                etree.SubElement(topgroup, inkex.addNS('path','svg'), radial_attr )
                # add the arcs # CCW rotation
                arc_offset = angle*i - (angle-trigger_angle)*self.options.phase
                t = 'rotate(%s)' % (arc_offset) 
                attribs = { inkex.addNS('label','inkscape'): 'trigger',
                            'style': str(inkex.Style(fill_style)), 'd': arc_path , 'transform': t,}
                etree.SubElement(pulsegroup, inkex.addNS('path','svg'), attribs )
            # Add animation of bouncing ball
            # Add pale grid on each image so can draw directly on template
            
        #
        if self.options.trigger:
            draw_SVG_circle(pulsegroup, triggerradius, 0, 0, 'trigger_ring', line_style)
            draw_SVG_circle(pulsegroup, triggerradius + thick, 0, 0, 'trigger_ring', line_style)
        
        # text Label
        font_height = min(32, max( 8, int(diameter/50.0)))
        text_style = { 'font-size': str(font_height),
                       'font-family': 'sans-serif',
                       'text-anchor': 'middle',
                       'text-align': 'center',
                       'fill': Black }
        text_atts = {'style':str(inkex.Style(text_style)),
                     'x': '0', 'y': '0' }
        text = etree.SubElement(labelgroup, 'text', text_atts)
        text.text = "Zoetrope"
        text_atts = {'style':str(inkex.Style(text_style)),
                     'x': '0', 'y': str(font_height*1.2) }
        text = etree.SubElement(labelgroup, 'text', text_atts)
        text.text = "Diameter = %4.2f%s. Divisions = %d" % (self.options.diameter, self.options.units, divisions)
        text_atts = {'style':str(inkex.Style(text_style)),
                     'x': '0', 'y': str(font_height*2.4) }
        if self.options.trigger:
            text = etree.SubElement(labelgroup, 'text', text_atts)
            text.text = "Pulse Duty = %4.2f, Phase = %4.2f" % (self.options.ratio, self.options.phase)
        
        # Distortion pattern
        if self.options.template:
            # Group for Labels
            t = 'translate(%s,%s)' % (0, -image_height-font_height*5 )
            g_attr = { inkex.addNS('label','inkscape'): 'Template', 'transform': t }
            templategroup = etree.SubElement(topgroup, 'g', g_attr )
            # Draw template
            arc_path =  self.build_trigger_arc(angle, diameter/2, diameter/2-image_height)
            t = 'rotate(%s)' % (-90+angle/2)
            attribs = { inkex.addNS('label','inkscape'): 'distorted image',
                        'style': str(inkex.Style(line_style)), 'd': arc_path , 'transform': t}
            image = etree.SubElement(templategroup, inkex.addNS('path','svg'), attribs )
            # Draw Image info
            image_width = pi*diameter/divisions
            ystart = -diameter/2.0 + image_height
            image_ratio = image_width / image_height
            text_atts = {'style':str(inkex.Style(text_style)),
                     'x': '0', 'y': str(ystart + font_height*2)  }
            text = etree.SubElement(templategroup, 'text', text_atts)
            text.text = "Aspect ratio=1:%4.2f" % (image_ratio)
            # template rect
            attr = {'x':str(-image_width*1.8), 'y':str(-diameter/2),
                    'width':str(image_width),
                    'height':str(image_height),
                    'style':str(inkex.Style(line_style))}
            template_sq = etree.SubElement(templategroup, 'rect', attr)
            # suggested sizes
            # image_height is in 90dpi pixels
            dpi_factor = self.svg.unittouu('1in')/float(self.options.dpi)
            h = int(image_height / float(dpi_factor))
            w = int(h*image_ratio)
            text_atts = {'style':str(inkex.Style(text_style)),
                     'x': '0', 'y': str(ystart + font_height*3.2) }
            text = etree.SubElement(templategroup, 'text', text_atts)
            text.text = "At %d dpi. Image = %d x %d pixels" % (self.options.dpi, w, h)
            
if __name__ == '__main__':       
    Zoetrope().run()
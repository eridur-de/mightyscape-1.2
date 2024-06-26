#!/usr/bin/env python3
'''
Copyright (C) 2017 Artem Synytsyn a.synytsyn@gmail.com

#TODO: Code cleaning and refactoring

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
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''

import inkex
from lxml import etree
from math import *

class KnobScale(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        # General settings
        pars.add_argument("--x", type=float, default=0.0, help="Center X")
        pars.add_argument("--y", type=float, default=0.0, help="Center Y")
        pars.add_argument("--radius", type=float, default=100.0, help="Knob radius")
        pars.add_argument("--linewidth", type=float, default=1)
        pars.add_argument("--angle", type=float, default=260.0, help="Angle of the knob scale in degrees")
        pars.add_argument("--angle_shifting", type=float, default=0.0, help="Angle shifting")
        pars.add_argument("--draw_arc", type=inkex.Boolean, default='True')
        pars.add_argument("--draw_centering_circle", type=inkex.Boolean, default='False')
        pars.add_argument("--logarithmic_scale", type=inkex.Boolean, default='False', help="")
        pars.add_argument("--invert", type=inkex.Boolean, default='False', help="")
        pars.add_argument("-u", "--units", default="px", help="units to measure size of knob")

        # Tick settings
        pars.add_argument("--n_ticks", type=int, default=5)
        pars.add_argument("--ticksize", type=float, default=10)
        pars.add_argument("--n_subticks", type=int, default=10)
        pars.add_argument("--subticksize", type=float, default=5)
        pars.add_argument("--style", default='marks_outwards', help="Style of marks")
        
        # Label settings
        pars.add_argument("--labels_enabled", type=inkex.Boolean, default='False')
        pars.add_argument("--rounding_level", type=int, default=0)
        pars.add_argument("--text_size", type=float, default=1)
        pars.add_argument("--text_offset", type=float, default=20)
        pars.add_argument("--start_value", type=float, default=0)
        pars.add_argument("--stop_value", type=float, default=10)
        # Dummy
        pars.add_argument("--tab")

    def draw_text(self, textvalue, radius, angular_position, text_size, parent):
        # Create text element
        text = etree.Element(inkex.addNS('text','svg'))
        text.text = textvalue
        # Set text position to center of document.
        text.set('x', str(self.x_offset + radius*cos(angular_position)))
        text.set('y', str(self.y_offset + radius*sin(angular_position) + text_size/2))

        # Center text horizontally with CSS style.
        style = {
                'text-align' : 'center',
                 'text-anchor': 'middle',
                 'alignment-baseline' : 'central',
                 'font-size' : str(text_size)
                 }

        text.set('style', str(inkex.Style(style)))
        parent.append(text)
    def draw_knob_arc(self, radius, parent, angle, angle_shifting, transform='' ):

        start_point_angle = angle_shifting + (angle - pi)/2.0
        end_point_angle = pi - start_point_angle + angle_shifting*2

        style = {   'stroke'        : '#000000',
                    'stroke-width'  : str(self.options.linewidth),
                    'fill'          : 'none'            }
        ell_attribs = {'style': str(inkex.Style(style)),
            inkex.addNS('cx','sodipodi')        :str(self.x_offset),
            inkex.addNS('cy','sodipodi')        :str(self.y_offset),
            inkex.addNS('rx','sodipodi')        :str(radius),
            inkex.addNS('ry','sodipodi')        :str(radius),
            inkex.addNS('start','sodipodi')     :str(end_point_angle),
            inkex.addNS('end','sodipodi')       :str(start_point_angle),
            inkex.addNS('open','sodipodi')      :'true',    #all ellipse sectors we will draw are open
            inkex.addNS('type','sodipodi')      :'arc',
            'transform'                         :transform

                }
        ell = etree.SubElement(parent, inkex.addNS('path','svg'), ell_attribs )

    def draw_centering_circle(self, radius, parent):

        style = {   'stroke'        : '#000000',
                    'stroke-width'  : '1',
                    'fill'          : 'none'            }
        ell_attribs = {'style':str(inkex.Style(style)),
            inkex.addNS('cx','sodipodi')        :str(self.x_offset),
            inkex.addNS('cy','sodipodi')        :str(self.y_offset),
            inkex.addNS('rx','sodipodi')        :str(radius),
            inkex.addNS('ry','sodipodi')        :str(radius),
            inkex.addNS('type','sodipodi')      :'arc'
            }
        ell = etree.SubElement(parent, inkex.addNS('path','svg'), ell_attribs )

    def draw_circle_mark(self, x_offset, y_offset, radius, mark_angle, mark_length, parent):

        cx = x_offset + radius*cos(mark_angle)
        cy = y_offset + radius*sin(mark_angle)
        r = mark_length / 2.0

        style = {
                'stroke': '#000000',
                'stroke-width':'0',
                'fill': '#000000'
                }

        circ_attribs = {
                'style':str(inkex.Style(style)),
                'cx':str(cx),
                'cy':str(cy),
                'r':str(r)
                }
        circle = etree.SubElement(parent, inkex.addNS('circle','svg'), circ_attribs )

    def draw_knob_line_mark(self, x_offset, y_offset, radius, mark_angle, mark_length, parent):
        x1 = x_offset + radius*cos(mark_angle)
        y1 = y_offset + radius*sin(mark_angle)
        x2 = x_offset + (radius + mark_length)*cos(mark_angle)
        y2 = y_offset + (radius + mark_length)*sin(mark_angle)

        line_style   = { 'stroke': '#000000',
                         'stroke-width': str(self.options.linewidth),
                         'fill': 'none'
                       }

        line_attribs = {'style' : str(inkex.Style(line_style)),
                        inkex.addNS('label','inkscape') : "none",
                        'd' : 'M '+str(x1) +',' +
                        str(y1) +' L '+str(x2)
                        +','+str(y2) }

        line = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )

    def draw_tick(self, radius, mark_angle, mark_size, parent):
        if (self.options.style == 'marks_inwards') or (self.options.style == 'marks_outwards'):
            self.draw_knob_line_mark(self.x_offset, self.y_offset, radius, mark_angle, mark_size, parent)
        elif self.options.style == 'marks_circles':
            self.draw_circle_mark(self.x_offset, self.y_offset, radius, mark_angle, mark_size, parent)

    def effect(self):
        parent = self.svg.get_current_layer()
        radius = self.svg.unittouu(str(self.options.radius) + self.options.units)
        self.x_offset = self.svg.unittouu(str(self.options.x) + self.options.units)
        self.y_offset = self.svg.unittouu(str(self.options.y) + self.options.units)
        angle = self.options.angle*pi/180.0
        angle_shifting = self.options.angle_shifting*pi/180.0
        n_ticks = self.options.n_ticks
        n_subticks = self.options.n_subticks
        is_outer = True
        if self.options.style == 'marks_inwards':
            is_outer = False

        tick_length = self.svg.unittouu(str(self.options.ticksize) + self.options.units)
        subtick_length = self.svg.unittouu(str(self.options.subticksize) + self.options.units)
        arc_radius = radius


        # Labeling settings
        if self.options.invert is True:
            end_num = self.options.start_value
            start_num = self.options.stop_value    
        else:
            start_num = self.options.start_value
            end_num = self.options.stop_value
        text_spacing = self.svg.unittouu(str(self.options.text_offset) + self.options.units)
        text_size = self.svg.unittouu(str(self.options.text_size) + self.options.units)

        if not is_outer:
            subtick_radius = radius + tick_length - subtick_length
            arc_radius = radius + tick_length
        else:
            subtick_radius = radius
            arc_radius = radius

        if self.options.draw_arc:
            self.draw_knob_arc(arc_radius, parent, angle, angle_shifting)

        if self.options.draw_centering_circle:
            self.draw_centering_circle(arc_radius + tick_length + text_size + text_spacing, parent)

        if self.options.logarithmic_scale:
            start_ticks_angle = 1.5*pi - 0.5*angle + angle_shifting
            for tick in range(n_ticks):
                self.draw_tick(radius, start_ticks_angle + angle*log(tick+1)/log(n_ticks),
                                    tick_length, parent)

                if self.options.labels_enabled:
                    if self.options.rounding_level > 0:
                        tick_text = str(round(start_num +
                            float(tick) * (end_num - start_num) / (n_ticks - 1),
                            self.options.rounding_level))
                    else:
                        tick_text = str(int(start_num + float(tick) * (end_num - start_num) / (n_ticks - 1)))

                    self.draw_text(tick_text, radius + tick_length + text_spacing,
                            start_ticks_angle + angle*log(tick+1)/log(n_ticks),
                            text_size,
                            parent)

                if tick == (n_ticks - 1):
                    break
                    
                for subtick in range(n_subticks):
                    self.draw_tick(subtick_radius, start_ticks_angle + angle*log(tick+1+(subtick+1)/(n_subticks+1))/log(n_ticks), 
                                 subtick_length, parent)        
        else:
            ticks_delta = angle / (n_ticks - 1)
            start_ticks_angle = 1.5*pi - 0.5*angle + angle_shifting

            for tick in range(n_ticks):
                self.draw_tick(radius, start_ticks_angle + ticks_delta*tick,
                                    tick_length, parent)

                if self.options.labels_enabled:
                    if self.options.rounding_level > 0:
                        tick_text = str(round(start_num +
                            float(tick) * (end_num - start_num) / (n_ticks - 1),
                            self.options.rounding_level))
                    else:
                        tick_text = str(int(start_num + float(tick) * (end_num - start_num) / (n_ticks - 1)))

                    self.draw_text(tick_text, radius + tick_length + text_spacing,
                            start_ticks_angle + ticks_delta*tick,
                            text_size,
                            parent)

                if tick == (n_ticks - 1):
                    break

                subticks_delta = ticks_delta / (n_subticks + 1)
                subtick_start_angle = start_ticks_angle + ticks_delta*tick + subticks_delta
                for subtick in range(n_subticks):
                    self.draw_tick(subtick_radius, subtick_start_angle + subticks_delta*subtick,
                                    subtick_length, parent)

if __name__ == '__main__':
    e = KnobScale().run()
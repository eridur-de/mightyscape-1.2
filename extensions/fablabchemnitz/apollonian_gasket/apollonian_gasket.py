#!/usr/bin/env python3

import inkex
import apolloniangasket_func
from lxml import etree

__version__ = '0.0'

def cplxs2pts(zs):
    tt = []
    for z in zs:
        tt.extend([z.real,z.imag])
    return tt

def draw_SVG_circle(parent, r, cx, cy, name):
    " structure an SVG circle entity under parent "
    circ_attribs = { 'cx': str(cx), 'cy': str(cy), 
                    'r': str(r),
                    inkex.addNS('label','inkscape'): name}
    circle = etree.SubElement(parent, inkex.addNS('circle','svg'), circ_attribs)

def draw_SVG_circleAsPath(parent, r, cx, cy, name):
    circ_attribs = {
        "d": "M {:0.6f}, {:0.6f} a {:0.6f},{:0.6f} 0 1,0 {:0.6f},0 a {:0.6f},{:0.6f} 0 1,0 {:0.6f},0".format(
            cx - r, cy, r, r, 2*r, r, r, -2*r),
        inkex.addNS('label','inkscape'): name}
    circle = etree.SubElement(parent, inkex.addNS('path','svg'), circ_attribs)

class Gasket(inkex.EffectExtension): # choose a better name
    
    def add_arguments(self, pars):
        pars.add_argument("--active_tab")
        pars.add_argument("--depth",type=int, default=3)
        pars.add_argument("--c1", type=float, default=2.0)
        pars.add_argument("--c2", type=float, default=3.0)
        pars.add_argument("--c3", type=float, default=3.0)
        pars.add_argument("--shrink", type=inkex.Boolean, default=True)
        pars.add_argument("--as_paths", type=inkex.Boolean, default=True)
              
    def calc_unit_factor(self):
        unit_factor = self.svg.unittouu(str(1.0) + self.options.units)
        return unit_factor

### -------------------------------------------------------------------
### Main function and is called when the extension is run.
    
    def effect(self):

        #set up path styles
        path_stroke = '#DD0000' # take color from tab3
        path_fill   = 'none'     # no fill - just a line
        path_stroke_width  = self.svg.unittouu(str(0.1) + "mm")
        page_id = self.options.active_tab # sometimes wrong the very first time
        
        style_curve = { 'stroke': path_stroke,
                 'fill': 'none',
                 'stroke-width': path_stroke_width }

        # This finds center of current view in inkscape
        t = 'translate(%s,%s)' % (self.svg.namedview.center[0], self.svg.namedview.center[1])
        
        # add a group to the document's current layer
        #all the circles inherit style from this group
        g_attribs = { inkex.addNS('label','inkscape'): 'zengon' + "_%d"%(self.options.depth),
                      inkex.addNS('transform-center-x','inkscape'): str(0),
                      inkex.addNS('transform-center-y','inkscape'): str(0),
                      'transform': t,
                      'style' : str(inkex.Style((style_curve))),
                      'info':'N: '}
        topgroup = etree.SubElement(self.svg.get_current_layer(), 'g', g_attribs)
           
        circles = apolloniangasket_func.main(c1=self.options.c1,
                         c2=self.options.c2,
                         c3=self.options.c3,
                         depth=self.options.depth)
        
        #shrink the circles so they don't touch
        #useful for laser cutting
        
        if self.options.shrink:
            circles = circles[1:]
            for cc in circles:
                cc.r = abs(cc.r)
                if cc.r >.5:
                    cc.r -= .1
                else:
                    cc.r *= .9
                
        scale_factor = 200
        for c in circles:  
            cx, cy, r = c.m.real, c.m.imag, abs(c.r)
            
            #rescale and add circle to document
            cx, cy, r  = scale_factor * cx , scale_factor * cy, scale_factor * r
            if self.options.as_paths is False:
                draw_SVG_circle(topgroup, r, cx, cy, 'apollian')
            else:
                draw_SVG_circleAsPath(topgroup, r, cx, cy, 'apollian')                    
                         
if __name__ == '__main__':
    Gasket().run()
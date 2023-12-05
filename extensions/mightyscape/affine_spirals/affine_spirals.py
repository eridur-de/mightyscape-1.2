#!/usr/bin/env python3

import inkex
from lxml import etree
from math import cos, sin, pi, exp
__version__ = '0.1'

def line(npts=40, x0=0, y0=0, delta=.5, sgn=1):
    #returns a list of points on a line (y = +/- x + c) starting at x0,y0
    return [ (x0 + delta*t, y0 + sgn*delta*t) for t in range(npts)]
    
def ff(v, ww=.25, ds=.4): 
    #covering map from R^2 ro punctured plane
    x,y = v
    r,u = exp(-ds*x), cos(pi*ww*y) + 1J*sin(pi*ww*y)
    return r*u
    
def mk_plugs(pts, noses):
	#returns a list of complex representing a plug type segment
    segs = [fit_plug(end_pts, noses) for end_pts in zip(pts,pts[1:]) ]
    tmp  = []
    for seg in segs:
        tmp.extend(seg) 
    return tmp
	
def fit_plug(ss, noses):
    a,b = ss
    rot = complex(b-a)
    pts = [0,.45,.4 + .15*1J, .6 + .15*1J, .55, 1]
    if noses is True:
        return [rot*z + a for z in pts]
    else:
        return ss

def pts2curve(cplxs):
    '''makes a polyline path element from a list of complex
    '''
    def cplx2pt(z):
        return (z.real,z.imag)
    
    scale = 200
    data = [cplx2pt( scale*z ) for z in cplxs ] 
    pth = [ '%.2f, %.2f '%z for z in data]
    return 'M '+ ''.join(pth) 
        
class AffineSpirals(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--num_lines", type=int, default=3)    
        pars.add_argument("--num_petals", type=int, default=3)   
        pars.add_argument("--shrink_ratio", type=float, default=3)
        pars.add_argument("--active-tab")
        pars.add_argument("--noses", type=inkex.Boolean, default=True)
             
    def calc_unit_factor(self):
        unit_factor = self.svg.unittouu(str(1.0) + self.options.units)
        return unit_factor

    def effect(self):
        path_stroke = '#DD0000' # take color from tab3
        path_fill   = 'none'     # no fill - just a line
        path_stroke_width  = 1. # can also be in form '0.6mm'
        page_id = self.options.active_tab # sometimes wrong the very first time
        
        styles = [ {'stroke':  path_stroke , 'fill': 'none', 'stroke-width': path_stroke_width},
                   {'stroke': 'none',  'fill': '#FFFF00', 'stroke-width': 0}]
        
        styles = [str(inkex.Style(x)) for x in styles]

        # This finds center of current view in inkscape
        t = 'translate(%s,%s)' % (self.svg.namedview.center[0], self.svg.namedview.center[1])
        
        # Make a nice useful name
        g_attribs = {inkex.addNS('label','inkscape'): 'koch',
                     inkex.addNS('transform-center-x','inkscape'): str(0),
                     inkex.addNS('transform-center-y','inkscape'): str(0),
                     'transform': t,
                     'style' : styles[1],
                     'info':'N: '+str(self.options.num_lines) }
        topgroup = etree.SubElement(self.svg.get_current_layer(), 'g', g_attribs)

        NN = 2*self.options.num_lines
        NP = self.options.num_petals
        SF = 2*self.options.shrink_ratio
        
        payload = []
        for y in range(-NP,NP):    
            mpts = [ff(z,ww=1./NP, ds=SF) for z in line(npts=NN, y0=y)]
            payload.append(mk_plugs(mpts, self.options.noses))
            mpts = [ff(z,ww=1./NP, ds=SF) for z in line(npts=NN, y0=y,sgn=-1 )]
            payload.append(mk_plugs(mpts, self.options.noses))
        
        payload = [pts2curve(cc) for cc in payload]
        payload = ' '.join(payload)
            
        curve_attribs = { 'style': styles[0], 'd': payload}
        etree.SubElement(topgroup, inkex.addNS('path','svg'), curve_attribs)

if __name__ == '__main__':
    AffineSpirals().run()
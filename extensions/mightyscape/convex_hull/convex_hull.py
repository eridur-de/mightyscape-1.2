#!/usr/bin/env python3

import inkex
import sys
import numpy as n
from inkex import PathElement
from inkex.paths import CubicSuperPath, Path
from inkex.transforms import Transform
from lxml import etree

link = lambda a,b: n.concatenate((a,b[1:]))
edge = lambda a,b: n.concatenate(([a],[b]))

'''

Convex Hull routine by Markus Kohler, found at https://gist.github.com/kohlerm/0337f7c64df42f21f96405b3f8e895f2, which itself is an implementation of:
https://github.com/flengyel/REST/blob/master/quickhull.py
Compute the convex hull of a set of points in the plane
Adapted from en.literateprograms.org/Quickhull_(Python,arrays)
Content available under MIT/X11 License at 
http://en.literateprograms.org/LiteratePrograms:Copyrights
Copyright (c) 2008 the authors listed in the page history
(see http://en.literateprograms.org/index.php?title=Quickhull_(Python,_arrays)&action=history)
Permission is hereby granted, free of charge, to any person obtaining a copy 
of this software and associated documentation files (the "Software"), to deal 
in the Software without restriction, including without limitation the rights 
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in 
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS 
IN THE SOFTWARE.
'''

def qhull(sample):
    def dome(sample,base): 
        sys.setrecursionlimit(20000) #dangerous stuff
        h, t = base
        dists = n.dot(sample-h, n.dot(((0,-1),(1,0)),(t-h)))
        outer = n.repeat(sample, dists>0, 0)

        if len(outer):
            pivot = sample[n.argmax(dists)]
            return link(dome(outer, edge(h, pivot)),
                        dome(outer, edge(pivot, t)))
        else:
            return base
    if len(sample) > 2:
    	axis = sample[:,0]
    	base = n.take(sample, [n.argmin(axis), n.argmax(axis)], 0)
    	return link(dome(sample, base),
                    dome(sample, base[::-1]))
    else:
        return sample
   
class ConvexHull(inkex.EffectExtension):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.paths = {}
        self.paths_clone_transform = {}
        
    def joinWithElement (self, element, path, makeGroup=False, cloneTransform=None):
        if (not path) or (len(path) == 0 ):
            return
        g = self.document.getroot()   
        # Now make a <path> element which contains the twist & is a child
        # of the new <g> element
        style = { 'stroke': '#000000', 'fill': 'none', 'stroke-width': str(self.svg.unittouu("1px")) }
        line_attribs = { 'style':str(inkex.Style(style)), 'd': path }
        if (cloneTransform != None ) and (cloneTransform != '' ):
            line_attribs['transform'] = cloneTransform
        etree.SubElement(g, inkex.addNS('path', 'svg' ), line_attribs) 

    def getControlPoints(self, element, n_array = None):
        if n_array == None:
            n_array = []
        if element.tag == inkex.addNS('path','svg'):
            #element.apply_transform()
            
            parent = element.getparent()
            if parent is not None:
                csp = Path(element.path.transform(parent.composed_transform())).to_arrays()
            else:
                csp = element.path.to_arrays()
            p = CubicSuperPath(csp)

            for subpath in p: # there may be several paths joined together (e.g. holes)
                for csp in subpath: # groups of three to handle control points.
                    # just the points no control points (handles)
                    n_array.append(csp[1][0])
                    n_array.append(csp[1][1])
        for child in element.getchildren():
            n_array += self.getControlPoints(child, n_array)
        return n_array

    def effect(self):
    
        if len(self.svg.selected) > 0:
            global output_elements, points
            
            n_array = []
            elements = self.svg.selection.filter(PathElement).values()
            if len(elements) > 0:
                for element in elements:
                    if element.tag == inkex.addNS('path','svg'):
                        n_array += self.getControlPoints(element, None)
    
                k = n.asarray(n_array)
                
                length = int(len(k)/2)
                c = k.reshape(length,2)
    
                hull_pts = qhull(c)
                
                pdata = ''
                for vertex in hull_pts:
                    if pdata == '':
                        pdata = 'M%f,%f' % (vertex[0], vertex[1] )
                    else:
                        pdata += 'L %f,%f' %  (vertex[0], vertex[1] )
                pdata += ' Z'        
                path = 'polygon'
                makeGroup = False
                paths_clone_transform = None
                self.joinWithElement(path, pdata, makeGroup, paths_clone_transform)
            else:
                inkex.errormsg('Selection seems not to contain svg:path elements. Maybe you have selected a group instead?')
                return
        else:
            inkex.errormsg('Please select some paths first.')
            return
            
if __name__ == '__main__':
    ConvexHull().run()
#!/usr/bin/env python3
'''
pathselection.py

Sunabe kazumichi 2009/9/29
http://dp48069596.lolipop.jp/

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

'''
import inkex, locale
import math
from lxml import etree
from inkex import paths
from inkex import bezier
from inkex import PathElement

# Set current system locale
locale.setlocale(locale.LC_ALL, '')

def cspseglength(sp1,sp2, tolerance = 0.001):
    bez = (sp1[1][:],sp1[2][:],sp2[0][:],sp2[1][:])    
    return bezier.bezierlength(bez, tolerance)    
def csplength(csp):
    lengths = []
    for sp in csp:
        lengths.append([])
        for i in range(1,len(sp)):
            l = cspseglength(sp[i-1],sp[i])
            lengths[-1].append(l)      
    return lengths

def roughBBox(path):
    xmin,xMax,ymin,yMax=path[0][0][0],path[0][0][0],path[0][0][1],path[0][0][1]
    for pathcomp in path:
        for pt in pathcomp:
               xmin=min(xmin,pt[0])
               xMax=max(xMax,pt[0])
               ymin=min(ymin,pt[1])
               yMax=max(yMax,pt[1])
               if xMax-xmin==0:
                   tn=0
               else :
                   tn=(yMax-ymin)/(xMax-xmin)
    return tn

class ColorizePathLengths(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("-s", "--selection", default=True, help="select path with length or slant")
        pars.add_argument("-1", "--len1", type=float, default=12)
        pars.add_argument("-2", "--len2", type=float, default=25)
        pars.add_argument("-3", "--len3", type=float, default=40)
        pars.add_argument("-4", "--len4", type=float, default=60)
        pars.add_argument("-5", "--len5", type=float, default=60)
        pars.add_argument("-6", "--hor", type=float, default=0.2)
        pars.add_argument("-7", "--ver", type=float, default=10)
  
    def effect(self):
        # loop over all selected paths
        if self.options.selection=="path_lengthselection":
            if len(self.svg.selected) > 0:
                for node in self.svg.selection.filter(PathElement).values():
                    if node.tag == inkex.addNS('path','svg'):  
                        l1,l2,l3,l4,l5=[],[],[],[],[]
                        p = paths.CubicSuperPath(inkex.paths.Path(node.get('d')))
                        slengths = csplength(p)
                        b = [slengths, p]
                        
                        # path length select
                        for x in range(0, len(slengths)):
                            if sum(b[0][x]) < self.options.len1:
                                l1.append(b[1][x])
                            if self.options.len2 > sum(b[0][x]) >= self.options.len1 :
                                l2.append(b[1][x])
                            if self.options.len3 > sum(b[0][x]) >= self.options.len2 :
                                l3.append(b[1][x])
                            if self.options.len4 > sum(b[0][x]) >= self.options.len3 :
                                l4.append(b[1][x])                        
                            if sum(b[0][x]) >= self.options.len4 :
                                l5.append(b[1][x])
    
                    # make path
                    lensel = [l1, l2, l3, l4, l5]
                    strlen = ['#FF0001', '#00FF02', '#AAFF03', '#87CEE4', '#000FF5']                        
                    for i, x in zip(strlen, lensel):
                            s = {'stroke-linejoin': 'miter', 'stroke-width': '0.5px', 
                                'stroke-opacity': '1.0', 'fill-opacity': '1.0', 
                                'stroke': i, 'stroke-linecap': 'butt', 'fill': 'none'}
                            attribs={'style':str(inkex.Style(s)),'d':str(paths.Path(paths.CubicSuperPath(x).to_path().to_arrays()))}
                            etree.SubElement(node.getparent(),inkex.addNS('path','svg'),attribs)
            else:
                self.msg('Please select some paths first.')
                return
            
        if self.options.selection=="path_slantselection":
            if len(self.svg.selected) > 0:
                for node in self.svg.selection.filter(PathElement).values():
                    if node.tag == inkex.addNS('path','svg'):  
                        hor1,ver2,slan3=[],[],[]
                        p = paths.CubicSuperPath(inkex.paths.Path(node.get('d')))
    
                        # path slant select
                        for i,x in enumerate(p):
                            tn=roughBBox(x)
                            if tn<self.options.hor:
                                hor1.append(p[i])
                            elif tn>self.options.ver:
                                ver2.append(p[i])
                            else:
                                slan3.append(p[i])
    
                    # make path
                    slnsel = [hor1, ver2, slan3]
                    strsln = ['#FF0001', '#00FF02', '#000FF5']                        
                    for i, x in zip(strsln, slnsel):
                            s = {'stroke-linejoin': 'miter', 'stroke-width': '0.5px', 
                                'stroke-opacity': '1.0', 'fill-opacity': '1.0', 
                                'stroke': i, 'stroke-linecap': 'butt', 'fill': 'none'}
                            attribs={'style':str(inkex.Style(s)),'d':str(paths.Path(paths.CubicSuperPath(x).to_path().to_arrays()))}
                            etree.SubElement(node.getparent(), inkex.addNS('path','svg'), attribs)
            else:
                self.msg('Please select some paths first.')
                return

if __name__ == '__main__':
    ColorizePathLengths().run()
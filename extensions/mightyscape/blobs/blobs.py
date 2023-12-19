#!/usr/bin/env python3

# These two lines are only needed if you don't put the script directly into
# the installation directory
import math
import inkex
import random
from lxml import etree

class Blobs(inkex.EffectExtension):
    """
Creates a random blob from a convex hull over n points.
The expected degree of the polygon is sqrt(n).  The corners
are blunted by the blunt parameter.  0 means sharp. 1 will
result in loopy splines.
    """
    def add_arguments(self, pars):
        pars.add_argument("--pgsizep", type=inkex.Boolean, default=True, help="Default rectangle to page size?")	
        pars.add_argument('--num',  type = int, default = 25, help = 'Number of random points to start with')
        pars.add_argument('--blunt',  type = float,  default = 0.3, help = 'Bluntness of corners. Should be < 1')
        pars.add_argument('--cave',  type = float, default = 0.0, help = 'Concavity. Less blobby and more splatty')
        pars.add_argument('--rx',  type = int,  default = 1000, help = 'Size of work area x')
        pars.add_argument('--ry',  type = int, default = 1000, help = 'Size of work area y')
        pars.add_argument('--sz',  type = float, default = 50., help = 'Size of a blob')
        pars.add_argument('--nb',  type = int, default = 10, help = 'Total number of blobs')
        pars.add_argument("--Nmain", default='top', help="Active tab.")

    def effect(self):
        global cave
        if self.options.pgsizep:
            svg = self.document.getroot()
            rx = int(self.svg.unittouu(svg.get('width')))
            ry = int(self.svg.unittouu(svg.attrib['height']))
        else:
            rx = self.options.rx
            ry = self.options.ry
        blunt = self.options.blunt
        cave = self.options.cave
        sz = self.options.sz
        nb = self.options.nb
        num = self.options.num

        # Get access to main SVG document element and get its dimensions.
        svg = self.document.getroot()

        # Create a new layer.
        layer = etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), 'Blob Layer')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')

        ctrs = [(random.randrange(rx) , random.randrange(ry))
                 for i in range(nb) ]
        for ctr in ctrs :
            points = [(random.gauss(ctr[0], sz) , random.gauss(ctr[1], sz))
                  for i in range(num) ]

            px = hull(points)
            pts = [points[px[i]] for i in range(len(px))]
        
            # Create path element
            path = etree.Element(inkex.addNS('path','svg'))
            path.set('style', str(inkex.Style({'fill':'#000000'})))
            pathstring = 'M ' + str(pts[0][0]) + ' ' + str(pts[0][1]) + ' '

            for j in range(len(pts)):
                k = (j+1) % len(pts)
                kk = (j+2) % len(pts)
                if j==0 :
                    (lasth, h1) = sHandles(pts[-1], pts[0], pts[1], blunt)
                (h2, hnext) = sHandles(pts[j], pts[k], pts[kk], blunt)
                pathstring += "C %f %f %f %f %f %f " % (h1[0], h1[1],
                                                        h2[0], h2[1],
                                                        pts[k][0], pts[k][1])
                h1 = hnext

            pathstring += 'Z'
            path.set('d', pathstring)
            layer.append(path)

def sHandles(pre, pt, post, blunt):
    '''I'm proud of this cute little construction for the
    spline handles. No doubt someone has thought of it before
    but, if not, its name is ACHC Andrew's Cute Handle
    Construction.  Note: no trig function calls.'''
    try :
        slope = (post[1] - pt[1]) / (post[0] - pt[0])
    except ZeroDivisionError :
        slope = math.copysign(1E30 , post[1] - pt[1])
    lenpre  = distance(pre, pt)
    lenpost = distance(pt, post)
    lenr = lenpre**2 / lenpost
    locx = math.copysign(lenr / math.sqrt(1. + slope**2) , post[0] - pt[0])
    mark = (pre[0] - locx , pre[1] - locx*slope)
    try :
        markslope = (pt[1] - mark[1]) / (pt[0] - mark[0])
    except ZeroDivisionError :
        markslope = math.copysign(1E30 , pt[1] - mark[1])
    prex = math.copysign(lenpre / math.sqrt(1. + markslope**2) ,
                          pt[0] - mark[0])
    hpre = (pt[0] - prex*blunt , pt[1] - prex*markslope*blunt)
    postx = prex*lenpost/lenpre
    hpost = (pt[0] + postx*blunt , pt[1] + postx*markslope*blunt)
    return (hpre, hpost)

"""Blunt=0.3 makes pleasingly round, mostly convex blobs. 0.4 makes them more
concave. 0.6 - 1.0  they're getting more and more pointy. 2.0 - 10. and they
grow appendages like hot-air balloons.  0.1 makes the corners pretty sharp.
0.0 and it's down to the convex hulls that are the basis of the blobs, that
is, polygons"""

def distance(a, b) :
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2 )

def hull(arg):
    """Convex hull by Graham scan."""
    xarr, yarr = zip(* arg)
    ymin = min(yarr)
    ind = findall(yarr, lambda y: y == ymin)
    if len(ind) > 1 :
        xshort = [xarr[j] for j in ind] 
        xmin = min(xshort)
        j = ind[xshort.index(xmin)]
        ind = j
    else :
        ind = ind[0]
    all = list(range(len(xarr)))
    del all[ind]
    all.sort(key=lambda i : (xarr[i] - xarr[ind]) /
             math.sqrt((xarr[i] - xarr[ind])**2 + (yarr[i] - yarr[ind])**2),
             reverse=True)
    if len(all) < 3 :
        all.insert(0, ind)
        return all
    ans = [ind]
    for i in all :
        if len(ans) == 1 :
            ans.append(i)
        else :
            while rightTurn(ans[-2], ans[-1], i, arg) :
                ans.pop()
            ans.append(i)

    return ans

def rightTurn(j, k, l, arg) :
    '''Cross product: Ax*By - Ay*Bx = Cz  '''
    ax = (arg[k][0] - arg[j][0])
    by = (arg[l][1] - arg[k][1])
    ay = (arg[k][1] - arg[j][1])
    bx = (arg[l][0] - arg[k][0])
    p = ax*by - ay*bx
    dot = ax*bx + ay*by
    cos = dot / math.sqrt((ax**2 + ay**2) * (bx**2 + by**2))
    crt = 1 - cave*2
    
    if p <= 0  :
        return cos < crt #We forgive right turns based on /cave/
    else :
        return False

def findall(a, f):
    r = []
    for x, j in zip(a, range(len(a))) :
        if f(x) :
            r.append(j)
    return r

if __name__ == '__main__':
    Blobs().run()
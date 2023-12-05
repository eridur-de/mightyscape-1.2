import numpy
import sys
from shaperrec import groups
from shaperrec import geometric
from shaperrec import internal

# *************************************************************
# debugging 
def void(*l):
    pass
def debug_on(*l):
    sys.stderr.write(' '.join(str(i) for i in l) +'\n') 
debug = void
#debug = debug_on

# *************************************************************
# Object manipulation functions

def toRemarkableShape( group ):
    """Test if PathGroup instance 'group' looks like a remarkable shape (ex: Rectangle).
    if so returns a new shape instance else returns group unchanged"""
    r = groups.Rectangle.isRectangle( group )
    if r : return r
    return group


def resetPrevNextSegment(segs):
    for i, seg in enumerate(segs[:-1]):
        s = segs[i+1]
        seg.next = s
        s.prev = seg           
    return segs


def fitSingleSegment(a):
    xmin, ymin, w, h = geometric.computeBox(a)
    inverse = w<h
    if inverse:
        a = numpy.roll(a, 1, axis=1)

    seg = regLin(a)
    if inverse:
        seg.inverse()
        #a = numpy.roll(a,1,axis=0)
    return seg
        
def regLin(a , returnOnlyPars=False):
    """perform a linear regression on 2dim array a. Creates a segment object in return """
    sumX = a[:, 0].sum()
    sumY = a[:, 1].sum()
    sumXY = (a[:, 1]*a[:, 0]).sum()
    a2 = a*a
    sumX2 = a2[:, 0].sum()
    sumY2 = a2[:, 1].sum()
    N = a.shape[0]

    pa = (N*sumXY - sumX*sumY)/ ( N*sumX2 - sumX*sumX)
    pb = (sumY - pa*sumX) /N
    if returnOnlyPars:
        return pa, -1, pb
    return internal.Segment(pa, -1, pb, a)


def smoothArray(a, n=2):
    count = numpy.zeros(a.shape)
    smootha = numpy.array(a)
    for i in range(n):
        count[i]=n+i+1
        count[-i-1] = n+i+1
    count[n:-n] = n+n+1
    #debug('smooth ', len(smooth[:-2]) [)
    for i in range(1, n+1):
        smootha[:-i] += a[i:]
        smootha[i:]  += a[:-i]
    return smootha/count

def buildTangents( points , averaged=True, isClosing=False):
    """build tangent vectors to the curve 'points'.
    if averaged==True, the tangents are averaged with their direct neighbours (use case : smoother tangents)"""
    tangents = numpy.zeros( (len(points), 2) )
    i=1
    tangents[:-i] += points[i:] - points[:-i] # i <- p_i+1 - p_i 
    tangents[i:]  += points[i:] - points[:-i] # i <- p_i - p_i-1
    if isClosing:
        tangents[0] += tangents[0] - tangents[-1]
        tangents[-1] += tangents[0] - tangents[-1]
    tangents *= 0.5
    if not isClosing:
        tangents[0] *=2
        tangents[-1] *=2


    ## debug('points ', points)
    ## debug('buildTangents --> ', tangents )
    
    if averaged:
        # average over neighbours
        avTan = numpy.array(tangents)
        avTan[:-1] += tangents[1:]
        avTan[1:]  += tangents[:-1]
        if isClosing:
            tangents[0]+=tangents[-1]
            tangents[1]+=tangents[0]
        avTan *= 1./3
        if not isClosing:
            avTan[0] *=1.5
            avTan[-1] *=1.5

    return avTan


def clusterAngles(array, dAng=0.15):
    """Cluster together consecutive angles with similar values (within 'dAng').
    array : flat array of angles
    returns [ ...,  (indi_0, indi_1),...] where each tuple are indices of cluster i
    """
    N = len(array)

    closebyAng = numpy.zeros( (N, 4), dtype=int)

    for i, a in enumerate(array):
        cb = closebyAng[i]
        cb[0] =i
        cb[2]=i
        cb[3]=i
        c=i-1
        # find number of angles within dAng in nearby positions
        while c>-1: # indices below i
            d=geometric.closeAngleAbs(a, array[c])
            if d>dAng:
                break
            cb[1]+=1                
            cb[2]=c
            c-=1
        c=i+1
        while c<N-1:# indices above i
            d=geometric.closeAngleAbs(a, array[c])
            if d>dAng:
                break
            cb[1]+=1                
            cb[3]=c
            c+=1
    closebyAng= closebyAng[numpy.argsort(closebyAng[:, 1]) ]

    clusteredPos = numpy.zeros(N, dtype=int)
    clusters = []
    for cb in reversed(closebyAng):
        if clusteredPos[cb[0]]==1:
            continue
        # try to build a cluster
        minI = cb[2]
        while clusteredPos[minI]==1:
            minI+=1
        maxI = cb[3]
        while clusteredPos[maxI]==1:
            maxI-=1
        for i in range(minI, maxI+1):
            clusteredPos[i] = 1
        clusters.append( (minI, maxI) )

    return clusters
        
    
                

def adjustAllAngles(paths):
    for p in paths:
        if p.isSegment() and p.newAngle is not None:
            p.adjustToNewAngle()
    # next translate to fit end points
    tr = numpy.zeros(2)
    for p in paths[1:]:
        if p.isSegment() and p.prev.isSegment():
            tr = p.prev.pointN - p.point1
        debug(' translating ', p, ' prev is', p.prev, '  ', tr, )
        p.translate(tr)

def adjustAllDistances(paths):
    for p in paths:
        if p.isSegment() and  p.newLength is not None:                
            p.adjustToNewDistance()
    # next translate to fit end points
    tr = numpy.zeros(2)
    for p in paths[1:]:
        if p.isSegment() and p.prev.isSegment():
            tr = p.prev.pointN - p.point1
        p.translate(tr)

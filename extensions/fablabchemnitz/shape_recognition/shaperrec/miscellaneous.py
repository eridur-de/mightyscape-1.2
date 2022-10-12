import sys
import inkex
from inkex import Path
import numpy
from shaperrec import manipulation
from lxml import etree



# *************************************************************
# debugging 
def void(*l):
    pass
def debug_on(*l):
    sys.stderr.write(' '.join(str(i) for i in l) +'\n') 
debug = void
#debug = debug_on

errwrite = void
    

# miscellaneous helper functions to sort

# merge consecutive segments with close angle

def mergeConsecutiveCloseAngles( segList , mangle =0.25 , q=0.5):

    def toMerge(seg):
        l=[seg]
        setattr(seg, 'merged', True)
        if hasattr(seg, "__next__") and seg.next.isSegment() :
            debug('merging segs ', seg.angle, ' with : ', seg.next.point1, seg.next.pointN, ' ang=', seg.next.angle)
            if geometric.deltaAngleAbs( seg.angle, seg.next.angle) < mangle:
                l += toMerge(seg.next)
        return l

    updatedSegs = []
    for i, seg in enumerate(segList[:-1]):
        if not seg.isSegment() :
            updatedSegs.append(seg)
            continue
        if  hasattr(seg, 'merged'):
            continue
        debug(i, ' inspect merge : ', seg.point1, '-', seg.pointN, seg.angle, ' q=', seg.quality())
        mList = toMerge(seg)
        debug('  --> tomerge ', len(mList))
        if len(mList)<2:
            delattr(seg, 'merged')
            updatedSegs.append(seg)
            continue
        points= numpy.concatenate( [p.points for p in mList] )
        newseg = fitSingleSegment(points)
        if newseg.quality()>q:
            delattr(seg, 'merged')
            updatedSegs.append(seg)
            continue
        for p in mList:
            setattr(seg, 'merged', True)
        newseg.sourcepoints = seg.sourcepoints
        debug('  --> post merge qual = ', newseg.quality(), seg.pointN, ' --> ', newseg.pointN, newseg.angle)
        newseg.prev = mList[0].prev
        newseg.next = mList[-1].__next__
        updatedSegs.append(newseg)
    if not hasattr(segList[-1], 'merged') : updatedSegs.append( segList[-1])
    return updatedSegs




def parametersFromPointAngle(point, angle):
    unitv = numpy.array([ numpy.cos(angle), numpy.sin(angle) ])
    ortangle = angle+numpy.pi/2
    normal = numpy.array([ numpy.cos(ortangle), numpy.sin(ortangle) ])
    genOffset = -normal.dot(point)
    a, b = normal
    return a, b, genOffset
    


def addPath(newList, refnode):
    """Add a node in the xml structure corresponding to the content of newList
    newList : list of Segment or Path
    refnode : xml node used as a reference, new point will be inserted a same level"""
    ele = etree.Element('{http://www.w3.org/2000/svg}path')
    errwrite("newList = " + str(newList) + "\n")
    ele.set('d', str(Path(newList)))
    refnode.xpath('..')[0].append(ele)
    return ele

def reformatList( listOfPaths):
    """ Returns a SVG paths list (same format as simplepath.parsePath) from a list of Path objects
     - Segments in paths are added in the new list
     - simple Path are retrieved from the original refSVGPathList and put in the new list (thus preserving original bezier curves)
    """
    newList = []
    first = True
    for  seg in listOfPaths:        
        newList += seg.asSVGCommand(first)
        first = False
    return newList


def clusterValues( values, relS=0.1 , refScaleAbs='range'  ):
    """form clusters of similar quantities from input 'values'.
    Clustered values are not necessarily contiguous in the input array. 
    Clusters size (that is max-min) is < relS*cluster_average """
    if len(values)==0:
        return []
    if len(values.shape)==1:
        sortedV = numpy.stack([ values, numpy.arange(len(values))], 1)
    else:
        # Assume value.shape = (N,2) and index are ok
        sortedV = values 
    sortedV = sortedV[ numpy.argsort(sortedV[:, 0]) ]

    sortedVV = sortedV[:, 0]
    refScale = sortedVV[-1]-sortedVV[0]
    #sortedVV += 2*min(sortedVV)) # shift to avoid numerical issues around 0

    #print sortedVV
    class Cluster:
        def __init__(self, delta, sum, indices):
            self.delta = delta
            self.sum = sum
            self.N=len(indices)
            self.indices = indices
        def size(self):
            return self.delta/refScale
        
        def combine(self, c):
            #print ' combine ', self.indices[0], c.indices[-1], ' -> ', sortedVV[c.indices[-1]] - sortedVV[self.indices[0]]
            newC = Cluster(sortedVV[c.indices[-1]] - sortedVV[self.indices[0]],
                           self.sum+c.sum,
                           self.indices+c.indices)
            return newC

        def originIndices(self):
            return tuple(int(sortedV[i][1]) for i in self.indices)

    def size_local(self):
        return self.delta / sum( sortedVV[i] for i in self.indices) *len(self.indices)
    def size_range(self):
        return self.delta/refScale
    def size_abs(self):
        return self.delta

    if refScaleAbs=='range':
        Cluster.size = size_range
    elif refScaleAbs=='local':
        Cluster.size = size_local
    elif refScaleAbs=='abs':
        Cluster.size = size_abs
        
    class ClusterPair:
        next=None
        prev=None
        def __init__(self, c1, c2 ):
            self.c1=c1
            self.c2=c2
            self.refresh()
        def refresh(self):
            self.potentialC =self.c1.combine(self.c2)
            self.size = self.potentialC.size()
        def setC1(self, c1):
            self.c1=c1
            self.refresh()
        def setC2(self, c2):
            self.c2=c2
            self.refresh()
            
    #ave = 0.5*(sortedVV[1:,0]+sortedV[:-1,0])
    #deltaR = (sortedV[1:,0]-sortedV[:-1,0])/ave

    cList = [Cluster(0, v, (i,)) for (i, v) in enumerate(sortedVV) ]
    cpList = [ ClusterPair( c, cList[i+1] ) for (i, c) in enumerate(cList[:-1]) ]
    manipulation.resetPrevNextSegment( cpList )

    #print cpList
    def reduceCL( cList ):
        if len(cList)<=1:
            return cList
        cp = min(cList, key=lambda cp:cp.size)    
        #print '==', cp.size , relS, cp.c1.indices , cp.c2.indices, cp.potentialC.indices

        while cp.size < relS:
            if hasattr(cp, "__next__"):
                cp.next.setC1(cp.potentialC)
                cp.next.prev = cp.prev
            if cp.prev:
                cp.prev.setC2(cp.potentialC)
                cp.prev.next = cp.__next__ if hasattr(cp, "__next__") else None
            cList.remove(cp)
            if len(cList)<2:
                break
            cp = min(cList, key=lambda cp:cp.size)    
        #print ' -----> ', [ (cp.c1.indices , cp.c2.indices) for cp in cList]
        return cList

    cpList = reduceCL(cpList)
    if len(cpList)==1:
        cp = cpList[0]
        if cp.potentialC.size()<relS:
            return [ cp.potentialC.originIndices() ]
    #print cpList
    if cpList==[]:
        return []
    finalCL = [ cp.c1.originIndices() for cp in cpList ]+[ cpList[-1].c2.originIndices() ]
    return finalCL


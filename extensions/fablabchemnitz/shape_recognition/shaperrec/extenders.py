import numpy
import sys
from shaperrec import manipulation

# *************************************************************
# debugging 
def void(*l):
    pass
def debug_on(*l):
    sys.stderr.write(' '.join(str(i) for i in l) +'\n') 
debug = void
#debug = debug_on

##**************************************
## 
class SegmentExtender:
    """Extend Segments part of a list of Path by aggregating points from neighbouring Path objects.

    There are 2 concrete subclasses for extending forward and backward (due to technical reasons).
    """

    def __init__(self, relD, fitQ):
        self.relD = relD
        self.fitQ = fitQ
        
    def nextPaths(self, seg):
        pL = []
        p = self.getNext(seg) # prev or next
        while p :
            if p.isSegment(): break
            if p.mergedObj is None: break
            pL.append(p)
            p = self.getNext(p)
        if pL==[]:
            return []
        return pL

    def extend(self, seg):
        nextPathL = self.nextPaths(seg)
        debug('extend ', self.extDir, seg, nextPathL, seg.length, len(nextPathL))
        if nextPathL==[]: return seg
        pointsToTest = numpy.concatenate( [p.points for p in nextPathL] )
        mergeD = seg.length*self.relD
        #print seg.point1 , seg.pointN,  pointsToTest
        pointsToFit, addedPoints = self.pointsToFit(seg, pointsToTest, mergeD)
        if len(pointsToFit)==0:
            return seg
        newseg = manipulation.fitSingleSegment(pointsToFit)
        if newseg.quality()>self.fitQ: # fit failed
            return seg
        debug( '  EXTENDING ! ', len(seg.points), len(addedPoints) )
        self.removePath(seg, newseg, nextPathL, addedPoints )
        newseg.points = pointsToFit
        seg.mergedObj= newseg
        newseg.sourcepoints = seg.sourcepoints

        return newseg

    @staticmethod
    def extendSegments(segmentList, relD=0.03, qual=0.5):
        """Perform Segment extension from list of Path segmentList
        returns the updated list of Path objects"""
        fwdExt = FwdExtender(relD, qual)
        bwdExt = BwdExtender(relD, qual)
        # tag all objects with an attribute pointing to the extended object
        for seg in segmentList:            
            seg.mergedObj = seg # by default the extended object is self
        # extend each segments, starting by the longest 
        for seg in sorted(segmentList, key = lambda s : s.length, reverse=True):
            if seg.isSegment():
                newseg=fwdExt.extend(seg)
                seg.mergedObj = bwdExt.extend(newseg)
        # the extension procedure has marked as None the mergedObj
        # which have been swallowed by an extension.
        #  filter them out :
        updatedSegs=[seg.mergedObj for seg in segmentList if seg.mergedObj]
        return updatedSegs


class FwdExtender(SegmentExtender):
    extDir='Fwd'
    def getNext(self, seg):
        return seg.__next__ if hasattr(seg, "__next__") else None
    def pointsToFit(self, seg, pointsToTest, mergeD):
        distancesToLine =abs(seg.a*pointsToTest[:, 0]+seg.b*pointsToTest[:, 1]+seg.c)        
        goodInd=len(pointsToTest)
        for i, d in reversed(list(enumerate(distancesToLine))):
            if d<mergeD: goodInd=i;break
        addedPoints = pointsToTest[:len(pointsToTest-goodInd)]
        #debug( ' ++ pointsToFit ' , mergeD, i ,len(pointsToTest), addedPoints , seg.points )
        return  numpy.concatenate([seg.points, addedPoints]), addedPoints
    def removePath(self, seg, newseg, nextPathL, addedPoints):
        npoints = len(addedPoints)
        acc=0
        newseg.prev = seg.prev
        for p in nextPathL:
            if (acc+len(p.points))<=npoints:
                p.mergedObj = None
                acc += len(p.points)
            else:
                newseg.next = p
                p.points = p.points[:(npoints-acc-len(p.points))]
                break

class BwdExtender(SegmentExtender):
    extDir='Bwd'
    def getNext(self, seg):
        return seg.prev
    def pointsToFit(self, seg, pointsToTest,  mergeD):
        #  TODO: shouldn't the distances be sorted cclosest to furthest
        distancesToLine =abs(seg.a*pointsToTest[:, 0]+seg.b*pointsToTest[:, 1]+seg.c)
        goodInd=len(pointsToTest)        
        for i, d in enumerate(distancesToLine):
            if d<mergeD: goodInd=i; break
        addedPoints = pointsToTest[goodInd:]
        #debug( ' ++ pointsToFit ' , mergeD, i ,len(pointsToTest), addedPoints , seg.points )
        return  numpy.concatenate([addedPoints, seg.points]), addedPoints
    def removePath(self, seg, newseg, nextPathL, addedPoints):
        npoints = len(addedPoints)
        acc=0
        newseg.next = seg.__next__ if hasattr(seg, "__next__") else None            
        for p in reversed(nextPathL):
            if (acc+len(p.points))<=npoints:
                p.mergedObj = None
                acc += len(p.points)
            else:
                newseg.prev = p        
                p.points = p.points[(npoints-acc-len(p.points)):]                        
                break


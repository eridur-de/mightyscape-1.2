import numpy
import sys
from shaperrec import geometric
from shaperrec import miscellaneous

# *************************************************************
# debugging 
def void(*l):
    pass
def debug_on(*l):
    sys.stderr.write(' '.join(str(i) for i in l) +'\n') 
debug = void
#debug = debug_on

# *************************************************************
# Internal Objects
class Path(object):
    """Private representation of a sequence of points.
    A SVG node of type 'path' is splitted in several of these Path objects.
    """
    next = None # next Path in the sequence of path corresponding to a SVG node
    prev = None # previous Path in the sequence of path corresponding to a SVG node
    sourcepoints = None  # the full list of points from which this path is a subset

    normalv = None # normal vector to this Path 
    
    def __init__(self, points):
        """points an array of points """
        self.points = points
        self.init()

    def init(self):
        self.effectiveNPoints = len(self.points)
        if self.effectiveNPoints>1:
            self.length, self.univ = geometric.dirAndLength(self.points[0], self.points[-1])
        else:
            self.length, self.univ = 0, numpy.array([0, 0])
        if self.effectiveNPoints>0:
            self.pointN=self.points[-1]
            self.point1=self.points[0]
            
    def isSegment(self):
        return False

    def quality(self):
        return 1000        

    def dump(self):
        n = len(self.points)
        if n>0:
            return 'path at '+str(self.points[0])+ ' to '+ str(self.points[-1])+'    npoints=%d / %d (eff)'%(n, self.effectiveNPoints)
        else:
            return 'path Void !'

    def setNewLength(self, l):
        self.newLength = l
        
    def removeLastPoints(self, n):
        self.points = self.points[:-n]
        self.init()
    def removeFirstPoints(self, n):
        self.points = self.points[n:]
        self.init()

    def costheta(self, seg):
        return self.unitv.dot(seg.unitv)

    def translate(self, tr):
        """Translate this path by tr"""
        self.points = self.points + tr

    def asSVGCommand(self, firstP=False):
        svgCommands = []
        com = 'M' if firstP else 'L'
        for p in self.points:
            svgCommands.append( [com, [p[0], p[1]] ] )
            com='L'
        return svgCommands


    def setIntersectWithNext(self, next=None):
        pass

    def mergedWithNext(self, newPath=None):
        """ Returns the combination of self and self.next.
        sourcepoints has to be set
        """
        if newPath is None: newPath = Path( numpy.concatenate([self.points, self.next.points]) )

        newPath.sourcepoints = self.sourcepoints
        newPath.prev = self.prev
        if self.prev : newPath.prev.next = newPath
        newPath.next = self.next.__next__
        if newPath.__next__:
            newPath.next.prev = newPath
        return newPath
        
# *************************************************************
#     
class Segment(Path):
    """ A segment. Defined by its line equation ax+by+c=0 and the points from orignal paths
    it is ensured that a**2+b**2 = 1
    """
    QUALITYCUT = 0.9
    
    newAngle    = None # temporary angle set during the "parralelization" step
    newLength = None   # temporary lenght set during the "parralelization" step

    # Segment Builders
    @staticmethod
    def from2Points( p1, p2, refPoints = None):
        dirV = p2-p1
        center = 0.5*(p2+p1)
        return Segment.fromCenterAndDir(center, dirV, refPoints)

    @staticmethod
    def fromCenterAndDir( center, dirV, refPoints=None):
        b = dirV[0]
        a = -dirV[1]
        c = - (a*center[0]+b*center[1])

        if refPoints is None:
            refPoints = numpy.array([ center-0.5*dirV, center+0.5*dirV] )
        s = Segment( a, b, c,  refPoints)
        return s

    
    def __init__(self, a,b,c, points, doinit=True):
        """a,b,c: the line parameters.
        points : the array of 2D points represented by this Segment
        doinit : if true will compute additionnal parameters to this Segment (first/last points, unit vector,...)
        """
        self.a = a
        self.b = b
        self.c = c
        
        self.points = points
        d = numpy.sqrt(a**2+b**2)
        if d != 1. :
            self.a /= d
            self.b /= d
            self.c /= d

        if doinit :
            self.init()


    def init(self):
        a, b, c = self.a, self.b, self.c
        x, y = self.points[0]
        self.point1 = numpy.array( [ b*(x*b-y*a) - c*a, a*(y*a-x*b) - c*b ] )
        x, y = self.points[-1]
        self.pointN = numpy.array( [ b*(x*b-y*a) - c*a, a*(y*a-x*b) - c*b ] )
        uv = self.computeDirLength()
        self.distancesToLine =  self.computeDistancesToLine(self.points)
        self.normalv = numpy.array( [ a, b ])

        self.angle = numpy.arccos( uv[0] )*numpy.sign(uv[1] )


    def computeDirLength(self):
        """re-compute and set unit vector and length """
        self.length, uv = geometric.dirAndLength(self.pointN, self.point1)
        self.unitv = uv
        return uv

    def isSegment(self):
        return True

    def recomputeEndPoints(self):
        a, b, c = self.a, self.b, self.c
        x, y = self.points[0]
        self.point1 = numpy.array( [ b*(x*b-y*a) - c*a, a*(y*a-x*b) - c*b ] )
        x, y = self.points[-1]
        
        self.pointN = numpy.array( [ b*(x*b-y*a) - c*a, a*(y*a-x*b) - c*b ] )

        self.length = numpy.sqrt( geometric.D2(self.pointN, self.point1) )

    def projectPoint(self, p):
        """ return the point projection of p onto this segment"""
        a, b, c = self.a, self.b, self.c
        x, y = p
        return numpy.array( [ b*(x*b-y*a) - c*a, a*(y*a-x*b) - c*b ] )        
        

    def intersect(self, seg):
        """Returns the intersection of this line with the line seg"""
        nu, nv = self.normalv, seg.normalv
        u = numpy.array([[-self.c], [-seg.c]])
        doRotation = min(nu.min(), nv.min()) <1e-4
        if doRotation:
            # rotate to avoid numerical issues
            nu = numpy.array(geometric.rotMat.dot(nu))[0]
            nv = numpy.array(geometric.rotMat.dot(nv))[0]
        m = numpy.matrix( (nu, nv) )        

        i =  (m**-1).dot(u) 
        i=numpy.array( i).swapaxes(0, 1)[0]
        debug('  intersection ', nu, nv, self.angle, seg.angle, ' --> ', i)
        if doRotation:
            i = geometric.unrotMat.dot(i).A1
        debug('   ', i)
        
        
        return i

    def setIntersectWithNext(self, next=None):
        """Modify self such as self.pointN is the intersection with next segment """
        if next is None:
            next = self.__next__
        if next and next.isSegment():
            if abs(self.normalv.dot(next.unitv)) < 1e-3:
                return
            debug(' Intersect', self, next,  ' from ', self.point1, self.pointN, ' to ', next.point1, next.pointN,)
            inter = self.intersect(next)
            debug('  --> ', inter, '  d=', geometric.D(self.pointN, inter) )
            next.point1 = inter
            self.pointN = inter
            self.computeDirLength()
            next.computeDirLength()
            
    def computeDistancesToLine(self, points):
        """points: array of points.
        returns the array of distances to this segment"""
        return abs(self.a*points[:, 0]+self.b*points[:, 1]+self.c)


    def distanceTo(self, point):
        return abs(self.a*point[0]+self.b*point[1]+self.c)        

    def inverse(self):
        """swap all x and y values.  """
        def inv(v):
            v[0], v[1] = v[1], v[0]
        for v in [self.point1, self.pointN, self.unitv, self.normalv]:
            inv(v)

        self.points = numpy.roll(self.points, 1, axis=1)
        self.a, self.b = self.b, self.a
        self.angle = numpy.arccos( self.unitv[0] )*numpy.sign(self.unitv[1] )
        return

    def dumpShort(self):
        return 'seg  '+'  '+str(self.point1 )+'to '+str(self.pointN)+ ' npoints=%d | angle,offset=(%.2f,%.2f )'%(len(self.points), self.angle, self.c)+'  ', self.normalv

    def dump(self):
        v = self.variance()
        n = len(self.points)
        return 'seg  '+str(self.point1 )+' , '+str(self.pointN)+ '  v/l=%.2f / %.2f = %.2f  r*numpy.sqrt(n)=%.2f  npoints=%d | angle,offset=(%.2f,%.2f )'%(v, self.length, v/self.length, v/self.length*numpy.sqrt(n), n, self.angle, self.c)
        
    def variance(self):
        d = self.distancesToLine
        return numpy.sqrt( (d**2).sum()/len(d) )

    def quality(self):
        n = len(self.points)
        return min(self.variance()/self.length*numpy.sqrt(n), 1000)

    def formatedSegment(self, firstP=False):
        return self.asSVGCommand(firstP)
    
    def asSVGCommand(self, firstP=False):

        if firstP:            
            segment = [ ['M', [self.point1[0], self.point1[1] ] ],
                        ['L', [self.pointN[0], self.pointN[1] ] ]
                        ]
        else:
            segment = [ ['L', [self.pointN[0], self.pointN[1] ] ] ]
        #debug("Segment, format : ", segment)
        return segment
        
    def replaceInList(self, startPos, fullList):
        code0 = fullList[startPos][0]
        segment = [ [code0, [self.point1[0], self.point1[1] ] ],
                     ['L', [self.pointN[0], self.pointN[1] ] ]
                    ]
        l = fullList[:startPos]+segment+fullList[startPos+len(self.points):]
        return l




    def mergedWithNext(self, doRefit=True):
        """ Returns the combination of self and self.next.
        sourcepoints has to be set
        """
        spoints = numpy.concatenate([self.points, self.next.points])

        if doRefit:
            newSeg = fitSingleSegment(spoints)
        else:
            newSeg = Segment.fromCenterAndDir(geometric.barycenter(spoints), self.unitv, spoints)
        
        newSeg = Path.mergedWithNext(self, newSeg)
        return newSeg

    

    def center(self):
        return 0.5*(self.point1+self.pointN)

    def box(self):
        return geometric.computeBox(self.points)


    def translate(self, tr):
        """Translate this segment by tr """
        c = self.c -self.a*tr[0] -self.b*tr[1]
        self.c =c
        self.pointN = self.pointN+tr
        self.point1 = self.point1+tr
        self.points +=tr
        
    def adjustToNewAngle(self):        
        """reset all parameters so that self.angle is change to self.newAngle """

        self.a, self.b, self.c = miscellaneous.parametersFromPointAngle( 0.5*(self.point1+self.pointN), self.newAngle)

        #print 'adjustToNewAngle ', self, self.angle, self.newAngle
        self.angle = self.newAngle
        self.normalv = numpy.array( [ self.a, self.b ])
        self.unitv = numpy.array( [ self.b, -self.a ])
        if abs(self.angle) > numpy.pi/2 :
            if self.b > 0: self.unitv *= -1
        elif self.b<0 : self.unitv  *= -1

        self.point1 = self.projectPoint(self.point1) # reset point1 
        if not hasattr(self, "__next__") or not self.next.isSegment():
                # move the last point (no intersect with next)

                pN = self.projectPoint(self.pointN)
                dirN = pN - self.point1                
                lN = geometric.length(pN, self.point1)
                self.pointN = dirN/lN*self.length + self.point1
                #print ' ... adjusting last seg angle ',p.dump() , ' normalv=', p.normalv, 'unitv ', p.unitv
        else:
            self.setIntersectWithNext()

    def adjustToNewDistance(self):
        self.pointN = self.newLength* self.unitv + self.point1
        self.length = self.newLength

    def tempLength(self):
        if self.newLength : return self.newLength
        else : return self.length

    def tempAngle(self):
        if self.newAngle: return self.newAngle
        return self.angle
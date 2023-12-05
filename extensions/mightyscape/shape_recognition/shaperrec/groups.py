import numpy
import sys
import inkex
from lxml import etree
from shaperrec import geometric
from shaperrec import miscellaneous
from shaperrec import internal
from shaperrec import manipulation

# *************************************************************
# debugging 
def void(*l):
    pass
def debug_on(*l):
    sys.stderr.write(' '.join(str(i) for i in l) +'\n') 
debug = void
#debug = debug_on

# *************************************************************
# *************************************************************
# Groups of Path
#
class PathGroup(object):
    """A group of Path representing one SVG node.
     - a list of Path
     - a list of SVG commands describe the full node (=SVG path element)
     - a reference to the inkscape node object
     
    """
    listOfPaths = []
    refSVGPathList = []
    isClosing = False
    refNode = None
    
    def __init__(self, listOfPaths, refSVGPathList, refNode=None, isClosing=False):
        self.refNode = refNode
        self.listOfPaths = listOfPaths
        self.refSVGPathList = refSVGPathList
        self.isClosing=isClosing
        
    def addToNode(self, node):
        newList = miscellaneous.reformatList( self.listOfPaths)        
        ele = miscellaneous.addPath( newList, node)
        debug("PathGroup ", newList)
        return ele

    def setNodeStyle(self, ele, node):
        style = node.get('style')
        cssClass = node.get('class')
        debug("style ", style)
        debug("class ", cssClass)
        if style == None and cssClass == None :
           style = 'fill:none; stroke:red; stroke-width:1'
        
        if not cssClass == None:
            ele.set('class', cssClass)
        if not style == None:
            ele.set('style', style)

    @staticmethod
    def toSegments(points, refSVGPathList, refNode, isClosing=False):
        """
        """
        segs = [ internal.Segment.from2Points(p, points[i+1], points[i:i+2] ) for (i, p) in enumerate(points[:-1]) ]
        manipulation.resetPrevNextSegment(segs)
        return PathGroup( segs, refSVGPathList, refNode, isClosing)

class TangentEnvelop(PathGroup):
    """Specialization where the Path objects are all Segments and represent tangents to a curve """
    def addToNode(self, node):
        newList = [ ]
        for s in self.listOfPaths:
            newList += s.asSVGCommand(firstP=True)
        debug("TangentEnvelop ", newList)
        ele = miscellaneous.addPath( newList, node)
        return ele

    def setNodeStyle(self, ele, node):
        style = node.get('style')+';marker-end:url(#Arrow1Lend)'
        ele.set('style', style)


class Circle(PathGroup):
    """Specialization where the list of Path objects
    is to be replaced by a Circle specified by a center and a radius.

    If an other radius 'rmax' is given than the object represents an ellipse.
    """
    isClosing= True
    def __init__(self, center, rad,  refNode=None, rmax=None, angle=0.):
        self.listOfPaths = []
        self.refNode = refNode
        self.center = numpy.array(center)
        self.radius = rad
        if rmax:
            self.type ='ellipse'
        else:
            self.type = 'circle'
        self.rmax = rmax
        self.angle = angle
        
    def addToNode(self, refnode):
        """Add a node in the xml structure corresponding to this rect
        refnode : xml node used as a reference, new point will be inserted a same level"""
        ele = etree.Element('{http://www.w3.org/2000/svg}'+self.type)

        ele.set('cx', str(self.center[0]))
        ele.set('cy', str(self.center[1]))
        if self.rmax:
            ele.set('ry', str(self.radius))
            ele.set('rx', str(self.rmax))
            ele.set('transform', 'rotate(%3.2f,%f,%f)'%(numpy.degrees(self.angle), self.center[0], self.center[1]))
        else:
            ele.set('r', str(self.radius))
        refnode.xpath('..')[0].append(ele)
        return ele


class Rectangle(PathGroup):
    """Specialization where the list of Path objects
    is to be replaced by a Rectangle specified by a center and size (w,h) and a rotation angle.

    """
    def __init__(self, center, size, angle, listOfPaths, refNode=None):
        self.listOfPaths = listOfPaths
        self.refNode = refNode
        self.center = center
        self.size = size
        self.bbox = size
        self.angle = angle
        pos = self.center - numpy.array( size )/2
        if angle != 0. :
            cosa = numpy.cos(angle)
            sina = numpy.sin(angle)            
            self.rotMat = numpy.matrix( [ [ cosa, sina], [-sina, cosa] ] )
            self.rotMatstr = 'matrix(%1.7f,%1.7f,%1.7f,%1.7f,0,0)'%(cosa, sina, -sina, cosa)


            #debug(' !!!!! Rotated rectangle !!', self.size, self.bbox,  ' angles ', a, self.angle ,' center',self.center)
        else :
            self.rotMatstr = None
        self.pos = pos
        debug(' !!!!! Rectangle !!', self.size, self.bbox,  ' angles ', self.angle, ' center', self.center)

    def addToNode(self, refnode):
        """Add a node in the xml structure corresponding to this rect
        refnode : xml node used as a reference, new point will be inserted a same level"""
        ele = etree.Element('{http://www.w3.org/2000/svg}rect')
        self.fill(ele)
        refnode.xpath('..')[0].append(ele)
        return ele
        
    def fill(self, ele):
        w, h = self.size
        ele.set('width', str(w))
        ele.set('height', str(h))
        w, h = self.bbox
        ele.set('x', str(self.pos[0]))
        ele.set('y', str(self.pos[1]))
        if self.rotMatstr:
            ele.set('transform', 'rotate(%3.2f,%f,%f)'%(numpy.degrees(self.angle), self.center[0], self.center[1]))
            #ele.set('transform', self.rotMatstr)       

    @staticmethod
    def isRectangle( pathGroup):
        """Check if the segments in pathGroups can form a rectangle.
        Returns a Rectangle or None"""
        #print 'xxxxxxxx isRectangle',pathGroups
        if isinstance(pathGroup, Circle ): return None
        segmentList = [p for p in pathGroup.listOfPaths if p.isSegment() ]#or p.effectiveNPoints >0]
        if len(segmentList) != 4:
            debug( 'rectangle Failed at length ', len(segmentList))
            return None
        a, b, c, d = segmentList

        if geometric.length(a.point1, d.pointN)> 0.2*(a.length+d.length)*0.5:
            debug('rectangle test failed closing ', geometric.length(a.point1, d.pointN), a.length, d.length)
            return None
        
        Aac, Abd = geometric.closeAngleAbs(a.angle, c.angle), geometric.closeAngleAbs(b.angle, d.angle)
        if  min(Aac, Abd) > 0.07 or max(Aac, Abd) >0.27 :
            debug( 'rectangle Failed at angles', Aac, Abd)
            return None
        notsimilarL = lambda d1, d2: abs(d1-d2)>0.20*min(d1, d2)

        pi, twopi = numpy.pi, 2*numpy.pi
        angles = numpy.array( [p.angle   for p in segmentList] )
        minAngleInd = numpy.argmin( numpy.minimum( abs(angles), abs( abs(angles)-pi), abs( abs(angles)-twopi) ) )
        rotAngle = angles[minAngleInd]
        width = (segmentList[minAngleInd].length + segmentList[(minAngleInd+2)%4].length)*0.5
        height = (segmentList[(minAngleInd+1)%4].length + segmentList[(minAngleInd+3)%4].length)*0.5
        # set rectangle center as the bbox center
        x, y, w, h = geometric.computeBox( numpy.concatenate( [ p.points for p in segmentList]) )
        r = Rectangle( numpy.array( [x+w/2, y+h/2]), (width, height), rotAngle, pathGroup.listOfPaths, pathGroup.refNode)
        
        debug( ' found a rectangle !! ', a.length, b.length, c.length, d.length )
        return r


class CurveGroup(PathGroup):
    """Specialization where the list of Path objects
    is to be replaced by a Rectangle specified by a center and size (w,h) and a rotation angle.

    """
    def __init__(self, center, size, angle, listOfPaths, refNode=None):
        self.listOfPaths = listOfPaths
        self.refNode = refNode
        self.center = center
        self.size = size
        self.bbox = size
        self.angle = angle
        pos = self.center - numpy.array( size )/2
        if angle != 0. :
            cosa = numpy.cos(angle)
            sina = numpy.sin(angle)            
            self.rotMat = numpy.matrix( [ [ cosa, sina], [-sina, cosa] ] )
            self.rotMatstr = 'matrix(%1.7f,%1.7f,%1.7f,%1.7f,0,0)'%(cosa, sina, -sina, cosa)


            #debug(' !!!!! Rotated rectangle !!', self.size, self.bbox,  ' angles ', a, self.angle ,' center',self.center)
        else :
            self.rotMatstr = None
        self.pos = pos
        debug(' !!!!! Rectangle !!', self.size, self.bbox,  ' angles ', self.angle, ' center', self.center)

    def addToNode(self, refnode):
        """Add a node in the xml structure corresponding to this rect
        refnode : xml node used as a reference, new point will be inserted a same level"""
        ele = etree.Element('{http://www.w3.org/2000/svg}rect')
        self.fill(ele)
        refnode.xpath('..')[0].append(ele)
        return ele
        
#    def fill(self, ele):
#        w, h = self.size
#        ele.set('width', str(w))
#        ele.set('height', str(h))
#        w, h = self.bbox
#        ele.set('x', str(self.pos[0]))
#        ele.set('y', str(self.pos[1]))
#        if self.rotMatstr:
#            ele.set('transform', 'rotate(%3.2f,%f,%f)'%(numpy.degrees(self.angle), self.center[0], self.center[1]))
#            #ele.set('transform', self.rotMatstr)       

    @staticmethod
    def isCurvedSegment( pathGroup):
        """Check if the segments in pathGroups can form a rectangle.
        Returns a Rectangle or None"""
        #print 'xxxxxxxx isRectangle',pathGroups
        if isinstance(pathGroup, Circle ): return None
        segmentList = [p for p in pathGroup.listOfPaths if p.isSegment() ]#or p.effectiveNPoints >0]
        if len(segmentList) != 4:
            debug( 'rectangle Failed at length ', len(segmentList))
            return None
        a, b, c, d = segmentList

        if geometric.length(a.point1, d.pointN)> 0.2*(a.length+d.length)*0.5:
            debug('rectangle test failed closing ', geometric.length(a.point1, d.pointN), a.length, d.length)
            return None
        
        Aac, Abd = geometric.closeAngleAbs(a.angle, c.angle), geometric.closeAngleAbs(b.angle, d.angle)
        if  min(Aac, Abd) > 0.07 or max(Aac, Abd) >0.27 :
            debug( 'rectangle Failed at angles', Aac, Abd)
            return None
        notsimilarL = lambda d1, d2: abs(d1-d2)>0.20*min(d1, d2)

        pi, twopi = numpy.pi, 2*numpy.pi
        angles = numpy.array( [p.angle   for p in segmentList] )
        minAngleInd = numpy.argmin( numpy.minimum( abs(angles), abs( abs(angles)-pi), abs( abs(angles)-twopi) ) )
        rotAngle = angles[minAngleInd]
        width = (segmentList[minAngleInd].length + segmentList[(minAngleInd+2)%4].length)*0.5
        height = (segmentList[(minAngleInd+1)%4].length + segmentList[(minAngleInd+3)%4].length)*0.5
        # set rectangle center as the bbox center
        x, y, w, h = geometric.computeBox( numpy.concatenate( [ p.points for p in segmentList]) )
        r = Rectangle( numpy.array( [x+w/2, y+h/2]), (width, height), rotAngle, pathGroup.listOfPaths, pathGroup.refNode)
        
        debug( ' found a rectangle !! ', a.length, b.length, c.length, d.length )
        return r

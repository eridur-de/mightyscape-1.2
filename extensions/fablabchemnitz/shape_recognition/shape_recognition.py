#!/usr/bin/env python
'''
Copyright (C) 2017 , Pierre-Antoine Delsart

This file is part of InkscapeShapeReco.

InkscapeShapeReco is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.
 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with InkscapeShapeReco; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA



Quick description:
This extension uses all selected path, ignoring all other selected objects.
It tries to regularize hand drawn paths BY :
 - evaluating if the path is a full circle or ellipse
 - else finding sequences of aligned points and replacing them by a simple segment.
 - changing the segments angles to the closest remarkable angle (pi/2, pi/3, pi/6, etc...)
 - eqalizing all segments lengths which are close to each other
 - replacing 4 segments paths by a rectangle object if this makes sens (giving the correct rotation to the rectangle). 

Requires numpy.

'''

import sys
sys.path.append('/usr/share/inkscape/extensions')
import inkex
import gettext
_ = gettext.gettext

# *************************************************************
# debugging 
def void(*l):
    pass
def debug_on(*l):
    sys.stderr.write(' '.join(str(i) for i in l) +'\n') 
debug = void
#debug = debug_on

from shaperrec import geometric
from shaperrec import internal
from shaperrec import groups
from shaperrec import manipulation
from shaperrec import extenders
from shaperrec import miscellaneous

import numpy
numpy.set_printoptions(precision=3)

class PreProcess():

    def removeSmallEdge(paths, wTot, hTot):
        """Remove small Path objects which stand between 2 Segments (or at the ends of the sequence).
        Small means the bbox of the path is less then 5% of the mean of the 2 segments."""
        if len(paths)<2:
            return
        def getdiag(points):
            xmin, ymin, w, h = geometric.computeBox(points)
            return numpy.sqrt(w**2+h**2), w, h
        removeSeg=[]
        def remove(p):
            removeSeg.append(p)
            if hasattr(p, "__next__") : p.next.prev = p.prev
            if p.prev: p.prev.next = p.__next__ if hasattr(p, "__next__") else None
            p.effectiveNPoints =0
            debug('      --> remove !', p, p.length, len(p.points))
        for p in paths:
            if len(p.points)==0 :
                remove(p)
                continue
            # select only path between 2 segments
            next, prev = p.__next__ if hasattr(p, "__next__") else None, p.prev
            if next is None: next = prev
            if prev is None: prev = next
            if not (False if next == None else next.isSegment()) or not (False if prev == None else prev.isSegment()) : continue
            #diag = getdiag(p.points)
            diag, w, h = getdiag(p.points)

            debug(p, p.pointN, ' removing edge  diag = ', diag, p.length,  '  l=', next.length+prev.length, 'totDim ', (wTot, hTot))
            debug( '    ---> ', prev, next)

            #t TODO: his needs to be parameterized
            # remove last or first very small in anycase
            doRemove = prev==next and (diag < 0.05*(wTot+hTot)*0.5 )
            if not doRemove:
                # check if this small
                isLarge = diag > (next.length+prev.length)*0.1  # check size relative to neighbour
                isLarge = isLarge or w > 0.2*wTot or h > 0.2*hTot # check size w.r.t total size
                
                # is it the small side of a long rectangle ?
                dd = prev.distanceTo(next.pointN)
                rect = abs(prev.unitv.dot(next.unitv))>0.98 and diag > dd*0.5
                doRemove = not( isLarge or rect )

            if doRemove:
                remove(p)

                if next != prev:
                    prev.setIntersectWithNext(next)
        debug('removed Segments ', removeSeg)
        for p in removeSeg:
            paths.remove(p)
    
    def prepareParrallelize( segs):
        """Group Segment by their angles (segments are grouped together if their deltAangle is within 0.15 rad)
        The 'newAngle' member of segments in a group are then set to the mean angle of the group (where angles are all
        considered in [-pi, pi])

        segs : list of segments
        """

        angles = numpy.array([s.angle for s in segs ])
        angles[numpy.where(angles<0)] += geometric._pi # we care about direction, not angle orientation
        clList = miscellaneous.clusterValues(angles, 0.30, refScaleAbs='abs')#was 15
        
        pi =  numpy.pi
        for cl in clList:
            anglecount = {}
            for angle in angles[list(cl)]:
            #	#angleDeg = int(angle * 360.0 / (2.0*pi))
            	if not angle in anglecount:
            		anglecount[angle] = 1
            	else:
            		anglecount[angle] += 1
		
            anglecount = {k: v for k, v in sorted(list(anglecount.items()), key=lambda item: item[1], reverse=True)}
            meanA = anglecount.popitem()[0]#.items()[1]#sorted(anglecount.items(), key = lambda kv:(kv[1], kv[0]), reverse=True)[1][1]
            #meanA = float(meanA) * (2.0*pi) / 360.0
            #meanA = angles[list(cl)].mean()
            for i in cl:
                seg = segs[i]
                seg.newAngle = meanA if seg.angle>=0. else meanA-geometric._pi
    
    
    def prepareDistanceEqualization(segs, relDelta=0.1):
        """ Input segments are grouped according to their length  :
          - for each length L, find all other lengths within L*relDelta. of L.
          - Find the larger of such subgroup.
          - repeat the procedure on remaining lengths until none is left.
        Each length in a group is set to the mean length of the group

        segs : a list of segments
        relDelta : float, minimum relative distance.
        """

        lengths = numpy.array( [x.tempLength() for x in segs] )
        clusters = miscellaneous.clusterValues(lengths, relDelta)

        if len(clusters)==1:
            # deal with special case with low num of segments
            # --> don't let a single segment alone
            if len(clusters[0])+1==len(segs):
                clusters[0]=list(range(len(segs))) # all

        allDist = []
        for cl in clusters:
            dmean = sum( lengths[i] for i in cl ) / len(cl)
            allDist.append(dmean)
            for i in cl:
                segs[i].setNewLength(dmean)
                debug( i, ' set newLength ', dmean, segs[i].length, segs[i].dumpShort())
                
        return allDist


    def prepareRadiusEqualization(circles, otherDists, relSize=0.2):
        """group circles radius and distances into cluster.
        Then set circles radius according to the mean of the clusters they belong to."""
        ncircles = len(circles)
        lengths = numpy.array( [c.radius for c in circles]+otherDists )
        indices = numpy.array( list(range(ncircles+len(otherDists))) )
        clusters = miscellaneous.clusterValues(numpy.stack([ lengths, indices ], 1 ), relSize, refScaleAbs='local' )

        debug('prepareRadiusEqualization radius ', repr(lengths))
        debug('prepareRadiusEqualization clusters ',  clusters)
        allDist = []
        for cl in clusters:
            dmean = sum( lengths[i] for i in cl ) / len(cl)
            #print cl , dmean , 
            allDist.append(dmean)
            if len(cl)==1:
                continue
            for i in cl:
                if i< ncircles:
                    circles[i].radius = dmean
        debug(' post radius ', [c.radius for c in circles] )
        return allDist


    def centerCircOnSeg(circles, segments, relSize=0.18):
        """ move centers of circles onto the segments if close enough"""
        for circ in circles:
            circ.moved = False
        for seg in segments:
            for circ in circles:                
                d = seg.distanceTo(circ.center)
                #debug( '      ', seg.projectPoint(circ.center))
                if d < circ.radius*relSize and not circ.moved :
                    circ.center = seg.projectPoint(circ.center)
                    circ.moved = True
                

    def adjustToKnownAngle( paths):
        """ Check current angle against remarkable angles. If close enough, change it
        paths : a list of segments"""
        for seg in paths:
            a = seg.tempAngle()
            i = (abs(geometric.vec_in_mPi_pPi(geometric.knownAngle - a) )).argmin()
            seg.newAngle = geometric.knownAngle[i]
            debug( '  Known angle ', seg, seg.tempAngle(), '  -> ', geometric.knownAngle[i]) 
            ## if abs(geometric.knownAngle[i] - a) < 0.08:        

class PostProcess():
    def mergeConsecutiveParralels(segments, options):
        ignoreNext=False
        newList=[]
        for s in segments:
            if ignoreNext:
                ignoreNext=False
                continue
            if not s.isSegment():
                newList.append(s)
                continue
            if not hasattr(s, "__next__"):
                newList.append(s)
                continue
            if not s.next.isSegment():
                newList.append(s)
                continue
            d = geometric.closeAngleAbs(s.angle, s.next.angle)
            if d < options.segAngleMergePara:
                debug("merging ", s.angle, s.next.angle )
                snew = s.mergedWithNext(doRefit=False)
                ignoreNext=True
                newList.append(snew)
            else:
                debug("notmerging ", s.angle, s.next.angle )
                newList.append(s)
        if len(segments)>len(newList):
            debug("merged parallel ", segments, '-->', newList)
        return newList
    
    def uniformizeShapes(pathGroupList, options):
        allSegs = [ p  for g in pathGroupList for p in g.listOfPaths if p.isSegment() ]

        if options.doParrallelize:
            PreProcess.prepareParrallelize(allSegs)
        if options.doKnownAngle:
            PreProcess.adjustToKnownAngle(allSegs)

        adjustAng = options.doKnownAngle or options.doParrallelize
        
        allShapeDist = []
        for g in [ group for group in pathGroupList if not isinstance(group, groups.Circle)]:
                # first pass : independently per path
                if adjustAng:
                    manipulation.adjustAllAngles(g.listOfPaths)
                    g.listOfPaths[:] = PostProcess.mergeConsecutiveParralels(g.listOfPaths, options)
                if options.doEqualizeDist:
                    allShapeDist=allShapeDist + PreProcess.prepareDistanceEqualization([p for p in g.listOfPaths if p.isSegment()], options.shapeDistLocal ) ##0.30
                    manipulation.adjustAllDistances([p for p in g.listOfPaths if p.isSegment()])      #findme was group.li..
                    
        ## # then 2nd global pass, with tighter criteria
        if options.doEqualizeDist:
            allShapeDist=PreProcess.prepareDistanceEqualization(allSegs, options.shapeDistGlobal) ##0.08
            for g in [ group for group in pathGroupList if not isinstance(group, groups.Circle)]:
                manipulation.adjustAllDistances([p for p in g.listOfPaths if p.isSegment()])
            
        #TODO: I think this is supposed to close thje paths and it is failing
        for g in pathGroupList: 
            if g.isClosing and not isinstance(g, groups.Circle):
                debug('Closing intersec ', g.listOfPaths[0].point1, g.listOfPaths[0].pointN )
                g.listOfPaths[-1].setIntersectWithNext(g.listOfPaths[0])  


        circles=[ group for group in pathGroupList if isinstance(group, groups.Circle)]
        if options.doEqualizeRadius:
            PreProcess.prepareRadiusEqualization(circles, allShapeDist)
        if options.doCenterCircOnSeg:
            PreProcess.centerCircOnSeg(circles, allSegs)

        pathGroupList = [manipulation.toRemarkableShape(g) for g in pathGroupList]
        return pathGroupList

class FitShapes():
    def checkForCircle(points, tangents):
        """Determine if the points and their tangents represent a circle

        The difficulty is to be able to recognize ellipse while avoiding paths small fluctuations a
        nd false positive due to badly drawn rectangle or non-convex closed curves.
        
        Method : we consider angle of tangent as function of lenght on path.
        For circles these are : angle = c1 x lenght + c0. (c1 ~1)

        We calculate dadl = d(angle)/d(length) and compare to c1.
        We use 3 criteria :
         * num(dadl > 6) : number of sharp angles
         * length(dadl<0.3)/totalLength : lengths of straight lines within the path.
         * totalLength/(2pi x radius) : fraction of lenght vs a plain circle

        Still failing to recognize elongated ellipses...
        
        """
        if len(points)<10:
            return False, 0

        if all(points[0]==points[-1]): # last exactly equals the first.
            # Ignore last point for this check
            points = points[:-1]
            tangents = tangents[:-1]
            #print 'Removed last ', points
        xmin, ymin, w, h = geometric.computeBox( points)
        diag2=(w*w+h*h)
        
        diag = numpy.sqrt(diag2)*0.5
        norms = numpy.sqrt(numpy.sum( tangents**2, 1 ))

        angles = numpy.arctan2(  tangents[:, 1], tangents[:, 0] )  
        #debug( 'angle = ', repr(angles))
        N = len(angles)
        
        deltas =  points[1:] - points[:-1] 
        deltasD = numpy.concatenate([ [geometric.D(points[0], points[-1])/diag], numpy.sqrt(numpy.sum( deltas**2, 1 )) / diag] )

        # locate and avoid the point when swicthing
        # from -pi to +pi. The point is around the minimum
        imin = numpy.argmin(angles)
        debug(' imin ', imin)
        angles = numpy.roll(angles, -imin)
        deltasD = numpy.roll(deltasD, -imin)
        n=int(N*0.1)
        # avoid fluctuations by removing points around the min
        angles=angles[n:-n]
        deltasD=deltasD[n:-n]
        deltasD = deltasD.cumsum()
        N = len(angles)

        # smooth angles to avoid artificial bumps
        angles = manipulation.smoothArray(angles, n=max(int(N*0.03), 2) )

        deltaA = angles[1:] - angles[:-1]
        deltasDD =  (deltasD[1:] -deltasD[:-1])
        deltasDD[numpy.where(deltasDD==0.)] = 1e-5*deltasD[0]
        dAdD = abs(deltaA/deltasDD)
        belowT, count = True, 0
        for v in dAdD:
            if v>6 and belowT:
                count+=1
                belowT = False
            belowT= (v<6)

        temp = (deltasD, angles, tangents, dAdD )
        fracStraight = numpy.sum(deltasDD[numpy.where(dAdD<0.3)])/(deltasD[-1]-deltasD[0])
        curveLength = deltasD[-1]/3.14
        #print "SSS ",count , fracStraight
        if curveLength> 1.4 or fracStraight>0.4 or count > 6:
            isCircle =False
        else: 
            isCircle= (count < 4 and fracStraight<=0.3) or \
                      (fracStraight<=0.1 and count<5)

        if not isCircle:
            return False, 0
            
        # It's a circle !
        radius = points - numpy.array([xmin+w*0.5, ymin+h*0.5])
        radius_n = numpy.sqrt(numpy.sum( radius**2, 1 )) # normalize

        mini = numpy.argmin(radius_n)        
        rmin = radius_n[mini]
        maxi = numpy.argmax(radius_n)        
        rmax = radius_n[maxi]
        # void points around maxi and mini to make sure the 2nd max is found
        # on the "other" side
        n = len(radius_n)
        radius_n[maxi]=0        
        radius_n[mini]=0        
        for i in range(1, int(n/8+1)):
            radius_n[(maxi+i)%n]=0
            radius_n[(maxi-i)%n]=0
            radius_n[(mini+i)%n]=0
            radius_n[(mini-i)%n]=0
        radius_n_2 = [ r for r in radius_n if r>0]
        rmax_2 = max(radius_n_2)
        rmin_2 = min(radius_n_2) # not good !!
        anglemax = numpy.arccos( radius[maxi][0]/rmax)*numpy.sign(radius[maxi][1])
        return True, (xmin+w*0.5, ymin+h*0.5, 0.5*(rmin+rmin_2), 0.5*(rmax+rmax_2), anglemax)
        
        
    def checkForArcs(points, tangents):
           """Determine if the points and their tangents represent a circle
   
           The difficulty is to be able to recognize ellipse while avoiding paths small fluctuations a
           nd false positive due to badly drawn rectangle or non-convex closed curves.
           
           Method : we consider angle of tangent as function of lenght on path.
           For circles these are : angle = c1 x lenght + c0. (c1 ~1)
   
           We calculate dadl = d(angle)/d(length) and compare to c1.
           We use 3 criteria :
            * num(dadl > 6) : number of sharp angles
            * length(dadl<0.3)/totalLength : lengths of straight lines within the path.
            * totalLength/(2pi x radius) : fraction of lenght vs a plain circle
   
           Still failing to recognize elongated ellipses...
           
           """
           if len(points)<10:
               return False, 0
   
           if all(points[0]==points[-1]): # last exactly equals the first.
               # Ignore last point for this check
               points = points[:-1]
               tangents = tangents[:-1]
               print(('Removed last ', points))
           xmin, ymin, w, h = geometric.computeBox( points)
           diag2=(w*w+h*h)
           
           diag = numpy.sqrt(diag2)*0.5
           norms = numpy.sqrt(numpy.sum( tangents**2, 1 ))
   
           angles = numpy.arctan2(  tangents[:, 1], tangents[:, 0] )  
           #debug( 'angle = ', repr(angles))
           N = len(angles)
           
           deltas =  points[1:] - points[:-1] 
           deltasD = numpy.concatenate([ [geometric.D(points[0], points[-1])/diag], numpy.sqrt(numpy.sum( deltas**2, 1 )) / diag] )
   
           # locate and avoid the point when swicthing
           # from -pi to +pi. The point is around the minimum
           imin = numpy.argmin(angles)
           debug(' imin ', imin)
           angles = numpy.roll(angles, -imin)
           deltasD = numpy.roll(deltasD, -imin)
           n=int(N*0.1)
           # avoid fluctuations by removing points around the min
           angles=angles[n:-n]
           deltasD=deltasD[n:-n]
           deltasD = deltasD.cumsum()
           N = len(angles)
   
           # smooth angles to avoid artificial bumps
           angles = manipulation.smoothArray(angles, n=max(int(N*0.03), 2) )
   
           deltaA = angles[1:] - angles[:-1]
           deltasDD =  (deltasD[1:] -deltasD[:-1])
           deltasDD[numpy.where(deltasDD==0.)] = 1e-5*deltasD[0]
           dAdD = abs(deltaA/deltasDD)
           belowT, count = True, 0
           
   
           self.temp = (deltasD, angles, tangents, dAdD )
           #TODO: Loop over deltasDD searching for curved segments, no sharp bumps and a curve of at least 1/4 pi
           curveStart = 0
           curveToTest= numpy.array([deltasDD[curveStart]]); 
           dAdDd = numpy.array([dAdD[curveStart]])
           v = dAdD[curveStart]
           belowT= (v<6)
           for i in range(1, deltasDD.size):           	                      	
           	curveToTest = numpy.append(curveToTest, deltasDD[i])
           	dAdDd = numpy.append(dAdDd, dAdD[i])
           	fracStraight = numpy.sum(curveToTest[numpy.where(dAdDd<0.3)])/(deltasD[i]-deltasD[curveStart])
           	curveLength = (deltasD[i]-deltasD[curveStart])/3.14
           	
           	v = dAdD[i]
           	if v>6 and belowT:	
           	    count+=1
           	    belowT = False
           	belowT= (v<6)
           	inkex.debug("SSS "+str(count) +":"+ str(fracStraight))
           	if curveLength> 1.4 or fracStraight>0.4 or count > 8:
           	    inkex.debug("curveLengtha:" + str(curveLength) +"fracStraight:"+str(fracStraight)+"count:"+str(count))
           	    isArc=False
           	    curveStart=int(i)
           	    curveToTest= numpy.array([deltasDD[curveStart]]); 
           	    v = dAdD[curveStart]
           	    dAdDd = numpy.array([dAdD[curveStart]])
           	    belowT= (v<6)
           	    count = 0
           	    continue
           	else:
           	    inkex.debug("curveLengthb:" + str(curveLength) +"fracStraight:"+str(fracStraight)+"count:"+str(count))
           	    isArc= (count < 4 and fracStraight<=0.3) or \
			(fracStraight<=0.1 and count<5)
   
           if not isArc:
               return False, 0
               
           # It's a circle !
           radius = points - numpy.array([xmin+w*0.5, ymin+h*0.5])
           radius_n = numpy.sqrt(numpy.sum( radius**2, 1 )) # normalize
   
           mini = numpy.argmin(radius_n)        
           rmin = radius_n[mini]
           maxi = numpy.argmax(radius_n)        
           rmax = radius_n[maxi]
           # void points around maxi and mini to make sure the 2nd max is found
           # on the "other" side
           n = len(radius_n)
           radius_n[maxi]=0        
           radius_n[mini]=0        
           for i in range(1, int(n/8+1)):
               radius_n[(maxi+i)%n]=0
               radius_n[(maxi-i)%n]=0
               radius_n[(mini+i)%n]=0
               radius_n[(mini-i)%n]=0
           radius_n_2 = [ r for r in radius_n if r>0]
           rmax_2 = max(radius_n_2)
           rmin_2 = min(radius_n_2) # not good !!
           anglemax = numpy.arccos( radius[maxi][0]/rmax)*numpy.sign(radius[maxi][1])
           return True, (xmin+w*0.5, ymin+h*0.5, 0.5*(rmin+rmin_2), 0.5*(rmax+rmax_2), anglemax)




    def tangentEnvelop(svgCommandsList, refNode, options):
        a, svgCommandsList = geometric.toArray(svgCommandsList)
        tangents = manipulation.buildTangents(a)

        newSegs = [ internal.Segment.fromCenterAndDir( p, t ) for (p, t) in zip(a, tangents) ]
        debug("build envelop ", newSegs[0].point1, newSegs[0].pointN)
        clustersInd = manipulation.clusterAngles( [s.angle for s in newSegs] )
        debug("build envelop cluster:  ", clustersInd)

        return TangentEnvelop( newSegs, svgCommandsList, refNode)

    def isClosing(wTot, hTot, d):
        aR = min(wTot/hTot, hTot/wTot)
        maxDim = max(wTot, hTot)
        # was 0.2
        return aR*0.5 > d/maxDim
        
        
    def curvedFromTangents(svgCommandsList, refNode, x, y, wTot, hTot, d, isClosing, sourcepoints, tangents, options):

#        debug('isClosing ', isClosing, maxDim, d)

        # global quantities :
        hasArcs = False
        res = ()
        # Check if circle -----------------------
        if isClosing:
            if len(sourcepoints)<9:
                return groups.PathGroup.toSegments(sourcepoints, svgCommandsList, refNode, isClosing=True)
            isCircle, res = FitShapes.checkForCircle( sourcepoints, tangents)        
            debug("Is Circle = ", isCircle )
            if isCircle:
                x, y, rmin, rmax, angle = res
                debug("Circle -> ", rmin, rmax, angle )
                if rmin/rmax>0.7:
                    circ = groups.Circle((x, y), 0.5*(rmin+rmax),  refNode )
                else:
                    circ = groups.Circle((x, y), rmin,  refNode, rmax=rmax, angle=angle)
                circ.points = sourcepoints
                return circ
            #else:
            #    hasArcs, res = FitShapes.checkForArcs( sourcepoints, tangents)   
        #else:
            #hasArcs, res = FitShapes.checkForArcs( sourcepoints, tangents)
        # -----------------------
        if hasArcs:
            x, y, rmin, rmax, angle = res
            debug("Circle -> ", rmin, rmax, angle )
            if rmin/rmax>0.7:
                circ = groups.Circle((x, y), 0.5*(rmin+rmax),  refNode )
            else:
                circ = groups.Circle((x, y), rmin,  refNode, rmax=rmax, angle=angle)
            circ.points = sourcepoints
            return circ
        return None
    
    def segsFromTangents(svgCommandsList, refNode, options):
        """Finds segments part in a list of points represented by svgCommandsList.

        The method is to build the (averaged) tangent vectors to the curve.
        Aligned points will have tangent with similar angle, so we cluster consecutive angles together
        to define segments.
        Then we extend segments to connected points not already part of other segments.
        Then we merge consecutive segments with similar angles.
        
        """
        sourcepoints, svgCommandsList = geometric.toArray(svgCommandsList)

        d = geometric.D(sourcepoints[0], sourcepoints[-1])
        x, y, wTot, hTot = geometric.computeBox(sourcepoints)
        if wTot == 0: wTot = 0.001
        if hTot == 0: hTot = 0.001
        if d==0:
            # then we remove the last point to avoid null distance
            # in other calculations
            sourcepoints = sourcepoints[:-1]
            svgCommandsList = svgCommandsList[:-1]
        
        isClosing = FitShapes.isClosing(wTot, hTot, d)
            
        if len(sourcepoints) < 4:
            return groups.PathGroup.toSegments(sourcepoints, svgCommandsList, refNode, isClosing=isClosing)

        tangents = manipulation.buildTangents(sourcepoints, isClosing=isClosing)
            
        aCurvedSegment = FitShapes.curvedFromTangents(svgCommandsList, refNode, x, y, wTot, hTot, d, isClosing, sourcepoints, tangents, options)
        
        if not aCurvedSegment == None:
            return aCurvedSegment

        # cluster points by angle of their tangents -------------
        tgSegs = [ internal.Segment.fromCenterAndDir( p, t ) for (p, t) in zip(sourcepoints, tangents) ]
        clustersInd = sorted(manipulation.clusterAngles( [s.angle for s in tgSegs] ))
        debug("build envelop cluster:  ", clustersInd)

        # build Segments from clusters 
        newSegs = []
        for imin, imax in clustersInd:
            if imin+1< imax: # consider clusters with more than 3 points
                seg = manipulation.fitSingleSegment(sourcepoints[imin:imax+1])
            elif imin+1==imax: # 2 point path : we build a segment
                seg = internal.Segment.from2Points(sourcepoints[imin], sourcepoints[imax], sourcepoints[imin:imax+1])
            else:
                seg = internal.Path( sourcepoints[imin:imax+1] )
            seg.sourcepoints = sourcepoints
            newSegs.append( seg )
        manipulation.resetPrevNextSegment( newSegs )
        debug(newSegs)
        # -----------------------


        # -----------------------
        # Merge consecutive Path objects 
        updatedSegs=[]
        def toMerge(p):
            l=[p]
            setattr(p, 'merged', True)
            if hasattr(p, "__next__") and not p.next.isSegment():
                l += toMerge(p.next)
            return l
        
        for i, seg in enumerate(newSegs[:-1]):
            if seg.isSegment():
                updatedSegs.append( seg)                
                continue
            if hasattr(seg, 'merged'): continue
            mergeList = toMerge(seg)
            debug('merging ', mergeList)
            p = internal.Path(numpy.concatenate([ p.points for p in mergeList]) )
            debug('merged == ', p.points)
            updatedSegs.append(p)

        if not hasattr(newSegs[-1], 'merged'): updatedSegs.append( newSegs[-1]) 
        debug("merged path", updatedSegs)
        newSegs = manipulation.resetPrevNextSegment( updatedSegs )


        # Extend segments -----------------------------------
        if options.segExtensionEnable:
            newSegs = extenders.SegmentExtender.extendSegments( newSegs, options.segExtensionDtoSeg, options.segExtensionQual )
            debug("extended segs", newSegs)
            newSegs = manipulation.resetPrevNextSegment( newSegs )
            debug("extended segs", newSegs)

        # ----------------------------------------
            

        # ---------------------------------------
        # merge consecutive segments with close angle
        updatedSegs=[]

        if options.segAngleMergeEnable:
            newSegs = miscellaneous.mergeConsecutiveCloseAngles( newSegs, mangle=options.segAngleMergeTol1 )
            newSegs=manipulation.resetPrevNextSegment(newSegs)
            debug(' __ 2nd angle merge')
            newSegs = miscellaneous.mergeConsecutiveCloseAngles( newSegs, mangle=options.segAngleMergeTol2 ) # 2nd pass
            newSegs=manipulation.resetPrevNextSegment(newSegs)
            debug('after merge ', len(newSegs), newSegs)
            # Check if first and last also have close angles.
            if isClosing and len(newSegs)>2 :
                first, last = newSegs[0], newSegs[-1]
                if first.isSegment() and last.isSegment():
                    if geometric.closeAngleAbs( first.angle, last.angle) < 0.1:
                        # force merge
                        points= numpy.concatenate( [  last.points, first.points] )
                        newseg = manipulation.fitSingleSegment(points)
                        newseg.next = first.__next__ if hasattr(first, "__next__") else None
                        last.prev.next = None
                        newSegs[0]=newseg
                        newSegs.pop()

        # -----------------------------------------------------
        # remove negligible Path/Segments between 2 large Segments
        if options.segRemoveSmallEdge:
            PreProcess.removeSmallEdge(newSegs, wTot, hTot)
            newSegs=manipulation.resetPrevNextSegment(newSegs)

            debug('after remove small ', len(newSegs), newSegs)
        # -----------------------------------------------------

        # -----------------------------------------------------
        # Extend segments to their intersections
        for p in newSegs:
            if p.isSegment() and hasattr(p, "__next__"):
                p.setIntersectWithNext()
        # -----------------------------------------------------
        
        return groups.PathGroup(newSegs, svgCommandsList, refNode, isClosing)




# *************************************************************
# The inkscape extension
# *************************************************************
class ShapeRecognition(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--title")
        pars.add_argument("--keepOrigin", dest="keepOrigin", default=False, type=inkex.Boolean, help="Do not replace path")
        pars.add_argument("--MainTabs")
        pars.add_argument("--segExtensionDtoSeg", dest="segExtensionDtoSeg", default=0.03, type=float, help="max distance from point to segment")
        pars.add_argument("--segExtensionQual", dest="segExtensionQual", default=0.5, type=float, help="segment extension fit quality")
        pars.add_argument("--segExtensionEnable", dest="segExtensionEnable", default=True, type=inkex.Boolean, help="Enable segment extension")
        pars.add_argument("--segAngleMergeEnable", dest="segAngleMergeEnable", default=True, type=inkex.Boolean, help="Enable merging of almost aligned consecutive segments")
        pars.add_argument("--segAngleMergeTol1", dest="segAngleMergeTol1", default=0.2, type=float, help="merging with tollarance 1")
        pars.add_argument("--segAngleMergeTol2", dest="segAngleMergeTol2", default=0.35, type=float, help="merging with tollarance 2")
        pars.add_argument("--segAngleMergePara", dest="segAngleMergePara", default=0.001, type=float, help="merge lines as parralels if they fit")
        pars.add_argument("--segRemoveSmallEdge", dest="segRemoveSmallEdge", default=True, type=inkex.Boolean, help="Enable removing very small segments")
        pars.add_argument("--doUniformization", dest="doUniformization", default=True, type=inkex.Boolean, help="Preform angles and distances uniformization")
        for opt in ["doParrallelize", "doKnownAngle", "doEqualizeDist", "doEqualizeRadius", "doCenterCircOnSeg"]:
            pars.add_argument( "--"+opt, dest=opt, default=True, type=inkex.Boolean, help=opt)
        pars.add_argument("--shapeDistLocal", dest="shapeDistLocal", default=0.3, type=float, help="Pthe percentage of difference at which we make lengths equal, locally")
        pars.add_argument("--shapeDistGlobal", dest="shapeDistGlobal", default=0.025, type=float, help="Pthe percentage of difference at which we make lengths equal, globally")
 

        
    def effect(self):

        rej='{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}type'
        paths = []
        for id, node in list(self.svg.selected.items()):
            if node.tag == '{http://www.w3.org/2000/svg}path' and rej not in list(node.keys()):                
                paths.append(node)

        shapes = self.extractShapes(paths)
        # add new shapes in SVG document
        self.addShapesToDoc( shapes )

    def extractShapesFromID( self, *nids, **options ):
        """for debugging purpose """
        eList = []
        for nid in nids:
            el = self.getElementById(nid)
            if el is None:
                print(("Cant find ", nid))
                return
            eList.append(el)
        class tmp:
            pass

        self.options = self.OptionParser.parse_args()[0]
        self.options._update_careful(options)
        nodes=self.extractShapes(eList)
        self.shape = nodes[0]


    def buildShape(self, node):
        def rotationAngle(tr):
            if tr and tr.startswith('rotate'):
                # retrieve the angle :
                return float(tr[7:-1].split(','))
            else:
                return 0.
            
        if node.tag.endswith('path'):
            g = FitShapes.segsFromTangents(node.path.to_arrays(), node, self.options)
        elif node.tag.endswith('rect'):
            tr = node.get('transform', None)
            if tr and tr.startswith('matrix'):
                return None # can't deal with scaling
            recSize = numpy.array([node.get('width'), node.get('height')])
            recCenter = numpy.array([node.get('x'), node.get('y')]) + recSize/2
            angle=rotationAngle(tr)
            g = groups.Rectangle( recSize, recCenter, 0, [], node)
        elif node.tag.endswith('circle'):
            g = groups.Circle(node.get('cx'), node.get('cy'), node.get('r'), [], node )
        elif node.tag.endswith('ellipse'):
            if tr and tr.startswith('matrix'):
                return None # can't deal with scaling
            angle=rotationAngle(tr)
            rx = node.get('rx')
            ry = node.get('ry')
            g = groups.Circle(node.get('cx'), node.get('cy'), ry, rmax=rx, angle=angle, refNode=node)

        return g
    
    def extractShapes( self, nodes ):
        """The main function.
        nodes : a list of nodes"""
        analyzedNodes = []

        # convert nodes to list of segments (groups.PathGroup) or Circle
        for n in nodes :
            g = self.buildShape(n)
            if g :
                analyzedNodes.append( g )

        # uniformize shapes
        if self.options.doUniformization:
            analyzedNodes = PostProcess.uniformizeShapes(analyzedNodes, self.options)

        return analyzedNodes       
        
    def addShapesToDoc(self, pathGroupList):
        for group in pathGroupList:
            
            debug("final ", group.listOfPaths, group.refNode )
            debug("final-style ", group.refNode.get('style'))
            # change to Rectangle if possible :
            finalshape = manipulation.toRemarkableShape( group )
            ele = group.addToNode( group.refNode)
            group.setNodeStyle(ele, group.refNode)
            if not self.options.keepOrigin:
                group.refNode.xpath('..')[0].remove(group.refNode)


        
if __name__ == '__main__':
    ShapeRecognition().run()
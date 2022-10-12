import numpy
import sys
import collections
numpy.set_printoptions(precision=3)

# *************************************************************
# debugging 
def void(*l):
    pass
def debug_on(*l):
    sys.stderr.write(' '.join(str(i) for i in l) +'\n') 
debug = void
#debug = debug_on

curveFragments = 10


def qudSmRelBezCurFrag(ctrlPts, startPoint):
    #just call the normal one with adjusted coordinates
    ctrlPts[0] = startPoint[-2] + ctrlPts[0]
    ctrlPts[1] =  startPoint[-1] + ctrlPts[1]
    return qudSmBezCurFrag(ctrlPts, startPoint)
    
def qudSmBezCurFrag(ctrlPts, startPoint):
    #There are no control points
    debug("startPoint: '", startPoint, "'")
    debug("shouldbethehandle: '", [startPoint[2] + (startPoint[2] - startPoint[0]), startPoint[3] + (startPoint[3] - startPoint[1])], "'")
    #ctrlPtsExt = [startPoint[2] + (startPoint[2] - startPoint[0]), startPoint[3] + (startPoint[3] - startPoint[1])] + ctrlPts
    ctrlPtsExt = [startPoint[-2] + (startPoint[-2] - startPoint[-4]), startPoint[-1] + (startPoint[-1] - startPoint[-3])] + ctrlPts
    debug("startPoint: '", startPoint, "'") 
    debug("ctrlPts: '", ctrlPts, "'")     
    debug("startPoint[-2:]: '", startPoint[-2:], "'") 
    debug("ctrlPtsExt: '", ctrlPtsExt, "'") 
    debug("shound be the same as non smooth: '", ctrlPtsExt)
    return cubBezCurFrag(ctrlPtsExt, startPoint[-2:])
    
def qudRelBezCurFrag(ctrlPts, startPoint):
    #just call the normal one with adjusted coordinates
    ctrlPts[0] = startPoint[-2] + ctrlPts[0]
    ctrlPts[1] =  startPoint[-1] + ctrlPts[1]
    return qudBezCurFrag(ctrlPts, startPoint)
    
def qudBezCurFrag(ctrlPts, startPoint):
    #tested working
    debug("startPoint: '", startPoint, "'") 
    return cubBezCurFrag(ctrlPts, startPoint[-2:])

def cubSmRelBezCurFrag(ctrlPts, startPoint):
    #just call the normal one with adjusted coordinates
    #[prevL[-1][0] + x[0:1][0] , prevL[1] + x[1:2][1]]
    ctrlPts[0] = startPoint[-2] + ctrlPts[0]
    ctrlPts[1] =  startPoint[-1] + ctrlPts[1]
    return cubSmBezCurFrag(ctrlPts, startPoint)
    
def cubSmBezCurFrag(ctrlPts, startPoint):
    #tested working
    #just call the normal one with adjusted coordinates    
    ctrlPtsExt = [startPoint[-2] + (startPoint[-2] - startPoint[-4]), startPoint[-1] + (startPoint[-1] - startPoint[-3])] + ctrlPts
    return cubBezCurFrag(ctrlPtsExt, startPoint[-2:])

def cubRelBezCurFrag(ctrlPts, startPoint):
    #just call the normal one with adjusted coordinates
    ctrlPts[0] = startPoint[-2] + ctrlPts[0]
    ctrlPts[1] =  startPoint[-1] + ctrlPts[1]
    return cubBezCurFrag(ctrlPts, startPoint)

def compute(t, points): #, _3d
    #// shortcuts
    if (t == 0) :
        #points[0].t = 0;
        return points[0:2]

    order = int((int(len(points)) / 2)) - 1;

    if (t == 1) :
        #points[order].t = 1;
        return points[order * 2:order * 2 + 2]

    mt = 1 - t
    p = points

#        // constant?
    if (order == 0):
        #points[0].t = t;
        return points[0:2]

    #// linear?
    if (order == 1):
        ret = [
            mt * p[0] + t * p[2],
            mt * p[1] + t * p[3]
    #         t: t,
            ]
    #      if (_3d) {
    #        ret.z = mt * p[0].z + t * p[1].z;
    #      }
        return ret

    #// quadratic/cubic curve?
    mt2 = 0
    a = b = c = d = 0
    if (order < 4):
        mt2 = mt * mt
        t2 = t * t
    else:
        sys.stderr.write("Order :'" + str(order) +"' beyond limits of function")
        return [0.0, 0.0]

    if (order == 2):
        p = p + [0,0]
        a = mt2
        b = mt * t * 2
        c = t2
    elif (order == 3):
        a = mt2 * mt
        b = mt2 * t * 3
        c = mt * t2 * 3
        d = t * t2

    ret = [
        a * p[0] + b * p[2] + c * p[4] + d * p[6],
        a * p[1] + b * p[3] + c * p[5] + d * p[7]
        ]
    #      if (_3d) {
    #        ret.z = a * p[0].z + b * p[1].z + c * p[2].z + d * p[3].z;
    #      }
    return ret
    
#TODO: Number of fragments should possibly be based upon the length of the segment.

def cubBezCurFrag(ctrlPts, startPoint):
    #tested working
     points =[]
     rng = range(0, curveFragments + 1)
     #sx = startPoint[0]
     #sy = startPoint[1]
     debug("control ", startPoint + ctrlPts)
     inputPoints = startPoint + ctrlPts
     for i in rng:
         t = (float(i) / float(len(rng) - 1))
         debug("t ", t,  ":", i)
         newp = compute(t, inputPoints)
         #newp= [(1-t) ** 3 * startPoint[0] + 3 * ((1-t) ** 2) * t* ctrlPts[0] +3 * (1-t) * (t ** 2) * ctrlPts[2] + (t ** 3) * ctrlPts[4],
         #(1-t) ** 3 * startPoint[1] + 3 * ((1-t) ** 2) * t* ctrlPts[1] +3 * (1-t) * (t ** 2) * ctrlPts[3] + (t ** 3) * ctrlPts[5]]
         points.append(newp)
     debug("result ", points)
     return points
     
# *************************************************************
# a list of geometric helper functions 
def toArray(parsedList):
    """Interprets a list of [(command, args),...]
    where command is a letter coding for a svg path command
          args are the argument of the command
    """
    
    # The set of commands is now complete, all absolute positioning has been tested, relative positioning still neds some more testing.
    # Curved parts of the path need fragmenting instead of just being taken as a straight line.
    interpretCommand = {
        'C': lambda x, prevL : cubBezCurFrag(x, prevL[-2:]), # cubic bezier curve. Ignore the curve. #TODO, fragment
        'c': lambda x, prevL : cubRelBezCurFrag(x, prevL[-2:]), # cubic bezier curve, relative. Ignore the curve. #TODO, fragment        
        'S': lambda x, prevL : cubSmBezCurFrag(x, prevL), # cubic bezier curve, smooth. TODO, fragment
        's': lambda x, prevL : cubSmRelBezCurFrag(x, prevL), # cubic bezier curve, smooth, relative. TODO, fragment
        'Q': lambda x, prevL : qudBezCurFrag(x, prevL), # quadratic bezier curve. TODO, fragment
        'q': lambda x, prevL : qudRelBezCurFrag(x, prevL), # quadratic bezier curve, relative TODO, fragment        
#[[prevL[-1][0] + x[0:1][0] , prevL[1] + x[1:2][1]]], # quadratic bezier curve, relative TODO, fragment                
        'T': lambda x, prevL : qudSmBezCurFrag(x, prevL), # quadratic bezier curve, smooth. TODO, fragment
        't': lambda x, prevL : qudSmRelBezCurFrag(x, prevL), # quadratic bezier curve, smooth, relative. TODO, fragment
        'L': lambda x, prevL : [x[0:2]], # Line
        'l': lambda x, prevL : [[prevL[0] + x[0:1][0] , prevL[1] + x[1:2][1]]], # Line, relative
        'M': lambda x, prevL : [x[0:2]], # Move
        'm': lambda x, prevL : [[prevL[0] + x[0:1][0] , prevL[1] + x[1:2][1]]], # Move, Relative
        'H': lambda x, prevL : [[x[0:1][0],prevL[1]]], # Horizontal
        'h': lambda x, prevL : [[prevL[0] + x[0:1][0], prevL[1]]], # Horizontal , relative
        'V': lambda x, prevL : [[prevL[0], x[0:1][0]]], # Verticle
        'v': lambda x, prevL : [[prevL[0], prevL[1] + x[0:1][0]]], # Verticle, relative
        'A': lambda x, prevL : [x[5:7]], # Arc segment
        'a': lambda x, prevL : [[prevL[0] + x[5:6][0] , prevL[1] + x[6:7][1]]], # Arc segment, relative
        'Z': lambda x, prevL : [prevL[0]], # Close path
        'z': lambda x, prevL : [prevL[0]], # Close path
        }

    #append the last set of attributes of the first element to the lookBack for cases where smooth or smooth quad segments appear at the begining of a path.
    lookBack = parsedList[0][1] + parsedList[0][1]
    points =[]
    for i, (c, arg) in enumerate(parsedList):
        debug('toArray ', i, c , arg)
        debug('lookBack: ', lookBack)
        newp = interpretCommand[c](arg, lookBack)
        
        #double up if there are only two point entries to support transition into smooth beziers or arrays of smooth beziers etc..
        if len(arg) == 2:
            arg = arg + arg

        #we only need to keep the last element in the lookBack, so remove any elemenmts in front.
        lookBack = arg

        debug('newPoints ', newp)
        points = points + newp
    a = numpy.array(points)


    # Some times we have points *very* close to each other
    # these do not bring any meaning full info, so we remove them
    #
    
    x, y, w, h = computeBox(a)
    sizeC = 0.5*(w+h)
    #deltas = numpy.zeros((len(a),2) )
    deltas = a[1:] - a[:-1] 
    #deltas[-1] = a[0] - a[-1]
    deltaD = numpy.sqrt(numpy.sum( deltas**2, 1 ))
    sortedDind = numpy.argsort(deltaD)
#    # expand longuest segments
    nexp = int(len(deltaD)*0.9)
    newpoints=[ None ]*len(a)
    medDelta = deltaD[sortedDind[int(len(deltaD)/2)] ]
    for i, ind in enumerate(sortedDind):
        if deltaD[ind]/sizeC<0.005: continue
        if i>nexp:
            np = int(deltaD[ind]/medDelta)
            pL = [a[ind]]
            #print i,'=',ind,'adding ', np,'  _ ', deltaD[ind], a[ind], a[ind+1]
            for j in range(np-1):
                f = float(j+1)/np
                #print '------> ', (1-f)*a[ind]+f*a[ind+1]
                pL.append( (1-f)*a[ind]+f*a[ind+1] )
            newpoints[ind] = pL
        else:
             newpoints[ind]=[a[ind]]
    if(D(a[0], a[-1])/sizeC > 0.005 ) :
        newpoints[-1]=[a[-1]]

    points = numpy.concatenate([p for p in newpoints if p!=None] )
#    ## print ' medDelta ', medDelta, deltaD[sortedDind[-1]]
#    ## print len(a) ,' ------> ', len(points)

    rel_norms = numpy.sqrt(numpy.sum( deltas**2, 1 )) / sizeC
    keep = numpy.concatenate([numpy.where( rel_norms >0.005 )[0], numpy.array([len(a)-1])])

    #return a[keep] , [ parsedList[i] for i in keep]
    #print len(a),' ',len(points)
    return points, []

rotMat = numpy.array( [[1, -1], [1, 1]] )/numpy.sqrt(2)
unrotMat = numpy.array( [[1, 1], [-1, 1]] )/numpy.sqrt(2)

def setupKnownAngles():
    pi = numpy.pi
    #l = [ i*pi/8 for i in range(0, 9)] +[ i*pi/6 for i in [1,2,4,5,] ]
    l = [ i*pi/8 for i in range(0, 9)] +[ i*pi/6 for i in [1, 2, 4, 5,] ] + [i*pi/12 for i in (1, 5, 7, 11)]
    knownAngle = numpy.array( l )
    return numpy.concatenate( [-knownAngle[:0:-1], knownAngle ])
knownAngle = setupKnownAngles()

_twopi =  2*numpy.pi
_pi = numpy.pi

def deltaAngle(a1, a2):
    d = a1 - a2 
    return d if d > -_pi else d+_twopi

def closeAngleAbs(a1, a2):
    d = abs(a1 - a2 )
    return min( abs(d-_pi), abs( _twopi - d), d)

def deltaAngleAbs(a1, a2):
    return abs(in_mPi_pPi(a1 - a2 ))

def in_mPi_pPi(a):
    if(a>_pi): return a-_twopi
    if(a<-_pi): return a+_twopi
    return a
vec_in_mPi_pPi = numpy.vectorize(in_mPi_pPi)

def D2(p1, p2):
    return ((p1-p2)**2).sum()

def D(p1, p2):
    return numpy.sqrt(D2(p1, p2) )

def norm(p):
    return numpy.sqrt( (p**2).sum() )

def computeBox(a):
    """returns the bounding box enclosing the array of points a
    in the form (x,y, width, height) """

    xmin, ymin = a[:, 0].min(), a[:, 1].min()
    xmax, ymax = a[:, 0].max(), a[:, 1].max()
    return xmin, ymin, xmax-xmin, ymax-ymin

def dirAndLength(p1, p2):
    #l = max(D(p1, p2) ,1e-4)
    l = D(p1, p2)
    uv = (p1-p2)/l
    return l, uv

def length(p1, p2):
    return numpy.sqrt( D2(p1, p2) )

def barycenter(points):
    """
    """
    return points.sum(axis=0)/len(points)
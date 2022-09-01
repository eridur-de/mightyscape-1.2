#!/usr/bin/env python3
# Based on gearUtils-03.js by Dr A.R.Collins
# Latest version:  <www.arc.id.au/gearDrawing.html>

# Calculation of Bezier coefficients for
# Higuchi et al. approximation to an involute.
# ref: YNU Digital Eng Lab Memorandum 05-1

from math import *

def rotate(p, t):
    return (p[0] * cos(t) - p[1] * sin(t), p[0] * sin(t) + p[1] * cos(t))

def SVG_move(p, t):
    pp = rotate(p, t)
    return 'M ' + str(pp[0]) + ',' + str(pp[1]) + '\n'

def SVG_line(p, t):
    pp = rotate(p, t)
    return 'L ' + str(pp[0]) + ',' + str(pp[1]) + '\n'

def SVG_circle(p, r, sweep, t):
    pp = rotate(p, t)
    return 'A ' + str(r) + ',' + str(r) + ' 0 0,' + str(sweep) + ' ' + str(pp[0]) + ',' + str(pp[1]) + '\n'

def SVG_curve(p, c1, c2, t):
    pp = rotate(p, t)
    c1p = rotate(c1, t)
    c2p = rotate(c2, t)
    return 'C ' + str(pp[0]) + ',' + str(pp[1]) + ' ' + str(c1p[0]) + ',' + str(c1p[1]) + ' ' + str(c2p[0]) + ',' + str(c2p[1]) + '\n'

def SVG_curve2(p1, c11, c12, p2, c21, c22, t):
    p1p = rotate(p1, t)
    c11p = rotate(c11, t)
    c12p = rotate(c12, t)
    p2p = rotate(p2, t)
    c21p = rotate(c21, t)
    c22p = rotate(c22, t)
    return 'C ' + str(p1p[0]) + ',' + str(p1p[1]) + ' ' + str(c11p[0]) + ',' + str(c11p[1]) + ' ' + str(c12p[0]) + ',' + str(c12p[1]) + ' ' + str(p2p[0]) + ',' + str(p2p[1]) + ' ' + str(c21p[0]) + ',' + str(c21p[1]) + ' ' + str(c22p[0]) + ',' + str(c22p[1]) + '\n'

def SVG_close():
    return 'Z\n'

def genInvolutePolar(Rb, R):  # Rb = base circle radius
    # returns the involute angle as function of radius R.
    return (sqrt(R*R - Rb*Rb) / Rb) - acos(Rb / R)

def rotate(pt, rads):  # rotate pt by rads radians about origin
    sinA = sin(rads)
    cosA = cos(rads)
    return [pt[0] * cosA - pt[1] * sinA,
            pt[0] * sinA + pt[1] * cosA]

def toCartesian(radius, angle):   # convert polar coords to cartesian
    return [radius * cos(angle), radius * sin(angle)]

def CreateExternalGear(m, Z, phi):
    # ****** external gear specifications
    addendum = m              # distance from pitch circle to tip circle
    dedendum = 1.25 * m         # pitch circle to root, sets clearance
    clearance = dedendum - addendum

    # Calculate radii
    Rpitch = Z * m / 2            # pitch circle radius
    Rb = Rpitch*cos(phi * pi / 180)  # base circle radius
    Ra = Rpitch + addendum    # tip (addendum) circle radius
    Rroot = Rpitch - dedendum # root circle radius
    fRad = 1.5 * clearance # fillet radius, max 1.5*clearance
    Rf = sqrt((Rroot + fRad) * (Rroot + fRad) - (fRad * fRad)) # radius at top of fillet
    if (Rb < Rf):
        Rf = Rroot + clearance

    # ****** calculate angles (all in radians)
    pitchAngle = 2 * pi / Z  # angle subtended by whole tooth (rads)
    baseToPitchAngle = genInvolutePolar(Rb, Rpitch)
    pitchToFilletAngle = baseToPitchAngle  # profile starts at base circle
    if (Rf > Rb):         # start profile at top of fillet (if its greater)
        pitchToFilletAngle -= genInvolutePolar(Rb, Rf)

    filletAngle = atan(fRad / (fRad + Rroot))  # radians

    # ****** generate Higuchi involute approximation
    fe = 1       # fraction of profile length at end of approx
    fs = 0.01    # fraction of length offset from base to avoid singularity
    if (Rf > Rb):
        fs = (Rf * Rf - Rb * Rb) / (Ra * Ra - Rb * Rb)  # offset start to top of fillet

    # approximate in 2 sections, split 25% along the involute
    fm = fs + (fe - fs) / 4   # fraction of length at junction (25% along profile)
    dedBez = BezCoeffs(m, Z, phi, 3, fs, fm)
    addBez = BezCoeffs(m, Z, phi, 3, fm, fe)

    dedInv = dedBez.involuteBezCoeffs()
    addInv = addBez.involuteBezCoeffs()

    # join the 2 sets of coeffs (skip duplicate mid point)
    inv = dedInv + addInv[1:]

    # create the back profile of tooth (mirror image)
    invR = [0 for i in range(0, len(inv))]  # involute profile along back of tooth
    for i in range(0, len(inv)):
        # rotate all points to put pitch point at y = 0
        pt = rotate(inv[i], -baseToPitchAngle - pitchAngle / 4)
        inv[i] = pt
        # generate the back of tooth profile nodes, mirror coords in X axis
        invR[i] = [pt[0], -pt[1]]

    # ****** calculate section junction points R=back of tooth, Next=front of next tooth)
    fillet = toCartesian(Rf, -pitchAngle / 4 - pitchToFilletAngle) # top of fillet
    filletR = [fillet[0], -fillet[1]]   # flip to make same point on back of tooth
    rootR = toCartesian(Rroot, pitchAngle / 4 + pitchToFilletAngle + filletAngle)
    rootNext = toCartesian(Rroot, 3 * pitchAngle / 4 - pitchToFilletAngle - filletAngle)
    filletNext = rotate(fillet, pitchAngle)  # top of fillet, front of next tooth

    # Draw the shapes in SVG
    t_inc = 2.0 * pi / float(Z)
    thetas = [(x * t_inc) for x in range(Z)]

    svg = SVG_move(fillet, 0) # start at top of fillet

    for theta in thetas:
        if (Rf < Rb):
            svg += SVG_line(inv[0], theta) # line from fillet up to base circle

        svg += SVG_curve2(inv[1], inv[2], inv[3],
                          inv[4], inv[5], inv[6], theta)

        svg += SVG_circle(invR[6], Ra, 1, theta) # arc across addendum circle

        # svg = SVG_move(invR[6]) # TEMP
        svg += SVG_curve2(invR[5], invR[4], invR[3],
                          invR[2], invR[1], invR[0], theta)

        if (Rf < Rb):
            svg += SVG_line(filletR, theta) # line down to topof fillet

        if (rootNext[1] > rootR[1]):    # is there a section of root circle between fillets?
            svg += SVG_circle(rootR, fRad, 0, theta) # back fillet
            svg += SVG_circle(rootNext, Rroot, 1, theta) # root circle arc

        svg += SVG_circle(filletNext, fRad, 0, theta)

    svg += SVG_close()

    return svg

def CreateInternalGear(m, Z, phi):
    addendum = 0.6 * m         # pitch circle to tip circle (ref G.M.Maitra)
    dedendum = 1.25 * m        # pitch circle to root radius, sets clearance

    # Calculate radii
    Rpitch = Z * m / 2           # pitch radius
    Rb = Rpitch * cos(phi * pi / 180)  # base radius
    Ra = Rpitch - addendum   # addendum radius
    Rroot = Rpitch + dedendum# root radius
    clearance = 0.25 * m       # gear dedendum - pinion addendum
    Rf = Rroot - clearance   # radius of top of fillet (end of profile)
    fRad = 1.5 * clearance     # fillet radius, 1 .. 1.5*clearance

    # ****** calculate subtended angles
    pitchAngle = 2 * pi / Z  # angle between teeth (rads)
    baseToPitchAngle = genInvolutePolar(Rb, Rpitch)
    tipToPitchAngle = baseToPitchAngle   # profile starts from base circle
    if (Ra > Rb):
        tipToPitchAngle -= genInvolutePolar(Rb, Ra)  # start profile from addendum
    pitchToFilletAngle = genInvolutePolar(Rb, Rf) - baseToPitchAngle
    filletAngle = 1.414 * clearance / Rf # to make fillet tangential to root

    # ****** generate Higuchi involute approximation
    fe = 1      # fraction of involute length at end of approx (fillet circle)
    fs = 0.01   # fraction of length offset from base to avoid singularity
    if (Ra > Rb):
        fs = (Ra*Ra - Rb*Rb) / (Rf*Rf - Rb*Rb)    # start profile from addendum (tip circle)

    # approximate in 2 sections, split 25% along the profile
    fm = fs + (fe - fs) / 4

    addBez = BezCoeffs(m, Z, phi, 3, fs, fm)
    dedBez = BezCoeffs(m, Z, phi, 3, fm, fe)
    addInv = addBez.involuteBezCoeffs()
    dedInv = dedBez.involuteBezCoeffs()

    # join the 2 sets of coeffs (skip duplicate mid point)
    invR = addInv + dedInv[1:]

    # create the front profile of tooth (mirror image)
    inv = [0 for i in range(0, len(invR))] # back involute profile
    for i in range(0, len(inv)):
        # rotate involute to put center of tooth at y = 0
        pt = rotate(invR[i], pitchAngle / 4 - baseToPitchAngle)
        invR[i] = pt
        # generate the back of tooth profile, flip Y coords
        inv[i] = [pt[0], -pt[1]]

    # ****** calculate coords of section junctions
    fillet = [inv[6][0], inv[6][1]]    # top of fillet, front of tooth
    tip = toCartesian(Ra, -pitchAngle / 4 + tipToPitchAngle)  # tip, front of tooth
    tipR = [tip[0], -tip[1]]  # addendum, back of tooth
    rootR = toCartesian(Rroot, pitchAngle / 4 + pitchToFilletAngle + filletAngle)
    rootNext = toCartesian(Rroot, 3 * pitchAngle / 4 - pitchToFilletAngle - filletAngle)
    filletNext = rotate(fillet, pitchAngle)  # top of fillet, front of next tooth

    # Draw the shapes in SVG
    t_inc = 2.0 * pi / float(Z)
    thetas = [(x * t_inc) for x in range(Z)]

    svg = SVG_move(fillet, 0) # start at top of fillet

    for theta in thetas:
        svg += SVG_curve2(inv[5], inv[4], inv[3],
                          inv[2], inv[1], inv[0], theta)

        if (Ra < Rb):
            svg += SVG_line(tip, theta) # line from end of involute to addendum (tip)

        svg += SVG_circle(tipR, Ra, 1, theta) # arc across tip circle

        if (Ra < Rb):
            svg += SVG_line(invR[0], theta) # line from addendum to start of involute

        svg += SVG_curve2(invR[1], invR[2], invR[3],
                          invR[4], invR[5], invR[6], theta)

        if (rootR[1] < rootNext[1]):    # there is a section of root circle between fillets
            svg += SVG_circle(rootR, fRad, 1, theta) # fillet on back of tooth

            svg += SVG_circle(rootNext, Rroot, 1, theta) # root circle arc

        svg += SVG_circle(filletNext, fRad, 1, theta) # fillet on next

    return svg

class BezCoeffs:
    def chebyExpnCoeffs(self, j, func):
        N = 50      # a suitably large number  N>>p
        c = 0
        for k in range(1, N + 1):
            c += func(cos(pi * (k - 0.5) / N)) * cos(pi * j * (k - 0.5) / N)

        return 2 *c / N

    def chebyPolyCoeffs(self, p, func):
        coeffs = [0, 0, 0, 0]
        fnCoeff = [0, 0, 0, 0]
        T = [[1, 0, 0, 0, 0], 
             [0, 1, 0, 0, 0],
             [0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0]
             ]

        # now generate the Chebyshev polynomial coefficient using
        # formula T(k+1) = 2xT(k) - T(k-1) which yields
        # T = [ [ 1,  0,  0,  0,  0,  0],    # T0(x) =  +1
        #       [ 0,  1,  0,  0,  0,  0],    # T1(x) =   0  +x
        #       [-1,  0,  2,  0,  0,  0],    # T2(x) =  -1  0  +2xx
        #       [ 0, -3,  0,  4,  0,  0],    # T3(x) =   0 -3x    0   +4xxx
        #       [ 1,  0, -8,  0,  8,  0],    # T4(x) =  +1  0  -8xx       0  +8xxxx
        #       [ 0,  5,  0,-20,  0, 16],    # T5(x) =   0  5x    0  -20xxx       0  +16xxxxx
        #     ...                     ]

        for k in range(1, p + 1):
            for j in range(0, len(T[k]) - 1):
                T[k + 1][j + 1] = 2 * T[k][j]
            for j in range(0, len(T[k - 1])):
                T[k + 1][j] -= T[k - 1][j]
                
        # convert the chebyshev function series into a simple polynomial
        # and collect like terms, out T polynomial coefficients
        for k in range(0, p + 1):
            fnCoeff[k] = self.chebyExpnCoeffs(k, func)
            coeffs[k] = 0

        for k in range(0, p + 1):
            for pwr in range(0, p + 1):
                coeffs[pwr] += fnCoeff[k] * T[k][pwr]

        coeffs[0] -= self.chebyExpnCoeffs(0, func) / 2  # fix the 0th coeff

        return coeffs

    # Equation of involute using the Bezier parameter t as variable
    def involuteXbez(self, t):
        # map t (0 <= t <= 1) onto x (where -1 <= x <= 1)
        x = t * 2 - 1
        # map theta (where ts <= theta <= te) from x (-1 <=x <= 1)
        theta = x * (self.te - self.ts) / 2 + (self.ts + self.te) / 2
        return self.Rb * (cos(theta) + theta * sin(theta))

    def involuteYbez(self, t):
        # map t (0 <= t <= 1) onto x (where -1 <= x <= 1)
        x = t * 2 - 1
        # map theta (where ts <= theta <= te) from x (-1 <=x <= 1)
        theta = x * (self.te - self.ts) / 2 + (self.ts + self.te) / 2
        return self.Rb * (sin(theta) - theta * cos(theta))

    def binom(self, n, k):
        coeff = 1
        for i in range(n - k + 1, n + 1):
            coeff *= i

        for i in range(1, k + 1):
            coeff /= i

        return coeff

    def bezCoeff(self, i, func):
        # generate the polynomial coeffs in one go
        polyCoeffs = self.chebyPolyCoeffs(self.p, func)

        bc = 0
        for j in range(0, i + 1):
            bc += self.binom(i, j) * polyCoeffs[j] / self.binom(self.p, j)

        return bc

    def involuteBezCoeffs(self):
        # calc Bezier coeffs
        bzCoeffs = []
        for i in range(0, self.p + 1):
            bcoeff = [0, 0]
            bcoeff[0] = self.bezCoeff(i, self.involuteXbez)
            bcoeff[1] = self.bezCoeff(i, self.involuteYbez)
            bzCoeffs.append(bcoeff)

        return bzCoeffs

    # Parameters:
    # module - sets the size of teeth (see gear design texts)
    # numTeeth - number of teeth on the gear
    # pressure angle - angle in degrees, usually 14.5 or 20
    # order - the order of the Bezier curve to be fitted [3, 4, 5, ..]
    # fstart - fraction of distance along tooth profile to start
    # fstop - fraction of distance along profile to stop
    def __init__(self, module, numTeeth, pressureAngle, order, fstart, fstop):
        self.Rpitch = module * numTeeth / 2       # pitch circle radius
        self.phi = pressureAngle        # pressure angle
        self.Rb = self.Rpitch * cos(self.phi * pi / 180) # base circle radius
        self.Ra = self.Rpitch + module               # addendum radius (outer radius)
        self.ta = sqrt(self.Ra * self.Ra - self.Rb * self.Rb) / self.Rb   # involute angle at addendum
        self.stop = fstop
        
        if (fstart < self.stop):
            self.start = fstart

        self.te = sqrt(self.stop) * self.ta          # involute angle, theta, at end of approx
        self.ts = sqrt(self.start) * self.ta         # involute angle, theta, at start of approx
        self.p = order                     # order of Bezier approximation
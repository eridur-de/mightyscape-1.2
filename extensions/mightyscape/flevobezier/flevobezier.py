#!/usr/bin/env python3
# Flevobezier: an Inkscape extension fitting Bezier curves
# Parcly Taxel / Jeremy Tan, 2019
# https://gitlab.com/parclytaxel

from __future__ import division
from math import *
from inkex.bezier import bezierpointatt
import inkex
import gettext
from inkex.paths import Path
import sys
def pout(t): sys.exit((gettext.gettext(t)))

class FlevoBezier(inkex.EffectExtension):

    def effect(self):
        if len(self.svg.selected) == 0: pout("Please select at least one path.")
        for obj in self.svg.selected: # The objects are the paths, which may be compound
            curr = self.svg.selected[obj]
            raw = Path(curr.get("d")).to_arrays()
            subpaths, prev = [], 0
            for i in range(len(raw)): # Breaks compound paths into simple paths
                if raw[i][0] == 'M' and i != 0:
                    subpaths.append(raw[prev:i])
                    prev = i
            subpaths.append(raw[prev:])
			
            output = ""
            for simpath in subpaths:
                closed = False
                if simpath[-1][0] == 'Z':
                    closed = True
                    if simpath[-2][0] == 'L': simpath[-1][1] = simpath[0][1]
                    else: simpath.pop()
                #nodes = [node(simpath[i][1][-2:]) for i in range(len(simpath))]
                nodes = []
                for i in range(len(simpath)):
                    if simpath[i][0] == 'V': # vertical and horizontal lines only have one point in args, but 2 are required
                        #inkex.utils.debug(simpath[i][0])
                        simpath[i][0]='L' #overwrite V with regular L command
                        add=simpath[i-1][1][0] #read the X value from previous segment
                        simpath[i][1].append(simpath[i][1][0]) #add the second (missing) argument by taking argument from previous segment
                        simpath[i][1][0]=add #replace with recent X after Y was appended
                    if simpath[i][0] == 'H': # vertical and horizontal lines only have one point in args, but 2 are required
                        #inkex.utils.debug(simpath[i][0])
                        simpath[i][0]='L' #overwrite H with regular L command
                        simpath[i][1].append(simpath[i-1][1][1]) #add the second (missing) argument by taking argument from previous segment				
                    #inkex.utils.debug(simpath[i])
                    nodes.append(node(simpath[i][1][-2:]))
                output += flevobezier(nodes, closed)
            curr.set("d", output)
			
# The main algorithm! Yay!
def flevobezier(points, z):
    if len(points) < 2: pout("A curve isn't a point, silly!")
    res = []
    prevtrail, trail, lead, window = 0, 0, 1, points[:2] # Start with first two points
    maybeover = False # Over by error followed by over by angle -> backup
    curcurve = [window[0], slide(window[0], window[1], 1 / 3), slide(window[0], window[1], 2 / 3), window[1]] # Current working curve, always a 4-list
    while lead + 1 < len(points):
        lead += 1
        window = points[trail:lead + 1] # Extend the window one more node
        v = window[-3] - window[-2]
        w = window[-1] - window[-2]
        try:
            dist(v) / dist(w)
        except ZeroDivisionError as e:
            pout("Division by zero. Check if your path contains duplicate handles.")
        if dotp(v, w) / dist(v) / dist(w) >= 0.5: # 60 degrees or less, over by angle
            if maybeover: # backup
                newcurve = stress(points[prevtrail:lead])[0]
                res[-3:] = newcurve[1:] # replace the last three nodes in res with those of newcurve
                trail = lead - 1
                maybeover = False
            else:
                if not res: res += curcurve[:1]
                res += curcurve[1:]
                prevtrail = trail
            trail = lead - 1
            window = points[trail:lead + 1]
            curcurve = [window[0], slide(window[0], window[1], 1 / 3), slide(window[0], window[1], 2 / 3), window[1]]
        else: # then see what to do based on how long the window is
            over = False
            if len(window) == 3: # Quadratic curve on three nodes stepped to a cubic
                t = chords(window)[1]
                qcurve = [window[0], (window[1] - (1 - t) * (1 - t) * window[0] - t * t * window[2]) / (2 * t * (1 - t)), window[2]]
                newcurve = [qcurve[0], slide(qcurve[0], qcurve[1], 2 / 3), slide(qcurve[1], qcurve[2], 1 / 3), qcurve[2]]
            elif len(window) == 4: # Cubic curve on four nodes
                newcurve = cubicfrom4(window)
            else: # Stress
                product = stress(window)
                shortseg = min([dist(window[i], window[i + 1]) for i in range(len(window) - 1)])
                # Stop condition: maximum error > 1 / 3 * minimum segment length
                if max(product[1]) > 0.33 * shortseg: over = True
                else: newcurve = product[0]
            if over: # Over by error bound
                maybeover = True
                if not res: res += curcurve[:1]
                res += curcurve[1:]
                prevtrail = trail
                trail = lead - 1
                window = points[trail:lead + 1]
                curcurve = [window[0], slide(window[0], window[1], 1 / 3), slide(window[0], window[1], 2 / 3), window[1]]
            else: curcurve, maybeover = newcurve, False
    if maybeover: # When it has reached the end...
        newcurve = stress(points[prevtrail:lead + 1])[0]
        res[-3:] = newcurve[1:]
    else:
        if not res: res += curcurve[:1]
        res += curcurve[1:] # If it has reached the end, accept curcurve
    # Smoothing
    ouro = res.pop() # Removes the final (redundant) node of closed paths. In the end, does not affect open paths.
    for t in range(0, len(res), 3):
        if t != 0 or z: # If not at beginning or if path is closed
            v = res[t - 1] - res[t] # Previous handle
            w = res[t + 1] - res[t] # Next handle
            try:
                angle = dotp(v, w) / dist(v) / dist(w)
                if angle <= -0.94: # ~ cos(160 degrees)
                    # Rotate opposing handles and make a straight line.
                    theta = (pi - acos(angle)) / 2 # Angle to rotate by
                    sign = 1 if (dirc(v) > dirc(w)) ^ (abs(dirc(v) - dirc(w)) >= pi) else -1 # Direction to rotate (WTF?)
                    res[t - 1] = res[t] + spin(v, sign * theta)
                    res[t + 1] = res[t] + spin(w, -sign * theta)
            except ZeroDivisionError:
                pout("Path has only one point left. Cannot continue")
    res.append(ouro)
    # Formatting and final output
    out = "M " + str(res[0])
    for c in range(1, len(res), 3): out += " ".join([" C", str(res[c]), str(res[c + 1]), str(res[c + 2])])
    if z: out += " Z "
    return out

'''Helper functions and classes below'''

# Node object as a helper to simplify code. Calling it point would be SO cliched.
class node:
    def __init__(self, x = None, y = None):
        if y != None: self.x, self.y = float(x), float(y)
        elif type(x) == list or type(x) == tuple: self.x, self.y = float(x[0]), float(x[1])
        else: self.x, self.y = 0.0, 0.0
    def __str__(self): return str(self.x) + " " + str(self.y)
    def __repr__(self): return str(self)
    def __add__(self, pode): return node(self.x + pode.x, self.y + pode.y) # Vector addition
    def __sub__(self, pode): return node(self.x - pode.x, self.y - pode.y) # and subtraction
    def __neg__(self): return node(-self.x, -self.y)
    def __mul__(self, scal): # Multiplication by a scalar
        if type(scal) == int or type(scal) == float: return node(self.x * scal, self.y * scal)
        else: return node(self.x * scal.x - self.y * scal.y, self.y * scal.x + self.x * scal.y) # Fallback does complex multiplication
    def __rmul__(self, scal): return self * scal
    def __truediv__(self, scal): # Division by a scalar
        if type(scal) == int or type(scal) == float: return node(self.x / scal, self.y / scal)
        else:
            n = scal.x * scal.x + scal.y * scal.y
            return node(self.x * scal.x + self.y * scal.y, self.y * scal.x - self.x * scal.y) / n # Fallback does complex division

# Operations on nodes
def dist(n0, n1 = None): return hypot(n1.y - n0.y, n1.x - n0.x) if n1 else hypot(n0.y, n0.x) # For these two functions
def dirc(n0, n1 = None): return atan2(n1.y - n0.y, n1.x - n0.x) if n1 else atan2(n0.y, n0.x) # n0 is the origin if n1 is present
def slide(n0, n1, t): return n0 + t * (n1 - n0)
def dotp(n0, n1): return n0.x * n1.x + n0.y * n1.y

# Operation on vectors: rotation. Positive theta means counterclockwise rotation.
def spin(v, theta): return node(v.x * cos(theta) - v.y * sin(theta), v.x * sin(theta) + v.y * cos(theta))

# Wrapper function for node curves to mesh with bezierpointatt
def curveat(curve, t): return node(bezierpointatt(((node.x, node.y) for node in curve), t))

# This function takes in a list of nodes and returns
# a list of numbers between 0 and 1 corresponding to the relative positions
# of said nodes (assuming consecutive nodes are linked by straight lines).
# The first item is always 0.0 and the last one 1.0.
def chords(nodes):
    lengths = [dist(nodes[i + 1], nodes[i]) for i in range(len(nodes) - 1)]
    ratios = [0.0] + [sum(lengths[:i + 1]) / sum(lengths) for i in range(len(lengths))]
    ratios[-1] = 1.0 # Just in case...
    return ratios

# Takes a list of four nodes and generates a curve passing through all based on chords().
# If lm and mu (the two params for the middle nodes) are not given they are calculated.
def cubicfrom4(nodes, p = None, q = None):
    if p == None or q == None:
        store = chords(nodes)
        lm, mu = store[1], store[2] # First one is short for lambda
    else: lm, mu = p, q
    a = 3 * (1 - lm) * (1 - lm) * lm
    b = 3 * (1 - lm) *      lm  * lm
    c = 3 * (1 - mu) * (1 - mu) * mu
    d = 3 * (1 - mu) *      mu  * mu
    x = nodes[1] - (1 - lm) ** 3 * nodes[0] - lm ** 3 * nodes[3]
    y = nodes[2] - (1 - mu) ** 3 * nodes[0] - mu ** 3 * nodes[3]
    det = a * d - b * c
    if not det: pout("Singular matrix!")
    l, m = (d * x - b * y) / det, (a * y - c * x) / det
    return [nodes[0], l, m, nodes[3]]

# Stress theory: takes a list of five or more nodes and stresses a curve to fit
def stress(string):
    # Make an initial guess considering the end nodes together with the 2nd/2nd last, 3rd/3rd last, ... nodes.
    # This is much faster than considering all sets of two interior nodes.
    callipers, seeds = chords(string), []
    middle = len(string) // 2
    for i in range(1, middle):
        seeds.append(cubicfrom4([string[0], string[i], string[-i - 1], string[-1]], callipers[i], callipers[-i - 1]))
    a, b = node(), node()
    for i in range(len(seeds)):
        a += seeds[i][1]
        b += seeds[i][2]
    curve = [string[0], a / len(seeds), b / len(seeds), string[-1]]
    # Refine by projection and handle shifting
    for i in range(5):
        for j in range(middle - 1, 0, -1):
            delta1, delta2 = project(curve, string[j]), project(curve, string[-j - 1])
            curve[1] += 2.5 * delta1
            curve[2] += 2.5 * delta2
    errors = [dist(project(curve, k)) for k in string]
    return curve, errors

# Projection of node onto cubic curve based on public domain code by Mike "Pomax" Kamermans
# https://pomax.github.io/bezierinfo/#projections
def project(curve, node):
    samples = 200
    lookup = [dist(curveat(curve, i / samples), node) for i in range(samples + 1)]
    mindist = min(lookup)
    t = lookup.index(mindist) / samples
    width = 1 / samples # Width of search interval
    while width > 1.0e-5:
        left  = dist(curveat(curve, max(t - width, 0)), node)
        right = dist(curveat(curve, min(t + width, 1)), node)
        if t == 0.0: left  = mindist + 1
        if t == 1.0: right = mindist + 1
        if left < mindist or right < mindist:
            mindist = min(left, right)
            t = max(t - width, 0.0) if left < right else min(t + width, 1.0)
        else: width /= 2
    projection = curveat(curve, t)
    return node - projection
    
if __name__ == '__main__':
    FlevoBezier().run()
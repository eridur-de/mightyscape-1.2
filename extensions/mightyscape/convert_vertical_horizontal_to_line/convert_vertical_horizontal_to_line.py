#!/usr/bin/env python3

#M 60.403,71.0937 V 89.268022 135.773

"""
Extension for InkScape 1.X

This extension converts an SVG path's d attribute the following way: find each V (vertical line) and each H (horizontal line) and replace it by a generic line (L type). 
A lot of extensions do not work with V and H, but with L commands. So this is just a helper extension for other extensions :-)

Example conversion:
from: M 60.403,71.0937 V 89.268022 135.773
to:   M 60.403 71.0937 L 60.403 89.268 L 60.403 135.773

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 23.08.2020
Last patch: 23.08.2020
License: GNU GPL v3
"""

from math import *
import inkex
from inkex.paths import Path, CubicSuperPath

class ConvertVerticalHorizontalToLine(inkex.EffectExtension):

    def effect(self):
        if len(self.svg.selected) == 0: exit("Please select at least one path.")
        for obj in self.svg.selected: # The objects are the paths, which may be compound
            if obj.tag == inkex.addNS('path','svg'):
                curr = self.svg.selected[obj]
                raw = Path(curr.get("d")).to_arrays()
                subpaths, prev = [], 0
                for i in range(len(raw)): # Breaks compound paths into simple paths
                    if raw[i][0] == 'M' and i != 0:
                        subpaths.append(raw[prev:i])
                        prev = i
                subpaths.append(raw[prev:])
    			
                seg = []
                for simpath in subpaths:
                    if simpath[-1][0] == 'Z':
                        simpath[-1][0] = 'L'
                        if simpath[-2][0] == 'L': simpath[-1][1] = simpath[0][1]
                        else: simpath.pop()
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
                        seg.append(simpath[i])
                curr.set("d", Path(seg))
            else:
                inkex.utils.debug("Object " + obj.get('id') + " is not a path. Please convert it to a path first.")
if __name__ == '__main__':
    ConvertVerticalHorizontalToLine().run()
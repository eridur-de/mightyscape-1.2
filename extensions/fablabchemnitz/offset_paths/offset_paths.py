#!/usr/bin/env python3

"""
Based on 
- https://github.com/TimeTravel-0/ofsplot

ToDo's
- break apart combined paths
- option to handle groups 

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Last Patch: 10.06.2021
License: GNU GPL v3

"""

import inkex
import math
from inkex.paths import CubicSuperPath
import re
import copy
import pyclipper

class OffsetPaths(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--tab')
        pars.add_argument('--unit')
        pars.add_argument("--offset_count", type=int, default=1, help="Number of offset paths")
        pars.add_argument("--offset", type=float, default=1.000, help="Offset amount")
        pars.add_argument("--init_offset", type=float, default=0.000, help="Initial Offset Amount")
        pars.add_argument("--offset_increase", type=float, default=0.000, help="Offset increase between iterations")
        pars.add_argument("--jointype", default="2", help="Join type")
        pars.add_argument("--endtype", default="3", help="End type")
        pars.add_argument("--miterlimit", type=float, default=3.0, help="Miter limit")
        pars.add_argument("--clipperscale", type=int, default=1024, help="Scaling factor. Should be a multiplicator of 2, like 2^4=16 or 2^10=1024. The higher the scale factor the higher the quality.")
        pars.add_argument("--copy_org", type=inkex.Boolean, default=True, help="copy original path")
        pars.add_argument("--individual", type=inkex.Boolean, default=True, help="Separate into individual paths")
        pars.add_argument("--group", type=inkex.Boolean, default=True, help="Put all offset paths into group")
        pars.add_argument("--path_types", default="both", help="Process open, closed or all paths!")
        
        
    def effect(self):
        unit_factor = 1.0 / self.svg.uutounit(1.0, self.options.unit)
        pathElements = self.svg.selection.filter(inkex.PathElement).values()
        count = sum(1 for pathElement in pathElements)
        pathElements = self.svg.selection.filter(inkex.PathElement).values() #we need to call this twice because the sum function consumes the generator
        if count == 0:
            inkex.errormsg("No paths selected.")
            exit()
        for pathElement in pathElements:
            csp = CubicSuperPath(pathElement.get('d'))
            
            '''
            check for closed or open paths
            '''
            isClosed = False
            raw = pathElement.path.to_arrays()
            if raw[-1][0] == 'Z' or \
                (raw[-1][0] == 'L' and raw[0][1] == raw[-1][1]) or \
                (raw[-1][0] == 'C' and raw[0][1] == [raw[-1][1][-2], raw[-1][1][-1]]) \
                :  #if first is last point the path is also closed. The "Z" command is not required
                isClosed = True
            if self.options.path_types == "open_paths" and isClosed is True:
                continue #skip this loop iteration
            elif self.options.path_types == "closed_paths" and isClosed is False:
                continue #skip this loop iteration
                        
            scale_factor = self.options.clipperscale # 2 ** 32 = 1024 - see also https://github.com/fonttools/pyclipper/wiki/Deprecating-SCALING_FACTOR
            pco = pyclipper.PyclipperOffset(self.options.miterlimit)
            
            JT = None #join types
            if self.options.jointype == "0":
                JT = pyclipper.JT_SQUARE
            elif self.options.jointype == "1":
                JT = pyclipper.JT_ROUND
            elif self.options.jointype == "2":
                JT = pyclipper.JT_MITER
                
            ET = None #end types
            if self.options.endtype == "0":
                ET = pyclipper.ET_CLOSEDPOLYGON
            elif self.options.endtype == "1":
                ET = pyclipper.ET_CLOSEDLINE
            elif self.options.endtype == "2":
                ET = pyclipper.ET_OPENBUTT
            elif self.options.endtype == "3":
                ET = pyclipper.ET_OPENSQUARE
            elif self.options.endtype == "4":                 
                ET = pyclipper.ET_OPENROUND
            
            newPaths = []

            # load in initial paths
            for subPath in csp:
                sub_simple = []
                for item in subPath:
                    itemx = [float(z) * scale_factor for z in item[1]]
                    sub_simple.append(itemx)
                pco.AddPath(sub_simple, JT, ET)

            # calculate offset paths for different offset amounts
            offset_list = []
            offset_list.append(self.options.init_offset * unit_factor)
            for i in range(0, self.options.offset_count):
                ofs_increase = +math.pow(float(i) * self.options.offset_increase * unit_factor, 2)
                if self.options.offset_increase < 0:
                    ofs_increase = -ofs_increase
                offset_list.append(offset_list[0] + float(i) * self.options.offset * unit_factor + ofs_increase * unit_factor)

            solutions = []
            for offset in offset_list:
                solution = pco.Execute(offset * scale_factor)
                solutions.append(solution)
                if len(solution) <= 0:
                    continue # no more loops to go, will provide no results.

            # re-arrange solutions to fit expected format & add to array
            for solution in solutions:
                for sol in solution:
                    solx = [[float(s[0]) / scale_factor, float(s[1]) / scale_factor] for s in sol]
                    sol_p = [[a, a, a] for a in solx]
                    sol_p.append(sol_p[0][:])
                    if sol_p not in newPaths:
                        newPaths.append(sol_p)

            if self.options.individual is True:
                parent = pathElement.getparent()
                if self.options.group is True: parentGroup = parent.add(inkex.Group(id="g-offset-{}".format(pathElement.attrib["id"])))
                idx = parent.index(pathElement) + 1
                idSuffix = 0
                for newPath in newPaths:
                    copyElement = copy.copy(pathElement)
                    elementId = copyElement.get('id')
                    copyElement.path = CubicSuperPath(newPath)
                    copyElement.set('id', elementId + str(idSuffix))
                    if self.options.group is True:
                        parentGroup.append(copyElement)
                    else:
                        parent.append(copyElement)
                    idSuffix += 1
                if self.options.group is True: parent.insert(idx, parentGroup)
                if self.options.copy_org is False:
                    pathElement.delete()
            else:
                if self.options.copy_org is True:
                    for subPath in csp:
                        newPaths.append(subPath)
                pathElement.set('d', CubicSuperPath(newPaths))

if __name__ == '__main__':
    OffsetPaths().run()
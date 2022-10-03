#!/usr/bin/env python3

'''
Extension for InkScape 1.0+

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 03.08.2020
Last patch: 04.11.2021
License: GNU GPL v3

ToDo:
    - id sorting: handle ids with/without numbers and sort by number

'''

import sys
import colorsys
import copy
import inkex
from inkex import Color, CubicSuperPath
from inkex.bezier import csplength, csparea

sys.path.append("../remove_empty_groups")
sys.path.append("../apply_transformations")

class FilterByLengthArea(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--tab')
        pars.add_argument('--debug', type=inkex.Boolean, default=False)
        pars.add_argument("--apply_transformations", type=inkex.Boolean, default=False, help="Run 'Apply Transformations' extension before running vpype. Helps avoiding geometry shifting")
        pars.add_argument("--breakapart", type=inkex.Boolean, default=True, help="Break apart selected path(s) into segments")
        pars.add_argument("--breakapart_total", type=inkex.Boolean, default=True, help="Gives the best results for nodes/<interval> filtering")
        pars.add_argument("--cleanup", type=inkex.Boolean, default = True, help = "Cleanup all unused groups/layers (requires separate extension)")
        pars.add_argument('--unit')
        pars.add_argument('--min_filter_enable', type=inkex.Boolean, default=True, help='Enable filtering min.')
        pars.add_argument('--min_threshold', type=float, default=0.000, help='Remove paths with an threshold smaller than this value')
        pars.add_argument('--max_filter_enable', type=inkex.Boolean, default=False, help='Enable filtering max.')
        pars.add_argument('--max_threshold', type=float, default=10000000.000, help='Remove paths with an threshold bigger than this value')
        pars.add_argument('--min_nodes', type=int, default=0, help='Min. nodes/<interval>')
        pars.add_argument('--max_nodes', type=int, default=10000000, help='Max. nodes/<interval>')
        pars.add_argument('--nodes_interval', type=float, default=10000000.000, help='Interval')
        pars.add_argument('--precision', type=int, default=3, help='Precision')
        pars.add_argument('--measure', default="length")
        pars.add_argument('--delete', type=inkex.Boolean, default=False)
        pars.add_argument('--color_mode', default="none")
        pars.add_argument('--color_single', type=Color, default='0xff00ffff')
        pars.add_argument('--sort_by_value', type=inkex.Boolean, default=False)
        pars.add_argument('--reverse_sort_value', type=inkex.Boolean, default=False)
        pars.add_argument('--sort_by_id', type=inkex.Boolean, default=False)
        pars.add_argument('--reverse_sort_id', type=inkex.Boolean, default=False)    
        pars.add_argument('--rename_ids', type=inkex.Boolean, default=False)    
        pars.add_argument('--set_labels', type=inkex.Boolean, default=False, help="Adds type and value to the element's label")    
        pars.add_argument('--remove_labels', type=inkex.Boolean, default=False, help="Remove labels (cleaning option for previous applications)")    
        pars.add_argument('--group', type=inkex.Boolean, default=False)    
  
    def breakContours(self, element, breakelements = None): #this does the same as "CTRL + SHIFT + K"
        if breakelements == None:
            breakelements = []
        if element.tag == inkex.addNS('path','svg'):
            parent = element.getparent()
            idx = parent.index(element)
            idSuffix = 0    
            raw = element.path.to_arrays()
            subPaths, prev = [], 0
            if self.options.breakapart_total is False:
                for i in range(len(raw)): # Breaks compound paths into simple paths
                    if raw[i][0] == 'M' and i != 0:
                        subPaths.append(raw[prev:i])
                        prev = i
                subPaths.append(raw[prev:])
            else:
                rawCopy = element.path.to_arrays() #we need another set of the same path
                for i in range(len(raw)): # Breaks compound paths into simple paths
                    if i != 0:
                        if raw[i][0]  == 'C': 
                            rawCopy[i][1] = [raw[i][1][-2], raw[i][1][-1]]
                        elif raw[i][0]  == 'L':
                            rawCopy[i][1] = [raw[i][1][0], raw[i][1][1]]
                        elif raw[i][0] == 'Z': #replace Z with another L command (which moves to the coordinates of the first M command in path) to have better overview
                            raw[-1][0] = 'L'
                            raw[-1][1] = raw[0][1]
                        rawCopy[i][0] = 'M' #we really need M. Does not matter if 'L' or 'C'.
                        #self.msg("s1={},s2={}".format(rawCopy[i-1], raw[i]))
                        subPaths.append([rawCopy[i-1], raw[i]])
                        prev = i
                subPaths = subPaths[::-1]
                    
            for subpath in subPaths:
                #self.msg(subpath)
                replacedelement = copy.copy(element)
                oldId = replacedelement.get('id')
                csp = CubicSuperPath(subpath)
                if len(subpath) > 1 and csp[0][0] != csp[0][1]: #avoids pointy paths like M "31.4794 57.6024 Z"
                    replacedelement.set('d', csp)
                    if len(subPaths) == 1:
                        replacedelement.set('id', "{}".format(oldId))
                    else:
                        replacedelement.set('id', "{}-{}".format(oldId, str(idSuffix)))
                        idSuffix += 1
                    parent.insert(idx, replacedelement)
                    breakelements.append(replacedelement)
            parent.remove(element)
        for child in element.getchildren():
            self.breakContours(child, breakelements)
        return breakelements
        
    def effect(self):
        global to_sort, so
        to_sort = []
        so = self.options
       
        applyTransformationsAvailable = False # at first we apply external extension
        try:
            import apply_transformations
            applyTransformationsAvailable = True
        except Exception as e:
            # self.msg(e)
            self.msg("Calling 'Apply Transformations' extension failed. Maybe the extension is not installed. You can download it from official InkScape Gallery. Skipping ...")           
       
        so.min_threshold = self.svg.unittouu(str(so.min_threshold) + self.svg.unit)
        so.max_threshold = self.svg.unittouu(str(so.max_threshold) + self.svg.unit)
        unit_factor = 1.0 / self.svg.uutounit(1.0, so.unit)
        if so.min_threshold == 0 or so.max_threshold == 0:
            inkex.utils.debug("One or both tresholds are zero. Please adjust.")
            return
        
        elements = []
        if len(self.svg.selected) > 0:
            for element in self.svg.selection.values():
                elements.extend(self.breakContours(element, None))
        else:
            data = self.document.xpath("//svg:path", namespaces=inkex.NSS)
            for element in data:
                elements.extend(self.breakContours(element, None))

        if so.debug is True: 
            inkex.utils.debug("Collecting svg:path elements ...")
            
        for element in elements: 
            # additional option to apply transformations. As we clear up some groups to form new layers, we might lose translations, rotations, etc.
            if so.apply_transformations is True and applyTransformationsAvailable is True:
                apply_transformations.ApplyTransformations().recursiveFuseTransform(element) 
            
            try:
                csp = element.path.transform(element.composed_transform()).to_superpath()

                if so.measure == "area":
                    area = round(-csparea(csp), so.precision) #is returned as negative value. we need to invert with
                    if (so.min_filter_enable is True and area < (so.min_threshold * (unit_factor * unit_factor))) or \
                       (so.max_filter_enable is True and area >= (so.max_threshold * (unit_factor * unit_factor))) or \
                       (so.min_filter_enable is False and so.max_filter_enable is False): #complete selection
                        if so.debug is True: 
                            inkex.utils.debug("id={}, area={:0.3f}{}^2".format(element.get('id'), area, so.unit))
                        to_sort.append({'element': element, 'value': area, 'type': 'area'})
                                       
                elif so.measure == "length":
                    slengths, stotal = csplength(csp) #get segment lengths and total length of path in document's internal unit
                    stotal = round(stotal, so.precision)
                    if (so.min_filter_enable is True and stotal < (so.min_threshold * unit_factor)) or \
                       (so.max_filter_enable is True and stotal >= (so.max_threshold * unit_factor)) or \
                       (so.min_filter_enable is False and so.max_filter_enable is False): #complete selection
                        if so.debug is True: 
                            inkex.utils.debug("id={}, length={:0.3f}{}".format(element.get('id'), self.svg.uutounit(str(stotal), so.unit), so.unit))
                        to_sort.append({'element': element, 'value': stotal, 'type': 'length'})
                                       
                elif so.measure == "nodes":
                    slengths, stotal = csplength(csp) #get segment lengths and total length of path in document's internal unit
                    stotal = round(stotal, so.precision)
                    nodes = len(element.path)
                    if (so.min_filter_enable is True and nodes / stotal < so.min_nodes / self.svg.unittouu(str(so.nodes_interval) + so.unit)) or \
                       (so.max_filter_enable is True and nodes / stotal > so.max_nodes / self.svg.unittouu(str(so.nodes_interval) + so.unit)) or \
                       (so.min_filter_enable is False and so.max_filter_enable is False): #complete selection
                        if so.debug is True: 
                            inkex.utils.debug("id={}, length={:0.3f}{}, nodes={}".format(element.get('id'), self.svg.uutounit(str(stotal), so.unit), so.unit, nodes))
                        to_sort.append({'element': element, 'value': nodes, 'type': 'nodes'})

            except Exception as e:
                #inkex.utils.debug(e)
                pass
            
        for i in range(0, len(to_sort)):
            element = to_sort[i].get('element')   
            if so.delete is True:
                element.delete()
                
        if so.delete is True:
            return #quit here
            
        if so.sort_by_value is True:
            to_sort.sort(key=lambda x: x.get('value')) #sort by target value
            
        if so.sort_by_id is True:
            to_sort.sort(key=lambda x: x.get('element').get('id')) #sort by id. will override previous value sort
            
        if so.group is True:
            group = inkex.Group(id=self.svg.get_unique_id("filtered"))
            self.svg.get_current_layer().add(group)          
            
        allIds = self.svg.get_ids()
        newIds = [] #we pre-populate this
        for i in range(0, len(to_sort)):
            newIds.append("{}{}".format(element.tag.replace('{http://www.w3.org/2000/svg}',''), i)) #should be element tag 'path'
                   
        for i in range(0, len(to_sort)):
            element = to_sort[i].get('element')
            
            if so.rename_ids is True:
                if newIds[i] in allIds: #already exist. lets rename that one before using it's id for the recent element
                    try:
                        renameIdPre = element.get('id') + "-"
                        renameId = self.svg.get_unique_id(renameIdPre)
                        #inkex.utils.debug("Trying to rename {} to {}".format(element.get('id'), renameId))
                        originalElement = self.svg.getElementById(newIds[i])
                        originalElement.set('id', renameId)
                    except Exception as e:
                        pass
                        #inkex.utils.debug(e)
                element.set('id', newIds[i])
            
            if so.sort_by_value is True:
                if so.reverse_sort_value is True:
                    idx = len(element.getparent())
                else:
                    idx = 0          
                element.getparent().insert(idx, element)
               
            if so.sort_by_id is True:
                if so.reverse_sort_id is True:
                    idx = len(element.getparent())
                else:
                    idx = 0          
                element.getparent().insert(idx, element)

            if so.color_mode == "colorize_rainbow":
                color = colorsys.hsv_to_rgb(i / float(len(to_sort)), 1.0, 1.0)
                element.style['stroke'] = '#%02x%02x%02x' % tuple(int(x * 255) for x in color)
                
            if so.color_mode == "colorize_single":
                element.style['stroke'] = so.color_single              
                
            if so.set_labels is True:
                element.set('inkscape:label', "{}={}".format(to_sort[i].get('type'), to_sort[i].get('value')))
                
            if so.remove_labels is True:
                element.pop('inkscape:label')
                           
            if so.group is True:
                group.append(element)
                
            #if len(group) == 0:
            #    group.delete()    
                
        if so.cleanup is True:
            try:
                import remove_empty_groups
                remove_empty_groups.RemoveEmptyGroups.effect(self)
            except:
                self.msg("Calling 'Remove Empty Groups' extension failed. Maybe the extension is not installed. You can download it from official InkScape Gallery. Skipping ...")

if __name__ == '__main__':
    FilterByLengthArea().run()
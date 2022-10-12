#!/usr/bin/env python3

"""
Extension for InkScape 1.0

This extension parses the selection and will put all elements into one single group. If you have a cluster with lots of groups and elements you will clean up this way (one top level group, all elements below it). If you select a single element or a set of elements you just wrap it like using CTRL + G (like making a usual group). You can also use this extension to filter out unwanted SVG elements at all.
 
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 13.08.2020
Last Patch: 13.09.2020
License: GNU GPL v3
"""

import inkex
import os
import sys
from lxml import etree

sys.path.append("../remove_empty_groups")
sys.path.append("../apply_transformations")

class UngrouperAndElementMigratorFilter(inkex.EffectExtension):

    allElements = [] #list of all (sub)elements to process within selection
    allGroups = [] #list of all groups (svg:g and svg:svg items) to delete for cleanup (for ungrouping)
    allDrops = [] #list of all other elements except svg:g and svg:svg to drop while migrating (for filtering)
    
    def add_arguments(self, pars):
        pars.add_argument("--tab")

        pars.add_argument("--operationmode", default=False, help="Operation mode")
        pars.add_argument("--parsechildren", type=inkex.Boolean, default=True, help="Perform operations on children of selection")
        pars.add_argument("--showdroplist", type=inkex.Boolean, default=False, help="Show list of dropped items")
        pars.add_argument("--shownewgroupname", type=inkex.Boolean, default=False, help="This helps to better identify the generated output.")
        pars.add_argument("--apply_transformations", type=inkex.Boolean, default=False, help="Run 'Apply Transformations' extension before running vpype. Helps avoiding geometry shifting")
        pars.add_argument("--cleanup", type=inkex.Boolean, default = True, help = "This will call the extension 'Remove Empty Groups' if available")
        pars.add_argument("--migrate_to", default = "group", help = "Migrate to")

        #pars.add_argument("--sodipodi",      type=inkex.Boolean, default=True)
        #pars.add_argument("--svg",           type=inkex.Boolean, default=True)
        pars.add_argument("--circle",         type=inkex.Boolean, default=True)
        pars.add_argument("--clipPath",       type=inkex.Boolean, default=True)
        pars.add_argument("--defs",           type=inkex.Boolean, default=True)
        pars.add_argument("--desc",           type=inkex.Boolean, default=True)
        pars.add_argument("--ellipse",        type=inkex.Boolean, default=True)
        pars.add_argument("--image",          type=inkex.Boolean, default=True)
        pars.add_argument("--guide",          type=inkex.Boolean, default=True)
        pars.add_argument("--line",           type=inkex.Boolean, default=True)
        pars.add_argument("--path",           type=inkex.Boolean, default=True)
        pars.add_argument("--polyline",       type=inkex.Boolean, default=True)
        pars.add_argument("--polygon",        type=inkex.Boolean, default=True)
        pars.add_argument("--rect",           type=inkex.Boolean, default=True)
        pars.add_argument("--text",           type=inkex.Boolean, default=True)
        pars.add_argument("--tspan",          type=inkex.Boolean, default=True)
        pars.add_argument("--linearGradient", type=inkex.Boolean, default=True)
        pars.add_argument("--radialGradient", type=inkex.Boolean, default=True)
        pars.add_argument("--mask",           type=inkex.Boolean, default=True)
        pars.add_argument("--meshGradient",   type=inkex.Boolean, default=True)
        pars.add_argument("--meshRow",        type=inkex.Boolean, default=True)
        pars.add_argument("--meshPatch",      type=inkex.Boolean, default=True)
        pars.add_argument("--metadata",       type=inkex.Boolean, default=True)
        pars.add_argument("--script",         type=inkex.Boolean, default=True)
        pars.add_argument("--symbol",         type=inkex.Boolean, default=True)
        pars.add_argument("--stop",           type=inkex.Boolean, default=True)
        pars.add_argument("--style",          type=inkex.Boolean, default=True)
        pars.add_argument("--switch",         type=inkex.Boolean, default=True)
        pars.add_argument("--use",            type=inkex.Boolean, default=True)
        pars.add_argument("--flowRoot",       type=inkex.Boolean, default=True)
        pars.add_argument("--flowRegion",     type=inkex.Boolean, default=True)
        pars.add_argument("--flowPara",       type=inkex.Boolean, default=True)
        pars.add_argument("--marker",         type=inkex.Boolean, default=True)
        pars.add_argument("--pattern",        type=inkex.Boolean, default=True)
        pars.add_argument("--rdfRDF",         type=inkex.Boolean, default=True)
        pars.add_argument("--ccWork",         type=inkex.Boolean, default=True)

    
    def effect(self):
        namespace = [] #a list of selected types we are going to process for filtering (dropping items)
        #namespace.append("{http://www.w3.org/2000/svg}sodipodi")       if self.options.sodipodi       else "" #do not do this. it will crash InkScape
        #namespace.append("{http://www.w3.org/2000/svg}svg")            if self.options.svg            else "" #we handle svg:svg the same type like svg:g
        namespace.append("{http://www.w3.org/2000/svg}circle")                        if self.options.circle         else ""
        namespace.append("{http://www.w3.org/2000/svg}clipPath")                      if self.options.clipPath       else ""
        namespace.append("{http://www.w3.org/2000/svg}defs")                          if self.options.defs           else ""     
        namespace.append("{http://www.w3.org/2000/svg}desc")                          if self.options.desc           else ""     
        namespace.append("{http://www.w3.org/2000/svg}ellipse")                       if self.options.ellipse        else ""
        namespace.append("{http://www.w3.org/2000/svg}image")                         if self.options.image          else ""
        namespace.append("{http://www.w3.org/2000/svg}line")                          if self.options.line           else ""
        namespace.append("{http://www.w3.org/2000/svg}polygon")                       if self.options.polygon        else ""
        namespace.append("{http://www.w3.org/2000/svg}path")                          if self.options.path           else ""
        namespace.append("{http://www.w3.org/2000/svg}polyline")                      if self.options.polyline       else ""
        namespace.append("{http://www.w3.org/2000/svg}rect")                          if self.options.rect           else ""
        namespace.append("{http://www.w3.org/2000/svg}text")                          if self.options.text           else ""
        namespace.append("{http://www.w3.org/2000/svg}tspan")                         if self.options.tspan          else ""
        namespace.append("{http://www.w3.org/2000/svg}linearGradient")                if self.options.linearGradient else ""
        namespace.append("{http://www.w3.org/2000/svg}radialGradient")                if self.options.radialGradient else ""
        namespace.append("{http://www.w3.org/2000/svg}meshGradient")                  if self.options.meshGradient   else ""
        namespace.append("{http://www.w3.org/2000/svg}meshRow")                       if self.options.meshRow        else ""
        namespace.append("{http://www.w3.org/2000/svg}meshPatch")                     if self.options.meshPatch      else ""
        namespace.append("{http://www.w3.org/2000/svg}script")                        if self.options.script         else ""
        namespace.append("{http://www.w3.org/2000/svg}symbol")                        if self.options.symbol         else ""
        namespace.append("{http://www.w3.org/2000/svg}mask")                          if self.options.mask           else ""
        namespace.append("{http://www.w3.org/2000/svg}metadata")                      if self.options.metadata       else ""
        namespace.append("{http://www.w3.org/2000/svg}stop")                          if self.options.stop           else ""
        namespace.append("{http://www.w3.org/2000/svg}style")                         if self.options.style          else ""
        namespace.append("{http://www.w3.org/2000/svg}switch")                        if self.options.switch         else ""
        namespace.append("{http://www.w3.org/2000/svg}use")                           if self.options.use            else ""
        namespace.append("{http://www.w3.org/2000/svg}flowRoot")                      if self.options.flowRoot       else ""
        namespace.append("{http://www.w3.org/2000/svg}flowRegion")                    if self.options.flowRegion     else ""
        namespace.append("{http://www.w3.org/2000/svg}flowPara")                      if self.options.flowPara       else ""
        namespace.append("{http://www.w3.org/2000/svg}marker")                        if self.options.marker         else ""
        namespace.append("{http://www.w3.org/2000/svg}pattern")                       if self.options.pattern        else ""
        namespace.append("{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}guide") if self.options.guide          else ""
        namespace.append("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF")          if self.options.rdfRDF         else ""
        namespace.append("{http://creativecommons.org/ns#}Work")                      if self.options.ccWork         else ""

        #self.msg(namespace)

        #in case the user made a manual selection instead of whole document parsing, we need to collect all required elements first
        def parseChildren(element):
            if element not in selected:
                selected.append(element)
            if self.options.parsechildren == True:   
                children = element.getchildren()
                if children is not None:
                    for child in children:
                        if child not in selected:
                            selected.append(child)
                        parseChildren(child) #go deeper and deeper

        #check the element for it's type and put it into the according list (either re-group or delete or just nothing)
        def parseElement(self, element):
            #if we only want to ungroup (flatten) the elements we just collect all elements in a list and put them in a new single group later
            if self.options.operationmode == "ungroup_only": 
                if element not in self.allElements:
                    if element.tag != inkex.addNS('g','svg') and element.tag != inkex.addNS('svg','svg') and element.tag != inkex.addNS('namedview','sodipodi'):
                        self.allElements.append(element)
            #if we dont want to ungroup but filter out elements, or ungroup and filter, we need to divide the elements with respect to the namespace (user selection)
            elif self.options.operationmode == "filter_only" or self.options.operationmode == "ungroup_and_filter":
                #self.msg(element.tag)
                #inkex.utils.debug(element.tag) - uncomment to find out the namespace of new elements
                if element.tag in namespace: #if the element is in namespace and no group type we will regroup the item. so we will not remove it
                    if element not in self.allElements:
                        self.allElements.append(element)
                else: #we add all remaining items (except svg:g and svg:svg) into the list for deletion
                    #self.msg(element.tag)
                    if element.tag != inkex.addNS('g','svg') and element.tag != inkex.addNS('svg','svg') and element.tag != inkex.addNS('namedview','sodipodi'):
                        if element not in self.allDrops:
                            self.allDrops.append(element)
            #finally the groups we want to get rid off are put into a another list. They will be deleted (depending on the mode) after parsing the element tree
            if self.options.operationmode == "ungroup_only" or self.options.operationmode == "ungroup_and_filter":
                if element.tag == inkex.addNS('g','svg') or element.tag == inkex.addNS('svg','svg'):
                    if element not in self.allGroups:
                        self.allGroups.append(element)

        applyTransformationsAvailable = False # at first we apply external extension
        try:
            import apply_transformations
            applyTransformationsAvailable = True
        except Exception as e:
            # self.msg(e)
            self.msg("Calling 'Apply Transformations' extension failed. Maybe the extension is not installed. You can download it from official InkScape Gallery. Skipping ...")
             
        if self.options.apply_transformations is True and applyTransformationsAvailable is True:
            apply_transformations.ApplyTransformations().recursiveFuseTransform(self.document.getroot()) 
             
        #check if we have selected elements or if we should parse the whole document instead
        selected = [] #total list of elements to parse
        if len(self.svg.selected) == 0:
            for element in self.document.getroot().iter(tag=etree.Element):
                if element != self.document.getroot():

                    selected.append(element)
        else:
            for element in self.svg.selected.values():
                parseChildren(element)
                
        #get all elements from the selection.
        for element in selected:
            parseElement(self, element)
           
        #some debugging block
        #check output
        #self.msg("--- Selected items (with or without children) ---")
        #self.msg(selected)
        #self.msg("--- All elements (except groups)---")
        #self.msg(len(self.allElements))
        #self.msg(self.allElements)
        #self.msg("--- All groups ---")
        #self.msg(len(self.allGroups))
        #self.msg(self.allGroups)
        #self.msg("--- All dropouts ---")
        #self.msg(len(self.allDrops))
        #self.msg(self.allDrops)


        migrate_log = "migrategroups.log"

        # Clean up possibly previously generated log file
        if os.path.exists(migrate_log):
            try:
                os.remove(migrate_log)
            except OSError as e: 
                self.msg("Error while deleting previously generated log file " + migrate_log)

        # show a list with items to delete. For ungroup mode it does not apply because we are not going to remove anything
        if self.options.operationmode == "filter_only" or self.options.operationmode == "ungroup_and_filter":
            if self.options.showdroplist:
                self.msg(str(len(self.allDrops)) + " elements were removed during nodes while migration.")
                if len(self.allDrops) > 100: #if we print too much to the output stream we will freeze InkScape forever wihtout any visual error message. So we write to file instead
                    migrate_log_file = open('migrategroups.log', 'w')
                else:
                    migrate_log_file = None
                for i in self.allDrops:
                    if i.get('id') is not None:
                        migrateString = i.tag.replace("{http://www.w3.org/2000/svg}","svg:") + " id:" + i.get('id')
                    else:
                        migrateString = i.tag #there are also some special elements without an id in the document, like rdf:RDF or cc:Work
                    if migrate_log_file is None:
                        self.msg(migrateString)
                    else:
                        migrate_log_file.write(migrateString + "\n")
                if migrate_log_file is not None:
                    migrate_log_file.close()
                    self.msg("Detailed output was dumped into file " + os.path.join(os.getcwd(), migrate_log))

        # remove all groups from the selection and form a new single group of it by copying with old IDs.
        if self.options.operationmode == "ungroup_only" or self.options.operationmode == "ungroup_and_filter":
            if len(self.allElements) > 0:
                newGroup = self.document.getroot().add(inkex.Group()) #make a new group at root level
                newGroup.set('id', self.svg.get_unique_id('migrate-')) #generate some known ID with the prefix 'migrate-'
                if self.options.migrate_to == "layer":
                    newGroup.set(inkex.addNS('groupmode', 'inkscape'), 'layer')

                if self.options.shownewgroupname == True:
                        self.msg("The migrated elements are now in group with ID " + str(newGroup.get('id')))
                index = 0
                for element in self.allElements: #we have a list of elements which does not cotain any other elements like svg:g or svg:svg 
                    newGroup.insert(index, element) #we do not copy any elements. we just rearrange them by moving to another place (group index)
                    index += 1 #we must count up the index or we would overwrite each previous element
    
       # remove the stuff from drop list list. this has to be done before we drop the groups where they are located in
        if self.options.operationmode == "filter_only" or self.options.operationmode == "ungroup_and_filter":
            if len(self.allDrops) > 0:
                for dropElement in self.allDrops:
                    if dropElement.getparent() is not None:
                        dropElement.getparent().remove(dropElement)
              
        # remove all the obsolete groups which are left over from ungrouping (flattening)
        if self.options.operationmode == "ungroup_only" or self.options.operationmode == "ungroup_and_filter":
            if len(self.allGroups) > 0:        
                for group in self.allGroups:
                    if group.getparent() is not None:
                        group.getparent().remove(group)
   
        # finally removed dangling empty groups using external extension (if installed)
        if self.options.cleanup == True:
            try:
                import remove_empty_groups
                remove_empty_groups.RemoveEmptyGroups.effect(self)
            except:
                self.msg("Calling 'Remove Empty Groups' extension failed. Maybe the extension is not installed. You can download it from official InkScape Gallery.")
         
if __name__ == '__main__':
    UngrouperAndElementMigratorFilter().run()
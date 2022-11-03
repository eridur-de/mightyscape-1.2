#!/usr/bin/env python3

"""
Extension for InkScape 1.2

CutOptim OS Wrapper script to make CutOptim work on Windows and Linux systems without duplicating .inx files

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 31.08.2020
Last patch: 03.11.2022
License: GNU GPL v3

"""

import inkex
import sys
import re
import os
import subprocess
from lxml import etree
from copy import deepcopy
import tempfile
from inkex.command import inkscape, inkscape_command

class CuttingOptimizer(inkex.EffectExtension):
  
    def openDebugFile(self, file):
        DETACHED_PROCESS = 0x00000008
        if os.name == 'nt':
            subprocess.Popen(["explorer", file], close_fds=True, creationflags=DETACHED_PROCESS, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).wait()
        else:
            subprocess.Popen(["xdg-open", file], close_fds=True, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).wait()
        
    def add_arguments(self, pars):
        args = sys.argv[1:] 
        for arg in args:
            key=arg.split("=")[0]
            if len(arg.split("=")) == 2:
                value=arg.split("=")[1]
                try:
                    if key != "--id":
                        pars.add_argument(key, default=key)             
                except:
                    pass #ignore duplicate id arg

    def effect(self):
        extension_dir = os.path.dirname(os.path.realpath(__file__))
        cmd = []
        if os.name == "nt":
            cutoptim = os.path.join(extension_dir, "CutOptim.exe")
        else:
            cutoptim = os.path.join(extension_dir, "CutOptim")
        cmd.append(cutoptim)
        
        elements = self.svg.selected
        if len(elements) > 0: #if selection is existing, then we export only selected items to a new svg, which is then going to be processed. Otherwise we process the whole SVG document
            extra_param = None
            template = self.svg.copy()
            for child in template.getchildren():
                if child.tag == '{http://www.w3.org/2000/svg}defs':
                    continue
                template.remove(child)
            group = etree.SubElement(template, '{http://www.w3.org/2000/svg}g')
            group.attrib['id'] = 'export_selection_transform'
            for element in self.svg.selected.values():
                elem_copy = deepcopy(element)
                elem_copy.attrib['transform'] = str(element.composed_transform())
                elem_copy.attrib['style'] = str(element.specified_style())            
                group.append(elem_copy)
            template.attrib['viewBox'] = self.svg.attrib['viewBox']
            template.attrib['width'] = self.svg.attrib['width']
            template.attrib['height'] = self.svg.attrib['height']   
            template.append(group)
            svg_out = os.path.join(tempfile.gettempdir(), self.svg.get_unique_id("selection") + '.svg')
            with open(svg_out, 'wb') as fp:
                fp.write(template.tostring())
            actions_list=[]
            actions_list.append("SelectionUnGroup")
            actions_list.append("export-type:svg")
            actions_list.append("export-filename:{}".format(svg_out))
            actions_list.append("export-do") 
            actions = ";".join(actions_list)
            cli_output = inkscape(svg_out, extra_param, actions=actions) #process recent file
            if len(cli_output) > 0:
                self.msg("Inkscape returned the following output when trying to run the file export; the file export may still have worked:")
                self.msg(cli_output)

        layerSum = 0
        layer_output_0 = False
        cancel_on_error = False
        for arg in vars(self.options):
            argval = str(getattr(self.options, arg))
            if arg not in ("tab", "output", "ids", "selected_nodes", "print_cmd"):
                #inkex.utils.debug(str(arg) + " = " + str(getattr(self.options, arg)))
                #fix behaviour of "original" arg which does not correctly gets interpreted if set to false
                if arg == "original" and argval == "false":
                    continue
                if arg == "input_file":
                    cmd.append("--file")
                    if len(elements) > 0:
                        cmd.append(svg_out)
                    else:
                        cmd.append(argval)
                elif arg == "layer_output_0": 
                    if argval == "true": 
                        layerSum += 0
                        layer_output_0 = True
                #elif arg == "layer_output_1":
                #    if argval == "true": layerSum += 1
                elif arg == "layer_output_2":
                    if argval == "true": layerSum += 2
                elif arg == "layer_output_4": 
                    if argval == "true": layerSum += 4
                elif arg == "layer_output_8":  
                    if argval == "true": layerSum += 8
                elif arg == "layer_output_16": 
                    if argval == "true": layerSum += 16
                elif arg == "cancel_on_error": 
                    if argval == "true": cancel_on_error = True
                else:
                    cmd.append("--{}={}".format(arg, argval))
        cmd.append("--layer_output")
        cmd.append("{}".format(layerSum))
        if layerSum == 0 and layer_output_0 is False:
            inkex.utils.debug("You need to enable at least one type of layer to continue!")
        output_file = None
        if os.name == "nt":
            output_file = "cutoptim.svg"    
        else:
            output_file = "/tmp/cutoptim.svg"
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except OSError as e: 
                pass

        cmd.append("--output")
        cmd.append(output_file)
        
        # run CutOptim with the parameters provided
        if self.options.print_cmd == "true":
            inkex.utils.debug("The following command would be executed on shell:\n")
            inkex.utils.debug(" ".join(cmd))
            exit(0)
        else:
            with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False) as cutoptim:
                cutoptim.wait()
                stdout, stderr = cutoptim.communicate()
                #inkex.utils.debug("stdout:\n{}".format(stdout.decode('UTF-8')))
                errors = stderr.decode('UTF-8')
                if len(errors) > 0:
                    inkex.utils.debug("Errors occured:\n{}".format(errors))
                if len(errors) > 0 and cancel_on_error is True:
                    inkex.utils.debug("Maybe enlarge your document size in case not all polygons could be placed and try again! Nesting was cancelled!")
                    exit(1)

        # check output existence
        try:
            stream = open(output_file, 'r')
        except FileNotFoundError as e:
            inkex.utils.debug("There was no SVG output generated. Cannot continue. Command was:\n")
            inkex.utils.debug(" ".join(cmd))
            exit(1)

        if self.options.original == "false": #we need to use string representation of bool
            for element in self.document.getroot():
                if isinstance(element, inkex.ShapeElement):
                    element.delete()

        if self.options.debug_file == "true": #we need to use string representation of bool
            self.openDebugFile("Debug_CutOptim.txt")

        # write the generated SVG into Inkscape's canvas
        doc = etree.parse(stream, parser=etree.XMLParser(huge_tree=True))
        stream.close()
        group = inkex.Group(id="CutOptim")
        '''
         0 = Placed_Layer
         1 = Original_Layer (Input Layer) <> see "Keep original layer"
         2 = Polygon_Layer
         4 = Large_Polygon_Layer
         8 = Hull_Placed_Layer
        16 = Placed_Polygon_Layer
        '''
        if layer_output_0 is False:
            l0 = None
        else:
            l0 =  doc.xpath('//svg:g[@inkscape:label="Placed_Layer"]',         namespaces=inkex.NSS)
        #l1 =  doc.xpath('//svg:g[@inkscape:label="Original_Layer"]',       namespaces=inkex.NSS)
        l2 =  doc.xpath('//svg:g[@inkscape:label="Polygon_Layer"]',        namespaces=inkex.NSS)
        l4 =  doc.xpath('//svg:g[@inkscape:label="Large_Polygon_Layer"]',  namespaces=inkex.NSS)
        l8 =  doc.xpath('//svg:g[@inkscape:label="Hull_Placed_Layer"]',    namespaces=inkex.NSS)
        l16 = doc.xpath('//svg:g[@inkscape:label="Placed_Polygon_Layer"]', namespaces=inkex.NSS)
        for layer in (l0, l2, l4, l8, l16): #,l1
            if layer is not None and len(layer) > 0:
                for element in layer:#[0].getchildren():
                    group.append(element)
        self.document.getroot().append(group)
       
if __name__ == '__main__':
    CuttingOptimizer().run()
#!/usr/bin/env python3

"""
Extension for InkScape 1.2

boxes.py wrapper script to make it work on Windows and Linux systems

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 27.04.2021
Last patch: 30.11.2022
License: GNU GPL v3

"""
import inkex
import sys
import os
from lxml import etree
import tempfile

class boxesPyWrapper(inkex.GenerateExtension):

    def add_arguments(self, pars):
        args = sys.argv[1:] 
        for arg in args:
            key=arg.split("=")[0]
            if len(arg.split("=")) == 2:
                value=arg.split("=")[1]
                try:
                    pars.add_argument(key, default=key)
                except:
                    pass #ignore duplicate id arg

    def generate(self):
        box_file = os.path.join(tempfile.gettempdir(), "box.svg")
        if os.path.exists(box_file):
            os.remove(box_file) #remove previously generated box file at the beginning

        boxes_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'boxes', 'scripts')
        cmd = 'python ' + os.path.join(boxes_dir, 'boxes') #the boxes python file (without .py ending) - we add python at the beginning to support Windows too    
        for arg in vars(self.options):
            if arg != "output" and arg != "ids" and arg != "selected_nodes":
                #inkex.utils.debug(str(arg) + " = " + str(getattr(self.options, arg)))
                #fix behaviour of "original" arg which does not correctly gets interpreted if set to false
                if arg == "original" and str(getattr(self.options, arg)) == "false":
                    continue
                if arg in ("input_file", "tab", "labels"):
                    continue
                else:
                    cmd += ' --' + arg + ' "' + str(getattr(self.options, arg)) + '"'
                    #cmd += ' --' + arg + '="' + str(getattr(self.options, arg)) + '"'
        cmd += " --output=" + box_file + " "
        cmd = cmd.replace("boxes --generator", "boxes")
        
        # run boxes with the parameters provided
        with os.popen(cmd, "r") as boxes:
            result = boxes.read()
        
        # check output existence
        try:
            stream = open(box_file, 'r')
        except FileNotFoundError as e:
            inkex.utils.debug("There was no " + box_file + " output generated. Cannot continue. Command was:")
            inkex.utils.debug(str(cmd))
            exit(1)
            
        # write the generated SVG into Inkscape's canvas
        p = etree.XMLParser(huge_tree=True)
        doc = etree.parse(stream, parser=etree.XMLParser(huge_tree=True))
        stream.close()
        if os.path.exists(box_file):
            os.remove(box_file) #remove previously generated box file at the end too      
            
        group = inkex.Group(id="boxes.py")
        for element in doc.getroot():
            group.append(element)
        return group
        
if __name__ == '__main__':
    boxesPyWrapper().run()
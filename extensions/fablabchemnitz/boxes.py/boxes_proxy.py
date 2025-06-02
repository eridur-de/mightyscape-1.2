#!/usr/bin/env python3

"""
Extension for Inkscape 1.2

boxes.py wrapper script to make it work on Windows and Linux systems

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 27.04.2021
Last patch: 05.07.2024
License: GNU GPL v3

"""
import boxes
import inkex
import sys
import subprocess
import os
from lxml import etree
import tempfile
import argparse
import xml.etree.ElementTree as ET

class boxesPyWrapper(inkex.GenerateExtension):

    def add_arguments(self, pars):
        args = sys.argv[1:]      
        for arg in args:
            key=arg.split("=")[0]
            if len(arg.split("=")) == 2:
                value=arg.split("=")[1]
                if key != "--id": #ignore duplicate id arg, which will throw error if an element is selected
                    pars.add_argument(key, default=key)

    def generate(self):
        box_file = os.path.join(tempfile.gettempdir(), "box.svg")
        if os.path.exists(box_file):
            os.remove(box_file) #remove previously generated box file at the beginning

        boxes_dir = os.path.join(os.path.dirname(boxes.__file__), 'scripts')
        boxes_executable = 'boxes_main.py'
                
        #get the correct python executable. If Inkscape has a custom interpreter in preferences.xml, we should honor it
        preferencesPath = os.environ["INKSCAPE_PROFILE_DIR"]
        preferencesXml = os.path.join(preferencesPath, "preferences.xml")
        customPythonInterpreter = None
        #inkex.utils.debug(preferencesXml)
        tree = ET.parse(preferencesXml)
        root = tree.getroot()
        for group in root.findall('group'):
            for attribute in group.attrib:
                if attribute == "python-interpreter":
                    #inkex.utils.debug(group.get("python-interpreter"))
                    customPythonInterpreter = group.get("python-interpreter")
        if os.name=="nt": #we want to omit using the python executable delivered by inkscape. we use our own installation from %PATH%
            pathlist=list(reversed(os.environ["PATH"].split(os.pathsep)))
            for path in pathlist:
                if "Python" in (str(path)): #if Python subdirectory is inside, theres a chance to have a correct installation
                    #inkex.utils.debug(path)
                    path = os.path.join(path, "python.exe")
                    if os.path.isfile(path) and os.access(path, os.X_OK):
                        #inkex.utils.debug(path)
                        PYTHONBIN = path
        else: #Linux/MacOS
            PYTHONBIN = "python"
            
        if customPythonInterpreter is not None:
            PYTHONBIN = customPythonInterpreter
                                          
        cmd = PYTHONBIN + ' ' + os.path.join(boxes_dir, boxes_executable) #the boxes python file (without .py ending) - we add python at the beginning to support Windows too    
        for arg in vars(self.options):
            if arg not in ("output", "ids", "selected_nodes"):
                #inkex.utils.debug(str(arg) + " = " + str(getattr(self.options, arg)))
                #fix behaviour of "original" arg which does not correctly gets interpreted if set to false
                if arg == "original" and str(getattr(self.options, arg)) == "false":
                    continue
                if arg in ("input_file", "tab"):
                    continue
                else:
                    cmd += ' --' + arg + ' "' + str(getattr(self.options, arg)) + '"'
                    #cmd += ' --' + arg + '="' + str(getattr(self.options, arg)) + '"'
        cmd += " --output=" + box_file + " "
        cmd = cmd.replace("{} --generator".format(boxes_executable), boxes_executable)
        
        # run boxes with the parameters provided
        #with os.popen(cmd, "r") as boxes:
        #    result = boxes.read()
        
        try:
            proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.wait()
        except OSError as e:
            raise OSError("{0}\nCommand failed: errno={1} {2}".format(' '.join(cmd), e.errno, e.strerror))
        stdout, stderr = proc.communicate()
        if stderr.decode('utf-8') != "":
            inkex.utils.debug("stderr: {}".format(stderr.decode('utf-8')))
            sys.exit(1)
        
        # check output existence
        try:
            stream = open(box_file, 'r')
        except FileNotFoundError as e:
            inkex.utils.debug("There was no " + box_file + " output generated. Cannot continue. Command was:")
            inkex.utils.debug(str(cmd))
            sys.exit(1)
            
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
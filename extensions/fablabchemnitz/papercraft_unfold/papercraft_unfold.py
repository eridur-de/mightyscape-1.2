#!/usr/bin/env python3
import sys
import os
import inkex
import tempfile
import shutil

import subprocess
from subprocess import Popen, PIPE
from lxml import etree

#specific imports for model-converter-python - d3 library to convert obj/off/ply to stl (https://github.com/nabeel3133/file-converter-.obj-to-.ply)
import functools as fc
import d3.model.tools as mt
from d3.model.basemodel import Vector

"""
Extension for InkScape 1.0

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 08.09.2020
Last patch: 25.04.2021
License: GNU GPL v3

This tool converts a STL/OFF/PLY/OBJ into binary STL Format. The STL then gets unfolded (flattened) to make a papercraft model.

#################################################################
ADMesh version 0.99.0dev
Copyright (C) 1995, 1996  Anthony D. Martin
Usage: /usr/share/inkscape/extensions/mightyscape-1.X/extensions/fablabchemnitz/papercraft/.libs/admesh [OPTION]... file

     --x-rotate=angle     Rotate CCW about x-axis by angle degrees
     --y-rotate=angle     Rotate CCW about y-axis by angle degrees
     --z-rotate=angle     Rotate CCW about z-axis by angle degrees
     --xy-mirror          Mirror about the xy plane
     --yz-mirror          Mirror about the yz plane
     --xz-mirror          Mirror about the xz plane
     --scale=factor       Scale the file by factor (multiply by factor)
     --scale-xyz=x,y,z    Scale the file by a non uniform factor
     --translate=x,y,z    Translate the file to x, y, and z
     --merge=name         Merge file called name with input file
 -e, --exact              Only check for perfectly matched edges
 -n, --nearby             Find and connect nearby facets. Correct bad facets
 -t, --tolerance=tol      Initial tolerance to use for nearby check = tol
 -i, --iterations=i       Number of iterations for nearby check = i
 -m, --increment=inc      Amount to increment tolerance after iteration=inc
 -u, --remove-unconnected Remove facets that have 0 neighbors
 -f, --fill-holes         Add facets to fill holes
 -d, --normal-directions  Check and fix direction of normals(ie cw, ccw)
     --reverse-all        Reverse the directions of all facets and normals
 -v, --normal-values      Check and fix normal values
 -c, --no-check           Don't do any check on input file
 -b, --write-binary-stl=name   Output a binary STL file called name
 -a, --write-ascii-stl=name    Output an ascii STL file called name
     --write-off=name     Output a Geomview OFF format file called name
     --write-dxf=name     Output a DXF format file called name
     --write-vrml=name    Output a VRML format file called name
     --help               Display this help and exit
     --version            Output version information and exit

The functions are executed in the same order as the options shown here.
So check here to find what happens if, for example, --translate and --merge
options are specified together.  The order of the options specified on the
command line is not important.

NOTE: If admesh on linux fails just run "make clean && make" to re-create the executable. There error could be like
"papercraft_unfold/admesh/linux/.libs/admesh: error while loading shared libraries: libadmesh.so.1: cannot open shared object file: No such file or directory"
admesh is sensible for moving from one dir to another

#################################################################
Module licenses
- papercraft      - 26307b8        (https://github.com/osresearch/papercraft)            - GPL v2 License
- admesh          - 0.98.3         (https://github.com/admesh/admesh)                    - GPL License
- fstl            -                (https://github.com/fstl-app/fstl)                    - MIT License
"""

class PapercraftUnfold(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--inputfile")
        pars.add_argument("--generatelabels", type=inkex.Boolean, default=True, help="Generate labels for edges")
        pars.add_argument("--resizetoimport", type=inkex.Boolean, default=True, help="Resize the canvas to the imported drawing's bounding box") 
        pars.add_argument("--extraborder", type=float, default=0.0)
        pars.add_argument("--extraborder_units")              
        pars.add_argument("--show_fstl", type=inkex.Boolean, default=True, help="Show converted (and fixed) STL in fstl Viewer")
        pars.add_argument("--exact", type=inkex.Boolean, default=True, help="Only check for perfectly matched edges")
        pars.add_argument("--nearby", type=inkex.Boolean, default=True, help="Find and connect nearby facets. Correct bad facets")
        pars.add_argument("--tolerance", type=float, default=0.0, help="Initial tolerance to use for nearby check")
        pars.add_argument("--iterations", type=int, default=1, help="Number of iterations for nearby check")
        pars.add_argument("--increment", type=float, default=0.0, help="Amount to increment tolerance after iteration")
        pars.add_argument("--remove_unconnected", type=inkex.Boolean, default=True, help="Remove facets that have 0 neighbors")
        pars.add_argument("--fill_holes", type=inkex.Boolean, default=True, help="Add facets to fill holes")
        pars.add_argument("--normal_directions", type=inkex.Boolean, default=True, help="Check and fix direction of normals (ie cw, ccw)")
        pars.add_argument("--reverse_all", type=inkex.Boolean, default=True, help="Reverse the directions of all facets and normals")
        pars.add_argument("--normal_values", type=inkex.Boolean, default=True, help="Check and fix normal values")
        pars.add_argument("--xy_mirror", type=inkex.Boolean, default=True)
        pars.add_argument("--yz_mirror", type=inkex.Boolean, default=True)
        pars.add_argument("--xz_mirror", type=inkex.Boolean, default=True)
        pars.add_argument("--scale", type=float, default=1.0)
                                 
    def effect(self):
        inputfile = self.options.inputfile
        if not os.path.exists(inputfile):
            inkex.utils.debug("The input file does not exist. Please select a proper file and try again.")
            exit(1)      
        converted_inputfile = os.path.join(tempfile.gettempdir(), os.path.splitext(os.path.basename(inputfile))[0] + ".stl")
        if os.path.exists(converted_inputfile):
              os.remove(converted_inputfile) #remove previously generated conversion file
        up_conversion = None
        
        try:
            with open(converted_inputfile, 'w') as f:
                f.write(mt.convert(inputfile, converted_inputfile, up_conversion))
        except UnicodeDecodeError as e: #conversion failed. Maybe it was a binary STL. Skipping and regular copy
            shutil.copy2(inputfile, converted_inputfile)


        # Run ADMesh mesh fixer to overwrite the STL with fixed output and binary file format for osresearch/papercraft
        if os.name=="nt":
            admesh_cmd = "admesh\\windows\\admesh.exe "
        else:
            admesh_cmd = "./admesh/linux/admesh "

        if self.options.xy_mirror == True: admesh_cmd += "--xy-mirror "
        if self.options.yz_mirror == True: admesh_cmd += "--yz-mirror "
        if self.options.xz_mirror == True: admesh_cmd += "--xz-mirror "
        if self.options.scale != 1.0: admesh_cmd += "--scale " + str(self.options.scale) + " "
        if self.options.exact == True: admesh_cmd += "--exact "
        if self.options.nearby == True: admesh_cmd += "--nearby "
        if self.options.tolerance > 0.0: admesh_cmd += "--tolerance " + str(self.options.tolerance) + " "
        if self.options.iterations > 1: admesh_cmd += "--iterations " + str(self.options.iterations) + " "
        if self.options.increment > 0.0: admesh_cmd += "--increment " + str(self.options.increment) + " "
        if self.options.remove_unconnected == True: admesh_cmd += "--remove-unconnected "
        if self.options.normal_directions == True: admesh_cmd += "--normal-directions "
        if self.options.fill_holes == True: admesh_cmd += "--fill-holes "
        if self.options.reverse_all == True: admesh_cmd += "--reverse-all "
        if self.options.normal_values == True: admesh_cmd += "--normal-values "    
        admesh_cmd += "\"" + converted_inputfile + "\" "
        admesh_cmd += "-b \"" + converted_inputfile + "\""
        p = Popen(admesh_cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        p.wait()
        if p.returncode != 0: 
           inkex.utils.debug("admesh failed: %d %s %s" % (p.returncode, stdout, stderr))
           exit(1)
         
        # Run papercraft flattening   
        converted_flattenfile = os.path.join(tempfile.gettempdir(), os.path.splitext(os.path.basename(inputfile))[0] + ".svg")
        if os.path.exists(converted_flattenfile):
              os.remove(converted_flattenfile) #remove previously generated conversion file
        if self.options.generatelabels:
            unfold_exec = "unfold_labels"
        else:
            unfold_exec = "unfold_nolabels"
        if os.name=="nt":
            papercraft_cmd = "unfold\\" + unfold_exec + ".exe" + " < \"" + converted_inputfile + "\" > \"" + converted_flattenfile + "\""
        else:
            papercraft_cmd = "./unfold/" + unfold_exec + " < \"" + converted_inputfile + "\" > \"" + converted_flattenfile + "\"" 
        p = Popen(papercraft_cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        p.wait()
        if p.returncode != 0: 
            inkex.utils.debug("osresearch/papercraft unfold failed: %d %s %s" % (p.returncode, stdout, stderr))
            
        # Open converted output in fstl       
        if self.options.show_fstl == True:
            if os.name=="nt":
                fstl_cmd = "fstl\\fstl.exe \"" + converted_inputfile + "\""
            else:
                fstl_cmd = "./fstl/fstl \"" + converted_inputfile + "\""
            p = Popen(fstl_cmd, shell=True)
            p.wait()
               
        # Write the generated SVG into InkScape's canvas
        try:
            stream = open(converted_flattenfile, 'r')
        except FileNotFoundError as e:
            inkex.utils.debug("There was no SVG output generated. Cannot continue")
            exit(1)
        p = etree.XMLParser(huge_tree=True)   
        try:
            doc = etree.parse(stream, parser=etree.XMLParser(huge_tree=True)).getroot()
        except BaseException as e:
            self.msg("Error: STL could not be unfolded")
            exit(1)
        finally:
            stream.close()

        doc.set('id', self.svg.get_unique_id('papercraft_unfold'))
        self.document.getroot().append(doc)

        #adjust viewport and width/height to have the import at the center of the canvas
        if self.options.resizetoimport:
            bbox = inkex.elements._selected.ElementList.bounding_box(doc)
            if bbox is not None:
                root = self.svg.getElement('//svg:svg');
                offset = self.svg.unittouu(str(self.options.extraborder) + self.options.extraborder_units)
                root.set('viewBox', '%f %f %f %f' % (bbox.left - offset, bbox.top - offset, bbox.width + 2 * offset, bbox.height + 2 * offset))
                root.set('width', bbox.width + 2 * offset)
                root.set('height', bbox.height + 2 * offset)
              
if __name__ == '__main__':
    PapercraftUnfold().run()
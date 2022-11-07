#!/usr/bin/env python3
import sys
import os
import inkex
import tempfile
import subprocess
from subprocess import Popen, PIPE
from lxml import etree
from inkex import Transform

"""
Extension for InkScape 1.0

Unfold and import DXF into InkScape using dxf2papercraft. This is some kind of wrapper extension utilizing kabeja to convert the dxf output from dxf2papercraft into SVG.
To make it work you need to install at least java.

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 11.09.2020
Last patch: 26.10.2021
License: GNU GPL v3

Module licenses
- dxf2papercraft (dxf2papercraft.sourceforge.net) - GPL v3 License
- kabeja (http://kabeja.sourceforge.net/) - Apache v2 License

ToDos:
- in case of errors maybe think about adding ezdxf library to filter unsupported entities (similar like done in dxfdwgimporter extension)
- maybe add some DXF model preview tool (maybe a useless idea at all)
"""

class DXF2Papercraft(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--tab")    
        pars.add_argument("--inputfile")
        pars.add_argument("--resizetoimport", type=inkex.Boolean, default=True, help="Resize the canvas to the imported drawing's bounding box") 
        pars.add_argument("--extraborder", type=float, default=0.0)
        pars.add_argument("--extraborder_units")
        pars.add_argument("--scalefactor", type=float, default=1.0, help="Manual scale factor")
        pars.add_argument("--nomerge", type=inkex.Boolean, default=False, help="No merging of faces into single polygon")
        pars.add_argument("--number", type=inkex.Boolean, default=False, help="Print face numbers (labels)")
        pars.add_argument("--divide", type=inkex.Boolean, default=False, help="Draw each face separate")
        pars.add_argument("--overlap", type=inkex.Boolean, default=False, help="Allow overlapping faces in cut-out sheet")
        pars.add_argument("--hide", type=inkex.Boolean, default=False, help="Hide glue tabs")
        pars.add_argument("--force", type=inkex.Boolean, default=False, help="Force glue tabs, even if intersecting faces")
        pars.add_argument("--split", default="", help="Comma separated list of face numbers to disconnect from the rest")
        pars.add_argument("--strategy", default=0, help="Generation strategy")
                   
    def effect(self):
        dxf_input = self.options.inputfile
        if not os.path.exists(dxf_input):
            inkex.utils.debug("The input file does not exist. Please select a proper file and try again.")
            exit(1)

        # Prepare output
        dxf_output = os.path.join(tempfile.gettempdir(), os.path.splitext(os.path.basename(dxf_input))[0] + ".dxf")
        svg_output = os.path.join(tempfile.gettempdir(), os.path.splitext(os.path.basename(dxf_input))[0] + ".svg")

        # Clean up possibly previously generated output file from dxf2papercraft
        if os.path.exists(dxf_output):
            try:
                os.remove(dxf_output)
            except OSError as e: 
                inkex.utils.debug("Error while deleting previously generated output file " + dxf_input)

        if os.path.exists("delete_me_later"):
            try:
                os.remove("delete_me_later")
            except OSError as e: 
                pass
        if os.path.exists("debug.dat"):
            try:
                os.remove("debug.dat")
            except OSError as e: 
                pass

        # Run dxf2papercraft (make unfold)
        if os.name=="nt":
            dxf2ppc_cmd = "dxf2papercraft\\dxf2papercraft.exe "
        else:
            dxf2ppc_cmd = "./dxf2papercraft/dxf2papercraft "
        if self.options.nomerge  == True: dxf2ppc_cmd += "--nomerge "
        if self.options.number   == True: dxf2ppc_cmd += "--number "
        if self.options.divide   == True: dxf2ppc_cmd += "--divide "
        if self.options.overlap  == True: dxf2ppc_cmd += "--overlap "
        if self.options.hide     == True: dxf2ppc_cmd += "--hide "
        if self.options.force    == True: dxf2ppc_cmd += "--force "
        if self.options.split is not None and self.options.split != "": 
            dxf2ppc_cmd += "--split " + str(self.options.split) + " " #warning. this option has no validator! 
        dxf2ppc_cmd += "--strategy " + self.options.strategy + " "
        dxf2ppc_cmd += "\"" + dxf_input + "\" "
        dxf2ppc_cmd += "\"" + dxf_output + "\""
        p = Popen(dxf2ppc_cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        p.wait()
        if p.returncode != 0: 
           inkex.utils.debug("dxf2papercraft failed: %d %s %s" % (p.returncode, stdout, stderr))
           exit(1)
         
        #print command 
        #inkex.utils.debug(dxf2ppc_cmd)
          
        if not os.path.exists(dxf_output):
            inkex.utils.debug("There was no DXF output generated by dxf2papercraft. Maybe the input file is not a correct 3D DXF. Please check your model file.")
            exit(1)
          
        # Convert the DXF output to SVG
        wd = os.path.join(os.getcwd(), "kabeja")
        proc = subprocess.Popen("java -jar launcher.jar -nogui -pipeline svg " + dxf_output + " " + svg_output, cwd=wd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0: 
           inkex.errormsg("kabeja failed: %d %s %s" % (proc.returncode, stdout, stderr))  

        # Write the generated SVG into InkScape's canvas
        try:
            stream = open(svg_output, 'r')
        except FileNotFoundError as e:
            inkex.utils.debug("There was no SVG output generated by kabeja. Cannot continue")
            exit(1)
        p = etree.XMLParser(huge_tree=True)
        doc = etree.parse(stream, parser=etree.XMLParser(huge_tree=True)).getroot()
        stream.close()
        
        dxfGroup = inkex.Group(id=self.svg.get_unique_id("dxf2papercraft-"))
        for element in doc.iter("{http://www.w3.org/2000/svg}g"):
            if element.get('id') != "draft":
                dxfGroup.append(element)
        self.document.getroot().add(dxfGroup)
                
        #apply scale factor
        translation_matrix = [[self.options.scalefactor, 0.0, 0.0], [0.0, self.options.scalefactor, 0.0]]            
        dxfGroup.transform = Transform(translation_matrix) @ dxfGroup.transform

        #Adjust viewport and width/height to have the import at the center of the canvas
        if self.options.resizetoimport:
            #push some calculation of all bounding boxes. seems to refresh something in the background which makes the bbox calculation working at the bottom
            for element in self.document.getroot().iter("*"):
                try:
                    element.bounding_box()
                except:
                    pass
            bbox = dxfGroup.bounding_box() #only works because we process bounding boxes previously. see top 
            if bbox is not None:
                root = self.svg.getElement('//svg:svg');
                offset = self.svg.unittouu(str(self.options.extraborder) + self.options.extraborder_units)
                root.set('viewBox', '%f %f %f %f' % (bbox.left - offset, bbox.top - offset, bbox.width + 2 * offset, bbox.height + 2 * offset))
                root.set('width', bbox.width + 2 * offset)
                root.set('height', bbox.height + 2 * offset)
            else:
                self.msg("Error resizing to bounding box.")

if __name__ == '__main__':
    DXF2Papercraft().run()
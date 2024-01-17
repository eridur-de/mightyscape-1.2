#!/usr/bin/env python3

import inkex
import os
import shutil
import sys
import subprocess
from subprocess import Popen, PIPE

'''
Simple extension to utilize QCAD Pro for some neat DXF operations. Based on:
- https://ribbonsoft.com/rsforum/viewtopic.php?t=6801
- https://qcad.org/rsforum/viewtopic.php?t=8471

written 14.01.2024 by Mario Voigt / Stadtfabrikanten e.V.

ToDos
- black colored paths are getting blue or brown when using DXF Export of QCAD. Why? How to change this?
- keep canvas format
- keep original SVG Unit
'''

class QCAD_SVG(inkex.OutputExtension):

    def __init__(self):
        inkex.Effect.__init__(self)

    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--qcad_dxf_format", default="dxflib", help="DXF Export Type")
        pars.add_argument("--qcad_join_polylines", type=inkex.Boolean, default=True, help="Join Polylines")
        pars.add_argument("--qcad_tolerance", type=float, default=0.001, help="Polyline Tolerance")
        pars.add_argument("--qcad_purge_duplicates", type=inkex.Boolean, default=False, help="Purge duplicate lines")
        pars.add_argument("--qcad_pro_path", default="~/opt/qcad-3.28.2-pro-linux-x86_64/qcad", help="Location of qcad pro executable")
        pars.add_argument("--debug", type=inkex.Boolean, default=False, help="Show debug info")
        pars.add_argument("--open_in_qcad", type=inkex.Boolean, default=False, help="Open export file in QCAD")

    def inplace_change(self, filename, old_string, new_string):
        with open(filename) as f:
            s = f.read()
        with open(filename, 'w') as f:
            s = s.replace(old_string, new_string)
            f.write(s)

    def effect(self):
        so = self.options
        
        if os.path.exists(so.input_file) is False:
            inkex.utils.debug("WARNING: File was not saved yet! Try again after saving.")
            exit(1)
        
        qcad_pro_path = os.path.relpath(so.qcad_pro_path)
        tmpdir_path = os.path.dirname(so.input_file)   
        export_path = self.document_path()
        qcad_script = "qcad-dxf-script.js"
        if so.qcad_join_polylines is True:
            qcad_join_polylines = "true"
        else:
            qcad_join_polylines = "false"
        qcad_tolerance = "{:6.6f}".format(so.qcad_tolerance)
        if so.qcad_purge_duplicates is True:
            qcad_purge_duplicates = "true"
        else:
            qcad_purge_duplicates = "false"
        qcad_dxf_format = so.qcad_dxf_format
        
        if so.debug is True:
            inkex.utils.debug("Input file:{}".format(so.input_file))
            inkex.utils.debug("/tmp dir Path:{}".format(tmpdir_path))
            inkex.utils.debug("Export Path{}".format(export_path))
            inkex.utils.debug("QCAD Pro Path: {}".format(qcad_pro_path))
            inkex.utils.debug("QCAD Polyline Tolerance: {}".format(qcad_tolerance))
            inkex.utils.debug("QCAD DXF Format: {}".format(qcad_dxf_format))
    
        #we must copy the input file to a new file with ending *.svg. Otherwise QCAD does not recognise the file type
        target_file = self.options.input_file + ".svg"
        shutil.copy2(self.options.input_file, target_file)
   
        #copy the qcad-dxf-script.js file to temporary location and modify its content
        shutil.copy2(qcad_script, tmpdir_path)
        qcad_script_tmp = os.path.join(tmpdir_path, qcad_script)
        self.inplace_change(qcad_script_tmp, "$SVG_PATH$", target_file)
        self.inplace_change(qcad_script_tmp, "$QCAD_JOIN_POLYLINES$", qcad_join_polylines)
        self.inplace_change(qcad_script_tmp, "$QCAD_TOLERANCE$", qcad_tolerance)
        self.inplace_change(qcad_script_tmp, "$EXPORT_PATH$", export_path)
        self.inplace_change(qcad_script_tmp, "$QCAD_DXF_FORMAT$", qcad_dxf_format)
        self.inplace_change(qcad_script_tmp, "$QCAD_PURGE_DUPLICATES$", qcad_purge_duplicates)

        #build the command and execute the script
        command = [qcad_pro_path + " -autostart \"" + qcad_script_tmp + "\""]
        proc = subprocess.Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0: #in this case we exit
            inkex.utils.debug("QCAD Console Output: %d %s %s" % (proc.returncode, stdout, stderr))
        if "Application already running" in stderr.decode('UTF-8'):
            inkex.utils.debug("Warning. QCAD already running. Please close it and run this extension again!")
        
        if so.debug is True:
            inkex.utils.debug(stdout.decode('UTF-8'))
            inkex.utils.debug(stderr.decode('UTF-8'))
        proc.wait()

        if so.open_in_qcad is True:
            command = [qcad_pro_path + " " + export_path]
            proc = subprocess.Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode != 0: #in this case we exit
                inkex.utils.debug("QCAD Console Output: %d %s %s" % (proc.returncode, stdout, stderr))
            
            if so.debug is True:
                inkex.utils.debug(stdout.decode('UTF-8'))
                inkex.utils.debug(stderr.decode('UTF-8'))
            proc.wait()
            
    #this is just implemented to avoid a warning. The file gets written twice, because its already generated by QCAD, then it gets written again by save() method
    def save(self, stream):
        with open(self.document_path(), 'rb') as finalfile:
            stream.write(finalfile.read())
        
if __name__ == '__main__':
    QCAD_SVG().run()
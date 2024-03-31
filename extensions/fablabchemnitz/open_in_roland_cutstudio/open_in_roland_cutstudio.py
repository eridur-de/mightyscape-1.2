#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
'''
Roland CutStudio export script
Copyright (C) 2014 - 2020 Max Gaukler <development@maxgaukler.de>

skeleton based on Visicut Inkscape Plugin :
Copyright (C) 2012 Thomas Oster, thomas.oster@rwth-aachen.de

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

from builtins import open
from builtins import map
from builtins import str
from builtins import range
import sys
import os
from subprocess import Popen
import subprocess
import shutil
import numpy
from functools import reduce
import atexit
import filecmp
try:
    from pathlib import Path
except ImportError:
    # Workaround for Python < 3.5
    class fakepath:
        def home(self):
            return os.path.expanduser("~")
    Path = fakepath()
import tempfile
import random
import string

DEVNULL = open(os.devnull, 'w')
atexit.register(DEVNULL.close)
# work around Inkscape 1.3 failing to start when it "calls itself" (Inkscape -> Extension -> Inkscape):
# https://gitlab.com/inkscape/inkscape/-/issues/4163
# https://gitlab.com/inkscape/extensions/-/merge_requests/534
# TODO: Rewrite most parts of this extension using the inkex python module. This removes the need for such workarounds.
os.environ["SELF_CALL"] = "true"

def message(s):
    sys.stderr.write(s+"\n")
def debug(s):
    message(s)

# copied from https://github.com/t-oster/VisiCut/blob/0abe785a30d5d5085dd3b5953b38239b1ff83358/tools/inkscape_extension/visicut_export.py
def which(program, raiseError, extraPaths=[], subdir=None):
    """
    find program in the $PATH environment variable and in $extraPaths.
    If $subdir is given, also look in the given subdirectory of each $PATH entry.
    """
    pathlist=os.environ["PATH"].split(os.pathsep)
    if "nt" in os.name:
        pathlist.append(os.environ.get('ProgramFiles','C:\\Program Files\\'))
        pathlist.append(os.environ.get('ProgramFiles(x86)','C:\\Program Files (x86)\\'))
        pathlist.append('C:\\Program Files\\') # needed for 64bit inkscape on 64bit Win7 machines
        pathlist.append(os.path.dirname(os.path.dirname(os.getcwd()))) # portable application in the current directory
    pathlist += extraPaths
    if subdir:
        pathlist = [os.path.join(p, subdir) for p in pathlist] + pathlist
    def is_exe(fpath):
        return os.path.isfile(fpath) and (os.access(fpath, os.X_OK) or fpath.endswith(".exe"))
    for path in pathlist:
      exe_file = os.path.join(path, program)
      if is_exe(exe_file):
        return exe_file
    if raiseError:
        raise Exception("Cannot find " + str(program) + " in any of these paths: " + str(pathlist) + ". Either the program is not installed, PATH is not set correctly, or this is a bug.")
    else:
        return None

# copied from https://github.com/t-oster/VisiCut/blob/0abe785a30d5d5085dd3b5953b38239b1ff83358/tools/inkscape_extension/visicut_export.py
# Strip SVG to only contain selected elements, convert objects to paths, unlink clones
# Inkscape version: takes care of special cases where the selected objects depend on non-selected ones.
# Examples are linked clones, flowtext limited to a shape and linked flowtext boxes (overflow into the next box).
#
# Inkscape is called with certain "actions" to do the required cleanup
# The idea is similar to http://bazaar.launchpad.net/~nikitakit/inkscape/svg2sif/view/head:/share/extensions/synfig_prepare.py#L181 , but more primitive - there is no need for more complicated preprocessing here
def stripSVG_inkscape(src, dest, elements):    
    # create temporary file for opening with inkscape.
    # delete this file later so that it will disappear from the "recently opened" list.
    tmpfile = tempfile.NamedTemporaryFile(delete=False, prefix='temp-visicut-', suffix='.svg')
    tmpfile.close()
    tmpfile = tmpfile.name
    import shutil
    shutil.copyfile(src, tmpfile)


    # Updated for Inkscape 1.2, released 16 May 2022
    # inkscape --export-overwrite --actions=action1;action2...
    # (see inkscape --help, inkscape --action-list)
    # (for debugging, you can look at the intermediate state by running inkscape --with-gui --actions=... my_filename.svg)
    # Note that it is (almost?) impossible to find a sequence that works in all cases.
    # Cases to consider:
    # - selecting whole groups
    # - selecting objects within a group
    # - selecting across groups/layers (e.g., enter group, select something, then Shift-click to select things from other layers)
    # Difficulties with Inkscape:
    # - "invert selection" does not behave as expected in all these cases,
    #   for example if a group is selected then inverting can select the elements within.
    # - Inkscape has a wonderful --export-id commandline switch, but it only works correctly with one ID

    # Solution:
    actions = []
    # - select objects
    actions += ["select-by-id:" + ",".join(elements)]
    # - convert to path
    actions +=  ["clone-unlink", "object-to-path"]
    # - create group of selection
    actions += ["selection-group"]
    # - set group ID to a known value. Use a pseudo-random value to avoid collisions
    target_group_id = "TARGET-GROUP-" + "".join(random.sample(string.ascii_lowercase, 20))
    actions += ["object-set-attribute:id," + target_group_id]
    # - set export options: use only the target group ID, nothing else
    actions += ["export-id-only:true", "export-id:" + target_group_id]
    # - export
    actions += ["export-do"]


    command = [INKSCAPEBIN, tmpfile, "--export-overwrite", "--actions=" + ";".join(actions)]
    # to print the resulting commandline:
    # print(" ".join(["'" + c + "'" for c in command]), file=sys.stderr)
    
    
    DEBUG = False
    if DEBUG:
        # Inkscape sometimes silently ignores wrong verbs, so we need to double-check that everything's right
        for action in actions:
            aciton_list = [line.split(":")[0] for line in subprocess.check_output([INKSCAPEBIN, "--action-list"], stderr=DEVNULL).split("\n")]
            if action not in action_list:
                sys.stderr.write("Inkscape does not have the action '{}'. Please report this as a VisiCut bug.".format(action))
        
    inkscape_output = "(not yet run)"
    try:
        #sys.stderr.write(" ".join(command))
        # run inkscape, buffer output
        inkscape = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        inkscape_output = inkscape.communicate()[0]
        if inkscape.returncode != 0:
            sys.stderr.write("Error: cleaning the document with inkscape failed. Something might still be shown in visicut, but it could be incorrect.\nInkscape's output was:\n" + str(inkscape_output))
    except:
        sys.stderr.write("Error: cleaning the document with inkscape failed. Something might still be shown in visicut, but it could be incorrect. Exception information: \n" + str(sys.exc_info()[0]) + "Inkscape's output was:\n" + str(inkscape_output))

    # move output to the intended destination filename
    os.rename(tmpfile, dest)




# header
# for debugging purposes you can open the resulting EPS file in Inkscape,
#  select all, ungroup multiple times
# --> now you can view the exported lines in inkscape
prefix="""
%!PS-Adobe-3.0 EPSF-3.0
%%LanguageLevel: 2
%%BoundingBox -10000 -10000 10000 10000
%%EndComments
%%BeginSetup
%%EndSetup
%%BeginProlog
% This code (until EndProlog) is from an inkscape-exported EPS, copyright unknown, see cairo-library
save
50 dict begin
/q { gsave } bind def
/Q { grestore } bind def
/cm { 6 array astore concat } bind def
/w { setlinewidth } bind def
/J { setlinecap } bind def
/j { setlinejoin } bind def
/M { setmiterlimit } bind def
/d { setdash } bind def
/m { moveto } bind def
/l { lineto } bind def
/c { curveto } bind def
/h { closepath } bind def
/re { exch dup neg 3 1 roll 5 3 roll moveto 0 rlineto
      0 exch rlineto 0 rlineto closepath } bind def
/S { stroke } bind def
/f { fill } bind def
/f* { eofill } bind def
/n { newpath } bind def
/W { clip } bind def
/W* { eoclip } bind def
/BT { } bind def
/ET { } bind def
/pdfmark where { pop globaldict /?pdfmark /exec load put }
    { globaldict begin /?pdfmark /pop load def /pdfmark
    /cleartomark load def end } ifelse
/BDC { mark 3 1 roll /BDC pdfmark } bind def
/EMC { mark /EMC pdfmark } bind def
/cairo_store_point { /cairo_point_y exch def /cairo_point_x exch def } def
/Tj { show currentpoint cairo_store_point } bind def
/TJ {
  {
    dup
    type /stringtype eq
    { show } { -0.001 mul 0 cairo_font_matrix dtransform rmoveto } ifelse
  } forall
  currentpoint cairo_store_point
} bind def
/cairo_selectfont { cairo_font_matrix aload pop pop pop 0 0 6 array astore
    cairo_font exch selectfont cairo_point_x cairo_point_y moveto } bind def
/Tf { pop /cairo_font exch def /cairo_font_matrix where
      { pop cairo_selectfont } if } bind def
/Td { matrix translate cairo_font_matrix matrix concatmatrix dup
      /cairo_font_matrix exch def dup 4 get exch 5 get cairo_store_point
      /cairo_font where { pop cairo_selectfont } if } bind def
/Tm { 2 copy 8 2 roll 6 array astore /cairo_font_matrix exch def
      cairo_store_point /cairo_font where { pop cairo_selectfont } if } bind def
/g { setgray } bind def
/rg { setrgbcolor } bind def
/d1 { setcachedevice } bind def
%%EndProlog
%%Page: 1 1
%%BeginPageSetup
%%PageBoundingBox: -10000 -10000 10000 10000
%%EndPageSetup
% This is a severely crippled fucked-up pseudo-postscript for importing in Roland CutStudio
% Do not even try to open it with something else
% FIXME opening with inkscape currently does not show any objects, although it worked some time in the past

% Inkscape header, not used by cutstudio
% Start
q -10000 -10000 10000 10000 rectclip q

0 g
0.286645 w
0 J
0 j
[] 0.0 d
4 M q
% Cutstudio Start
"""
postfix="""
% Cutstudio End

%this is necessary for CutStudio so that the last line isnt skipped:
0 0 m

% Inkscape footer
S Q
Q Q
showpage
%%Trailer
end restore
%%EOF
"""

def EPS2CutstudioEPS(src, dest, mirror=False):
    def outputFromStack(stack, n, transformCoordinates=True):
        arr=stack[-(n+1):-1]
        if transformCoordinates:
            arrTransformed=[]
            for i in range(n//2):
                arrTransformed+=transform(arr[2*i], arr[2*i+1])
            return output(arrTransformed+[stack[-1]])
        else:
            return output(arr+[stack[-1]])
    def transform(x, y):
        #debug("trafo from: {} {}".format(x, y))
        p=numpy.array([[float(x),float(y),1]]).transpose()
        multiply = lambda a, b: numpy.matmul(a, b)
        # concatenate transformations by multiplying: new = transformation x previousTransformtaion
        m=reduce(multiply, scalingStack[::-1])
        m=m.transpose()
        #debug("with {}".format(m))
        pnew = numpy.matmul(m, p)
        x=float(pnew.item(0))
        y=float(pnew.item(1))
        #debug("to: {} {}".format(x, y))
        return [x, y]
    def outputMoveto(x, y):
        [xx, yy]=transform(x, y)
        return output([str(xx), str(yy), "m"])
    def outputLineto(x, y):
        [xx, yy]=transform(x, y)
        return output([str(xx), str(yy), "l"])
    def output(array):
        array=list(map(str, array))
        output=" ".join(array)
        #debug("OUTPUT: "+output)
        return output + "\n"
    stack=[]
    scalingStack=[numpy.identity(3)]
    if mirror:
        scalingStack.append(numpy.diag([-1, 1, 1]))
    lastMoveCoordinates=None
    outputStr=prefix
    inputFile=open(src)
    outputFile=open(dest, "w")
    for line in inputFile.readlines():
        line=line.strip()
        if line.startswith("%"):
            # comment line
            continue
        if line.endswith("re W n"): 
            continue # ignore clipping rectangle
        #debug(line)
        for item in line.split(" "):
            item=item.strip()
            if item=="":
                continue
            #debug("INPUT: " + item.__repr__())
            stack.append(item)
            if item=="h": # close path
                assert lastMoveCoordinates,  "closed path before first moveto"
                outputStr += outputLineto(float(lastMoveCoordinates[0]), float(lastMoveCoordinates[1]))
            elif item == "c": # bezier curveto
                outputStr += outputFromStack(stack, 6)
                stack=[]
            elif item=="re": # rectangle
                    x=float(stack[-5])
                    y=float(stack[-4])
                    dx=float(stack[-3])
                    dy=float(stack[-2])
                    outputStr += outputMoveto(x, y)
                    outputStr += outputLineto(x+dx, y)
                    outputStr += outputLineto(x+dx, y+dy)
                    outputStr += outputLineto(x, y+dy)
                    outputStr += outputLineto(x, y)
            elif item=="cm": # matrix transformation
                newTrafo=numpy.array([[float(stack[-7]), float(stack[-6]), 0], [float(stack[-5]), float(stack[-4]), 0], [float(stack[-3]), float(stack[-2]), 1]])
                #debug("applying trafo "+str(newTrafo))
                scalingStack[-1] = numpy.matmul(scalingStack[-1], newTrafo)
            elif item=="q": # save graphics state to stack
                scalingStack.append(numpy.identity(3))
            elif item=="Q": # pop graphics state from stack
                scalingStack.pop()
            elif item in ["m", "l"]:
                if item=="m": # moveto
                    lastMoveCoordinates=stack[-3:-1]
                elif item=="l": # lineto
                    pass
                outputStr += outputFromStack(stack, 2)
                stack=[]
            else:
                pass # do nothing
    outputStr += postfix
    outputFile.write(outputStr)
    outputFile.close()
    inputFile.close()

if os.name=="nt": # windows
    INKSCAPEBIN = which("inkscape.exe", True, subdir="Inkscape")
else:
    INKSCAPEBIN=which("inkscape", True)

assert os.path.isfile(INKSCAPEBIN),  "cannot find inkscape binary " + INKSCAPEBIN

selectedElements=[]
for arg in sys.argv[1:]:
    if arg[0] == "-":
        if len(arg) >= 5 and arg[0:5] == "--id=":
            selectedElements +=[arg[5:]]
    else:
        filename = arg
if "--selftest" in sys.argv:
    filename = "./test-input.svg"

if len(selectedElements)==0:
    shutil.copyfile(filename, filename+".filtered.svg")
else:
    # only take selected elements
    stripSVG_inkscape(src=filename, dest=filename+".filtered.svg", elements=selectedElements)

cmd = [INKSCAPEBIN, "-T", "--export-ignore-filters",  "--export-area-drawing", "--export-filename="+filename+".inkscape.eps", filename+".filtered.svg"]
inkscape_eps_file = filename + ".inkscape.eps"

#debug(" ".join(cmd))
assert 0 == subprocess.call(cmd, stderr=DEVNULL), 'EPS conversion failed: command returned error: ' + '"' + '" "'.join(cmd) + '"'
assert os.path.exists(inkscape_eps_file), 'EPS conversion failed: command did not create result file: ' + '"' + '" "'.join(cmd) + '"' 


if "--selftest" in sys.argv:
    # used for unit-testing: fixed location of output file
    destination = "./test-output-actual.cutstudio.eps"
else:
    # normally
    destination = filename + ".cutstudio.eps"

EPS2CutstudioEPS(inkscape_eps_file, destination, mirror=("--mirror=true" in sys.argv))

if "--selftest" in sys.argv:
    # unittest: compare with known reference output
    TEST_REFERENCE_FILE = "./test-output-reference.cutstudio.eps"
    assert filecmp.cmp(destination, TEST_REFERENCE_FILE), "Test output changed. Please compare " + destination + " and " + TEST_REFERENCE_FILE
    print("Selftest successful :-)")
    sys.exit(0)

if os.name=="nt":
    DETACHED_PROCESS = 8 # start as "daemon"
    Popen([which("CutStudio\\CutStudio.exe", True), "/import", destination], creationflags=DETACHED_PROCESS, close_fds=True)
else: #check if we have access to "wine"
    CUTSTUDIO_C_DRIVE = str(Path.home()) + "/.wine/drive_c/"
    CUTSTUDIO_PATH_LINUX_WINE = CUTSTUDIO_C_DRIVE + "Program Files (x86)/CutStudio/CutStudio.exe"
    CUTSTUDIO_COMMANDLINE = ["wine", CUTSTUDIO_PATH_LINUX_WINE, "/import", r'C:\cutstudio.eps']
    try:
        if not which("wine", False):
            raise Exception("Cannot find 'wine'")
        if not os.path.exists(CUTSTUDIO_PATH_LINUX_WINE):
            raise Exception("Cannot find CutStudio in " + CUTSTUDIO_PATH_LINUX_WINE)
        shutil.copyfile(destination, CUTSTUDIO_C_DRIVE + "cutstudio.eps")
        subprocess.check_call(CUTSTUDIO_COMMANDLINE, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except Exception as exc:
        message("Could not open CutStudio.\nInstead, your file was saved to:\n" + destination + "\n" + \
            "Please open that with CutStudio manually. \n\n" + \
            "Tip: On Linux, you can use 'wine' to install CutStudio 3.10. Then, the file will be directly opened with CutStudio. \n" + \
            " Diagnostic information: \n" + str(exc))
        #os.popen("/usr/bin/xdg-open " + filename)
        #Popen(["inkscape", filename+".filtered.svg"], stderr=DEVNULL)
        #Popen(["inkscape", filename+".cutstudio.eps"])
#os.unlink(filename+".filtered.svg")
#os.unlink(filename)
#os.unlink(filename+".cutstudio.eps")

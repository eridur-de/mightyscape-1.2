#!/usr/bin/env python3
"""
Inkcut, Plot HPGL directly from Inkscape.
   extension.py

   Copyright 2010-2018 The Inkcut Team

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
   MA 02110-1301, USA.
"""
import os
import sys

import inkex
import shutil
from lxml import etree
import subprocess
from inkcut import contains_text, convert_objects_to_paths

DEBUG = False

try:
    from subprocess import DEVNULL # py3k
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')

class InkscapeInkcutPlugin(inkex.Effect):
    def effect(self):
        """ Like cut but requires no selection and does no validation for
        text nodes.
        """

        nodes = self.svg.selected
        if not len(nodes):
            inkex.errormsg("There were no paths were selected.")
            return

        document = self.document
        if contains_text(self.svg.selected.values()):
            document = convert_objects_to_paths(self.args[-1], self.document)

        #: If running from source
        if DEBUG:
            python = '~/inkcut/venv/bin/python'
            inkcut = '~/inkcut/main.py'
            cmd = [python, inkcut]
        else:
            cmd = ['inkcut']
            
        if shutil.which('inkcut') is None:
            inkex.errormsg("Error: inkcut executable not found!")
            return

        cmd += ['open', '-',
               '--nodes']+[str(k) for k in nodes.keys()]
        p = subprocess.Popen(cmd,
                             stdin=subprocess.PIPE,
                             stdout=DEVNULL,
                             stderr=subprocess.STDOUT,
                             close_fds=sys.platform != "win32")
        p.stdin.write(etree.tostring(document))
        p.stdin.close()
        
        # Set the returncode to avoid this warning when popen is garbage collected:
        # "ResourceWarning: subprocess XXX is still running".
        # See https://bugs.python.org/issue38890 and
        # https://bugs.python.org/issue26741.
        p.returncode = 0

if __name__ == '__main__':
    InkscapeInkcutPlugin().run()
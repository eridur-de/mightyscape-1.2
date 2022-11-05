#!/usr/bin/env python3
"""
Inkcut, Plot HPGL directly from Inkscape.
   inkcut.py

   Copyright 2018 The Inkcut Team

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
   
   #edit by Mario Voigt:
   - latest version tested: Inkcut 2.1.5
"""
import os
import inkex
from lxml import etree
from subprocess import Popen, PIPE
import shutil
from shutil import copy2
import inkex.command


def contains_text(nodes):
    for node in nodes:
        tag = node.tag[node.tag.rfind("}")+1:]
        if tag == 'text':
            return True
    return False

def convert_objects_to_paths(file, document):
    tempfile = os.path.splitext(file)[0] + "-prepare.svg"
    copy2(file, tempfile)
    actions_list = []
    actions_list.append("select-all")
    actions_list.append("clone-unlink-recursive")
    actions_list.append("object-to-path")
    actions = ";".join(actions_list)
    cli_output = inkex.command.inkscape(tempfile, "--export-overwrite", actions=actions)
    if len(cli_output) > 0:
        self.msg("Inkscape returned the following output when trying to run the file export; the file export may still have worked:")
        self.msg(cli_output)
        return document.getroot()
    else:
        return etree.parse(tempfile).getroot()

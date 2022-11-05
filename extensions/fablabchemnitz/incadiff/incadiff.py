#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (C) 2021 Thomas Maziere <thomas.maziere@incaya.fr>

Largely and mostly inspired by inx-pathops (https://gitlab.com/moini_ink/inx-pathops/)
Copyright (C) 2014  Ryan Lerch (multiple difference)
              2016  Maren Hachmann <marenhachmannATyahoo.com>
                    (refactoring, extend to multibool)
              2017  su_v <suv-sf@users.sf.net>
                    Rewrite to support large selections (process in chunks), to
                    improve performance (support groups, z-sort ids with python
                    instead of external query), and to extend GUI options.


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
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

"""
incadiff
Apply successive difference operations on superimposed paths. Useful for plotter addicts.
"""

import os
from shutil import copy2
import time
from lxml import etree
import inkex
import inkex.command

def timed(f):
    """Minimalistic timer for functions."""
    # pylint: disable=invalid-name
    start = time.time()
    ret = f()
    elapsed = time.time() - start
    return ret, elapsed


def get_defs(node):
    """Find <defs> in children of *node*, return first one found."""
    path = '/svg:svg//svg:defs'
    try:
        return node.xpath(path, namespaces=inkex.NSS)[0]
    except IndexError:
        return etree.SubElement(node, inkex.addNS('defs', 'svg'))


def is_group(node):
    """Check node for group tag."""
    return node.tag == inkex.addNS('g', 'svg')


def is_path(node):
    """Check node for path tag."""
    return node.tag == inkex.addNS('path', 'svg')


def is_basic_shape(node):
    """Check node for SVG basic shape tag."""
    return node.tag in (inkex.addNS(tag, 'svg') for tag in ('rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon'))


def is_custom_shape(node):
    """Check node for Inkscape custom shape type."""
    return inkex.addNS('type', 'sodipodi') in node.attrib


def is_shape(node):
    """Check node for SVG basic shape tag or Inkscape custom shape type."""
    return is_basic_shape(node) or is_custom_shape(node)


def has_path_effect(node):
    """Check node for Inkscape path-effect attribute."""
    return inkex.addNS('path-effect', 'inkscape') in node.attrib


def is_modifiable_path(node):
    """Check node for editable path data."""
    return is_path(node) and not (has_path_effect(node) or
                                  is_custom_shape(node))


def is_image(node):
    """Check node for image tag."""
    return node.tag == inkex.addNS('image', 'svg')


def is_text(node):
    """Check node for text tag."""
    return node.tag == inkex.addNS('text', 'svg')


def does_pathops(node):
    """Check whether node is supported by Inkscape path operations."""
    return (is_path(node) or
            is_shape(node) or
            is_text(node))


# ----- list processing helper functions

def recurse_selection(node, id_list, level=0, current=0):
    """Recursively process selection, add checked elements to id list."""
    current += 1
    if not level or current <= level:
        if is_group(node):
            for child in node:
                id_list = recurse_selection(child, id_list, level, current)
    if does_pathops(node):
        id_list.append(node.get('id'))
    return id_list


def z_sort(node, alist):
    """Return new list sorted in document order (depth-first traversal)."""
    ordered = []
    id_list = list(alist)
    count = len(id_list)
    for element in node.iter():
        element_id = element.get('id')
        if element_id is not None and element_id in id_list:
            id_list.remove(element_id)
            ordered.append(element_id)
            count -= 1
            if not count:
                break
    return ordered


def z_iter(node, alist):
    """Return iterator over ids in document order (depth-first traversal)."""
    id_list = list(alist)
    for element in node.iter():
        element_id = element.get('id')
        if element_id is not None and element_id in id_list:
            id_list.remove(element_id)
            yield element_id


def chunks(alist, max_len):
    """Chunk a list into sublists of max_len length."""
    for i in range(0, len(alist), max_len):
        yield alist[i:i+max_len]


class Incadiff(inkex.EffectExtension):

    def __init__(self):
        inkex.Effect.__init__(self)
        self.actions_list = []

    def get_selected_ids(self):
        """Return a list of valid ids for inkscape path operations."""
        id_list = []
        if len(self.svg.selected) == 0:
            pass
        else:
            level = 0
            for node in self.svg.selected.values():
                recurse_selection(node, id_list, level)
        if len(id_list) < 2:
            inkex.errormsg("This extension requires at least 2 elements " +
                           "of type path, shape or text. " +
                           "The elements can be part of selected groups, " +
                           "or directly selected.")
            return None
        if len(id_list) > 64:
            inkex.errormsg("You should not select more than 64 shapes/paths, " +
                           "and ideally you should apply this extension to small groups of objects.")
            return None
        
        else:
            return id_list

    def get_sorted_ids(self):
        """Return a list with z-sorted ids."""
        sorted_ids = None
        id_list = self.get_selected_ids()
        if id_list is not None:
            sorted_ids = list(z_iter(self.document.getroot(), id_list))
            return (sorted_ids)
        else:
            return
        

    def run_cmd(self, tempfile):
        actions = ";".join(self.actions_list)
        cli_output = inkex.command.inkscape(tempfile, "--export-overwrite", actions=actions)
        if len(cli_output) > 0:
            self.msg("Inkscape returned the following output when trying to run the file export; the file export may still have worked:")
            self.msg(cli_output)
            
    def duplicate_and_diff(self, id_list, tempfile):
        # for each selected path, duplicate and diff for each path below
        nb_shapes = len(id_list)
        for i in range(0, nb_shapes):
            top_path = id_list[i]
            j = i
            while j > 0:
                j -= 1
                self.actions_list.append("select-by-id:"+top_path)
                self.actions_list.append("duplicate")
                self.actions_list.append("select-by-id:" + id_list[j])
                self.actions_list.append("path-difference")
                self.actions_list.append("unselect-by-id:"+top_path)
            if nb_shapes > 20:
                self.run_cmd(tempfile)
                self.actions_list = []
        if len(self.actions_list) > 0:
            self.run_cmd(tempfile)
            self.actions_list = []

    def loop_diff(self):
        """Loop through selected items and run external command(s)."""

        tempfile = self.options.input_file + "-incadiff.svg"
        # prepare
        # we need to do this because command line Inkscape with gui
        # gives lots of info dialogs when the file extension isn't 'svg'
        # so the inkscape() call cannot open the file without user
        # interaction, and fails in the end when trying to save
        copy2(self.options.input_file, tempfile)

        # loop through selected paths
        id_list = self.get_sorted_ids()
        if id_list is not None:
            self.duplicate_and_diff(id_list, tempfile)
        else:
            return

        
        # replace current document with content of temp copy file
        self.document = inkex.load_svg(tempfile)
        # update self.svg
        self.svg = self.document.getroot()

        # purge missing tagrefs (see below)
        self.update_tagrefs()
        # clean up
        self.cleanup(tempfile)

    def cleanup(self, tempfile):
        try:
            os.remove(tempfile)
        except Exception:  # pylint: disable=broad-except
            pass

    def effect(self):
        if self.has_tagrefs():
            # unsafe to use with extensions ...
            inkex.utils.errormsg("This document uses Inkscape selection sets. " +
                                 "Modifying the content with this extension " +
                                 "may cause Inkscape to crash on reload or close. " +
                                 "Please delete the selection sets, " +
                                 "save the document under a new name and " +
                                 "try again in a new Inkscape session.")
        else:
            self.loop_diff()

    def has_tagrefs(self):
        """Check whether document has selection sets with tagrefs."""
        defs = get_defs(self.document.getroot())
        inkscape_tagrefs = defs.findall(
            "inkscape:tag/inkscape:tagref", namespaces=inkex.NSS)
        return len(inkscape_tagrefs) > 0

    def update_tagrefs(self, mode='purge'):
        """Check tagrefs for deleted objects."""
        defs = get_defs(self.document.getroot())
        inkscape_tagrefs = defs.findall(
            "inkscape:tag/inkscape:tagref", namespaces=inkex.NSS)
        if len(inkscape_tagrefs) > 0:
            for tagref in inkscape_tagrefs:
                href = tagref.get(inkex.addNS('href', 'xlink'))[1:]
                if self.svg.getElementById(href) is None:
                    if mode == 'purge':
                        tagref.getparent().remove(tagref)
                    elif mode == 'placeholder':
                        temp = etree.Element(inkex.addNS('path', 'svg'))
                        temp.set('id', href)
                        temp.set('d', 'M 0,0 Z')
                        self.document.getroot().append(temp)

    # ----- workaround to fix Effect() performance with large selections

    def collect_ids(self, doc=None):
        """Iterate all elements, build id dicts (doc_ids, selected)."""
        doc = self.document if doc is None else doc
        id_list = list(self.options.ids)
        for node in doc.getroot().iter(tag=etree.Element):
            if 'id' in node.attrib:
                node_id = node.get('id')
                self.doc_ids[node_id] = 1
                if node_id in id_list:
                    self.svg.selected[node_id] = node
                    id_list.remove(node_id)

    def getselected(self):
        """Overload Effect() method."""
        self.collect_ids()

    def getdocids(self):
        """Overload Effect() method."""
        pass


if __name__ == '__main__':
    Incadiff().run()

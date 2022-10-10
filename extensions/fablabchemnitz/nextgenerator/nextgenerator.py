#!/usr/bin/env python3
# coding=utf-8
#
# NextGenerator - an Inkscape extension to export images with automatically replaced values
# Copyright (C) 2008  Aurélio A. Heckert (original Generator extension in Bash)
#               2019-2021  Maren Hachmann (Python rewrite, update for Inkscape 1.0)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
An Inkscape extension to automatically replace values (text, attribute values)
in an SVG file and to then export the result to various file formats.

This is useful e.g. for generating images for name badges and other similar items.
"""

from __future__ import unicode_literals

import os
import csv
import json
import time #for debugging purposes
import inkex
import html
from inkex.command import inkscape

__version__ = '1.2'

class NextGenerator(inkex.base.TempDirMixin, inkex.base.InkscapeExtension):
    """Generate image files by replacing variables in the current file"""

    def add_arguments(self, pars):
        pars.add_argument("-c", "--csv_file", type=str, dest="csv_file", help="path to a CSV file")
        pars.add_argument("-e", "--extra-vars", help="additional variables to replace and the corresponding columns, in JSON format")
        pars.add_argument("-n", "--num_sets", type=int, default="1", help="number of sets in the template")
        pars.add_argument("-f", "--format", help="file format to export to: png, pdf, svg, ps, eps")
        pars.add_argument("-d", "--dpi", type=int, default="300", help="dpi value for exported raster images")
        pars.add_argument("-o", "--output_folder", help="path to output folder")
        pars.add_argument("-p", "--file_pattern", help="pattern for the output file")

        pars.add_argument("-t", "--tab", default="", help="not needed at all")
        pars.add_argument("-l", "--helptabs", default="", help="not needed at all")
        pars.add_argument("-i", "--id", default="", help="not needed at all")

    def effect(self):

        # load the attributes that should be replaced in addition to textual values
        if self.options.extra_vars == None:
            self.options.extra_vars = '{}'

        extra_vars = json.loads(self.options.extra_vars)


        # load the CSV file
        # spaces around commas will be stripped
        csv.register_dialect('generator', 'excel', skipinitialspace=True)

        with open(self.options.csv_file, newline='', encoding='utf-8-sig') as csvfile:

            data = csv.DictReader(csvfile, dialect='generator')

            if self.options.num_sets == 1:
                for row in data:
                    export_base_name = self.options.file_pattern
                    self.new_doc = self.document
                    for i, (key, value) in enumerate(row.items()):
                        search_string = "%VAR_" + key + "%"
                        # replace any occurrances of %VAR_my_variable_name% in the SVG file source code
                        self.new_doc = self.new_doc.replace(search_string, html.escape(value))
                        # build the file name, still without file extension
                        export_base_name = export_base_name.replace(search_string, value)
                    for key, svg_cont in extra_vars.items():
                        if key in row.keys():
                            # replace any attributes and other SVG content by the values from the CSV file
                            self.new_doc = self.new_doc.replace(svg_cont, row[key])
                        else:
                            inkex.errormsg("The replacements in the generated images may be incomplete. Please check your entry '{key}' in the field for the non-text values.").format(key=key)
                    if self.export(export_base_name) != True:
                        return

            elif self.options.num_sets > 1:
                # we need a list to access specific rows and to be able to count it
                data = list(data)

                # check if user's indication of num_sets is compatible with file
                for key in data[0].keys():
                    num_occurr = self.document.count("%VAR_" + key + "%")
                    # We ignore keys that don't appear in the document
                    if num_occurr != 0 and num_occurr != self.options.num_sets:
                        return inkex.errormsg("There are {0} occurrances of the variable '{1}' in the document, but the number of sets you indicated is {2}. Please make sure that each set contains all variables and that there are just as many sets in your document as you indicate.".format(num_occurr, key, self.options.num_sets))

                # abusing negative floor division which rounds to the next lowest number to figure out how many pages we will get
                num_exports = -((-len(data))//self.options.num_sets) 
                # now we hope that the document is properly prepared and the stacking order cycles through datasets - if not, the result will be nonsensical, but we can't know.

                for export_file_num in range(num_exports):
                    # we only number the export files if there are sets
                    export_base_name = "".join([x if x.isalnum() else "_" for x in self.options.file_pattern]) + '_{}'.format(str(export_file_num)) 
                    self.new_doc = self.document
                    
                    for set_num in range(self.options.num_sets):
                        
                        # number of the data row in the CSV file
                        n = export_file_num * self.options.num_sets + set_num
                        if n < len(data):
                            dataset = data[n]
                        else:
                            # no more values available, stop trying to replace them
                            break
                        
                        for i, (key, value) in enumerate(dataset.items()):
                            search_string = "%VAR_" + key + "%"
                            # replace the next occurrance of %VAR_my_variable_name% in the SVG file source code
                            self.new_doc = self.new_doc.replace(search_string, html.escape(value), 1)

                        for key, svg_cont in extra_vars.items():
                            if key in dataset.keys():
                                # replace any attributes and other SVG content by the values from the CSV file
                                self.new_doc = self.new_doc.replace(svg_cont, dataset[key], 1)
                            else:
                                inkex.errormsg(_("The replacements in the generated images may be incomplete. Please check your entry '{key}' in the field for the non-text values.").format(key=key))
                    self.export(export_base_name)

    def export(self, export_base_name):

        export_file_name = '{0}.{1}'.format(export_base_name, self.options.format)

        if os.path.exists(self.options.output_folder):
            export_file_path = os.path.join(self.options.output_folder, export_file_name)
        else:
            inkex.errormsg("The selected output folder does not exist.")
            return False


        if self.options.format == 'svg':
            # would use this, but it cannot overwrite, nor handle strings for writing...:
            # write_svg(self.new_doc, export_file_path)
            with open(export_file_path, 'w') as f:
                f.write(self.new_doc)
        else:

            actions = {
                'png' : 'export-dpi:{dpi};export-filename:{file_name};export-do;FileClose'.\
                        format(dpi=self.options.dpi, file_name=export_file_path),
                'pdf' : 'export-dpi:{dpi};export-pdf-version:1.5;export-text-to-path;export-filename:{file_name};export-do;FileClose'.\
                        format(dpi=self.options.dpi, file_name=export_file_path),
                'ps'  : 'export-dpi:{dpi};export-text-to-path;export-filename:{file_name};export-do;FileClose'.\
                        format(dpi=self.options.dpi, file_name=export_file_path),
                'eps' : 'export-dpi:{dpi};export-text-to-path;export-filename:{file_name};export-do;FileClose'.\
                        format(dpi=self.options.dpi, file_name=export_file_path),
                }

            # create a temporary svg file from our string
            temp_svg_name = '{0}.{1}'.format(export_base_name, 'svg')
            temp_svg_path = os.path.join(self.tempdir, temp_svg_name)
            #inkex.utils.debug("temp_svg_path=" + temp_svg_path)
            with open(temp_svg_path, 'w') as f:
                 f.write(self.new_doc)
                 #inkex.utils.debug("self.new_doc=" + self.new_doc)
            # let Inkscape do the exporting
            # self.debug(actions[self.options.format])
            cli_output = inkscape(temp_svg_path, actions=actions[self.options.format])

            if len(cli_output) > 0:
                self.debug(_("Inkscape returned the following output when trying to run the file export; the file export may still have worked:"))
                self.debug(cli_output)
                return False
        return True
    
    def load(self, stream):
        return str(stream.read(), 'utf-8')

    def save(self, stream):
        # must be implemented, but isn't needed.
        pass

if __name__ == '__main__':
    NextGenerator().run()
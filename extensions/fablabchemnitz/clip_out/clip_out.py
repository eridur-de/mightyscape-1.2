#!/usr/bin/env python3
# coding=utf-8
#
# Copyright (C) [2021] [Matt Cottam], [mpcottam@raincloud.co.uk]
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
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
#
# #############################################################################
#  Clip Out - Export multiple clipped images using paths / shapes and a background image
#  After setting the options in the main dialogue
#  Assign a shortcut in Inkscape Edit>Preferences>Interface>Keyboard to org.inkscape.inklinea.clip_out.noprefs
#  For shortcut triggered quick export
#  It does require that you have saved
#  Your svg file at least once before using ( will not work on an unsaved svg )
#  Requires Inkscape 1.1+ -->
# #############################################################################
import random

import inkex
from inkex import command
from pathlib import Path
from datetime import datetime
import tempfile, shutil, os
from lxml import etree

import time

conversions = {
    'in': 96.0,
    'pt': 1.3333333333333333,
    'px': 1.0,
    'mm': 3.779527559055118,
    'cm': 37.79527559055118,
    'm': 3779.527559055118,
    'km': 3779527.559055118,
    'Q': 0.94488188976378,
    'pc': 16.0,
    'yd': 3456.0,
    'ft': 1152.0,
    '': 1.0,  # Default px
}


def make_temp_svg(self):
    temp_svg_file = tempfile.NamedTemporaryFile(mode='r+', delete='false', suffix='.svg')
    # Write the contents of the updated svg to a tempfile to use with command line
    my_svg_string = self.svg.root.tostring().decode("utf-8")
    temp_svg_file.write(my_svg_string)
    return temp_svg_file


def inkscape_command_line_export(self, my_temp_svg_filename_path, my_export_path, export_png_actions):
    if Path(my_export_path).is_dir():
        cli_output = inkex.command.inkscape(my_temp_svg_filename_path, export_png_actions)
        if len(cli_output) > 0:
            self.msg("Inkscape returned the following output when trying to run the file export; the file export may still have worked:")
            self.msg(cli_output)
    else:
        inkex.errormsg('Please Select An Export Folder')


def make_image_frame(self, background_image):
    found_units = self.svg.unit

    unit_conversion_factor = conversions[found_units]

    bbox_x = background_image.bounding_box().left / unit_conversion_factor
    bbox_y = background_image.bounding_box().top / unit_conversion_factor
    bbox_width = background_image.bounding_box().width / unit_conversion_factor
    bbox_height = background_image.bounding_box().height / unit_conversion_factor

    top_left = str(f'{bbox_x} {bbox_y}')
    top_right_x = str(bbox_x + bbox_width)
    top_right_y = str(bbox_y)
    bottom_right_x = str(bbox_x + bbox_width)
    bottom_right_y = str(bbox_y + bbox_height)
    bottom_left_x = str(bbox_x)
    bottom_left_y = str(bbox_y + bbox_height)

    rect_path = f'M  {top_left} L {top_right_x} {top_right_y} L {bottom_right_x} {bottom_right_y} L {bottom_left_x} {bottom_left_y} Z'
    path_id = 'inverse_clip_frame' + str(random.randrange(10000, 99999))
    parent = self.svg.get_current_layer()
    rect_path_object = etree.SubElement(parent, inkex.addNS('path', 'svg'))
    rect_path_object.attrib['id'] = path_id
    rect_path_object.attrib['d'] = rect_path
    rect_path_object.style['stroke'] = 'black'
    rect_path_object.style['stroke-width'] = '1px'

    return rect_path_object.get_id()


def command_line_call(self):

    # Get export path
    my_export_path = self.options.save_path

    # Get name of currently open Inkscape file
    my_filename = self.svg.name

    # Check to see if user has saved file at least once
    if len(my_filename) < 2:
        inkex.errormsg('Please Save Your File First')
        return

    # Get png dpi setting
    png_dpi = self.options.png_dpi

    # Get crop settings
    if self.options.canvas_to_selection == 'true':
        canvas_to_selection = 'FitCanvasToSelection;'
        is_cropped = 'cropped_'
    else:
        canvas_to_selection = ''
        is_cropped = ''

    # Look at selection list 1st item must be background image
    my_objects = self.svg.selected
    # Exit if less than 2 objects are selected
    if len(my_objects) < 2:
        return
    if my_objects[-1].TAG != 'image':
        inkex.errormsg('Last Selected Object Must Be An Image')
        return

    # Clip background image by each object and export to png

    my_background = my_objects[-1]
    my_background_id = my_background.get_id()

    # Create a rectangular path same size as image to be clipped used for inverse only
    image_frame_id = make_image_frame(self, my_background)

    # my_temp_filename_path = make_temp_svg(my_file_path, my_filename)
    my_temp_svg_file = make_temp_svg(self)
    my_temp_svg_filename_path = my_temp_svg_file.name

    for my_object in my_objects:

        # current date and time to time stamp
        timestamp = datetime.today().replace(microsecond=0)
        timestamp_suffix = str(timestamp.strftime('%Y-%m-%d-%H-%M-%S'))

        # This loop looks at each clipping object, ignores any image objects
        if my_object.TAG != 'image':
            my_object_id = my_object.get_id()

            # Build a formatted string for command line actions

            # --batch-process ( or --with-gui ) is required if verbs are used in addition to actions
            my_actions = '--actions='

            export_png_actions = ''

            # For Positive Clip
            if self.options.clip_type_inverse is False:

                # Creates individual object clipped files
                if self.options.output_set == 'separate' or self.options.output_set == 'master_and_separate':
                    my_png_export_filename_path = my_export_path + '/' + my_filename.replace('.svg',
                                                                                             '_' + my_object_id + '_' + is_cropped + timestamp_suffix + '.png')

                    export_png_actions = my_actions + f'select-by-id:{my_background_id}; \
                    selection-stack-down; \
                    select-by-id:{my_background_id},{my_object_id}; \
                    select-invert; \
                    delete-selection; \
                    select-all; \
                    object-set-clip; \
                    select-all; \
                    {canvas_to_selection} \
                    export-filename:{my_png_export_filename_path}; \
                    export-dpi:{png_dpi}; \
                    export-do'

                    export_png_actions = export_png_actions.replace(' ', '')

                    inkscape_command_line_export(self, my_temp_svg_filename_path, my_export_path, export_png_actions)
                        
            # For Inverse Clip
            else:
                if self.options.output_set == 'separate' or self.options.output_set == 'master_and_separate':
                    my_png_export_filename_path = my_export_path + '/' + my_filename.replace('.svg',
                        '_' + my_object_id + '_''inverse_' + is_cropped + timestamp_suffix + '.png')

                    export_png_actions = my_actions + f'select-by-id:{image_frame_id},{my_object_id},{my_background_id}; \
                    select-invert; \
                    delete-selection; \
                    select-by-id:{image_frame_id}; \
                    selection-stack-down; \
                    unselect-by-id:{image_frame_id}; \
                    select-by-id:{image_frame_id},{my_object_id}; \
                    path-difference; \
                    unselect-by-id:{image_frame_id},{my_object_id}; \
                    select-by-id:{my_background_id}; \
                    selection-stack-down; \
                    select-all; \
                    object-set-clip; \
                    select-all; \
                    {canvas_to_selection} \
                    export-filename:{my_png_export_filename_path}; \
                    export-dpi:{png_dpi}; \
                    export-do'

                    export_png_actions = export_png_actions.replace(' ', '')

                    inkscape_command_line_export(self, my_temp_svg_filename_path, my_export_path, export_png_actions)


    if self.options.output_set == 'master_only' or self.options.output_set == 'master_and_separate':

        # Creates a master image with all clipped objects
        my_actions = '--actions='
        my_object_id_list = ''

        for my_object in my_objects:
            if my_object.TAG != 'image':
                # Build select ID string length - Windows has a max cmdline string length of 8192
                my_object_id = my_object.get_id()
                my_object_id_list += f'{my_object_id},'
        # Remove last comma from id list
        my_object_id_list = my_object_id_list.rstrip(',')

        if self.options.clip_type_inverse is False:

            my_png_export_filename_path = my_export_path + '/' + my_filename.replace('.svg',
                '_' + 'master_' + is_cropped + timestamp_suffix + '.png')

            export_png_actions = my_actions + f' \
            select-by-id:{my_object_id_list},{my_background_id}; \
            select-invert; \
            delete-selection; \
            select-clear; \
            select-by-id:{my_object_id_list}; \
            path-combine; \
            select-clear; \
            select-by-id:{my_background_id}; \
            selection-stack-down; \
            select-clear; \
            select-all; \
            object-set-clip; \
            select-all; \
            {canvas_to_selection} \
            export-filename:{my_png_export_filename_path}; \
            export-dpi:{png_dpi}; \
            export-do;'

        else:

            my_png_export_filename_path = my_export_path + '/' + my_filename.replace('.svg',
                '_' + 'inverse_master_' + is_cropped + timestamp_suffix + '.png')

            export_png_actions = my_actions + f' \
            select-by-id:{my_object_id_list},{my_background_id},{image_frame_id}; \
            select-invert; \
            delete-selection; \
            select-by-id:{my_object_id_list}; \
            path-combine; \
            select-clear; \
            select-by-id:{image_frame_id}; \
            selection-stack-down; \
            select-all; \
            unselect-by-id:{my_background_id}; \
            path-difference; \
            select-clear; \
            select-by-id:{my_background_id}; \
            selection-stack-down; \
            select-all; \
            object-set-clip; \
            select-all; \
            {canvas_to_selection} \
            export-filename:{my_png_export_filename_path}; \
            export-dpi:{png_dpi}; \
            export-do;'

        export_png_actions = export_png_actions.replace(' ', '')

    inkscape_command_line_export(self, my_temp_svg_filename_path, my_export_path, export_png_actions)
        
    # Remove rectangular path
    image_frame = self.svg.getElementById(image_frame_id)
    image_frame.delete()

    # Close temp file
    my_temp_svg_file.close()
    
class ClipOut(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--clip_type_inverse", type=inkex.Boolean, default=False)
        pars.add_argument("--notebook_main", default=0)
        pars.add_argument("--output_set", default=0)
        pars.add_argument("--canvas_to_selection", default=0)
        pars.add_argument("--save_path", default=str(Path.home()))
        pars.add_argument("--png_dpi", type=int, default=96)

    def effect(self):
        command_line_call(self)


if __name__ == '__main__':
    ClipOut().run()

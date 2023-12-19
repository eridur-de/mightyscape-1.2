#! /usr/bin/python3

'''
Copyright (C) 2021 Scott Pakin, scott-ink@pakin.org

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
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301, USA.

'''

import base64
import inkex
import io
import PIL.Image
import random
import sys

class PixelsToObjects(inkex.EffectExtension):
    "Copy an object to the coordinates of each pixel in an image."

    def add_arguments(self, pars):
        'Process program parameters passed in from the UI.'
        pars.add_argument('--tab', help='The selected UI tab when OK was pressed')
        pars.add_argument('--scale', type=float,  help='Factor by which to scale image coordinates')
        pars.add_argument('--color-stroke', type=inkex.Boolean, help="Color the object's stroke to match the pixel color")
        pars.add_argument('--color-fill', type=inkex.Boolean, help='Fill the object with the pixel color')
        pars.add_argument('--ignore-bg', type=inkex.Boolean, help='Ignore background-colored pixels')
        pars.add_argument('--obj-select', choices=['coords', 'rr', 'random'], help='Specify how to iterate among multiple selected objects')

    def _get_selection(self):
        'Return an image and an object.'
        # Bin the objects in the current selection.
        img = None
        objs = []
        for s in self.svg.selection.values():
            if isinstance(s, inkex.Image):
                if img == None:
                    img = s  # First image encountered
                else:
                    objs.append(s)  # All remaining images are consider "other" objects
            else:
                objs.append(s)  # All non-images are "other" objects

        # Ensure the selection is valid.
        if img == None or objs == []:
            inkex.utils.errormsg(_('Pixels to Objects requires that one image and at least one additional object be selected.'))
            sys.exit(1)
        return img, objs

    def _generate_coords2obj(self, objs):
        '''Return a function that maps pixel coordinates to an object in a
        given list of SVG objects.'''
        n_objs = len(objs)
        obj_select = self.options.obj_select
        if obj_select == 'coords':
            return lambda x, y: objs[(x + y)%n_objs]
        if obj_select == 'rr':
            idx = 0
            def coords2obj_rr(x, y):
                nonlocal idx
                obj = objs[idx]
                idx = (idx + 1)%len(objs)
                return obj
            return coords2obj_rr
        if obj_select == 'random':
            return lambda x, y: objs[random.randint(0, n_objs - 1)]
        inkex.errormessage(_('internal error: unhandled object-selection type "%s"' % obj_select))
        sys.exit(1)

    def _copy_object_to(self, obj, xy):
        '''Copy an object and center the copy on the given coordinates,
        optionally recoloring its stroke and/or fill'''
        # Create a transform that moves the object to the origin.
        xform = inkex.Transform(obj.get('transform'))
        pos = obj.bounding_box(obj.composed_transform()).center
        xform.add_translate(-pos)

        # Modify the transform to move the object to the target coordinates.
        xform.add_translate(xy)

        # Duplicate the object and apply the transform.
        new_obj = obj.duplicate()
        new_obj.update(transform=xform)
        return new_obj

    def _read_image(self, img_elt):
        'Read an image from either the SVG file itself or an external file.'
        # Read the image from an external file.
        fname = img_elt.get('sodipodi:absref')
        if fname != None:
            # Fully qualified filename.  Read it directly.
            return PIL.Image.open(fname)
        xlink = img_elt.get('xlink:href')
        if not xlink.startswith('data:'):
            # Unqualified filename.  Try reading it directly although there's a
            # good chance this will fail.
            return PIL.Image.open(fname)

        # Read an image embedded in the SVG file itself.
        try:
            mime, dtype_data = xlink[5:].split(';', 1)
            dtype, data64 = dtype_data.split(',', 1)
        except ValueError:
            inkex.errormsg('failed to parse embedded image data')
            sys.exit(1)
        if dtype != 'base64':
            inkex.errormsg('embedded image is encoded as %s, but this plugin supports only base64' % dtype)
            sys.exit(1)
        raw_data = base64.decodebytes(data64.encode('utf-8'))
        return PIL.Image.open(io.BytesIO(raw_data))

    def _guess_background_color(self, img):
        'Return the most commonly occurring color, assuming it represents the background.'
        wd, ht = img.size
        tally, bg_color = max(img.getcolors(wd*ht))
        return bg_color

    def _pixels_to_objects(self, img, coords2obj, bg_color, scale, change_stroke, change_fill):
        '''Perform the core functionality of this extension, using pixel
        coordinates to place object replicas.'''
        # Create a new group for all the objects we'll create.
        group = inkex.Group()
        parent = self.svg.selection.first().getparent()
        parent.add(group)

        # Convert each pixel to a replica of the object, optionally
        # recoloring it.
        wd, ht = img.size
        for y in range(ht):
            for x in range(wd):
                xy = (x, y)
                pix = img.getpixel(xy)
                if pix == bg_color:
                    continue
                obj = coords2obj(x, y)
                new_obj = self._copy_object_to(obj, inkex.Vector2d(xy)*scale)
                if change_stroke:
                    new_obj.style['stroke'] = '#%02x%02x%02x' % (pix[0], pix[1], pix[2])
                    new_obj.style['stroke-opacity'] = '%.10g' % (pix[3]/255.0)
                if change_fill:
                    new_obj.style['fill'] = '#%02x%02x%02x' % (pix[0], pix[1], pix[2])
                    new_obj.style['fill-opacity'] = '%.10g' % (pix[3]/255.0)
                group.add(new_obj)

    def effect(self):
        '''Given a bitmap image and an object, copy the object to each
        coordinate of the image that contains a colored pixel.'''
        img_elt, objs = self._get_selection()
        img = self._read_image(img_elt).convert('RGBA')
        if self.options.ignore_bg:
            bg_color = self._guess_background_color(img)
        else:
            bg_color = None
        scale = self.options.scale
        change_stroke = self.options.color_stroke
        change_fill = self.options.color_fill
        coords2obj = self._generate_coords2obj(objs)
        self._pixels_to_objects(img, coords2obj, bg_color, scale, change_stroke, change_fill)
        img.close()

if __name__ == '__main__':
    PixelsToObjects().run()

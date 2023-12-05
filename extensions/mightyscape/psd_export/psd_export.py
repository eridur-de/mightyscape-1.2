#!/usr/bin/env python3
#
# Copyright (C) 2006 Aaron Spike, aaron@ekips.org
# Copyright (C) 2010-2012 Nicolas Dufour, nicoduf@yahoo.fr
# (Windows support and various fixes)
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
"""
Export to Gimp's XCF file format including Grids and Guides.
"""

import os
from collections import OrderedDict

import inkex
from inkex.base import TempDirMixin
from inkex.command import take_snapshot, call
from inkex.localization import inkex_gettext as _

class PSDExport(TempDirMixin, inkex.OutputExtension):
    """
    Provide a quick and dirty way of using gimp to output an xcf from Inkscape.

    Both Inkscape and Gimp must be installed for this extension to work.
    """
    dir_prefix = 'gimp-out-'

    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("-d", "--guides", type=inkex.Boolean, help="Save Guides")
        pars.add_argument("-r", "--grid", type=inkex.Boolean, help="Save Grid")
        pars.add_argument("-b", "--background", type=inkex.Boolean, help="Save background color")
        pars.add_argument("-i", "--dpi", type=float, default=96.0, help="File resolution")

    def get_guides(self):
        """Generate a list of horzontal and vertical only guides"""
        horz_guides = []
        vert_guides = []
        # Grab all guide tags in the namedview tag
        for guide in self.svg.namedview.get_guides():
            if guide.is_horizontal:
                # GIMP doesn't like guides that are outside of the image
                if 0 < guide.point.y < self.svg.height:
                    # The origin is at the top in GIMP land
                    horz_guides.append(str(guide.point.y))
            elif guide.is_vertical:
                # GIMP doesn't like guides that are outside of the image
                if 0 < guide.point.x < self.svg.width:
                    vert_guides.append(str(guide.point.x))

        return ('h', ' '.join(horz_guides)), ('v', ' '.join(vert_guides))

    def get_grid(self):
        """Get the grid if asked for and return as gimpfu script"""
        scale = (self.svg.scale) * (self.options.dpi / 96.0)
        # GIMP only allows one rectangular grid
        xpath = "sodipodi:namedview/inkscape:grid[@type='xygrid' and (not(@units) or @units='px')]"
        if self.svg.xpath(xpath):
            node = self.svg.getElement(xpath)
            for attr, default, target in (('spacing', 1, 'spacing'), ('origin', 0, 'offset')):
                fmt = {'target': target}
                for dim in 'xy':
                    # These attributes could be nonexistent
                    unit = float(node.get(attr + dim, default))
                    unit = self.svg.uutounit(unit, "px") * scale
                    fmt[dim] = int(round(float(unit)))
                yield '(gimp-image-grid-set-{target} img {x} {y})'.format(**fmt)

    @property
    def docname(self):
        """Get the document name suitable for export"""
        return self.svg.get('sodipodi:docname') or 'document'

    def save(self, stream):

        pngs = OrderedDict()
        valid = False

        for node in self.svg.xpath("/svg:svg/*[name()='g' or @style][@id]"):
            if not len(node): # pylint: disable=len-as-condition
                # Ignore empty layers
                continue

            valid = True
            node_id = node.get('id')
            name = node.get("inkscape:label", node_id)

            pngs[name] = take_snapshot(
                self.document,
                dirname=self.tempdir,
                name=name,
                dpi=int(self.options.dpi),
                export_id=node_id,
                export_id_only=True,
                export_area_page=True,
                export_background_opacity=int(bool(self.options.background))
            )

        if not valid:
            inkex.errormsg(_('This extension requires at least one non empty layer.'))
            return

        xcf = os.path.join(self.tempdir, "{}.psd".format(self.docname))
        script_fu = """
(tracing 1)
(define
  (png-to-layer img png_filename layer_name)
  (let*
    (
      (png (car (file-png-load RUN-NONINTERACTIVE png_filename png_filename)))
      (png_layer (car (gimp-image-get-active-layer png)))
      (xcf_layer (car (gimp-layer-new-from-drawable png_layer img)))
    )
    (gimp-image-add-layer img xcf_layer -1)
    (gimp-drawable-set-name xcf_layer layer_name)
  )
)
(let*
  (
    (img (car (gimp-image-new 200 200 RGB)))
  )
  (gimp-image-set-resolution img {dpi} {dpi})
  (gimp-image-undo-disable img)
  (for-each
    (lambda (names)
      (png-to-layer img (car names) (cdr names))
    )
    (map cons '("{files}") '("{names}"))
  )

  (gimp-image-resize-to-layers img)
""".format(
    dpi=self.options.dpi,
    files='" "'.join(pngs.values()),
    names='" "'.join(list(pngs))
)

        if self.options.guides:
            for dim, guides in self.get_guides():
                script_fu += """
  (for-each
    (lambda ({d}Guide)
      (gimp-image-add-{d}guide img {d}Guide)
    )
    '({g})
  )""".format(d=dim, g=guides)

        # Grid
        if self.options.grid:
            for fu_let in self.get_grid():
                script_fu += "\n" + fu_let + "\n"

        script_fu += """
  (gimp-image-undo-enable img)
  (file-psd-save RUN-NONINTERACTIVE img (car (gimp-image-get-active-layer img)) "{xcf}" "{xcf}" 0 0))
(gimp-quit 0)
            """.format(xcf=xcf)

        #please install with apt/dnf to install gimp. Do not use snap or flatpak installations
        call('gimp', "-b", "-", i=True, batch_interpreter="plug-in-script-fu-eval", stdin=script_fu)

        with open(xcf, 'rb') as fhl:
            stream.write(fhl.read())

if __name__ == '__main__':
    PSDExport().run()

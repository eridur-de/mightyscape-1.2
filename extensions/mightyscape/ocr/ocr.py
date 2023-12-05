#!/usr/bin/env python3

# Copyright (C) 2021 Amal Santhosh , amalsanp@gmail.com

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

import inkex
import pytesseract
from PIL import Image
import cairosvg
import os

class OcrOutputExtension(inkex.OutputExtension):

    def add_arguments(self, pars):
        pars.add_argument('--lang',default='eng',help='Language')

    def effect(self):
        try:
            img = 'read.png'
            cairosvg.svg2png(url = self.file_io.name, write_to = img)
            text = pytesseract.image_to_string(Image.open(img), lang = self.options.lang)
            self.msg(text.rstrip())
            os.remove('read.png')
        except Exception as e:
            self.msg(e)
            self.msg("Image reading failed!")
            return
        
    def save(self, stream):
        pass

if __name__ == '__main__':
    OcrOutputExtension().run()

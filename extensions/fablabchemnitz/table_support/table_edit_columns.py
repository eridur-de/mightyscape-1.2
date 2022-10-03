#!/usr/bin/env python3
"""
table.py
Table support for Inkscape

Copyright (C) 2011 Cosmin Popescu, cosminadrianpopescu@gmail.com

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

import sys
import os
import table

sys.path.append(os.path.dirname(sys.argv[0]))

class Table(table.TableEngine):
    
    def add_arguments(self, pars):
        pars.add_argument("--width", default='10mm', help='The new width')
    
    def doinkex(self):
        self.editSize(self.options.width, self.cell_type_column)

if __name__ == '__main__':   #pragma: no cover
    Table().run()

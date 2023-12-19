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
    def __init__(self):
        table.TableEngine.__init__(self)

    def doinkex(self):
        self.fitPageWidth()

if __name__ == '__main__':   #pragma: no cover
    Table().run()

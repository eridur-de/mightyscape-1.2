#!/usr/bin/env python3

'''
render_sudoku.py
A sudoku generator plugin for Inkscape, but also can be used as a standalone
command line application.

Copyright (C) 2011 Chris Savery <chrissavery(a)gmail.com>

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
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

__version__ = "0.1"

import inkex
import os
import subprocess
from lxml import etree
from inkex import Color

class Sudoku(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--difficulty",default="mixed", help='How difficult to make puzzles.')
        pars.add_argument("--rows", type=int, default=1, help='Number of puzzle rows.')
        pars.add_argument("--cols", type=int, default=1, help='Number of puzzle columns.') 
        pars.add_argument("--puzzle_size", type=int, default=6, help='The width & height of each puzzle.')
        pars.add_argument("--puzzle_gap", type=int, default=1, help='The space between puzzles.')
        pars.add_argument("--color_text", type=Color, default=255, help='Color for given numbers.') 
        pars.add_argument("--color_bkgnd", type=Color, default=4243148799, help='Color for the puzzle background.')
        pars.add_argument("--color_puzzle",type=Color, default=2290779647, help='Border color for the puzzles.')
        pars.add_argument("--color_boxes", type=Color, default=3298820351, help='Border color for puzzle boxes.')
        pars.add_argument("--color_cells", type=Color, default=1923076095, help='Border color for the puzzle cells.')
        pars.add_argument("--units", help="The unit of the dimensions")

    def draw_grid(self, g_puz, x, y):
        bkgnd_style = {'stroke':'none', 'stroke-width':'2', 'fill':self.options.color_bkgnd }      
        puzzle_style = {'stroke':self.options.color_puzzle, 'stroke-width':'2', 'fill':'none' }
        boxes_style = {'stroke':self.options.color_boxes, 'stroke-width':'2', 'fill':'none' }
        cells_style = {'stroke':self.options.color_cells, 'stroke-width':'1', 'fill':'none' }
        g = etree.SubElement(g_puz, 'g')
        self.draw_rect(g, bkgnd_style, self.left+x, self.top+y, self.size, self.size)
        self.draw_rect(g, cells_style, self.left+x+self.size/9, self.top+y, self.size/9, self.size)
        self.draw_rect(g, cells_style, self.left+x+self.size/3+self.size/9, self.top+y, self.size/9, self.size)
        self.draw_rect(g, cells_style, self.left+x+2*self.size/3+self.size/9, self.top+y, self.size/9, self.size)
        self.draw_rect(g, cells_style, self.left+x, self.top+y+self.size/9, self.size, self.size/9)
        self.draw_rect(g, cells_style, self.left+x, self.top+y+self.size/3+self.size/9, self.size, self.size/9)
        self.draw_rect(g, cells_style, self.left+x, self.top+y+2*self.size/3+self.size/9, self.size, self.size/9)      
        self.draw_rect(g, boxes_style, self.left+x+self.size/3, self.top+y, self.size/3, self.size)
        self.draw_rect(g, boxes_style, self.left+x, self.top+y+self.size/3, self.size, self.size/3)
        self.draw_rect(g, puzzle_style, self.left+x, self.top+y, self.size, self.size)
        
    def draw_rect(self, g, style, x, y, w, h):
        attribs = {'style':str(inkex.Style(style)), 'x':str(x), 'y':str(y), 'height':str(h), 'width':str(w) }
        etree.SubElement(g, inkex.addNS('rect','svg'), attribs)    
        
    def fill_puzzle(self, g_puz, x, y, data):
        cellsize = self.size / 9
        txtsize = self.size / 12
        offset = (cellsize + txtsize)/2.25
        g = etree.SubElement(g_puz, 'g')
        text_style = {'font-size':str(txtsize),
                      'fill':self.options.color_text,
                      'font-family':'arial',
                      'text-anchor':'middle', 'text-align':'center' }
        #inkex.utils.debug(len(data))
        for n in range(len(data)):
            #inkex.utils.debug(str(n))
            #inkex.utils.debug("data["+str(n)+"]="+str(data[n]))
            if str(data[n]) in "123456789":
                attribs = {'style': str(inkex.Style(text_style)), 
                    'x': str(self.left + x + n%9 * cellsize + cellsize/2  ), 'y': str(self.top + y + n//9 * cellsize + offset ) }
                etree.SubElement(g, 'text', attribs).text = str(data[n])


    def effect(self):
        extension_dir = os.path.dirname(os.path.realpath(__file__))
        if os.name == "nt":
            qqwing = os.path.join(extension_dir, "qqwing.exe")
        else:
            qqwing = os.path.join(extension_dir, "qqwing")
        args = [qqwing, "--one-line", "--generate", str(self.options.rows * self.options.cols)]
        if self.options.difficulty != 'mixed':
            args.extend(["--difficulty", self.options.difficulty])
        with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as qqwing_process:
            data = qqwing_process.communicate()
            #inkex.utils.debug(data)
            data_processed = data[0].decode('UTF-8').splitlines()
    
            parent = self.document.getroot()
            self.doc_w = self.svg.unittouu(parent.get('width'))
            self.doc_h = self.svg.unittouu(parent.get('height'))
            self.size = self.svg.unittouu(str(self.options.puzzle_size) + self.options.units)
            self.gap = self.svg.unittouu(str(self.options.puzzle_gap) + self.options.units)
            self.shift = self.size + self.gap
            self.left = (self.doc_w - (self.options.cols * self.shift - self.gap))/2
            self.top = (self.doc_h - (self.options.rows * self.shift - self.gap))/2
            self.sudoku_g = etree.SubElement(parent, 'g', {'id':'sudoku'})
            for row in range(0, self.options.rows):
                for col in range(0, self.options.cols):
                    g = etree.SubElement(self.sudoku_g, 'g', {'id':'puzzle_'+str(col)+str(row)})
                    self.draw_grid(g, col*self.shift, row*self.shift)
                    self.fill_puzzle(g, col*self.shift, row*self.shift, data_processed[col+row*self.options.cols])

if __name__ == '__main__':
    Sudoku().run()
#!/usr/bin/env python3

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Author: Giacomo Mirabassi <giacomo@mirabassi.it>
# Version: 0.2

import os
import re
import subprocess
import math
import inkex
import shutil

inkex.localization.localize

class JPEGExport(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--path", default="")
        pars.add_argument("--bgcol", default="#ffffff")
        pars.add_argument("--quality",type=int, default="90")
        pars.add_argument("--density", type=int, default="90")
        pars.add_argument("--page", type=inkex.Boolean, default=False)
        pars.add_argument("--fast", type=inkex.Boolean, default=True)

    def effect(self):
        """get selected item coords and call command line command to export as a png"""
        # The user must supply a directory to export:
        if not self.options.path:
            inkex.errormsg(_('Please indicate a file name and path to export the jpg.'))
            exit()
        if not os.path.basename(self.options.path):
            inkex.errormsg(_('Please indicate a file name.'))
            exit()
        if not os.path.dirname(self.options.path):
            inkex.errormsg(_('Please indicate a directory other than your system\'s base directory.'))
            exit()
          
        # Test if the directory exists and filename is valid:
        filebase = os.path.dirname(self.options.path)
        if not os.path.exists(filebase):
            inkex.errormsg(_('The directory "%s" does not exist.') % filebase)
            exit()
        filename = os.path.splitext(os.path.basename(self.options.path))
        filename_base = filename[0]
        filename_ending = filename[1]
        if self.get_valid_filename(filename_base) != filename_base:
            inkex.errormsg(_('The file name "%s" is invalid.') % filename_base)
            return 
        if filename_ending != 'jpg' or filename_ending != 'jpeg':
            filename_ending = 'jpg'
        outfile = os.path.join(filebase, filename_base + '.' + filename_ending)
   
        shutil.copy(self.options.input_file, self.options.input_file + ".svg") #make a file copy with file ending to suppress import warnings
        curfile = self.options.input_file + ".svg"
        #inkex.utils.debug("curfile:" + curfile)
        
        # Test if color is valid
        _rgbhexstring = re.compile(r'#[a-fA-F0-9]{6}$')
        if not _rgbhexstring.match(self.options.bgcol):
            inkex.errormsg(_('Please indicate the background color like this: \"#abc123\" or leave the field empty for white.'))
            exit()

        bgcol = self.options.bgcol

        if self.options.page == False:
            if len(self.svg.selected) == 0:
                inkex.errormsg(_('Please select something.'))
                exit()

            coords=self.processSelected()
            self.exportArea(int(coords[0]),int(coords[1]),int(coords[2]),int(coords[3]),curfile,outfile,bgcol)

        elif self.options.page == True:
            self.exportPage(curfile,outfile,bgcol)

    def processSelected(self):
        """Iterate trough nodes and find the bounding coordinates of the selected area"""
        startx=None
        starty=None
        endx=None
        endy=None
        nodelist=[]
        root=self.document.getroot();
        toty=self.svg.unittouu(root.attrib['height'])
        scale = self.svg.unittouu('1px')
        props=['x', 'y', 'width', 'height']

        for id in self.svg.selected:
            if self.options.fast == True:
                nodelist.append(self.svg.getElementById(id)) 
            else:  # uses command line
                rawprops=[]
                for prop in props:
                    command=("inkscape", "--query-id", id, "--query-"+prop, self.options.input_file)
                    proc=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    proc.wait()
                    rawprops.append(math.ceil(self.svg.unittouu(proc.stdout.read())))
                    proc.stdout.close()
                    proc.stderr.close()
                nodeEndX = rawprops[0] + rawprops[2]
                nodeStartY = toty - rawprops[1] - rawprops[3]
                nodeEndY = toty - rawprops[1]

                if rawprops[0] < startx or startx is None:
                    startx = rawprops[0]

                if nodeStartY < starty or starty is None:
                    starty = nodeStartY

                if nodeEndX > endx or endx is None:
                    endx = nodeEndX

                if nodeEndY > endy or endy is None:
                    endy = nodeEndY
        

        if self.options.fast == True:
            bbox = sum([node.bounding_box() for node in nodelist], None)
            #inkex.utils.debug(bbox) - see transform.py
            '''
             width = property(lambda self: self.x.size)
             height = property(lambda self: self.y.size)
             top = property(lambda self: self.y.minimum)
             left = property(lambda self: self.x.minimum)
             bottom = property(lambda self: self.y.maximum)
             right = property(lambda self: self.x.maximum)
             center_x = property(lambda self: self.x.center)
             center_y = property(lambda self: self.y.center)
            '''
            startx = math.ceil(bbox.left)
            endx = math.ceil(bbox.right)
            h = -bbox.top + bbox.bottom
            starty = toty - math.ceil(bbox.top) -h
            endy = toty - math.ceil(bbox.top)

        coords = [startx / scale, starty / scale, endx / scale, endy / scale]
        return coords

    def exportArea(self, x0, y0, x1, y1, curfile, outfile, bgcol):
        tmp = self.getTmpPath()
        command="inkscape --export-area %s:%s:%s:%s -d %s --export-filename \"%sjpinkexp.png\" -b \"%s\" \"%s\"" % (x0, y0, x1, y1, self.options.density, tmp, bgcol, curfile)
        p = subprocess.Popen(command, shell=True)
        return_code = p.wait()
        self.tojpeg(outfile)
        #inkex.utils.debug("command:" + command)
        #inkex.utils.debug("Errorcode:" + str(return_code))

    def exportPage(self, curfile, outfile, bgcol):
        tmp = self.getTmpPath()
        command = "inkscape --export-area-drawing -d %s --export-filename \"%sjpinkexp.png\" -b \"%s\" \"%s\"" % (self.options.density, tmp, bgcol, curfile)
        p = subprocess.Popen(command, shell=True)
        return_code = p.wait()
        self.tojpeg(outfile)
        #inkex.utils.debug("command:" + command)
        #inkex.utils.debug("Errorcode:" + str(return_code))
		
    def tojpeg(self, outfile):
        tmp = self.getTmpPath()
        if os.name == 'nt':
	        outfile = outfile.replace("\\","\\\\")
        # set the ImageMagick command to run based on what's installed
        if shutil.which('magick'):
            command = "magick \"%sjpinkexp.png\" -sampling-factor 4:4:4 -strip -interlace JPEG -colorspace RGB -quality %s -density %s \"%s\" " % (tmp, self.options.quality, self.options.density, outfile)
            # inkex.utils.debug(command)
        elif shutil.which('convert'):
            command = "convert \"%sjpinkexp.png\" -sampling-factor 4:4:4 -strip -interlace JPEG -colorspace RGB -quality %s -density %s \"%s\" " % (tmp, self.options.quality, self.options.density, outfile)
            # inkex.utils.debug(command)
        else:
            inkex.errormsg(_('ImageMagick does not appear to be installed.'))
            exit()   
        p = subprocess.Popen(command, shell=True)
        return_code = p.wait()
        #inkex.utils.debug("command:" + command)
        #inkex.utils.debug("Errorcode:" + str(return_code))

    def getTmpPath(self):
        """Define the temporary folder path depending on the operating system"""
        if os.name == 'nt':
            return os.getenv('TEMP') + '\\'
        else:
            return '/tmp/'

    def get_valid_filename(self, s):
        s = str(s).strip().replace(" ", "_")
        return re.sub(r"(?u)[^-\w.]", "", s)

if __name__ == '__main__':
    JPEGExport().run()
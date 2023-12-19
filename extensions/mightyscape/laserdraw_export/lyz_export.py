#!/usr/bin/env python3
'''
This file output script for Inkscape creates Laser Draw (LaserDRW) LYZ files.

File history:
0.1 Initial code (2/5/2017)
0.2 - Added support for rectangle, circle and ellipse (2/7/2017)
    - Added option to automatically convert text to paths
0.3 - Fixed x,y translation when view box is used in SVG file for scaling (2/10/2017)
0.4 - Changed limits in resolution to 100 dpi minimum and 1000 dpi maximum (if you get an out of memory error in LaserDRW try reducing the resolution)
0.5 - Removed some messages that were not needed
    - Fixed default resolution in inx files
0.6 - Made compatible with Python 3 and Inkscape 1.0

Copyright (C) 2017-2020 Scorch www.scorchworks.com
Derived from dxf_outlines.py by Aaron Spike and Alvin Penner

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

import math
import tempfile, os, sys, shutil
from subprocess import Popen, PIPE
import zipfile
import re

import lyz_inkex           as inkex
import lyz_simplestyle     as simplestyle
import lyz_simpletransform as simpletransform
import lyz_cubicsuperpath  as cubicsuperpath
import lyz_cspsubdiv       as cspsubdiv
from lyz_library       import LYZ_CLASS

## Subprocess timout stuff ######
from threading import Timer
def run_external(cmd, timeout_sec):
  proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
  kill_proc = lambda p: p.kill()
  timer = Timer(timeout_sec, kill_proc, [proc])
  try:
    timer.start()
    stdout,stderr = proc.communicate()
  finally:
    timer.cancel()
##################################
    
class LYZExport(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.flatness = 0.01
        self.lines =[]
        self.Cut_Type = {}
        self.Xsize=40
        self.Ysize=40
        self.margin = 2
        self.PNG_DATA = None
        self.png_area = "--export-area-page"
        self.timout = 60 #timeout time for external calls to Inkscape in seconds 

        self.OptionParser.add_option("--area_select", type="string", default="page_area")
        self.OptionParser.add_option("--cut_select", type="string", default="zip")
        self.OptionParser.add_option("--resolution", type="int", default=1000)
        self.OptionParser.add_option("--margin", type="float", default=2.00)
        self.OptionParser.add_option("--inkscape_version", type="int", default=100)
        self.OptionParser.add_option("--txt2paths", type="inkbool", default=False)
             
        self.layers = ['0']
        self.layer = '0'
        self.layernames = []
        self.PYTHON_VERSION = sys.version_info[0]
      
      
    def stream_binary_data(self,filename):
        # Change the format for STDOUT to binary to support
        # writing the binary output file through STDOUT
        if os.name == 'nt': #if sys.platform == "win32":
            try:
                import msvcrt
                #msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)  
                msvcrt.setmode(1, os.O_BINARY)
            except:
                pass
        # Open the temporary file for reading
        out = open(filename,'rb')
        # Send the contents of the temp file to STDOUT
        if self.PYTHON_VERSION < 3:
            sys.stdout.write(out.read())
        else:
            sys.stdout.buffer.write(out.read())
        out.close()
        
    
    def output(self):
        #create OS temp folder
        self.tmp_dir = tempfile.mkdtemp()
        
        if (self.cut_select=="image"  ):
            LYZ=LYZ_CLASS()
            LYZ.setup_new_header()
            LYZ.add_png(self.PNG_DATA,self.Xsize,self.Ysize)
            LYZ.set_size(self.Xsize+self.margin,self.Ysize+self.margin)
            LYZ.set_margin(self.margin)
            image_file = os.path.join(self.tmp_dir, "image.lyz")
            LYZ.write_file(image_file)
        
        if (self.cut_select=="all"    ) or (self.cut_select=="zip" ):
            LYZ=LYZ_CLASS()
            LYZ.setup_new_header()
            LYZ.add_png(self.PNG_DATA,self.Xsize,self.Ysize)
            for line in self.lines:
                ID=line[7]
                if (self.Cut_Type[ID]=="cut") or (self.Cut_Type[ID]=="engrave"):
                    LYZ.add_line(line[0],line[1],line[2],line[3],0.025)
            LYZ.set_size(self.Xsize+self.margin,self.Ysize+self.margin)
            LYZ.set_margin(self.margin)
            all_file = os.path.join(self.tmp_dir, "all.lyz")
            LYZ.write_file(all_file)
        
        if (self.cut_select=="raster" ) or (self.cut_select=="zip" ):
            LYZ=LYZ_CLASS()
            LYZ.setup_new_header()
            LYZ.add_png(self.PNG_DATA,self.Xsize,self.Ysize)
            LYZ.set_size(self.Xsize+self.margin,self.Ysize+self.margin)
            LYZ.set_margin(self.margin)
            raster_file = os.path.join(self.tmp_dir, "01_raster_engrave.lyz")
            LYZ.write_file(raster_file)
        
        if (self.cut_select=="vector_red" ) or (self.cut_select=="zip" ):
            LYZ=LYZ_CLASS()
            LYZ.setup_new_header()
            for line in self.lines:
                ID=line[7]
                if (self.Cut_Type[ID]=="cut"):
                    LYZ.add_line(line[0],line[1],line[2],line[3],0.025)
            LYZ.set_size(self.Xsize+self.margin,self.Ysize+self.margin)
            LYZ.set_margin(self.margin)
            cut_file = os.path.join(self.tmp_dir, "03_vector_cut.lyz")
            LYZ.write_file(cut_file)
        
        if (self.cut_select=="vector_blue" ) or (self.cut_select=="zip" ):
            LYZ=LYZ_CLASS()
            LYZ.setup_new_header()
            for line in self.lines:
                ID=line[7]
                if (self.Cut_Type[ID]=="engrave"):
                    LYZ.add_line(line[0],line[1],line[2],line[3],0.025)
            LYZ.set_size(self.Xsize+self.margin,self.Ysize+self.margin)
            LYZ.set_margin(self.margin)
            engrave_file = os.path.join(self.tmp_dir, "02_vector_engrave.lyz")
            LYZ.write_file(engrave_file)
        
        if (self.cut_select=="image"  ):
            self.stream_binary_data(image_file)
        
        if (self.cut_select=="all"    ):
            self.stream_binary_data(all_file)
        
        if (self.cut_select=="raster" ):
            self.stream_binary_data(raster_file)
        
        if (self.cut_select=="vector_red" ):
            self.stream_binary_data(cut_file)
        
        if (self.cut_select=="vector_blue"):
            self.stream_binary_data(engrave_file)
            
        if (self.cut_select=="zip" ):
            # Add image LYZ file? Encode zip file names?
            zip_file = os.path.join(self.tmp_dir, "lyz_files.zip")
            z = zipfile.ZipFile(zip_file, 'w')
            z.write(all_file    , os.path.basename(all_file)    )
            z.write(raster_file , os.path.basename(raster_file) )
            z.write(cut_file    , os.path.basename(cut_file)    )
            z.write(engrave_file, os.path.basename(engrave_file))
            z.write(sys.argv[-1], "design.svg"                  )
            z.close()
            self.stream_binary_data(zip_file)

        #Delete the temp folder and file
        shutil.rmtree(self.tmp_dir)
        
    def dxf_line(self,csp,pen_width=0.025,color=None,path_id="",layer="none"):
        x1 =  csp[0][0]
        y1 =  csp[0][1]
        x2 =  csp[1][0]
        y2 =  csp[1][1]
        self.lines.append([x1,-y1,x2,-y2,layer,pen_width,color,path_id])

    def colmod(self,r,g,b,path_id):
        if (r,g,b) ==(255,0,0):
            self.Cut_Type[path_id]="cut"
            (r,g,b) = (255,255,255)
        elif (r,g,b)==(0,0,255):
            self.Cut_Type[path_id]="engrave"
            (r,g,b) = (255,255,255)
        else:
            self.Cut_Type[path_id]="raster"
            (r,g,b) = (0,0,0)
    
        return '%02x%02x%02x' % (r,g,b)
        
    def process_shape(self, node, mat):
        rgb = (0,0,0)
        path_id = node.get('id') 
        style   = node.get('style')
        self.Cut_Type[path_id]="raster" # Set default type to raster
        
        color_props_fill = ('fill', 'stop-color', 'flood-color', 'lighting-color')
        color_props_stroke = ('stroke',)
        color_props = color_props_fill + color_props_stroke
        
        #####################################################
        ## The following is ripped off from Coloreffect.py ##
        #####################################################
        if style:
            declarations = style.split(';')
            for i,decl in enumerate(declarations):
                parts = decl.split(':', 2)
                if len(parts) == 2:
                    (prop, col) = parts
                    prop = prop.strip().lower()
                    #if prop in color_props:
                    if prop == 'stroke':
                        col= col.strip()
                        if simplestyle.isColor(col):
                            c=simplestyle.parseColor(col)
                            new_val='#'+self.colmod(c[0],c[1],c[2],path_id)
                        else:
                            new_val = col
                        if new_val != col:
                            declarations[i] = prop + ':' + new_val
            node.set('style', ';'.join(declarations))

        #####################################################
        if node.tag == inkex.addNS('path','svg'):
            d = node.get('d')
            if not d:
                return
            p = cubicsuperpath.parsePath(d)
        elif node.tag == inkex.addNS('rect','svg'):
            x = float(node.get('x'))
            y = float(node.get('y'))
            width = float(node.get('width'))
            height = float(node.get('height'))
            #d = "M %f,%f %f,%f %f,%f %f,%f Z" %(x,y, x+width,y,  x+width,y+height, x,y+height) 
            #p = cubicsuperpath.parsePath(d)
            rx = 0.0
            ry = 0.0
            if node.get('rx'):
                rx=float(node.get('rx'))
            if node.get('ry'):
                ry=float(node.get('ry'))
                
            if max(rx,ry) > 0.0:
                if rx==0.0 or ry==0.0:
                    rx = max(rx,ry)
                    ry = rx
                #msg = "rx = %f ry = %f " %(rx,ry)
                #inkex.errormsg(msg)
                L1 = "M %f,%f %f,%f "      %(x+rx       , y          , x+width-rx , y          )
                C1 = "A %f,%f 0 0 1 %f,%f" %(rx         , ry         , x+width    , y+ry       )
                L2 = "M %f,%f %f,%f "      %(x+width    , y+ry       , x+width    , y+height-ry)
                C2 = "A %f,%f 0 0 1 %f,%f" %(rx         , ry         , x+width-rx , y+height   )
                L3 = "M %f,%f %f,%f "      %(x+width-rx , y+height   , x+rx       , y+height   )
                C3 = "A %f,%f 0 0 1 %f,%f" %(rx         , ry         , x          , y+height-ry)
                L4 = "M %f,%f %f,%f "      %(x          , y+height-ry, x          , y+ry       )
                C4 = "A %f,%f 0 0 1 %f,%f" %(rx         , ry         , x+rx       , y          )
                d =  L1 + C1 + L2 + C2 + L3 + C3 + L4 + C4    
            else:
                d = "M %f,%f %f,%f %f,%f %f,%f Z" %(x,y, x+width,y,  x+width,y+height, x,y+height) 
            p = cubicsuperpath.parsePath(d)
            
        elif node.tag == inkex.addNS('circle','svg'):
            cx = float(node.get('cx') )
            cy = float(node.get('cy'))
            r  = float(node.get('r'))
            d  = "M %f,%f A   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f Z" %(cx+r,cy, r,r,cx,cy+r,  r,r,cx-r,cy,  r,r,cx,cy-r, r,r,cx+r,cy)
            p = cubicsuperpath.parsePath(d)
        
        elif node.tag == inkex.addNS('ellipse','svg'):
            cx = float(node.get('cx')) 
            cy = float(node.get('cy'))
            rx = float(node.get('rx'))
            ry = float(node.get('ry'))
            d  = "M %f,%f A   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f Z" %(cx+rx,cy, rx,ry,cx,cy+ry,  rx,ry,cx-rx,cy,  rx,ry,cx,cy-ry, rx,ry,cx+rx,cy)
            p = cubicsuperpath.parsePath(d) 
        else:
            return
        trans = node.get('transform')
        if trans:
            mat = simpletransform.composeTransform(mat, simpletransform.parseTransform(trans))
        simpletransform.applyTransformToPath(mat, p)
        
        ###################################################
        ## Break Curves down into small lines
        ###################################################
        f = self.flatness
        is_flat = 0
        while is_flat < 1:
            try:
                cspsubdiv.cspsubdiv(p, f)
                is_flat = 1
            except IndexError:
                break
            except:
                f += 0.1
                if f>2 :
                  break
                  #something has gone very wrong.
        ###################################################
        for sub in p:
            for i in range(len(sub)-1):
                s = sub[i]
                e = sub[i+1]
                self.dxf_line([s[1],e[1]],0.025,rgb,path_id)
                
                    
    def process_clone(self, node):
        trans = node.get('transform')
        x = node.get('x')
        y = node.get('y')
        mat = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
        if trans:
            mat = simpletransform.composeTransform(mat, simpletransform.parseTransform(trans))
        if x:
            mat = simpletransform.composeTransform(mat, [[1.0, 0.0, float(x)], [0.0, 1.0, 0.0]])
        if y:
            mat = simpletransform.composeTransform(mat, [[1.0, 0.0, 0.0], [0.0, 1.0, float(y)]])
        # push transform
        if trans or x or y:
            self.groupmat.append(simpletransform.composeTransform(self.groupmat[-1], mat))
        # get referenced node
        refid = node.get(inkex.addNS('href','xlink'))
        refnode = self.getElementById(refid[1:])
        if refnode is not None:
            if refnode.tag == inkex.addNS('g','svg'):
                self.process_group(refnode)
            elif refnode.tag == inkex.addNS('use', 'svg'):
                self.process_clone(refnode)
            else:
                self.process_shape(refnode, self.groupmat[-1])
        # pop transform
        if trans or x or y:
            self.groupmat.pop()

    def process_group(self, group):
        if group.get(inkex.addNS('groupmode', 'inkscape')) == 'layer':
            style = group.get('style')
            if style:
                style = simplestyle.parseStyle(style)
                if style.has_key('display'):
                    if style['display'] == 'none' and self.options.layer_option and self.options.layer_option=='visible':
                        return
            layer = group.get(inkex.addNS('label', 'inkscape'))
              
            layer = layer.replace(' ', '_')
            if layer in self.layers:
                self.layer = layer
        trans = group.get('transform')
        if trans:
            self.groupmat.append(simpletransform.composeTransform(self.groupmat[-1], simpletransform.parseTransform(trans)))
        for node in group:
            if node.tag == inkex.addNS('g','svg'):
                self.process_group(node)
            elif node.tag == inkex.addNS('use', 'svg'):
                self.process_clone(node)
            else:
                self.process_shape(node, self.groupmat[-1])
        if trans:
            self.groupmat.pop()
            
            
    def Make_PNG(self):
        #create OS temp folder
        tmp_dir = tempfile.mkdtemp()
        svg_temp_file = os.path.join(tmp_dir, "LYZimage.svg")
        png_temp_file = os.path.join(tmp_dir, "LYZpngdata.png")

        dpi = "%d" %(self.options.resolution)
        if self.inkscape_version >= 100:
            cmd = [ "inkscape", self.png_area, "--export-dpi", dpi, \
                    "--export-background","rgb(255, 255, 255)","--export-background-opacity", \
                    "255" ,"--export-type=png", "--export-filename=%s" %(png_temp_file), svg_temp_file ]
        else:
            cmd = [ "inkscape", self.png_area, "--export-dpi", dpi, \
                    "--export-background","rgb(255, 255, 255)","--export-background-opacity", \
                    "255" ,"--export-png", png_temp_file, svg_temp_file ]
        
        if (self.cut_select=="raster") or (self.cut_select=="all") or (self.cut_select=="zip"):            
            self.document.write(svg_temp_file)            
            #cmd = [ "inkscape", self.png_area, "--export-dpi", dpi, "--export-background","rgb(255, 255, 255)","--export-background-opacity", "255" ,"--export-png", png_temp_file, svg_temp_file ]
            #p = Popen(cmd, stdout=PIPE, stderr=PIPE)
            #stdout, stderr = p.communicate()
            run_external(cmd, self.timout)
        else:    
            shutil.copyfile(sys.argv[-1], svg_temp_file)
            #cmd = [ "inkscape", self.png_area, "--export-dpi", dpi, "--export-background","rgb(255, 255, 255)","--export-background-opacity", "255" ,"--export-png", png_temp_file, svg_temp_file ]
            #p = Popen(cmd, stdout=PIPE, stderr=PIPE)
            #stdout, stderr = p.communicate()
            run_external(cmd, self.timout)
        try:
            with open(png_temp_file, 'rb') as f:
                self.PNG_DATA = f.read()
        except:
            inkex.errormsg("PNG generation timed out.\nTry saving again.\n\n")
            
        #Delete the temp folder and any files
        shutil.rmtree(tmp_dir)   
    
    def unit2mm(self, string):
        # Returns mm given a string representation of units in another system
        # a dictionary of unit to user unit conversion factors
        uuconv = {'in': 25.4,
                  'pt': 25.4/72.0,
                  'px': 25.4/self.inkscape_dpi,
                  'mm': 1.0,
                  'cm': 10.0,
                  'm' : 1000.0,
                  'km': 1000.0*1000.0,
                  'pc': 25.4/6.0,
                  'yd': 25.4*12*3,
                  'ft': 25.4*12}
  
        unit = re.compile('(%s)$' % '|'.join(uuconv.keys()))
        param = re.compile(r'(([-+]?[0-9]+(\.[0-9]*)?|[-+]?\.[0-9]+)([eE][-+]?[0-9]+)?)')
 
        p = param.match(string)
        u = unit.search(string)
        if p:
            retval = float(p.string[p.start():p.end()])
        else:
            inkex.errormsg("Size was not determined returning zero value")
            retval = 0.0
        if u:
            retunit = u.string[u.start():u.end()]
        else:
            inkex.errormsg("units not understood assuming px  at %d dpi" %(self.inkscape_dpi))
            retunit = 'px'
            
        try:
            return retval * uuconv[retunit]
        except KeyError:
            return retval
    
    def effect(self):        
        msg = ""
        #area_select = self.options.area_select # "page_area", "object_area"
        area_select       = "page_area"
        self.cut_select   = self.options.cut_select   # "vector_red", "vector_blue", "raster", "all", "image", "Zip"
        self.margin       = self.options.margin       # float value
        #self.inkscape_dpi = self.options.inkscape_dpi # float value
        self.inkscape_version = self.options.inkscape_version # float value
        self.txt2paths    = self.options.txt2paths    # boolean Value
        
        
        if self.inkscape_version > 91:
            self.inkscape_dpi = 96
        else:
            self.inkscape_dpi = 90
        
        if (self.txt2paths):
            #create OS temp folder
            tmp_dir = tempfile.mkdtemp()
            txt2path_file = os.path.join(tmp_dir, "txt2path.svg")
            if self.inkscape_version >= 100:
                cmd = [ "inkscape", "--export-text-to-path","--export-plain-svg", "--export-filename=%s" %(txt2path_file), sys.argv[-1] ]
            else:
                cmd = [ "inkscape", "--export-text-to-path","--export-plain-svg",txt2path_file, sys.argv[-1] ]
                
            run_external(cmd, self.timout)
            self.document.parse(txt2path_file)
            #Delete the temp folder and any files
            shutil.rmtree(tmp_dir)
               
        h_uu = self.unittouu(self.document.getroot().xpath('@height', namespaces=inkex.NSS)[0])
        w_uu = self.unittouu(self.document.getroot().xpath('@width' , namespaces=inkex.NSS)[0])
        
        h_mm = self.unit2mm(self.document.getroot().xpath('@height', namespaces=inkex.NSS)[0])
        w_mm = self.unit2mm(self.document.getroot().xpath('@width', namespaces=inkex.NSS)[0])
        
        try:
            view_box_str = self.document.getroot().xpath('@viewBox', namespaces=inkex.NSS)[0]
            view_box_list = view_box_str.split(' ')
            Wpix = float(view_box_list[2])
            Hpix = float(view_box_list[3])
            scale = h_mm/Hpix
            Dx = float(view_box_list[0]) / ( float(view_box_list[2])/w_mm )
            Dy = float(view_box_list[1]) / ( float(view_box_list[3])/h_mm )
        except:
            #inkex.errormsg("Using Default Inkscape Scale")
            scale = 25.4/self.inkscape_dpi
            Dx = 0
            Dy = 0
        
        for node in self.document.getroot().xpath('//svg:g', namespaces=inkex.NSS):
            if node.get(inkex.addNS('groupmode', 'inkscape')) == 'layer':
                layer = node.get(inkex.addNS('label', 'inkscape'))
                self.layernames.append(layer.lower())
                # if self.options.layer_name and self.options.layer_option and self.options.layer_option=='name' and not layer.lower() in self.options.layer_name:
                    # continue
                layer = layer.replace(' ', '_')
                if layer and not layer in self.layers:
                    self.layers.append(layer)

        #self.groupmat = [[[scale, 0.0, 0.0], [0.0, -scale, h_mm]]]
        self.groupmat = [[[scale,    0.0,  0.0-Dx],
                          [0.0  , -scale, h_mm+Dy]]]
        #doc = self.document.getroot()
        self.process_group(self.document.getroot())
        #################################################
        
        # msg = msg + self.getDocumentUnit() + "\n"
        # msg = msg + "scale  = %f\n" %(scale)
        msg = msg + "Height(mm)= %f\n" %(h_mm)
        msg = msg + "Width (mm)= %f\n" %(w_mm)
        # msg = msg + "h_uu   = %f\n" %(h_uu)
        # msg = msg + "w_uu   = %f\n" %(w_uu)

        #inkex.errormsg(msg)
        
        if (area_select=="object_area"):
            self.png_area = "--export-area-drawing" 
            xmin= self.lines[0][0]+0.0
            xmax= self.lines[0][0]+0.0
            ymin= self.lines[0][1]+0.0
            ymax= self.lines[0][1]+0.0
            for line in self.lines:
                x1= line[0]
                y1= line[1]
                x2= line[2]
                y2= line[3]
                xmin = min(min(xmin,x1),x2)
                ymin = min(min(ymin,y1),y2)
                xmax = max(max(xmax,x1),x2)
                ymax = max(max(ymax,y1),y2)
        else:
            self.png_area = "--export-area-page"
            xmin= 0.0
            xmax=  w_mm 
            ymin= -h_mm 
            ymax= 0.0
            
        self.Xsize=xmax-xmin
        self.Ysize=ymax-ymin
        Xcenter=(xmax+xmin)/2.0
        Ycenter=(ymax+ymin)/2.0
        for ii in range(len(self.lines)):
            self.lines[ii][0] = self.lines[ii][0]-Xcenter
            self.lines[ii][1] = self.lines[ii][1]-Ycenter
            self.lines[ii][2] = self.lines[ii][2]-Xcenter
            self.lines[ii][3] = self.lines[ii][3]-Ycenter
        
        if (self.cut_select=="raster") or \
           (self.cut_select=="all"   ) or \
           (self.cut_select=="image" ) or \
           (self.cut_select=="zip"   ):
            self.Make_PNG()
        
LYZExport().affect()
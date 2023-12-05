#!/usr/bin/env python3
'''
(C) 2018 Juergen Weigert <juergen@fabmail.org>, distribute under GPLv2 or ask

This is an input extension for inkscape to read STL files.

Requires: (python-lxml | python3-lxml), slic3r
For optional(!) rotation support:
  Requires: (python-numpy-stl | python3-numpy-stl)
  If you get ImportError: cannot import name 'mesh'
  although an stl module is installed, then you have the wrong stl module.
  Try 'pip3 uninstall stl; pip3 install numpy-stl'

2018-12-22 jw, v0.1 Initial draught
                       v0.1 First working standalone tool.
2018-12-26 jw, v0.3 Mesh rotation support via numpy-stl. Fully optional.
                       v0.4 Works fine as an inkscape input extension under Linux.
2019-03-01 jw, v0.5 numbers and center option added.
2019-07-17 jw, v0.6 fixed ry rotation.

2021-05-14 - Mario Voigt: 
    - changed extension to support ply,off,obj,stl by using OpenMesh
    - moved extension to sub menu structure (allows preview)
    - added different options

#Notes
 * requires exactly Slic3r-1.3.1-dev
      -> https://dl.slic3r.org/dev/linux/
      -> https://dl.slic3r.org/dev/win/
 * Notes to other Slic3r forks
     * does not work with Slic3r PE (Prusa Edition) (no export-svg option)
     * does not work with PrusaSlicer (no export-svg option)
 * does not work with IceSL slicer (https://icesl.loria.fr; no command line options) 

#ToDos
 * add some algorithm to handle fill for alternating paths. Issue at the moment: Imagine a char "A" in 3D. 
   It conatains an outline and a line path. Because those two paths are not combined both get filled but they do not render the char A correctly
 
'''
import sys
import os
import re
import subprocess
from lxml import etree
from subprocess import Popen, PIPE
import inkex
from inkex import Color, Transform
import tempfile
import openmesh as om


sys_platform = sys.platform.lower()
if sys_platform.startswith('win'):
  slic3r = 'slic3r-console.exe'
elif sys_platform.startswith('darwin'):
  slic3r = 'slic3r'
else:   # Linux
  slic3r = os.environ['HOME']+ '/Downloads/Slic3r-1.3.1-dev-x86_64.AppImage'
  if not os.path.exists(slic3r):
    slic3r = 'slic3r'

class SlicerSTLInput(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--tab')

        #Processor
        pars.add_argument('--slic3r_cmd', default="slic3r", help="Command to invoke slic3r.")
        
        #Input
        pars.add_argument('--inputfile', help='Input file (OBJ/OFF/PLY/STL)')
        pars.add_argument('--scalefactor', type=float, default=1.0, help='Scale the model to custom size')
        pars.add_argument("--max_num_faces", type=int, default=200, help="If the STL file has too much detail it contains a large number of faces. This will make processing extremely slow. So we can limit it.")
        pars.add_argument('--layer_height', type=float, default=1.000, help='slic3r layer height, probably in mm. Default: per slic3r config')
        pars.add_argument('--layer_number', type=int, default=0, help='Specific layer number')

        #Transforms
        pars.add_argument('--rx', type=float, default=None, help='Rotate STL object around X-Axis before importing.')
        pars.add_argument('--ry', type=float, default=None, help='Rotate STL object around Y-Axis before importing.')
        pars.add_argument('--rz', type=float, default=None, help='Rotate STL object around Z-Axis before importing.')
        pars.add_argument('--mirrorx', type=inkex.Boolean, default=False, help='Mirror X')
        pars.add_argument('--mirrory', type=inkex.Boolean, default=False, help='Mirror Y')
     
        #Output
        pars.add_argument('--numbers', type=inkex.Boolean, default=False, help='Add layer numbers.')
        pars.add_argument('--center', type=inkex.Boolean, default=False, help='Add center marks.')
        pars.add_argument("--resizetoimport", type=inkex.Boolean, default=True, help="Resize the canvas to the imported drawing's bounding box") 
        pars.add_argument("--extraborder", type=float, default=0.0)
        pars.add_argument("--extraborder_units")

        #Style
        pars.add_argument("--use_fill_color", type=inkex.Boolean, default=False, help="Use fill color")
        pars.add_argument("--fill_color", type=Color, default='1943148287', help="Fill color")
        pars.add_argument("--min_fill_opacity", type=float, default=0.0, help="Min fill opacity")
        pars.add_argument("--max_fill_opacity", type=float, default=1.0, help="Max fill opacity")
        pars.add_argument("--diffuse_fill_opacity",  default="regular", help="Diffuse fill opacity per layer")
        
        pars.add_argument("--use_stroke_color", type=inkex.Boolean, default=True, help="Use stroke color")
        pars.add_argument('--stroke_color', type=Color, default='879076607', help="Stroke color")
        
        pars.add_argument("--stroke_units", default="mm", help="Stroke width units")
        pars.add_argument("--min_stroke_width", type=float, default=1.0, help="Min stroke width")
        pars.add_argument("--max_stroke_width", type=float, default=1.0, help="Max stroke width")
        pars.add_argument("--diffuse_stroke_width",  default="regular", help="Diffuse stroke width per layer")
        
        pars.add_argument("--min_stroke_opacity", type=float, default=0.0, help="Min stroke opacity")
        pars.add_argument("--max_stroke_opacity", type=float, default=1.0, help="Max stroke opacity")
        pars.add_argument("--diffuse_stroke_opacity",  default="regular", help="Diffuse stroke opacity per layer") 

    def effect(self):             
        args = self.options
     
        if not os.path.exists(args.slic3r_cmd):
            inkex.utils.debug("Slic3r not found. Please define a correct location.")
            exit(1)
        
        if args.min_fill_opacity > args.max_fill_opacity:
            inkex.utils.debug("Min fill opacity may not be larger than max fill opacity. Adjust and try again!")
            exit(1)
        if args.min_stroke_width > args.max_stroke_width:
            inkex.utils.debug("Min stroke width may not be larger than max stroke width. Adjust and try again!")
            exit(1)
        if args.min_stroke_opacity > args.max_stroke_opacity:
            inkex.utils.debug("Min stroke opacity may not be larger than max stroke opacity. Adjust and try again!")
            exit(1)
   
        #############################################
        # test slic3r command
        #############################################
        if sys_platform.startswith('win'):
            # assert we run the commandline version of slic3r
            args.slic3r_cmd = re.sub('slic3r(\.exe)?$', 'slic3r-console.exe', args.slic3r_cmd, flags=re.I)       
        cmd = [args.slic3r_cmd, '--version']
        try:
            proc = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            hint="Maybe use --slic3r-cmd option?"
            inkex.utils.debug("{0}\nCommand failed: errno={1} {2}\n\n{3}".format(' '.join(cmd), e.errno, e.strerror, hint), file=sys.stderr)
            sys.exit(1)
        stdout, stderr = proc.communicate()
        
        #############################################
        # prepare STL input (also accept and convert obj, stl, ply, off)
        #############################################
        outputfilebase = os.path.splitext(os.path.basename(args.inputfile))[0]
        converted_inputfile = os.path.join(tempfile.gettempdir(), outputfilebase + ".stl")
        if not os.path.exists(args.inputfile):
            inkex.utils.debug("The input file does not exist.")
            exit(1)
        input_mesh = om.read_trimesh(args.inputfile)
        if input_mesh.n_faces() > args.max_num_faces:
            inkex.utils.debug("Aborted. Target STL file has " + str(input_mesh.n_faces()) + " faces, but only " + str(args.max_num_faces) + " are allowed.")
            exit(1)     
        om.write_mesh(converted_inputfile, input_mesh) #read + convert, might throw errors; warning. output is ASCII but cannot controlled to be set to binary because om.Options() is not available in python binding yet
        if not os.path.exists(converted_inputfile):
            inkex.utils.debug("The converted input file does not exist.")
            exit(1)
        args.inputfile = converted_inputfile #overwrite
    
        #############################################
        # create the layer slices
        #############################################
        svgfile = re.sub('\.stl', '.svg', args.inputfile, flags=re.IGNORECASE)  
        # option --layer-height does not work. We use --scale instead...
        scale = 1.0 / args.layer_height
        cmd  = [
            args.slic3r_cmd, 
            '--no-gui', 
            '--scale', str(scale), 
            '--rotate-x', str(args.rx),
            '--rotate-y', str(180+args.ry), #we import the style like PrusaSlicer would import on the plate
            '--rotate', str(args.rz), 
            '--first-layer-height', '0.1mm', 
            '--export-svg', '-o', svgfile, args.inputfile]
              
        def scale_points(pts, scale):
            """ str='276.422496,309.4 260.209984,309.4 260.209984,209.03 276.422496,209.03' """
            return re.sub('\d*\.\d*', lambda x: str(float(x.group(0))*scale), pts)
        
        def bbox_info(slic3r, file):
            cmd = [ slic3r, '--no-gui', '--info', file ]
            p = Popen(cmd, stdout=PIPE, stderr=PIPE)
            out, err = p.communicate()
            if len(err) > 0:
                raise ValueError(err)
        
            bb = {}
            for l in out.decode().split("\n"):
                m = re.match('((min|max)_[xyz])\s*=\s*(.*)', l)
                if m: bb[m.group(1)] = float(m.group(3))
            if (len(bb) != 6):
                raise ValueError("slic3r --info did not return 6 elements for bbox")
            return bb
        
        if args.center is True:
            bb = bbox_info(args.slic3r_cmd, args.inputfile)
            # Ouch: bbox info gives us stl coordinates. slic3r translates them into svg px using 75dpi.
            cx = (-bb['min_x'] + bb['max_x']) * 0.5 * 1/scale * 25.4 / 75
            cy = (-bb['min_y'] + bb['max_y']) * 0.5 * 1/scale * 25.4 / 75  

        try:
            proc = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            raise OSError("{0}\nCommand failed: errno={1} {2}".format(' '.join(cmd), e.errno, e.strerror))
        stdout, stderr = proc.communicate()
        
        if not b'Done.' in stdout:
            inkex.utils.debug("Command failed: {0}".format(' '.join(cmd)))
            inkex.utils.debug("OUT: " + str(stdout))
            inkex.utils.debug("ERR: " + str(stderr))
            sys.exit(1)
        
        # slic3r produces correct svg files, but with polygons instead of paths, and with undefined strokes.
        # When opened with inkscape, most lines are invisible and polygons cannot be edited.
        # To fix these issues, we postprocess the svg file:
        # * replace polygon nodes with corresponding path nodes.
        # * replace style attribute in polygon nodes with one that has a black stroke
        
        stream = open(svgfile, 'r')
        p = etree.XMLParser(huge_tree=True)
        doc = etree.parse(stream, parser=p)
        stream.close()
        
        ## To change the document units to mm, insert directly after the root node:
        # e.tag = '{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}namedview'
        # e.attrib['id'] = "base"
        # e.attrib['{http://www.inkscape.org/namespaces/inkscape}document-units'] = "mm"
            
        totalPolygoncount = 0
        for e in doc.iterfind('//{*}polygon'):
            totalPolygoncount += 1
            
        polygoncount = 0
        
        if args.use_fill_color is False:
            fill = "none"
        else:
            fill = args.fill_color
        
        for e in doc.iterfind('//{*}polygon'):
            polygoncount += 1
            if args.diffuse_fill_opacity == "front_to_back":
                fill_opacity =  (args.max_fill_opacity - (polygoncount / totalPolygoncount) * (args.max_fill_opacity - args.min_fill_opacity)) + args.min_fill_opacity
            elif args.diffuse_fill_opacity == "back_to_front":
                fill_opacity = ((polygoncount / totalPolygoncount) * (args.max_fill_opacity - args.min_fill_opacity)) + args.min_fill_opacity
            elif args.diffuse_fill_opacity == "no_diffuse":
                fill_opacity = args.max_fill_opacity
            else:
                inkex.utils.debug("Error: unkown diffuse fill opacity option")
                exit(1)
     
            if args.diffuse_stroke_width == "front_to_back":
                stroke_width =  (args.max_stroke_width - (polygoncount / totalPolygoncount) * (args.max_stroke_width - args.min_stroke_width)) + args.min_stroke_width
            elif args.diffuse_stroke_width == "back_to_front":
                stroke_width = ((polygoncount / totalPolygoncount) * (args.max_stroke_width - args.min_stroke_width)) + args.min_stroke_width
            elif args.diffuse_stroke_width == "no_diffuse":
                stroke_width = args.max_stroke_width
            else:
                inkex.utils.debug("Error: unkown diffuse stroke width option")
                exit(1)
            if self.options.stroke_units != "hairline":
                stroke_width = self.svg.unittouu(str(stroke_width) + self.options.stroke_units)
          
            if args.diffuse_stroke_opacity == "front_to_back":
                stroke_opacity =  (args.max_stroke_opacity - (polygoncount / totalPolygoncount) * (args.max_stroke_opacity - args.min_stroke_opacity)) + args.min_stroke_opacity
            elif args.diffuse_stroke_opacity == "back_to_front":
                stroke_opacity = ((polygoncount / totalPolygoncount) * (args.max_stroke_opacity - args.min_stroke_opacity)) + args.min_stroke_opacity
            elif args.diffuse_stroke_opacity == "no_diffuse":
                stroke_opacity = args.max_stroke_opacity
            else:
                inkex.utils.debug("Error: unkown diffuse stroke opacity option")
                exit(1)
                
            if args.use_stroke_color is False:
                stroke = ""
            else:
                stroke = "stroke:{}".format(args.stroke_color)
            # e.tag = '{http://www.w3.org/2000/svg}polygon'
            # e.attrib = {'{http://slic3r.org/namespaces/slic3r}type': 'contour', 'points': '276.422496,309.4 260.209984,309.4 260.209984,209.03 276.422496,209.03', 'style': 'fill: white'}
            e.tag = re.sub('polygon$', 'path', e.tag)
            e.attrib['id'] = 'polygon%d' % polygoncount
            e.attrib['{http://www.inkscape.org/namespaces/inkscape}connector-curvature'] = '0'
            e.attrib['style'] = 'fill:{};fill-opacity:{};{};stroke-opacity:{};stroke-width:{}'.format(fill, fill_opacity, stroke, stroke_opacity, stroke_width)
            if self.options.stroke_units == "hairline":
                e.attrib['style'] = e.attrib.get('style') + ";vector-effect:non-scaling-stroke;-inkscape-stroke:hairline;"
            e.attrib['d'] = 'M ' + re.sub(' ', ' L ', scale_points(e.attrib['points'], 1/scale)) + ' Z'

            if args.mirrorx is True:
                mx = -1
            else:
                mx = +1
            if args.mirrory is True:
                my = -1
            else:
                my = +1
                
            if args.mirrorx is True or args.mirrory is True:
                e.attrib['transform'] = 'scale({},{})'.format(mx, my)
            del e.attrib['points']
            if e.attrib.get('{http://slic3r.org/namespaces/slic3r}type') == 'contour':
                # remove contour, but keep all slic3r:type='hole', whatever it is worth later.
                del e.attrib['{http://slic3r.org/namespaces/slic3r}type']
        
        layercount = 0
        for e in doc.iterfind('//{*}g'):
            if e.attrib['{http://slic3r.org/namespaces/slic3r}z'] and e.attrib['id']:
                layercount+=1
                e.attrib['{http://www.inkscape.org/namespaces/inkscape}label'] = \
                    e.attrib['id'] \
                    + " slic3r:z={}mm".format(round(float(e.attrib['{http://slic3r.org/namespaces/slic3r}z']),3))
                del e.attrib['{http://slic3r.org/namespaces/slic3r}z']
                e.attrib['id'] = "stl-layer{}".format(layercount)
                # for some fun with our inkscape-paths2openscad extension, add sibling to e:
                # <svg:desc id="descpoly60">Depth: 1mm\nOffset: 31mm</svg:desc>
                desc = etree.Element('{http://www.w3.org/2000/svg}desc')
                desc.attrib['id'] = 'descl'+str(layercount)
                desc.text = "Depth: %.2fmm\nRaise: %.2fmm\n" % (1/scale, layercount/scale)
                e.append(desc)
                if args.numbers is True:
                    num = etree.Element('{http://www.w3.org/2000/svg}text')
                    num.attrib['id'] = 'textnum'+str(layercount)
                    num.attrib['x'] = str(layercount*2)
                    num.attrib['y'] = str(layercount*4+10)
                    num.attrib['style'] = 'fill:#00FF00;fill-opacity:1;stroke:#00FF00;font-family:FreeSans;font-size:10pt;stroke-opacity:1;stroke-width:0.1'
                    num.text = "%d" % layercount
                    e.append(num)
                if args.center is True:
                    cc = etree.Element('{http://www.w3.org/2000/svg}path')
                    cc.attrib['id'] = 'ccross'+str(layercount)
                    cc.attrib['style'] = 'fill:none;fill-opacity:1;stroke:#0000FF;font-family:FreeSans;font-size:10pt;stroke-opacity:1;stroke-width:0.1'
                    cc.attrib['d'] = 'M %s,%s v 10 M %s,%s h 10 M %s,%s h 4' % (cx, cy-5,  cx-5, cy,  cx-2, cy+5)
                    e.append(cc)
        
        etree.cleanup_namespaces(doc.getroot(), top_nsmap={
            'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
            'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'})
    
        #inkex.utils.debug("{0}: {1} polygons in {2} layers converted to paths.".format(svgfile, polygoncount, layercount))

        if self.options.layer_number != 0:
            groups = doc.xpath("//svg:g", namespaces=inkex.NSS)
            for element in groups:
            #for element in doc.getroot().iter("{http://www.w3.org/2000/svg}g"):
                if self.options.layer_number > 0:
                    if element.get('id').split('stl-layer')[1] != str(self.options.layer_number):
                        element.getparent().remove(element) #element.delete() does not work. why?
                else:
                    if element.get('id').split('stl-layer')[1] != str(len(groups) + self.options.layer_number):
                        element.getparent().remove(element) #element.delete() does not work. why?
        if layercount == 0:
            inkex.utils.debug("No layers imported. Try to lower your layer height")
            exit(1)
        #inkex.utils.debug(totalPolygoncount)
        if totalPolygoncount == 0:
            inkex.utils.debug("No polygons imported (empty groups). Try to lower your layer height")
            exit(1)

        stl_group = inkex.Group(id=self.svg.get_unique_id("slic3r-stl-input-")) #make a new group at root level
        stl_group.insert(0, inkex.Desc("Imported file: {}".format(self.options.inputfile)))
        self.svg.get_current_layer().append(stl_group)

        for element in doc.getroot().iter("{http://www.w3.org/2000/svg}g"):
            stl_group.append(element)

        #apply scale factor
        translation_matrix = [[args.scalefactor, 0.0, 0.0], [0.0, args.scalefactor, 0.0]]
        stl_group.transform = Transform(translation_matrix) @ stl_group.transform

        #adjust canvas to the inserted unfolding
        if args.resizetoimport:
            #push some calculation of all bounding boxes. seems to refresh something in the background which makes the bbox calculation working at the bottom
            for element in self.document.getroot().iter("*"):
                try:
                    element.bounding_box()
                except:
                    pass
            bbox = stl_group.bounding_box() #only works because we process bounding boxes previously. see top 
            if bbox is not None:
                namedView = self.document.getroot().find(inkex.addNS('namedview', 'sodipodi'))
                root = self.svg.getElement('//svg:svg');
                offset = self.svg.unittouu(str(args.extraborder) + args.extraborder_units)
                root.set('viewBox', '%f %f %f %f' % (bbox.left - offset, bbox.top - offset, bbox.width + 2 * offset, bbox.height + 2 * offset))
                root.set('width', "{:0.6f}{}".format(bbox.width + 2 * offset, self.svg.unit))
                root.set('height', "{:0.6f}{}".format(bbox.height + 2 * offset, self.svg.unit))
            else:
                inkex.utils.debug("Error resizing to canvas.")
 

if __name__ == '__main__':
    SlicerSTLInput().run()
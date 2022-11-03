#!/usr/bin/env python3

from copy import deepcopy
from pathlib import Path
import logging
import math
import os
import sys
import subprocess
from subprocess import Popen, PIPE
import inkex
from inkex import Rectangle
import inkex.command
from inkex.command import inkscape, inkscape_command
import tempfile
from PIL import Image
import base64
from io import BytesIO
import warnings
warnings.simplefilter('ignore', Image.DecompressionBombWarning)
from lxml import etree
from scour.scour import scourString

logger = logging.getLogger(__name__)

DETACHED_PROCESS = 0x00000008
GROUP_ID = 'export_selection_transform'

class ExportObject(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--wrap_transform", type=inkex.Boolean, default=False, help="Wrap final document in transform")
        pars.add_argument("--border_offset", type=float, default=1.000, help="Add border offset around selection")
        pars.add_argument("--border_offset_unit", default="mm", help="Offset unit")
        pars.add_argument("--export_dir", default="~/inkscape_export/",    help="Location to save exported documents")
        pars.add_argument("--opendir", type=inkex.Boolean, default=False, help="Open containing output directory after export")
        pars.add_argument("--dxf_exporter_path", default="/usr/share/inkscape/extensions/dxf_outlines.py", help="Location of dxf_outlines.py")
        pars.add_argument("--export_svg", type=inkex.Boolean, default=False, help="Create a svg file")
        pars.add_argument("--export_dxf", type=inkex.Boolean, default=False, help="Create a dxf file")
        pars.add_argument("--export_pdf", type=inkex.Boolean, default=False, help="Create a pdf file")
        pars.add_argument("--export_png", type=inkex.Boolean, default=False, help="Create a png file")
        pars.add_argument("--png_dpi", type=float, default=96, help="PNG DPI (applies for export and replace)")
        pars.add_argument("--replace_by_png", type=inkex.Boolean, default=False, help="Replace selection by png export")
        pars.add_argument("--newwindow", type=inkex.Boolean, default=False, help="Open file in new Inkscape window")      
        pars.add_argument("--skip_errors", type=inkex.Boolean, default=False, help="Skip on errors")

    def openExplorer(self, dir):
        if os.name == 'nt':
            Popen(["explorer", dir], close_fds=True, creationflags=DETACHED_PROCESS).wait()
        else:
            Popen(["xdg-open", dir], close_fds=True, start_new_session=True).wait()

    def spawnIndependentInkscape(self, file): #function to spawn non-blocking inkscape instance. the inkscape command is available because it is added to ENVIRONMENT when Inkscape main instance is started
        if not os.path.exists(file):
            inkex.utils.debug("Error. {} does not exist!".format(file))
            exit(1)
        warnings.simplefilter('ignore', ResourceWarning) #suppress "enable tracemalloc to get the object allocation traceback"
        if os.name == 'nt':
            Popen(["inkscape", file], close_fds=True, creationflags=DETACHED_PROCESS)
        else:
            subprocess.Popen(["inkscape", file], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        warnings.simplefilter("default", ResourceWarning)

    def effect(self):
        scale_factor = self.svg.unittouu("1px")
        
        svg_export = self.options.export_svg
        #extra_param = "--batch-process"
        extra_param = None
        
        if self.options.export_svg is False and \
            self.options.export_dxf is False and \
            self.options.export_pdf is False and \
            self.options.export_png is False and \
            self.options.replace_by_png is False and \
            self.options.newwindow is False:
            inkex.utils.debug("You must select at least one option to continue!")
            return

        if self.options.replace_by_png is True:
            self.options.border_offset = 0 #override

        if not self.svg.selected:
            inkex.errormsg("Selection is empty. Please select some objects first!")
            return

        if self.options.export_dxf is True:
            #preflight check for DXF input dir
            if not os.path.exists(self.options.dxf_exporter_path):
                inkex.utils.debug("Location of dxf_outlines.py does not exist. Please select a proper file and try again.")
                exit(1)
            
        export_dir = Path(self.absolute_href(self.options.export_dir))
        os.makedirs(export_dir, exist_ok=True)

        offset = self.svg.unittouu(str(self.options.border_offset) + self.options.border_offset_unit)

        bbox = inkex.BoundingBox()

        selected = self.svg.selected
        firstId = selected[0].get('id')
        parent = self.svg.getElementById(firstId).getparent()

        for element in selected.values():
            transform = inkex.Transform()
            parent = element.getparent()
            if parent is not None and isinstance(parent, inkex.ShapeElement):
                transform = parent.composed_transform()
            try:
                '''
                ...rectangles cause some strangle scaling issue, offendingly caused by namedview units.
                The rectangle attributes are set in px. They ignore the real units from namedview. 
                Strange fact: ellipses, spirals and other primitives work flawlessly.
                '''
                if isinstance (element, inkex.Rectangle) or \
                   isinstance (element, inkex.Circle) or \
                   isinstance (element, inkex.Ellipse):
                    bbox += element.bounding_box(transform) * scale_factor
                elif isinstance (element, inkex.TextElement) or \
                     isinstance (element, inkex.Tspan):
                    if self.options.skip_errors is False:
                        self.msg("Text elements are not supported!")
                        return
                    else:
                        continue  
                else:
                    bbox += element.bounding_box(transform)
            except Exception:
                logger.exception("Bounding box not computed")
                logger.info("Skipping bounding box")
                transform = element.composed_transform()
                x1, y1 = transform.apply_to_point([0, 0])
                x2, y2 = transform.apply_to_point([1, 1])
                bbox += inkex.BoundingBox((x1, x2), (y1, y2))
             
        template = self.create_document()
        svg_filename = None

        group = etree.SubElement(template, '{http://www.w3.org/2000/svg}g')
        group.attrib['id'] = GROUP_ID
        group.attrib['transform'] = str(inkex.Transform(((1, 0, -bbox.left), (0, 1, -bbox.top))))

        for element in self.svg.selected.values():
            if element.tag == inkex.addNS('image', 'svg'):
                continue #skip images
            elem_copy = deepcopy(element)
            elem_copy.attrib['transform'] = str(element.composed_transform())
            elem_copy.attrib['style'] = str(element.specified_style())            
            group.append(elem_copy)

        template.attrib['viewBox'] = f'{-offset} {-offset} {bbox.width + offset * 2} {bbox.height + offset * 2}'
        template.attrib['width'] = f'{bbox.width + offset * 2}' + self.svg.unit
        template.attrib['height'] = f'{bbox.height + offset * 2}' + self.svg.unit

        if svg_filename is None:
            filename_base = element.attrib.get('id', None).replace(os.sep, '_')
            if filename_base:
                svg_filename = filename_base + '.svg'
        if not filename_base: #should never be the case. Inkscape might crash if the id attribute is empty or not existent due to invalid SVG
            filename_base = self.svg.get_unique_id("selection")
            svg_filename = filename_base + '.svg'

        if len(group) == 0:
            self.msg("Selection does not contain any vector data.")
            exit(1)

        template.append(group)
        svg_out = os.path.join(tempfile.gettempdir(), svg_filename)

        if self.options.wrap_transform is False:
            #self.load(inkscape_command(template.tostring(), select=GROUP_ID, verbs=['SelectionUnGroup;FileSave'])) #fails due to new bug
            
            #workaround
            self.save_document(template, svg_out) #export recent file
            actions_list=[]
            actions_list.append("SelectionUnGroup")
            actions_list.append("export-type:svg")
            actions_list.append("export-filename:{}".format(svg_out))
            actions_list.append("export-do") 
            actions = ";".join(actions_list)
            cli_output = inkscape(svg_out, extra_param, actions=actions) #process recent file
            if len(cli_output) > 0:
                self.msg("Inkscape returned the following output when trying to run the file export; the file export may still have worked:")
                self.msg(cli_output)
            self.load(svg_out) #reload recent file
            
            template = self.svg
            for child in template.getchildren():
                if child.tag == '{http://www.w3.org/2000/svg}metadata':
                    template.remove(child)

        self.save_document(template, svg_out) # save one into temp dir to access for dxf/pdf/new window instance

        if self.options.export_svg is True:
            self.save_document(template, export_dir / svg_filename)
        
        if self.options.opendir is True:
            self.openExplorer(export_dir)
            
        if self.options.newwindow is True:
            #inkscape(os.path.join(export_dir, svg_filename)) #blocking cmd
            self.spawnIndependentInkscape(os.path.join(tempfile.gettempdir(), svg_filename)) #non-blocking
            
        if self.options.export_dxf is True:
            #ensure that python command is available #we pass 25.4/96 which stands for unit mm. See inkex.units.UNITS and dxf_outlines.inx
            cmd = [
                sys.executable, #the path of the python interpreter which is used for this script 
                self.options.dxf_exporter_path, 
                '--output=' + os.path.join(export_dir, filename_base + '.dxf'), 
                r'--units=25.4/96', 
                os.path.join(tempfile.gettempdir(), svg_filename)
                ]
            proc = Popen(cmd, shell=False, stdout=PIPE, stderr=PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                inkex.utils.debug("%d %s %s" % (proc.returncode, stdout, stderr))

        if self.options.export_pdf is True:    
            cli_output = inkscape(os.path.join(tempfile.gettempdir(), svg_filename), extra_param, actions='export-pdf-version:1.5;export-text-to-path;export-filename:{file_name};export-do'.format(file_name=os.path.join(export_dir, filename_base + '.pdf')))
            if len(cli_output) > 0:
                self.msg("Inkscape returned the following output when trying to run the file export; the file export may still have worked:")
                self.msg(cli_output)
            
        if self.options.export_png is True:
            png_export=os.path.join(export_dir, filename_base + '.png')
            try:
                os.remove(png_export)
            except OSError as e: 
                #inkex.utils.debug("Error while deleting previously generated output file " + png_export)
                pass
            actions_list=[]
            actions_list.append("export-background:white")
            actions_list.append("export-type:png")
            actions_list.append("export-dpi:{}".format(self.options.png_dpi))
            actions_list.append("export-filename:{}".format(png_export))
            actions_list.append("export-do") 
            actions = ";".join(actions_list)
            cli_output = inkscape(os.path.join(tempfile.gettempdir(), svg_filename), extra_param, actions=actions)
            if len(cli_output) > 0:
                self.msg("Inkscape returned the following output when trying to run the file export; the file export may still have worked:")
                self.msg(cli_output)
                
        if self.options.replace_by_png is True:
            #export to png file to temp
            png_export=os.path.join(tempfile.gettempdir(), filename_base + '.png')
            try:
                os.remove(png_export)
            except OSError as e: 
                #inkex.utils.debug("Error while deleting previously generated output file " + png_export)
                pass
            actions_list=[]
            actions_list.append("export-background:white")
            actions_list.append("export-type:png")
            actions_list.append("export-dpi:{}".format(self.options.png_dpi))
            actions_list.append("export-filename:{}".format(png_export))
            actions_list.append("export-do") 
            actions = ";".join(actions_list)
            cli_output = inkscape(os.path.join(tempfile.gettempdir(), svg_filename), extra_param, actions=actions)
            if len(cli_output) > 0:
                self.msg("Inkscape returned the following output when trying to run the file export; the file export may still have worked:")
                self.msg(cli_output)         
            #then remove the selection and replace it by png
            #self.msg(parent.get('id'))
            for element in selected.values():
                element.delete()
            #read png file and get base64 string from it
            try:
                img = Image.open(png_export)
            except Image.DecompressionBombError as e: #we could also increse PIL.Image.MAX_IMAGE_PIXELS = some large int
                self.msg("Error. Image is too large ({} x {} px). Reduce DPI and try again!".format(self.svg.uutounit(bbox.width), self.svg.uutounit(bbox.height)))
                exit(1)
            output_buffer = BytesIO()
            img.save(output_buffer, format='PNG')
            byte_data = output_buffer.getvalue()
            base64_str = base64.b64encode(byte_data).decode('UTF-8')
            #finally replace the svg:path(s) with svg:image
            imgReplacement = etree.SubElement(Rectangle(), '{http://www.w3.org/2000/svg}image')
            imgReplacement.attrib['x'] = str(bbox.left)
            imgReplacement.attrib['y'] = str(bbox.top)
            imgReplacement.attrib['width'] = str(bbox.width)
            imgReplacement.attrib['height'] = str(bbox.height)
            imgReplacement.attrib['id'] = firstId
            imgReplacement.attrib['{http://www.w3.org/1999/xlink}href'] = "data:image/png;base64,{}".format(base64_str)
            parent.append(imgReplacement)
            if parent.attrib.has_key('transform'):
                del parent.attrib['transform'] #remove transform

                
    def create_document(self):
        document = self.svg.copy()
        for child in document.getchildren():
            if child.tag == '{http://www.w3.org/2000/svg}defs':
                continue
            document.remove(child)
        return document

    def save_document(self, document, filename):
        with open(filename, 'wb') as fp:
            document = document.tostring()
            fp.write(scourString(document).encode('utf8'))


if __name__ == '__main__':
    ExportObject().run()
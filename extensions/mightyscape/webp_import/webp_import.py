#!/usr/bin/env python3

import sys
import os
import argparse
import inkex
import shutil
from inkex import Rectangle
from PIL import Image
import base64
from io import BytesIO, StringIO
import subprocess
from lxml import etree

class WebpImport(inkex.InputExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('inputfile')
        
    def effect(self):
        if os.name == 'nt':
            tmp =  os.getenv('TEMP') + '\\'
        else:
            tmp = '/tmp/'
        convertfile = os.path.join(tmp, "webp.png")
        if shutil.which('magick'):
            command = "magick \"%s\" \"%s\" " % (self.options.inputfile, convertfile)
        elif shutil.which('convert'):
            command = "convert \"%s\" \"%s\" " % (self.options.inputfile, convertfile)
        else:
            inkex.errormsg('ImageMagick does not appear to be installed.')
            exit()   
        p = subprocess.Popen(command, shell=True)
        return_code = p.wait()
        #inkex.utils.debug("command:" + command)
        #inkex.utils.debug("Errorcode:" + str(return_code))
        
        try:
            img = Image.open(convertfile)
        except Image.DecompressionBombError as e: #we could also increse PIL.Image.MAX_IMAGE_PIXELS = some large int
            self.msg("Error. Image is too large. Reduce DPI and try again!")
            exit(1)
        output_buffer = BytesIO()
        img.save(output_buffer, format='PNG')
        width, height = img.size
        byte_data = output_buffer.getvalue()
        base64_str = base64.b64encode(byte_data).decode('UTF-8')
        webp = etree.SubElement(Rectangle(), '{http://www.w3.org/2000/svg}image')
        webp.attrib['x'] = str(0)
        webp.attrib['y'] = str(0)
        webp.attrib['width'] = str(width)
        webp.attrib['height'] = str(height)
        webp.attrib['{http://www.w3.org/1999/xlink}href'] = "data:image/png;base64,{}".format(base64_str)
        base = ('<svg xmlns="http://www.w3.org/2000/svg"'
                ' width="{}px" height="{}px" viewBox="{} {} {} {}"/>'
               ).format(width, height, 0, 0, width, height)
        output = StringIO(base)
        tree = etree.parse(output)
        output.close()
        tree.getroot().append(webp)
        svgfile = os.path.join(tmp, "webp.svg")
        with open(svgfile, 'w') as file:
            tree.write(svgfile)
        with open(svgfile, 'r') as newfile:
            sys.stdout.write(newfile.read())

    def load(self, stream):
        return str(stream.read())

if __name__ == '__main__':
    WebpImport().run()
                
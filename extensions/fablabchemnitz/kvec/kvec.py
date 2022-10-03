#!/usr/bin/env python3

import sys
import inkex
import os
import base64
import urllib.request as urllib
from PIL import Image
from io import BytesIO
from lxml import etree
from inkex import Color

class KVEC (inkex.EffectExtension):

    def checkImagePath(self, element):
        xlink = element.get('xlink:href')
        if xlink and xlink[:5] == 'data:':
            # No need, data alread embedded
            return

        url = urllib.urlparse(xlink)
        href = urllib.url2pathname(url.path)

        # Primary location always the filename itself.
        path = self.absolute_href(href or '')

        # Backup directory where we can find the image
        if not os.path.isfile(path):
            path = element.get('sodipodi:absref', path)

        if not os.path.isfile(path):
            inkex.errormsg('File not found "{}". Unable to embed image.').format(path)
            return

        if (os.path.isfile(path)):
            return path
  
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        
        #General Settings
        pars.add_argument("--keeporiginal", type=inkex.Boolean, default=False, help="Keep original image on canvas")
        pars.add_argument("--fittooriginal", type=inkex.Boolean, default=False, help="Fit to original dimensions")
        pars.add_argument("--debug", type=inkex.Boolean, default=False, help="Enable debug output")
        pars.add_argument("--sysmalloc", type=inkex.Boolean, default=True, help="Use system-malloc routines")
        pars.add_argument("--text", type=inkex.Boolean, default=True, help="Text output")
        pars.add_argument("--font", type=inkex.Boolean, default=True, help="Generate optimized set of parameters")
        pars.add_argument("--sort", default="max", help="Type of sort order for vectors")

        #Geometry/Quality
        pars.add_argument("--grit", type=int, default=0, help="Filter out details smaller than x pixels")
        pars.add_argument("--gapfill", type=int, default=0, help="Gap fill (jumping)")
        pars.add_argument("--centerline", default="off", help="Generates single lines if linewidth small enough")
        pars.add_argument("--bezier", type=inkex.Boolean, default=False, help="Generate Bezier-curves")
        pars.add_argument("--errbez", type=int, default=3, help="Error-Parameter for Bezier-curves")
        pars.add_argument("--reduce", default="orthogonal", help="Type of line reducing")
        pars.add_argument("--overlapp", type=inkex.Boolean, default=False, help="Polygons overlap (1px)")
        pars.add_argument("--smooth", type=inkex.Boolean, default=False, help="Smoothing of polylines") 
        pars.add_argument("--winding", default="original", help="Winding")
        pars.add_argument("--high_resolution", type=inkex.Boolean, default=False, help="High vectorization resolution") 
        pars.add_argument("--subsampling", type=inkex.Boolean, default=False, help="If enabled, the output vectors are subsampled by a factor of 2. This will reduce the size of the output file and will also result in smoothing the vectors") 
        pars.add_argument("--lossless", type=inkex.Boolean, default=False, help="Generate lossless image") 
        pars.add_argument("--progressive", type=inkex.Boolean, default=False, help="image is build up from two successive layers (one 'rough' picture without details and one refined picture which contains only details).")
        pars.add_argument("--progressive_gritfactor", type=int, default=2, help="The first layer has a grit-value multiplied by this")
        pars.add_argument("--progressive_colorfactor", type=int, default=2, help="The first layer has a quantize-value divided by this")

        #Colors/Styles
        pars.add_argument("--quantize", type=int, default=32, help="Color quantization")
        pars.add_argument("--delta", type=int, default=0, help="Delta")
        pars.add_argument("--fill", default="solid", help="Fill")
        pars.add_argument("--lwidth", type=int, default=0, help="Line width")
        pars.add_argument("--black", type=inkex.Boolean, default=False, help="Output-color is always black")
        pars.add_argument("--palette", default="optimize", help="Palette")
        pars.add_argument("--color_vectorization", default="normal", help="Color vectorization")
        pars.add_argument("--colspace", default="rgb", help="Colorspace conversion parameters")
        pars.add_argument("--colsep", default="rgb", help="Color separation parameters")
        pars.add_argument("--tcolor_mode", default="none", help="Transparency color")
        pars.add_argument("--tcolor_custom", type=Color, default=255, help="User-defined transparency color (RGB values)")
        pars.add_argument("--vcolor_mode", default="none", help="Pick out regions with color")
        pars.add_argument("--vcolor", type=Color, default=255, help="Region color")
    def effect(self):
        
        so = self.options
        
        if (so.ids):
            for element in self.svg.selected.values():
                if element.tag == inkex.addNS('image', 'svg'):
                    self.path = self.checkImagePath(element)  # This also ensures the file exists
                    if self.path is None:  # check if image is embedded or linked
                        image_string = element.get('{http://www.w3.org/1999/xlink}href')
                        # find comma position
                        i = 0
                        while i < 40:
                            if image_string[i] == ',':
                                break
                            i = i + 1
                        image = Image.open(BytesIO(base64.b64decode(image_string[i + 1:len(image_string)])))
                    else:
                        image = Image.open(self.path)
                                      
                    if element.get('width')[-1].isdigit() is False or element.get('height')[-1].isdigit() is False:
                        inkex.utils.debug("Image seems to have some weird dimensions in XML structure. Please remove units from width and height attributes at <svg:image>")
                        return

                    # Write the embedded or linked image to temporary directory
                    if os.name == "nt":
                        exportfile = "kvec.png"
                    else:
                        exportfile = "/tmp/kvec.png"
                        
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    image.save(exportfile, "png")
           
                    #some crash avoidings
                    if so.lossless is True:
                        so.color_vectorization = "normal"
                        so.bezier = False
                        so.font = False
                        so.black = False
                    if so.high_resolution is True:
                        so.overlapp = False
           
                    ## Build up command according to your settings from extension GUI
                    if os.name == "nt":
                        command = "kvec.exe"
                    else:
                        command = "./kvec"
                    command += " " + exportfile #input
                    command += " " + exportfile + ".svg" #output
                    command += " -format svg"
                    
                    #General Settings
                    if so.sysmalloc is False: command += " -sysmalloc off"
                    if so.font is True: command += " -font"
                    if so.text is False: command += " -text off"
                    command += " -sort " + so.sort

                    #Geometry/Quality
                    if so.grit > 0: command += " -grit " + str(so.grit)
                    command += " -gapfill " + str(so.gapfill)
                    command += " -centerline " + so.centerline
                    command += " -winding " + so.winding
                    if so.bezier is True: command += " -bezier"
                    command += " -errbez " + str(so.errbez)
                    if so.overlapp is True: command += " -overlapp"
                    if so.smooth is True: command += " -smooth on"
                    command += " -reduce " + str(so.reduce)
                    if so.high_resolution is True: command += " -resolution high"
                    if so.subsampling is True: command += " -subsampling"
                    if so.lossless is True: command += " -lossless"
                    if so.progressive is True:
                        command += " -progressive gritfactor " + str(so.progressive_gritfactor)
                        command += " -progressive colorfactor " + str(so.progressive_colorfactor)  

                    #Colors/Styles
                    command += " -quantize " + str(so.quantize)
                    command += " -delta " + str(so.delta)
                    command += " -fill " + so.fill
                    command += " -lwidth " + str(so.lwidth)
                    command += " -palette " + so.palette
                    if so.black is True: command += " -black"
                    if so.color_vectorization != "normal":  command += " -" + so.color_vectorization
                    command += " -colspace " + so.colspace
                    command += " -colsep " + so.colsep
                    if so.tcolor_mode == "auto":
                        command += " -tcolor auto"
                    elif so.tcolor_mode == "custom":
                        command += " -tcolor color {} {} {}".format(so.tcolor_custom.red, so.tcolor_custom.green, so.tcolor_custom.blue)
                    if so.vcolor_mode == "matching": 
                        command += " -vcolor {} {} {}".format(so.vcolor.red, so.vcolor.green, so.vcolor.blue)
                    elif so.vcolor_mode == "not_matching": 
                        command += " -vcolor {} {} {}".format(-so.vcolor.red, -so.vcolor.green, -so.vcolor.blue)
                                            
                    #some debug stuff    
                    if so.debug is True: 
                        command += " -debug all"
                        inkex.utils.debug(command)
                    
                    # Create the vector new SVG file
                    with os.popen(command, "r") as proc:
                        result = proc.read()
                        if so.debug is True: inkex.utils.debug(result)

                    # proceed if new SVG file was successfully created
                    doc = None
                    if os.path.exists(exportfile + ".svg"):
                        # Delete the temporary png file again because we do not need it anymore
                        if os.path.exists(exportfile):
                            os.remove(exportfile)
 
                        # new parse the SVG file and insert it as new group into the current document tree
                        doc = etree.parse(exportfile + ".svg").getroot()
                        
                        parent = element.getparent()
                        idx = parent.index(element)
                        #newGroup = self.document.getroot().add(inkex.Group())
                        newGroup = inkex.Group()
                        parent.insert(idx + 1,newGroup)
                        for child in doc:
                            newGroup.append(child)
                            
                        #doc.get('height')
                        #doc.get('width')
                        #doc.get('viewBox')
                        if so.fittooriginal is True: #fitting does not work in all cases so we make it available as option
                            bbox = newGroup.bounding_box()
                            newGroup.attrib['transform'] = "matrix({:0.6f}, 0, 0, {:0.6f}, {:0.6f}, {:0.6f})".format(
                                #float(element.get('width')) / float(doc.get('width')),
                                #float(element.get('height')) / float(doc.get('height')),
                                float(element.get('width')) / bbox.width,
                                float(element.get('height')) / bbox.height,
                                float(element.get('x')) - (float(element.get('width')) / bbox.width) * bbox.left,
                                float(element.get('y')) - (float(element.get('height')) / bbox.height) * bbox.top
                                )

                        # Delete the temporary svg file
                        if os.path.exists(exportfile + ".svg"):
                            try:
                                os.remove(exportfile + ".svg")
                            except:
                                pass
                    
                    else:
                        inkex.utils.debug("Error while creating output file! :-( The \"kvec\" executable seems to be missing, has no exec permissions or platform is imcompatible.")
                        exit(1)
                    #remove the old image or not                    
                    if so.keeporiginal is not True:
                        element.delete()
        else:
            inkex.utils.debug("No image found for tracing. Please select an image first.")        

if __name__ == '__main__':
    KVEC().run()
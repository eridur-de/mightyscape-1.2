#!/usr/bin/env python3
#
# An extension to generate SVG/PNG labels (stickers) for use with our item inventory system. 
# It pulls a .csv file from a server URL (protected by basic auth) and exports and prints the labels to a Brother QL-720NW label printer
# Documentation: https://wiki.fablabchemnitz.de/display/TEED/Werkstattorientierung+im+FabLab+-+Digtales+Inventar
#
# Made by FabLab Chemnitz / Stadtfabrikanten e.V. - Developer: Mario Voigt (year 2021)
#
# This extension is based on the "original" barcode extension included in default Inkscape Extension Set, which is licensed by the following:
#
# Copyright (C) 2009 John Beard john.j.beard@gmail.com
#
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

import csv
import os
import shutil
import urllib.request
from lxml import etree
import inkex
from inkex import Rectangle
from inkex.command import inkscape
import re
import subprocess
from subprocess import Popen, PIPE
from tkinter import Tk, font

INVALID_BIT = 2

# CODEWORD STREAM GENERATION =========================================
# take the text input and return the codewords,
# including the Reed-Solomon error-correcting codes.
# =====================================================================

def get_codewords(text, nd, nc, inter, size144):
    # convert the data to the codewords
    data = list(encode_to_ascii(text))

    if not size144:  # render a "normal" datamatrix
        data_blocks = partition_data(data, nd * inter)  # partition into data blocks of length nd*inter -> inter Reed-Solomon block
        data_blocks = interleave(data_blocks, inter)  # interleave consecutive inter blocks if required
        data_blocks = reed_solomon(data_blocks, nd, nc)  # generate and append the Reed-Solomon codewords
        data_blocks = combine_interleaved(data_blocks, inter, nd, nc, False)  # concatenate Reed-Solomon blocks bound for the same datamatrix
    return data_blocks


# Takes a codeword stream and splits up into "inter" blocks.
# eg interleave( [1,2,3,4,5,6], 2 ) -> [1,3,5], [2,4,6]
def interleave(blocks, inter):
    if inter == 1:  # if we don"t have to interleave, just return the blocks
        return blocks
    else:
        result = []
        for block in blocks:  # for each codeword block in the stream
            block_length = int(len(block) / inter)  # length of each interleaved block
            inter_blocks = [[0] * block_length for i in range(inter)]  # the interleaved blocks

            for i in range(block_length):  # for each element in the interleaved blocks
                for j in range(inter):  # for each interleaved block
                    inter_blocks[j][i] = block[i * inter + j]

            result.extend(inter_blocks)  # add the interleaved blocks to the output

        return result

# Combine interleaved blocks into the groups for the same datamatrix
#
# e.g combine_interleaved( [[d1, d3, d5, e1, e3, e5], [d2, d4, d6, e2, e4, e6]], 2, 3, 3 )
#   --> [[d1, d2, d3, d4, d5, d6, e1, e2, e3, e4, e5, e6]]
def combine_interleaved(blocks, inter, nd, nc, size144):
    if inter == 1:  # the blocks aren"t interleaved
        return blocks
    else:
        result = []
        for i in range(len(blocks) // inter):  # for each group of "inter" blocks -> one full datamatrix
            data_codewords = []  # interleaved data blocks

            if size144:
                nd_range = 1558  # 1558 = 156*8 + 155*2
                nc_range = 620  # 620 = 62*8 + 62*2
            else:
                nd_range = nd * inter
                nc_range = nc * inter

            for j in range(nd_range):  # for each codeword in the final list
                data_codewords.append(blocks[i * inter + j % inter][j // inter])

            for j in range(nc_range):  # for each block, add the ecc codewords
                data_codewords.append(blocks[i * inter + j % inter][nd + j // inter])

            result.append(data_codewords)
        return result

def encode_to_ascii(text):
    """Encode this text into chunks, ascii or digits"""
    i = 0
    while i < len(text):
        # check for double digits, if the next char is also a digit
        if text[i].isdigit() and (i < len(text) - 1) and text[i + 1].isdigit():
            yield int(text[i] + text[i + 1]) + 130
            i += 2  # move on 2 characters
        else:  # encode as a normal ascii,
            yield ord(text[i]) + 1  # codeword is ASCII value + 1 (ISO 16022:2006 5.2.3)
            i += 1  # next character

# partition data into blocks of the appropriate size to suit the
# Reed-Solomon block being used.
# e.g. partition_data([1,2,3,4,5], 3) -> [[1,2,3],[4,5,PAD]]
def partition_data(data, rs_data):
    PAD_VAL = 129  # PAD codeword (ISO 16022:2006 5.2.3)
    data_blocks = []
    i = 0
    while i < len(data):
        if len(data) >= i + rs_data:  # we have a whole block in our data
            data_blocks.append(data[i:i + rs_data])
            i = i + rs_data
        else:  # pad out with the pad codeword
            data_block = data[i:len(data)]  # add any remaining data
            pad_pos = len(data)
            padded = False
            while len(data_block) < rs_data:  # and then pad with randomised pad codewords
                if not padded:
                    data_block.append(PAD_VAL)  # add a normal pad codeword
                    padded = True
                else:
                    data_block.append(randomise_pad_253(PAD_VAL, pad_pos))
                pad_pos += 1
            data_blocks.append(data_block)
            break

    return data_blocks


# Pad character randomisation, to prevent regular patterns appearing
# in the data matrix
def randomise_pad_253(pad_value, pad_position):
    pseudo_random_number = ((149 * pad_position) % 253) + 1
    randomised = pad_value + pseudo_random_number
    if randomised <= 254:
        return randomised
    else:
        return randomised - 254

# REED-SOLOMON ENCODING ROUTINES =====================================

# "prod(x,y,log,alog,gf)" returns the product "x" times "y"
def prod(x, y, log, alog, gf):
    if x == 0 or y == 0:
        return 0
    else:
        result = alog[(log[x] + log[y]) % (gf - 1)]
        return result

# generate the log & antilog lists:
def gen_log_alog(gf, pp):
    log = [0] * gf
    alog = [0] * gf

    log[0] = 1 - gf
    alog[0] = 1

    for i in range(1, gf):
        alog[i] = alog[i - 1] * 2

        if alog[i] >= gf:
            alog[i] = alog[i] ^ pp

        log[alog[i]] = i

    return log, alog


# generate the generator polynomial coefficients:
def gen_poly_coeffs(nc, log, alog, gf):
    c = [0] * (nc + 1)
    c[0] = 1

    for i in range(1, nc + 1):
        c[i] = c[i - 1]

        j = i - 1
        while j >= 1:
            c[j] = c[j - 1] ^ prod(c[j], alog[i], log, alog, gf)
            j -= 1

        c[0] = prod(c[0], alog[i], log, alog, gf)

    return c


# "ReedSolomon(wd,nd,nc)" takes "nd" data codeword values in wd[]
# and adds on "nc" check codewords, all within GF(gf) where "gf" is a
# power of 2 and "pp" is the value of its prime modulus polynomial */
def reed_solomon(data, nd, nc):
    # parameters of the polynomial arithmetic
    gf = 256  # operating on 8-bit codewords -> Galois field = 2^8 = 256
    pp = 301  # prime modulus polynomial for ECC-200 is 0b100101101 = 301 (ISO 16022:2006 5.7.1)

    log, alog = gen_log_alog(gf, pp)
    c = gen_poly_coeffs(nc, log, alog, gf)

    for block in data:  # for each block of data codewords

        block.extend([0] * (nc + 1))  # extend to make space for the error codewords

        # generate "nc" checkwords in the list block
        for i in range(0, nd):
            k = block[nd] ^ block[i]

            for j in range(0, nc):
                block[nd + j] = block[nd + j + 1] ^ prod(k, c[nc - j - 1], log, alog, gf)

        block.pop()

    return data


# MODULE PLACEMENT ROUTINES===========================================
#   These routines take a steam of codewords, and place them into the
#   DataMatrix in accordance with Annex F of BS ISO/IEC 16022:2006

def bit(byte, bit_ch):
    """bit() returns the bit"th bit of the byte"""
    # the MSB is bit 1, LSB is bit 8
    return (byte >> (8 - bit_ch)) % 2

def module(array, nrow, ncol, row, col, bit_ch):
    """place a given bit with appropriate wrapping within array"""
    if row < 0:
        row = row + nrow
        col = col + 4 - ((nrow + 4) % 8)

    if col < 0:
        col = col + ncol
        row = row + 4 - ((ncol + 4) % 8)

    array[row][col] = bit_ch

def place_square(case, array, nrow, ncol, row, col, char):
    """Populate corner cases (0-3) and utah case (-1)"""
    for i in range(8):
        x, y = [
            [(row - 1, 0), (row - 1, 1), (row - 1, 2), (0, col - 2),
             (0, col - 1), (1, col - 1), (2, col - 1), (3, col - 1)],
            [(row - 3, 0), (row - 2, 0), (row - 1, 0), (0, col - 4),
             (0, col - 3), (0, col - 2), (0, col - 1), (1, col - 1)],
            [(row - 3, 0), (row - 2, 0), (row - 1, 0), (0, col - 2),
             (0, col - 1), (1, col - 1), (2, col - 1), (3, col - 1)],
            [(row - 1, 0), (row - 1, col - 1), (0, col - 3), (0, col - 2),
             (0, col - 1), (1, col - 3), (1, col - 2), (1, col - 1)],

            # "utah" places the 8 bits of a utah-shaped symbol character in ECC200
            [(row - 2, col -2), (row - 2, col -1), (row - 1, col - 2), (row - 1, col - 1),
             (row - 1, col), (row, col - 2), (row, col - 1), (row, col)],
        ][case][i]
        module(array, nrow, ncol, x, y, bit(char, i + 1))
    return 1

def place_bits(data, nrow, ncol):
    """fill an nrow x ncol array with the bits from the codewords in data."""
    # initialise and fill with -1"s (invalid value)
    array = [[INVALID_BIT] * ncol for i in range(nrow)]
    # Starting in the correct location for character #1, bit 8,...
    char = 0
    row = 4
    col = 0
    while True:

        # first check for one of the special corner cases, then...
        if (row == nrow) and (col == 0):
            char += place_square(0, array, nrow, ncol, nrow, ncol, data[char])
        elif (row == nrow - 2) and (col == 0) and (ncol % 4):
            char += place_square(1, array, nrow, ncol, nrow, ncol, data[char])
        elif (row == nrow - 2) and (col == 0) and (ncol % 8 == 4):
            char += place_square(2, array, nrow, ncol, nrow, ncol, data[char])
        elif (row == nrow + 4) and (col == 2) and ((ncol % 8) == 0):
            char += place_square(3, array, nrow, ncol, nrow, ncol, data[char])

        # sweep upward diagonally, inserting successive characters,...
        while (row >= 0) and (col < ncol):
            if (row < nrow) and (col >= 0) and (array[row][col] == INVALID_BIT):
                char += place_square(-1, array, nrow, ncol, row, col, data[char])
            row -= 2
            col += 2

        row += 1
        col += 3

        # & then sweep downward diagonally, inserting successive characters,...
        while (row < nrow) and (col >= 0):
            if (row >= 0) and (col < ncol) and (array[row][col] == INVALID_BIT):
                char += place_square(-1, array, nrow, ncol, row, col, data[char])
            row += 2
            col -= 2

        row += 3
        col += 1

        # ... until the entire array is scanned
        if not ((row < nrow) or (col < ncol)):
            break

    # Lastly, if the lower righthand corner is untouched, fill in fixed pattern */
    if array[nrow - 1][ncol - 1] == INVALID_BIT:
        array[nrow - 1][ncol - 2] = 0
        array[nrow - 1][ncol - 1] = 1
        array[nrow - 2][ncol - 1] = 0
        array[nrow - 2][ncol - 2] = 1

    return array  # return the array of 1"s and 0"s

def add_finder_pattern(array, data_nrow, data_ncol, reg_row, reg_col):
    # get the total size of the datamatrix
    nrow = (data_nrow + 2) * reg_row
    ncol = (data_ncol + 2) * reg_col

    datamatrix = [[0] * ncol for i in range(nrow)]  # initialise and fill with 0"s

    for i in range(reg_col):  # for each column of data regions
        for j in range(nrow):
            datamatrix[j][i * (data_ncol + 2)] = 1  # vertical black bar on left
            datamatrix[j][i * (data_ncol + 2) + data_ncol + 1] = j % 2  # alternating blocks

    for i in range(reg_row):  # for each row of data regions
        for j in range(ncol):
            datamatrix[i * (data_nrow + 2) + data_nrow + 1][j] = 1  # horizontal black bar at bottom
            datamatrix[i * (data_nrow + 2)][j] = (j + 1) % 2  # alternating blocks

    for i in range(data_nrow * reg_row):
        for j in range(data_ncol * reg_col):
            # offset by 1, plus two for every addition block
            dest_col = j + 1 + 2 * (j // data_ncol)
            dest_row = i + 1 + 2 * (i // data_nrow)

            datamatrix[dest_row][dest_col] = array[i][j]  # transfer from the plain bit array

    return datamatrix

def get_valid_filename(s):
    s = str(s).strip().replace(" ", "_")
    return re.sub(r"(?u)[^-\w.]", "", s)

def splitAt(string, length):
    return ' '.join(string[i:i+length] for i in range(0,len(string),length))

class InventorySticker(inkex.Effect):
    
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--server_address", default="https://the.domain.de/items.csv")
        pars.add_argument("--htuser", default="user")
        pars.add_argument("--htpassword", default="password")
        pars.add_argument("--sticker_ids", default="*")
        pars.add_argument("--target_url", default="qwa.es")
        pars.add_argument("--target_owner", default="Stadtfabrikanten e.V.")
        pars.add_argument("--export_dir", default="/home/")
        pars.add_argument("--flat_export", type=inkex.Boolean, default=False)
        pars.add_argument("--preview", type=inkex.Boolean, default=False)
        pars.add_argument("--export_svg", type=inkex.Boolean, default=True)
        pars.add_argument("--export_png", type=inkex.Boolean, default=False)
        pars.add_argument("--print_png", type=int, default=0)     
        pars.add_argument("--print_device", default="04f9:2044")     
        
    def effect(self):
        globalFont = "Miso"
        misoAvailable = False
        root = Tk()
        for f in font.families():
            if f.lower() == globalFont.lower():
                misoAvailable = True
                break
        if misoAvailable is False:
            inkex.errormsg("Warning: " + globalFont + " Font could not be found. Did you properly install the font? Please note: Stickers will look malformed!")
        
        # Adjust the document view for the desired sticker size
        root = self.svg.getElement("//svg:svg")

        subline_fontsize = 40 #px; one line of bottom text (id and owner) creates a box of that height
          
        #our DataMatrix has size 16x16, each cube is sized by 16x16px -> total size is 256x256px. We use 4px padding for all directions
        DataMatrix_xy = 16
        DataMatrix_height = 16 * DataMatrix_xy
        DataMatrix_width = DataMatrix_height
        sticker_padding = 4
        sticker_height = DataMatrix_height + subline_fontsize + 3 * sticker_padding
        sticker_width = 696
        
        #configure font sizes and box heights to define how large the font size may be at maximum (to omit overflow)
        objectNameMaxHeight = sticker_height - 2 * subline_fontsize - 4 * sticker_padding
        objectNameMaxLines = 5
        objectNameFontSize = objectNameMaxHeight / objectNameMaxLines #px; generate main font size from lines and box size
    
        root.set("width", str(sticker_width) + "px")
        root.set("height", str(sticker_height) + "px")
        root.set("viewBox", "%f %f %f %f" % (0, 0, sticker_width, sticker_height))

        #clean the document (make it blank) to avoid printing duplicated things
        for node in self.document.xpath('//*', namespaces=inkex.NSS):
            if node.TAG not in ('svg', 'defs', 'namedview'):
                node.delete()
            
        #set the document units
        self.document.getroot().find(inkex.addNS("namedview", "sodipodi")).set("inkscape:document-units", "px")

        # Download the recent inventory CSV file and parse line by line to create an inventory sticker
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self.options.server_address, self.options.htuser, self.options.htpassword)
        handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
        opener = urllib.request.build_opener(handler)
               
        try:
            inventoryData = opener.open(self.options.server_address).read().decode("utf-8")
            urllib.request.install_opener(opener)
        
            inventoryCSVParent = os.path.join(self.options.export_dir, "InventorySticker")       
            inventoryCSV = os.path.join(inventoryCSVParent, "inventory.csv")    
           
            # To avoid messing with old stickers we remove the directory on Client before doing something new
            shutil.rmtree(inventoryCSVParent, ignore_errors=True) #remove the output directory before doing new job
                      
            # we are going to write the imported Server CSV file temporarily. Otherwise CSV reader seems to mess with the file if passed directly        
            if not os.path.exists(inventoryCSVParent):
                os.mkdir(inventoryCSVParent)
            with open(inventoryCSV, 'w', encoding="utf-8") as f:
                f.write(inventoryData)
                f.close()
    
            #parse sticker Ids from user input
            if self.options.sticker_ids != "*":
                sticker_ids = self.options.sticker_ids.split(",")
            else:
                sticker_ids = None
            
            with open(inventoryCSV, 'r', encoding="utf-8") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=",")
                
                totalOutputs = 0
                for row in csv_reader:
                    internal_id = row[0]
                    doc_title   = row[1]
                    sticker_id  = row[2]
                    level       = row[3]
                    zone        = row[4]
                    
                    if sticker_ids is None or sticker_id in sticker_ids:
                        totalOutputs += 1
                        #create new sub directories for each non-existent FabLab zone (if flat export is disabled)
                        if self.options.flat_export == False:
                            if not zone:
                                zoneDir = os.path.join(inventoryCSVParent, get_valid_filename("Keinem Bereich zugeordnet"))
                            else:
                                zoneDir = os.path.join(inventoryCSVParent, get_valid_filename(zone)) #remove invalid charaters from zone
                            if not os.path.exists(zoneDir):
                                os.mkdir(zoneDir)
                        else:
                            zoneDir = inventoryCSVParent #use top directory
    
                        #Generate the recent sticker content
                        stickerGroup = self.document.getroot().add(inkex.Group(id="InventorySticker_Id" + sticker_id)) #make a new group at root level
                        DataMatrixStyle = inkex.Style({"stroke": "none", "stroke-width": "1", "fill": "#000000"})
                        DataMatrixAttribs = {"style": str(DataMatrixStyle), "height": str(DataMatrix_xy) + "px", "width": str(DataMatrix_xy) + "px"}
                        
                        # 1 - create DataMatrix (create a 2d list corresponding to the 1"s and 0s of the DataMatrix)
                        encoded = self.encode(self.options.target_url + "/" + sticker_id)
                        DataMatrixGroup = stickerGroup.add(inkex.Group(id="DataMatrix_Id" + sticker_id)) #make a new group at root level
                        for x, y in self.render_data_matrix(encoded, DataMatrix_xy):
                            DataMatrixAttribs.update({"x": str(x + sticker_padding), "y": str(y + sticker_padding)})
                            etree.SubElement(DataMatrixGroup, inkex.addNS("rect","svg"), DataMatrixAttribs)
                        
                        inline_size = sticker_width - DataMatrix_width - 3 * sticker_padding #remaining width for objects next to the DataMatrix  
                        x_pos = DataMatrix_width + 2 * sticker_padding
                    
                        # 2 - Add Object Name Text                      
                        objectName = etree.SubElement(stickerGroup,
                            inkex.addNS("text", "svg"),
                            {
                                "font-size": str(objectNameFontSize) + "px",
                                "x": str(x_pos) + "px",
                                #"xml:space": "preserve", #we cannot add this here because Inkscape throws an error
                                "y": str(objectNameFontSize) + "px",
                                "text-align" : "left", 
                                "text-anchor": "left", 
                                "vertical-align" : "bottom",
                                #style: inline-size required for text wrapping inside box; letter spacing is required to remove the additional whitespaces. The letter spacing depends to the selected font family (Miso)
                                "style": str(inkex.Style({"fill": "#000000", "writing-mode": "horizontal-tb", "inline-size": str(inline_size) + "px", "stroke": "none", "font-family": globalFont, "font-weight": "bold", "letter-spacing": "-3.66px"})) 
                            }
                        )
                        objectName.set("id", "objectName_Id" + sticker_id)
                        objectName.set("xml:space", "preserve") #so we add it here instead .. if multiple whitespaces in text are coming after each other just render them (preserve!)
                        objectNameTextSpan = etree.SubElement(objectName, inkex.addNS("tspan", "svg"), {})
                        objectNameTextSpan.text = splitAt(doc_title, 1) #add 1 whitespace after each chacter. So we can simulate a in-word line break (break by char instead by word)
                    
                        # 3 - Add Object Id Text - use the same position but revert text anchors/align
                        objectId = etree.SubElement(stickerGroup,
                            inkex.addNS("text", "svg"),
                            {
                                "font-size": str(subline_fontsize) + "px",
                                "x": str(sticker_padding) + "px",
                                "y": "30px",
                                "transform": "translate(0," + str(sticker_height - subline_fontsize) + ")",
                                "text-align" : "left", 
                                "text-anchor": "left", 
                                "vertical-align" : "bottom",
                                "style": str(inkex.Style({"fill": "#000000", "inline-size":str(inline_size) + "px", "stroke": "none", "font-family": globalFont, "font-weight": "bold"})) #inline-size required for text wrapping
                            }
                        )
                        objectId.set("id", "objectId_Id" + sticker_id)
                        objectIdTextSpan = etree.SubElement(objectId, inkex.addNS("tspan", "svg"), {})
                        objectIdTextSpan.text = "Thing #" + sticker_id
          
                        # 4 - Add Owner Text
                        owner = etree.SubElement(stickerGroup,
                            inkex.addNS("text", "svg"),
                            {
                                "font-size": str(subline_fontsize) + "px",
                                "x": str(x_pos) + "px",
                                "y": "30px",
                                "transform": "translate(0," + str(sticker_height - subline_fontsize) + ")",
                                "text-align" : "right", 
                                "text-anchor": "right", 
                                "vertical-align" : "bottom",
                                "style": str(inkex.Style({"fill": "#000000", "inline-size":str(inline_size) + "px", "stroke": "none", "font-family": globalFont, "font-weight": "300"})) #inline-size required for text wrapping
                            }
                        )
                        owner.set("id", "owner_Id" + sticker_id)
                        ownerTextSpan = etree.SubElement(owner, inkex.addNS("tspan", "svg"), {})
                        ownerTextSpan.text = self.options.target_owner

                        # 5 - Add Level Text
                        levelText = etree.SubElement(stickerGroup,
                            inkex.addNS("text", "svg"),
                            {
                                "font-size": str(subline_fontsize) + "px",
                                "x": str(x_pos) + "px",
                                "y": "30px",
                                "transform": "translate(0," + str(sticker_height - subline_fontsize - subline_fontsize) + ")",
                                "text-align" : "right", 
                                "text-anchor": "right", 
                                "vertical-align" : "bottom",
                                "style": str(inkex.Style({"fill": "#000000", "inline-size":str(inline_size) + "px", "stroke": "none", "font-family": globalFont, "font-weight": "bold"})) #inline-size required for text wrapping
                            }
                        )
                        levelText.set("id", "level_Id" + sticker_id)
                        levelTextTextSpan = etree.SubElement(levelText, inkex.addNS("tspan", "svg"), {})
                        levelTextTextSpan.text = level
                   
                        # 6 - Add horizontal divider line
                        line_thickness = 2 #px
                        line_x_pos = 350 #px; start of the line (left coord)
                        line_length = sticker_width - line_x_pos
                        divider = etree.SubElement(stickerGroup,
                            inkex.addNS("path", "svg"),
                            {
                                "d": "m " + str(line_x_pos) + "," + str(sticker_height - subline_fontsize - subline_fontsize) + " h " + str(line_length) ,
                                "style": str(inkex.Style({"fill": "none", "stroke": "#000000", "stroke-width": str(line_thickness) + "px", "stroke-linecap": "butt", "stroke-linejoin":"miter", "stroke-opacity": "1"})) #inline-size required for text wrapping
                            }
                        )
                        divider.set("id", "divider_Id" + sticker_id)
                    
                        if self.options.preview == False:
                            export_file_name = sticker_id + "_" + get_valid_filename(doc_title)
                            export_file_path = os.path.join(zoneDir, export_file_name)
                           
                            #"Export" as SVG by just copying the recent SVG document to the target directory. We need to remove special characters to have valid file names on Windows/Linux
                            export_file_svg = open(export_file_path + ".svg", "w", encoding="utf-8")
                            export_file_svg.write(str(etree.tostring(self.document), "utf-8"))
                            export_file_svg.close() 
                                
                            if self.options.export_png == False and self.options.export_svg == False:
                                inkex.errormsg("Nothing to export. Generating preview only ...")
                                break
                                
                            if self.options.export_png == True: #we need to generate SVG before to get PNG. But if user selected PNG only we need to remove SVG afterwards
                                #Make PNG from SVG (slow because each file is picked up separately. Takes about 10 minutes for 600 files                        
                                inkscape(export_file_path + ".svg", actions="export-dpi:96;export-background:white;export-filename:{file_name};export-do;FileClose".format(file_name=export_file_path + ".png"))
      
                            #fix for "usb.core.USBError: [Errno 13] Access denied (insufficient permissions)"
                            #echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="04f9", ATTR{idProduct}=="2044", MODE="666"' > /etc/udev/rules.d/99-garmin.rules && sudo udevadm trigger
                            if self.options.print_png > 0:
                                if self.options.export_png == False:
                                    inkex.errormsg("No file output for printing. Please set 'Export PNG' to true first.")
                                else:
                                    for x in range(self.options.print_png):
                                        command = "brother_ql -m QL-720NW --backend pyusb --printer usb://" + self.options.print_device + " print -l 62 --600dpi -r auto " + export_file_path + ".png"
                                        p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE) #forr Windows: shell=False
                                        stdout, stderr = p.communicate()
                                        p.wait()
                                        if p.returncode != 0:
                                            std_out = stdout.decode('utf-8')
                                            std_err = stderr.decode('utf-8')
                                            if std_err.endswith("ValueError: Device not found\n") is True:
                                                self.msg("Printer device not found or offline. Check for power, cables and entered printer interface ID")
                                            else:
                                                inkex.errormsg("brother_ql returned errors:\nError code {:d}\n{}\n{}".format(p.returncode, std_out, std_err))

                            if self.options.export_svg != True: #If user selected PNG only we need to remove SVG again
                                os.remove(export_file_path + ".svg")
                             
                            self.document.getroot().remove(stickerGroup) #remove the stickerGroup again
                        else: #create preview by just breaking the for loop without executing remove(stickerGroup)
                            break
                csv_file.close() 
                if totalOutputs == 0:
                    self.msg("No output was generated. Check if your entered IDs are valid!")
        except Exception as e:
            inkex.errormsg(e)
            #inkex.errormsg("Wrong inventory.csv URL or invalid credentials for Basic Auth")

    # parameters for the selected datamatrix size
    #   drow        number of rows in each data region
    #   dcol        number of cols in each data region
    #   reg_row     number of rows of data regions
    #   reg_col     number of cols of data regions
    #   nd          number of data codewords per reed-solomon block
    #   nc          number of ECC codewords per reed-solomon block
    #   inter       number of interleaved Reed-Solomon blocks
    def encode(self, text, nrow = 16, ncol = 16, data_nrow = 14, data_ncol = 14, reg_row = 1, reg_col = 1, nd = 12, nc = 12, inter = 1):
        """
        Take an input string and convert it to a sequence (or sequences)
        of codewords as specified in ISO/IEC 16022:2006 (section 5.2.3)
        """
        # generate the codewords including padding and ECC
        codewords = get_codewords(text, nd, nc, inter, nrow == 144)

        # break up into separate arrays if more than one DataMatrix is needed
        module_arrays = []
        for codeword_stream in codewords:  # for each datamatrix
            # place the codewords" bits across the array as modules
            bit_array = place_bits(codeword_stream, data_nrow * reg_row, data_ncol * reg_col)
            # add finder patterns around the modules
            module_arrays.append(add_finder_pattern(bit_array, data_nrow, data_ncol, reg_row, reg_col))

        return module_arrays

    def render_data_matrix(self, module_arrays, size):
        """turn a 2D array of 1"s and 0"s into a set of black squares"""
        spacing = 16 * size * 1.5
        for i, line in enumerate(module_arrays):
            height = len(line)
            width = len(line[0])

            for y in range(height):  # loop over all the modules in the datamatrix
                for x in range(width):
                    if line[y][x] == 1:  # A binary 1 is a filled square
                        yield (x * size + i * spacing, y * size)
                    elif line[y][x] == INVALID_BIT:  # we have an invalid bit value
                        inkex.errormsg("Invalid bit value, {}!".format(line[y][x]))

if __name__ == "__main__":
    InventorySticker().run()

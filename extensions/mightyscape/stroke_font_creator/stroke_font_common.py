#!/usr/bin/env python3

'''
Defintion of Common functions and variables used by stroke font extensions

Copyright (C) 2019  Shrinivas Kulkarni

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''

import sys, os, fileinput, re, locale
from inkex import errormsg, addNS, NSS
from xml.dom.minidom import parse, Document
from math import ceil
from lxml import etree
from inkex import Style, Boolean
from inkex.paths import Path, CubicSuperPath, Transform
from inkex import bezier

# sys path already includes the module folder
from stroke_font_manager import CharData, getFontNames, xAscent, \
    xDescent, xCapHeight, xXHeight, xSpaceROff, xFontId, xSize

class CommonDefs:
    # inx filed that have the font list to be synchronized
    inxFilesWithDynFont = ['render_stroke_font_text.inx', 'edit_stroke_font.inx']

    vgScaleFact = 2.
    lineT = .005

    idAttribName = 'id'
    hGuideIDPrefix = 'h_'
    lvGuideIDPrefix = 'lv_'
    rvGuideIDPrefix = 'rv_'

    fontOtherInfo = 'otherInfo'

    encoding = sys.stdin.encoding
    if(encoding == 'cp0' or encoding is None):
        encoding = locale.getpreferredencoding()

def getPartsFromCubicSuper(csp):
    parts = []
    for subpath in csp:
        part = []
        prevBezPt = None            
        for i, bezierPt in enumerate(subpath):
            if(prevBezPt != None):
                seg = [prevBezPt[1], prevBezPt[2], bezierPt[0], bezierPt[1]]
                part.append(seg)
            prevBezPt = bezierPt
        parts.append(part)
    return parts

def formatStyle(styleStr):
    return str(Style(styleStr))


def getCubicSuperPath(d = None):
    if(d == None): return CubicSuperPath([])
    return CubicSuperPath(Path(d).to_superpath())
def getCubicLength(csp):
    return bezier.csplength(csp)[1]


def getCubicBoundingBox(csp):
    bbox = csp.to_path().bounding_box()
    return bbox.left, bbox.right, bbox.top, bbox.bottom

def formatSuperPath(csp):
    return csp.__str__()


def getParsedPath(d):
    return [[seg.letter, list(seg.args)] for seg in Path(d).to_absolute()]

def applyTransform(mat, csp):
    csp.transform(mat)


def getTranslatedPath(d, posX, posY):
    path = Path(d)
    path.translate(posX, posY, inplace = True)
    return path.to_superpath().__str__()

def getTransformMat(matAttr):
    return Transform(matAttr)

def getCurrentLayer(effect):
    return effect.svg.get_current_layer()


def getViewCenter(effect):
    return effect.svg.namedview.center

def computePtInNode(vc, layer):
    return (-layer.transform).apply_to_point(vc)

def getSelectedElements(effect):
    return effect.svg.selected


def getEtree():
    return  etree

def getAddFnTypes(effect):
    addFn = effect.arg_parser.add_argument
    typeFloat = float
    typeInt = int
    typeString = str
    typeBool = Boolean

    return addFn, typeFloat, typeInt, typeString, typeBool

def runEffect(effect):
    effect.run()
    
def getDecodedChars(chars):
    return chars

def indentStr(cnt):
    ostr = ''
    for i in range(0, cnt):
        ostr += ' '
    return ostr

def getXMLItemsStr(sectMarkerLine, sectMarker, fontNames):
    lSpaces = sectMarkerLine.find(sectMarker)
    outStr = indentStr(lSpaces) + sectMarker + ' [start] -->\n'
    for fName in fontNames:
        outStr += indentStr(lSpaces + 4) + '<item value="' + fName + '">' + fName + '</item>\n'
    outStr += indentStr(lSpaces) + sectMarker + ' [end] -->\n'
    return outStr

def syncFontList(extPath):
    sectMarker = '<!-- ##! dynamically generated portion'

    sectMarkerLine = None
    xmlFilePaths = [extPath + "/" +  f for f in CommonDefs.inxFilesWithDynFont]

    try:
        fontNames = getFontNames(extPath)
        for xf in xmlFilePaths:
            for line in fileinput.input(xf, inplace = True):
                if sectMarker in line:
                    if(sectMarkerLine != None):
                        eval("print(getXMLItemsStr(sectMarkerLine, sectMarker, fontNames), end = '')")

                        sectMarkerLine = None
                    else:
                        sectMarkerLine = line
                else:
                    if(sectMarkerLine == None):
                        eval("print(line, end = '')")

    except Exception as e:
        errormsg('Error updating font list...\n' + str(e))

def addGridLine(layer, posX, posY, length, lType, style, attribs):
    line = etree.Element(addNS('path','svg'))
    d = 'M '+str(posX) + ' ' + str(posY) +' '+ lType +' '

    if(lType == 'H'):
        d += str(posX + length)
    if(lType == 'V'):
        d += str(posY + length)

    line.set('style', formatStyle(style))
    line.set('d', d)

    for key in attribs:
        line.set(key, attribs[key])

    layer.append(line)

def addText(layer, textStr, posX, posY, style):
    text = etree.Element(addNS('text','svg'))
    text.text = textStr

    text.set('x', str(posX))
    text.set('y', str(posY))

    text.set('style', formatStyle(style))

    layer.append(text)


def createTempl(callback, effect, extraInfo, rowCnt, glyphCnt, \
    vgScaleFact, createRvGuides, lineT, newCallBackLayerName = None):

        hgStyle = {'stroke-width':str(lineT), 'opacity':'1', 'stroke':'#ff0066'}
        lvgStyle = {'stroke-width':str(lineT), 'opacity':'1', 'stroke':'#00aa88'}
        rvgStyle = {'stroke-width':str(lineT), 'opacity':'1', 'stroke':'#1b46ff'}

        fontSize = extraInfo[xSize]
        spcY = fontSize * 3
        spcX = fontSize * 3

        fontSize = extraInfo[xSize]
        vLineH = fontSize * vgScaleFact

        colCnt = int(ceil(float(glyphCnt) / float(rowCnt)))

        docW = (colCnt + 1) * spcX
        docH = (rowCnt + 1) * spcY

        svg = effect.document.getroot()
        svg.set('width', str(docW))
        svg.set('height', str(docH))

        #Remove viewbox
        if('viewBox' in svg.attrib):
            svg.attrib.pop('viewBox')

        currLayers = svg.xpath('//svg:g', namespaces = NSS)
        for layer in currLayers:
            # Note: getparent()
            parentLayer = layer.getparent()

            if(parentLayer != None):
                parentLayer.remove(layer)

        currExtraElems = svg.xpath('//svg:' + CommonDefs.fontOtherInfo, namespaces = NSS)
        for elem in currExtraElems:
            parentElem = elem.getparent()
            parentElem.remove(elem)

        extraInfoElem = etree.SubElement(svg, CommonDefs.fontOtherInfo)
        extraInfoElem.set(xAscent, str(extraInfo[xAscent]))
        extraInfoElem.set(xDescent, str(extraInfo[xDescent]))
        extraInfoElem.set(xCapHeight, str(extraInfo[xCapHeight]))
        extraInfoElem.set(xXHeight, str(extraInfo[xXHeight]))
        extraInfoElem.set(xSpaceROff, str(extraInfo[xSpaceROff]))
        extraInfoElem.set(xFontId, str(extraInfo[xFontId]))
        extraInfoElem.set(xSize, str(extraInfo[xSize]))

        templLayer = etree.SubElement(svg, 'g')
        templLayer.set(addNS('label', 'inkscape'), 'Guides')
        templLayer.set(addNS('groupmode', 'inkscape'), 'layer')

        if(newCallBackLayerName != None):
            callbackLayer = etree.SubElement(svg, 'g')
            callbackLayer.set(addNS('label', 'inkscape'), newCallBackLayerName)
            callbackLayer.set(addNS('groupmode', 'inkscape'), 'layer')
        else:
            callbackLayer = templLayer

        editLayer = etree.SubElement(svg, 'g')
        editLayer.set(addNS('label', 'inkscape'), 'Glyphs')
        editLayer.set(addNS('groupmode', 'inkscape'), 'layer')
        editLayer.set('id', 'glyph')#TODO: How to make this dynamic?
        view = svg.namedview
        view.set(addNS('current-layer', 'inkscape'), editLayer.get('id'))

        for row in range(0, rowCnt):

            hAttribs = {CommonDefs.idAttribName : CommonDefs.hGuideIDPrefix + str(row)}
            addGridLine(templLayer, 0, \
                (row + 1) * spcY, docW, 'H', hgStyle, hAttribs)

            for col in range(0, colCnt):
                glyphIdx = row * colCnt + col

                if(glyphIdx >= glyphCnt):
                    break

                posX = (col + 1) * spcX
                posY = (row + 1) * spcY# + lineT / 2

                #Caller can create whatever it wants at this position
                rOffset = callback(callbackLayer, editLayer, glyphIdx, posX, posY)
                if(rOffset == None):
                    rOffset = fontSize

                lvAttribs = {CommonDefs.idAttribName : CommonDefs.lvGuideIDPrefix + \
                     str(row).zfill(4) + '_' + str(col).zfill(4)}

                addGridLine(templLayer, \
                    posX, posY + fontSize / 1.5, -vLineH, 'V', \
                        lvgStyle, lvAttribs)

                if(createRvGuides):
                    rvAttribs = {CommonDefs.idAttribName : CommonDefs.rvGuideIDPrefix + \
                        str(row).zfill(4) + '_' + str(col).zfill(4)}

                    addGridLine(templLayer, \
                        posX + rOffset, posY + fontSize / 1.5, -vLineH, 'V', \
                            rvgStyle, rvAttribs)

def getCharStyle(strokeWidth, naChar):
    #na character is a filled box
    naStyle = { 'stroke': '#000000', 'fill': '#000000', 'stroke-width': strokeWidth}
    charStyle = { 'stroke': '#000000', 'fill': 'none', 'stroke-width': strokeWidth,
        'stroke-linecap':'round', 'stroke-linejoin':'round'}

    if(naChar):
        return naStyle
    else:
        return charStyle

class InkscapeCharData(CharData):
    def __init__(self, char, rOffset, pathStr, glyphName):
        self.pathStr = pathStr
        super(InkscapeCharData, self).__init__(char, rOffset, glyphName)

    def getBBox(self):
        return getCubicBoundingBox(getCubicSuperPath(self.pathStr))

    def scaleGlyph(self, scaleX, scaleY):
        self.rOffset *= scaleX
        cspath = getCubicSuperPath(self.pathStr)
        for subpath in cspath:
            for bezierPts in subpath:
                for i in range(0, len(bezierPts)):
                    #No worries about origin...
                    bezierPts[i] = [bezierPts[i][0] * scaleX, bezierPts[i][1] * scaleY]
        self.pathStr = formatSuperPath(cspath)
        self.bbox = getCubicBoundingBox(cspath)

class InkscapeCharDataFactory:
    def __init__(self):
        pass

    def getCharData(self, char, rOffset, pathStr, glyphName):
        return InkscapeCharData(char, rOffset, pathStr, glyphName)

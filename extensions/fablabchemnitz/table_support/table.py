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
import math

import inkex
from inkex import Guide
from lxml import etree
import base_transform
import re

class TableEngine(base_transform.BaseTransform):

    defaultId = 'inkscape-table'
    cell_type_row = 'row'
    cell_type_column = 'column'
    normalizeFactor = 5
    tablesCount = 0
    tables = None
    selectedTables = {}
    mergedCells = {}
    tablesTexts = {}
    get_tables = True
    auto_split = True
    delimiter = ','

    def __init__(self, get_tables = True, auto_split = True):
        inkex.NSS['inkex'] = 'http://sodipodi.sourceforge.net/DTD/inkex-0.dtd'
        self.get_tables = get_tables
        self.auto_split = auto_split
        base_transform.BaseTransform.__init__(self)

    def getTablesCount(self):
        node = self.document.xpath('//inkex:tables', namespaces = inkex.NSS)
        if len(node) == 0:
            xml = '<inkex:tables xmlns:inkex="http://sodipodi.sourceforge.net/DTD/inkex-0.dtd" count="0"/>'
            self.document.getroot().append(etree.fromstring(xml))
            node = self.document.xpath('//inkex:tables', namespaces = inkex.NSS)
        else:
            self.tablesCount = int(node[0].attrib['count'])

        self.tables = node[0]

    def isTableCell(self, id):
        el = self.svg.getElementById(id)
        if (el == None):
            return False

        if (self.isset(el.attrib, inkex.addNS('table-id', 'inkex'))):
            tableId = el.attrib[inkex.addNS('table-id', 'inkex')]
            if (re.search('\\-text$', tableId)):
                return False
            else:
                return True

        return False

    def effect(self):
        self.getTablesCount()
        if (self.get_tables):
            self.getAllTables()
            if (self.auto_split):
                for id, table in self.selectedTables.items():
                    for i in range(len(table)):
                        for j in range(len(table[i])):
                            if (table[i][j] != None):
                                points = self.splitCell(table[i][j])
                                if (points != False):
                                    if (self.isset(self.mergedCells, id)):
                                        self.mergedCells[id].append(points)
                                    else:
                                        self.mergedCells[id] = [points]
                for tableId in self.mergedCells:
                    self.getTable(tableId)
        self.doinkex()
        if (self.get_tables):
            if (self.auto_split):
                for tableId in self.mergedCells:
                    self.getTableText(tableId)
                    for points in self.mergedCells[tableId]:
                        if (not self.isset(points, 'removed')):
                            self.mergeTable(tableId, points)

    def newCell(self, x, y, width, height, id, i, j, transform = None):
        #path = '//*[@inkex:table-id="%s"]' % id
        _id = self.svg.get_unique_id(id)
        etree.SubElement(self.svg.get_current_layer(), 'rect', {
            'id': _id,
            'style': 'fill:none;stroke:#000000;stroke-width:1px;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none',
            'width': str(width) + 'px',
            'height': str(height) + 'px',
            'x': str(x) + 'px',
            'y': str(y) + 'px',
            inkex.addNS('table-id', 'inkex'): id,
            inkex.addNS('row', 'inkex'): str(i),
            inkex.addNS('column', 'inkex'): str(j)
        })

        if (transform != None):
            el = self.svg.getElementById(_id)
            el.set('transform', transform)

        return _id

        '''
        _id = self.svg.get_unique_id(id)
        content = '<rect style="fill:none;stroke:#000000;stroke-width:1px;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none"\n\
                id="' + _id + '"\n\
                width="' + str(width) + '"\n\
                height="' + str(height) + '"\n\
                x="' + str(x) + '"\n\
                y="' + str(y) + '"\n\
                />'

        self.svg.get_current_layer().append(etree.XML(content))
        el = self.svg.getElementById(_id)
        el.set(inkex.addNS('table-id', 'inkex'), id)
        el.set(inkex.addNS('row', 'inkex'), str(i))
        el.set(inkex.addNS('column', 'inkex'), str(j))
        '''

    def create(self, width, height, cols, rows):
        tableId = self.defaultId + str(self.tablesCount)
        self.tablesCount += 1
        self.tables.set('count', str(self.tablesCount))
        content = '<inkex:table xmlns:inkex="http://sodipodi.sourceforge.net/DTD/inkex-0.dtd" table-id="' + tableId + '" rows="' + str(rows) + '" columns="' + str(cols) + '"/>'
        self.tables.append(etree.fromstring(content))

        width = self.sizeToPx(width, 'x')
        height = self.sizeToPx(height, 'y')

        x = 0
        y = 0

        content = ''

        for i in range(rows):
            x = 0
            for j in range(cols):
                self.newCell(x, y, width, height, tableId, i, j)
                x += width
            y += height

    def getTree(self, id):
        ids = [id]
        el = self.svg.getElementById(id)
        for _el in list(el):
            for _id in self.getTree(_el.attrib['id']):
                ids.append(_id)
        return ids


    def getSubSelectedIds(self):
        ids = []
        for id in self.svg.selected.ids:
            for _id in self.getTree(id):
                ids.append(_id)
        return ids

    def getAllTables(self):
        ids = self.getSubSelectedIds()
        for id in ids:
            el = self.svg.getElementById(id)
            if (self.isTableCell(id)):
                tableId = el.attrib[inkex.addNS('table-id', 'inkex')]
                if (not self.isset(self.selectedTables, tableId)):
                    self.getTable(tableId)
                    self.tablesTexts[tableId] = self.getTableText(tableId)

    def getTableDimensions(self, tableId):
        nodes = self.tables.xpath('//inkex:table[@table-id="' + tableId + '"]', namespaces = inkex.NSS)
        if (len(nodes) > 0):
            return {'rows': int(nodes[0].attrib['rows']), 'cols': int(nodes[0].attrib['columns'])}
        return False

    def setTableDimensions(self, tableId, dimensions):
        table_dim = self.tables.xpath('//inkex:table[@table-id="' + tableId + '"]', namespaces = inkex.NSS)
        if (len(table_dim) > 0):
            table_dim[0].set('rows', str(dimensions['rows']))
            table_dim[0].set('columns', str(dimensions['cols']))


    def getTable(self, tableId):
        nodes = self.tables.xpath('//inkex:table[@table-id="' + tableId + '"]', namespaces = inkex.NSS)
        if (len(nodes) > 0):
            cols = int(nodes[0].attrib['columns'])
            rows = int(nodes[0].attrib['rows'])
            table = [[None for i in range(cols)] for j in range(rows)]
            path = '//*[@inkex:table-id="' + tableId + '"]'
            cells = self.document.xpath(path, namespaces = inkex.NSS)
            for cell in cells:
                i = int(cell.attrib[inkex.addNS('row', 'inkex')])
                j = int(cell.attrib[inkex.addNS('column', 'inkex')])
                table[i][j] = cell.attrib['id']
            self.selectedTables[tableId] = table

    def getTableText(self, tableId):
        nodes = self.tables.xpath('//inkex:table[@table-id="' + tableId + '"]', namespaces = inkex.NSS)
        if (len(nodes) > 0):
            cols = int(nodes[0].attrib['columns'])
            rows = int(nodes[0].attrib['rows'])
            texts = [[None for i in range(cols)] for j in range(rows)]
            path = '//*[@inkex:table-id="' + tableId + '-text"]'
            cells = self.document.xpath(path, namespaces = inkex.NSS)
            for cell in cells:
                i = int(cell.attrib[inkex.addNS('row', 'inkex')])
                j = int(cell.attrib[inkex.addNS('column', 'inkex')])
                texts[i][j] = cell.attrib['id']
            return texts
        return None

    def doAddGuide(self, el, type):
        px = self.sizeToPx(str(self.svg.unittouu(self.document.getroot().attrib['height'])), 'y')

        position = self.getPosition(el)
        if (position != False):
            c = position['coordinates']
            a = position['matrix']
            x = c[0]
            y = c[1]
            angle = math.acos(a[0][0]) * 180 / math.pi
            if angle < 90:
                angle = 90 - angle
            elif angle < 180:
                angle = 180 - angle
            elif angle < 270:
                angle = 270 - angle
            else:
                angle = 360 - angle
            if (type == self.cell_type_row):
                angle += 90
            self.svg.namedview.add(Guide().move_to(str(x), str(px - y), angle))
            
    def _addGuides(self, tableId, type):
        table = self.selectedTables[tableId]
        
        count = len(table)
        if (type == self.cell_type_column):
            count = len(table[0])

        for i in range(count):
            _i = i
            _j = 0
            if (type == self.cell_type_column):
                _i = 0
                _j = i
            el = self.svg.getElementById(table[_i][_j])
            self.doAddGuide(el, type)

            if (i == count - 1):
                if (type == self.cell_type_column):
                    el.attrib['x'] = str(self.sizeToPx(el.attrib['x'], 'x') + self.sizeToPx(el.attrib['width'], 'x'))
                else:
                    el.attrib['y'] = str(self.sizeToPx(el.attrib['y'], 'y') + self.sizeToPx(el.attrib['height'], 'y'))
                self.doAddGuide(el, type)
                if (type == self.cell_type_column):
                    el.attrib['x'] = str(self.sizeToPx(el.attrib['x'], 'x') - self.sizeToPx(el.attrib['width'], 'x'))
                else:
                    el.attrib['y'] = str(self.sizeToPx(el.attrib['y'], 'y') - self.sizeToPx(el.attrib['height'], 'y'))

    def addGuides(self, type):
        for tableId in self.selectedTables:
            self._addGuides(tableId, type)

    def doEditText(self, id, fontSize):
        el = self.svg.getElementById(id)
        if (not self.isTableCell(id)):
            return

        position = self.getPosition(el)
        if (position != False):
            a = position['matrix']
            if (not self.isUnitMatrix(a)):
                transform = 'transform="' + self.matrix2string(a) + '"'
            else:
                transform = ''
            content = '<flowRoot id="' + self.svg.get_unique_id(el.attrib[inkex.addNS('table-id', 'inkex')]) + '" xmlns:inkex="http://sodipodi.sourceforge.net/DTD/inkex-0.dtd" ' + transform + ' \
            inkex:table-id="' + el.attrib[inkex.addNS('table-id', 'inkex')]  + '-text" inkex:row="' + el.attrib[inkex.addNS('row', 'inkex')] + '" inkex:column="' + el.attrib[inkex.addNS('column', 'inkex')] + '" \
            style="font-size:' + fontSize + ';font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;text-align:start;line-height:125%;letter-spacing:0px;word-spacing:0px;text-anchor:start;fill:#000000;fill-opacity:1;stroke:none;font-family:Sans;-inkscape-font-specification:Sans"\
            xml:space="preserve"><flowRegion id="' + self.svg.get_unique_id(el.attrib[inkex.addNS('table-id', 'inkex')]) + '"><rect id="' + self.svg.get_unique_id(el.attrib[inkex.addNS('table-id', 'inkex')]) + '" style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;text-align:start;text-anchor:start;font-family:Sans;-inkscape-font-specification:Sans"\
            x="' + el.attrib['x'] + '"\
            y="' + el.attrib['y'] + '"\
            width="' + el.attrib['width'] + '"\
            height="' + el.attrib['height'] + '"/></flowRegion><flowPara id="' + self.svg.get_unique_id(el.attrib[inkex.addNS('table-id', 'inkex')]) + '">text here</flowPara></flowRoot>'

            self.svg.get_current_layer().append(etree.fromstring(content))

    def editText(self, fontSize):
        ids = self.getSubSelectedIds()
        
        for id in ids:
            self.doEditText(id, fontSize)

    def getColumnIndex(self, id):
        el = self.svg.getElementById(id)
        if (self.isset(el.attrib, inkex.addNS('column', 'inkex'))):
            return int(el.attrib[inkex.addNS('column', 'inkex')])

        return -1

    def getRowIndex(self, id):
        el = self.svg.getElementById(id)
        if (self.isset(el.attrib, inkex.addNS('row', 'inkex'))):
            return int(el.attrib[inkex.addNS('row', 'inkex')])

        return -1

    def setTextRect(self, text, c):
        for child in list(text):
            if (child.tag == inkex.addNS('flowRegion', 'svg')):
                for subchild in list(child):
                    if (subchild.tag == inkex.addNS('rect', 'svg')):
                        for key, value in c.items():
                            if value != None:
                                subchild.set(key, str(value))
                break
        
    def getTextRect(self, text):
        for child in list(text):
            if (child.tag == inkex.addNS('flowRegion', 'svg')):
                for subchild in list(child):
                    if (subchild.tag == inkex.addNS('rect', 'svg')):
                        return subchild

        return None

    def moveCells(self, tableId, idx, delta, type):
        table = self.selectedTables[tableId]
        texts = self.tablesTexts[tableId]
        if (type == self.cell_type_column):
            starti = 0
            startj = idx
        else:
            starti = idx
            startj = 0

        for i in range(starti, len(table)):
            for j in range(startj, len(table[i])):
                el = self.svg.getElementById(table[i][j])
                position = self.getPosition(el)
                if (position != False):
                    c = [self.sizeToPx(el.attrib['x'], 'x'), self.sizeToPx(el.attrib['y'], 'y')]
                    c[0] += delta[0]
                    c[1] += delta[1]
                    el.set('x', str(c[0]))
                    el.set('y', str(c[1]))
                    if (texts != None):
                        if (texts[i][j] != None):
                            el = self.svg.getElementById(texts[i][j])
                            rect = self.getTextRect(el)
                            if (rect != None):
                                c[0] = self.sizeToPx(rect.attrib['x'], 'x') + delta[0]
                                c[1] = self.sizeToPx(rect.attrib['y'], 'y') + delta[1]
                            self.setTextRect(el, {'x': c[0], 'y': c[1]})

    def setCellSize(self, tableId, idx, size, type):
        table = self.selectedTables[tableId]
        texts = self.tablesTexts[tableId]
        if (type == self.cell_type_column):
            size = self.sizeToPx(size, 'x')
            old_size = self.sizeToPx(self.svg.getElementById(table[0][idx]).attrib['width'], 'x')
        else:
            size = self.sizeToPx(size, 'y')
            old_size = self.sizeToPx(self.svg.getElementById(table[idx][0]).attrib['height'], 'y')
            
        if (type == self.cell_type_column):
            delta = [size - old_size, 0, 1]
        else:
            delta = [0, size - old_size, 1]
            
        if ((idx + 1 < len(table) and type == self.cell_type_row) or (idx + 1 < len(table[0]) and type == self.cell_type_column)):
            self.moveCells(tableId, idx + 1, delta, type)

        count = len(table[idx])
        if (type == self.cell_type_column):
            count = len(table)

        for i in range(count):
            _i = idx
            _j = i
            if type == self.cell_type_column:
                _i = i
                _j = idx
            el = self.svg.getElementById(table[_i][_j])
            param = 'height'
            if (type == self.cell_type_column):
                param = 'width'

            el.set(param, str(size))

            if texts != None:
                if texts[_i][_j] != None:
                    el = self.svg.getElementById(texts[_i][_j])
                    self.setTextRect(el, {param: size})

    def editSize(self, size, type):
        processed = {}
        for node in self.svg.selected.values():
            id = node.get('id')
            if (self.isTableCell(id)):
                tableId = node.attrib[inkex.addNS('table-id', 'inkex')]
                if (type == self.cell_type_column):
                    idx = self.getColumnIndex(id)
                else:
                    idx = self.getRowIndex(id)
                if (not self.isset(processed, tableId)):
                    processed[tableId] = []

                if (not self.isset(processed[tableId], idx)):
                    self.setCellSize(tableId, idx, size, type)
                    processed[tableId].append(idx)

    def getTableWidth(self, tableId):
        table = self.selectedTables[tableId]
        width = 0
        for i in range(len(table[0])):
            el = self.svg.getElementById(table[0][i])
            width += self.sizeToPx(el.attrib['width'], 'x')

        return width

    def getTableHeight(self, tableId):
        table = self.selectedTables[tableId]
        height = 0
        for i in range(len(table)):
            el = self.svg.getElementById(table[i][0])
            height += self.sizeToPx(el.attrib['height'], 'y')

        return height

    def setTableSize(self, tableId, size, type):
        if (type == self.cell_type_column):
            size = self.sizeToPx(size, 'x')
            old_size = self.getTableWidth(tableId)
        else:
            size = self.sizeToPx(size, 'y')
            old_size = self.getTableHeight(tableId)

        factor = size / old_size
        table = self.selectedTables[tableId]
        count = len(table)
        if (type == self.cell_type_column):
            count = len(table[0])
        
        for i in range(count):
            if (type == self.cell_type_column):
                el = self.svg.getElementById(table[0][i])
                new_size = self.sizeToPx(el.attrib['width'], 'x') * factor
            else:
                el = self.svg.getElementById(table[i][0])
                new_size = self.sizeToPx(el.attrib['height'], 'y') * factor
            self.setCellSize(tableId, i, str(new_size), type)

    def editTable(self, width, height):
        for id in self.selectedTables:
            self.setTableSize(id, width, self.cell_type_column)
            self.setTableSize(id, height, self.cell_type_row)

    def getTablePosition(self, tableId):
        table = self.selectedTables[tableId]
        el = self.svg.getElementById(table[0][0])
        return self.getPosition(el)

    def fitPage(self):
        width = str(self.svg.unittouu(self.document.getroot().attrib['width']))
        height = str(self.svg.unittouu(self.document.getroot().attrib['height']))
        
        for id in self.selectedTables:
            position = self.getTablePosition(id)
            if (position != False):
                c = position['coordinates']
                self.moveCells(id, 0, [-c[0], -c[1], 1], type)
                self.setTableSize(id, width, self.cell_type_column)
                self.setTableSize(id, height, self.cell_type_row)

    def fitPageWidth(self):
        width = str(self.svg.unittouu(self.document.getroot().attrib['width']))

        for id in self.selectedTables:
            position = self.getTablePosition(id)
            if (position != False):
                c = position['coordinates']
                self.moveCells(id, 0, [-c[0], 0, 1], type)
                self.setTableSize(id, width, self.cell_type_column)
                
    def fitPageHeight(self):
        height = str(self.svg.unittouu(self.document.getroot().attrib['height']))

        for id in self.selectedTables:
            position = self.getTablePosition(id)
            if (position != False):
                c = position['coordinates']
                self.moveCells(id, 0, [0, -c[1], 1], type)
                self.setTableSize(id, height, self.cell_type_row)

    def getSelectedListIds(self):
        idList = []
        for id in self.getSubSelectedIds():
            idList.append(id)
        return idList

    def getCellText(self, tableId, i, j):
        texts = self.tablesTexts[tableId]
        if (texts != None):
            if (texts[i][j] != None):
                return self.svg.getElementById(texts[i][j])
        return None

    def getMergePoints(self, tableId):
        dim = self.getTableDimensions(tableId)
        table = self.selectedTables[tableId]
        idList = self.getSelectedListIds()
        start = []
        for i in range(dim['rows']):
            for j in range(dim['cols']):
                if (idList.count(table[i][j]) > 0):
                    start = [i, j]
                    break
            if len(start) > 0:
                break

        if (len(start) != 2):
            return False

        end = [1, 1]

        for i in range(start[0] + 1, len(table)):
            if (idList.count(table[i][start[1]]) > 0):
                end[0] += 1
            else:
                break

        for i in range(start[1] + 1, len(table[0])):
            if (idList.count(table[start[0]][i]) > 0):
                end[1] += 1
            else:
                break

        for i in range(start[0], start[0] + end[0]):
            for j in range(start[1], start[1] + end[1]):
                if (idList.count(table[i][j]) == 0):
                    return False

        return {'i': start[0], 'j': start[1], 'rows': end[0], 'cols': end[1]}

    def mergeTable(self, tableId, points = None):
        if (points == None):
            points = self.getMergePoints(tableId)
            if (points == False):
                inkex.errormsg('You have to select the cells to form a rectangle from a single table.')
                return

        table = self.selectedTables[tableId]
        cell = self.svg.getElementById(table[points['i']][points['j']])
        width = 0
        height = 0
        widths = ''
        heights = ''

        for i in range(points['i'], points['i'] + points['rows']):
            el = self.svg.getElementById(table[i][points['j']])
            height += self.sizeToPx(el.attrib['height'], 'y')
            if (heights != ''):
                heights += self.delimiter
            heights += el.attrib['height']

        for j in range(points['j'], points['j'] + points['cols']):
            el = self.svg.getElementById(table[points['i']][j])
            width += self.sizeToPx(el.attrib['width'], 'x')
            if (widths != ''):
                widths += self.delimiter
            widths += el.attrib['width']

        for i in range(points['i'], points['i'] + points['rows']):
            for j in range(points['j'], points['j'] + points['cols']):
                if (i != points['i'] or j != points['j']):
                    el = self.svg.getElementById(table[i][j])
                    el.getparent().remove(el)
                    text = self.getCellText(tableId, i, j)
                    if (text != None):
                        text.getparent().remove(text)

        cell.set('width', str(width) + 'px')
        cell.set('height', str(height) + 'px')
        cell.set(inkex.addNS('merged', 'inkex'), str(points['rows']) + self.delimiter + str(points['cols']))
        cell.set(inkex.addNS('merged-columns-widths', 'inkex'), widths)
        cell.set(inkex.addNS('merged-rows-heights', 'inkex'), heights)

        text = self.getCellText(tableId, points['i'], points['j'])

        if (text != None):
            rect = self.getTextRect(text)
            rect.set('width', str(width) + 'px')
            rect.set('height', str(height) + 'px')


    def mergeMerge(self):
        for id in self.selectedTables:
            self.mergeTable(id)

    def splitCell(self, cellId):
        cell = self.svg.getElementById(cellId)
        if (self.isset(cell.attrib, inkex.addNS('merged', 'inkex'))):
            tableId = cell.attrib[inkex.addNS('table-id', 'inkex')]
            row = int(cell.attrib[inkex.addNS('row', 'inkex')])
            column =  int(cell.attrib[inkex.addNS('column', 'inkex')])
            position = self.getPosition(cell)

            merge_size = cell.attrib[inkex.addNS('merged', 'inkex')].split(self.delimiter)
            widths = cell.attrib[inkex.addNS('merged-columns-widths', 'inkex')].split(self.delimiter)
            heights = cell.attrib[inkex.addNS('merged-rows-heights', 'inkex')].split(self.delimiter)

            y = self.sizeToPx(cell.attrib['y'], 'y')

            for i in range(row, row + int(merge_size[0])):
                x = self.sizeToPx(cell.attrib['x'], 'x')
                for j in range(column, column + int(merge_size[1])):
                    if (i != row or j != column):
                        transform = None
                        if position != False:
                            a = position['matrix']
                            if (not self.isUnitMatrix(a)):
                                transform = self.matrix2string(a)
                        self.newCell(x, y, self.sizeToPx(widths[j - column], 'x'), self.sizeToPx(heights[i - row], 'y'), tableId, i, j, transform)
                    x += self.sizeToPx(widths[j - column], 'x')
                y += self.sizeToPx(heights[i - row], 'y')

            result = {'i': row, 'j': column, 'rows': int(merge_size[0]), 'cols': int(merge_size[1])}
            cell.set('width', widths[0])
            cell.set('height', heights[0])
            text = self.getCellText(tableId, row, column)
            if (text != None):
                rect = self.getTextRect(text)
                rect.set('width', widths[0])
                rect.set('height', heights[0])
            del cell.attrib[inkex.addNS('merged', 'inkex')]
            del cell.attrib[inkex.addNS('merged-columns-widths', 'inkex')]
            del cell.attrib[inkex.addNS('merged-rows-heights', 'inkex')]

            return result
        return False

    def mergeSplit(self):
        for id in self.svg.selected.ids:
            self.splitCell(id)

    def updateMergedPoints(self, tableId, idx, delta, type):
        if (self.get_tables):
            if (self.auto_split):
                if (self.isset(self.mergedCells, tableId)):
                    for points in self.mergedCells[tableId]:
                        cond1 = idx > points['i'] and idx < points['i'] + points['rows']
                        cond2 = idx <= points['i']
                        if (type == self.cell_type_column):
                            cond1 = idx > points['j'] and idx < points['j'] + points['cols']
                            cond2 = idx <= points['j']

                        if (cond1):
                            if (type == self.cell_type_column):
                                points['cols'] += delta
                                if (points['cols'] <= 1):
                                    points['removed'] = 1
                            else:
                                points['rows'] += delta
                                if (points['rows'] <= 1):
                                    points['removed'] = 1
                        elif (cond2):
                            if (type == self.cell_type_column):
                                if (delta == -1 and idx == points['j']):
                                    points['cols'] += delta
                                    if (points['cols'] <= 1):
                                        points['removed'] = 1
                                else:
                                    points['j'] += delta
                            else:
                                if (delta == -1 and idx == points['i']):
                                    points['rows'] += delta
                                    if (points['rows'] <= 1):
                                        points['removed'] = 1
                                else:
                                    points['i'] += delta

    def incrementCoordonate(self, tableId, idx, inc, type):
        table = self.selectedTables[tableId]
        texts = self.getTableText(tableId)
        starti = idx
        startj = 0
        dim = self.getTableDimensions(tableId)
        if type == self.cell_type_column:
            dim['cols'] += inc
        else:
            dim['rows'] += inc
        self.setTableDimensions(tableId, dim)
        
        if (type == self.cell_type_column):
            starti = 0
            startj = idx

        for i in range(starti, len(table)):
            for j in range(startj, len(table[i])):
                cell = self.svg.getElementById(table[i][j])
                text = self.svg.getElementById(texts[i][j])
                if (type == self.cell_type_column):
                    cell.set(inkex.addNS('column', 'inkex'), str(int(cell.attrib[inkex.addNS('column', 'inkex')]) + inc))
                    if (text != None):
                        text.set(inkex.addNS('column', 'inkex'), str(int(text.attrib[inkex.addNS('column', 'inkex')]) + inc))
                else:
                    cell.set(inkex.addNS('row', 'inkex'), str(int(cell.attrib[inkex.addNS('row', 'inkex')]) + inc))
                    if (text != None):
                        text.set(inkex.addNS('row', 'inkex'), str(int(text.attrib[inkex.addNS('row', 'inkex')]) + inc))

    def addCell(self, tableId, idx, type):
        table = self.selectedTables[tableId]
        if (type == self.cell_type_column):
            if (idx != -1):
                delta = [self.sizeToPx(self.svg.getElementById(table[0][idx]).attrib['width'], 'x'), 0, 1]
            else:
                delta = [self.sizeToPx(self.svg.getElementById(table[0][0]).attrib['width'], 'x'), 0, 1]
        else:
            if (idx != -1):
                delta = [0, self.sizeToPx(self.svg.getElementById(table[idx][0]).attrib['height'], 'y'), 1]
            else:
                delta = [0, self.sizeToPx(self.svg.getElementById(table[0][0]).attrib['height'], 'y'), 1]

        count = len(table)
        if type == self.cell_type_row:
            if (idx != -1):
                count = len(table[idx])
            else:
                count = len(table[0])
        for i in range(count):
            if (type == self.cell_type_column):
                if (idx != -1):
                    cell = self.svg.getElementById(table[i][idx])
                else:
                    cell = self.svg.getElementById(table[i][0])
            else:
                if (idx != -1):
                    cell = self.svg.getElementById(table[idx][i])
                else:
                    cell = self.svg.getElementById(table[0][i])

            position = self.getPosition(cell)
            transform = ''
            if (position != False):
                a = position['matrix']
                if (not self.isUnitMatrix(a)):
                    transform = self.matrix2string(a)
            x = self.sizeToPx(cell.attrib['x'], 'x')
            y = self.sizeToPx(cell.attrib['y'], 'y')
            width = self.sizeToPx(cell.attrib['width'], 'x')
            height = self.sizeToPx(cell.attrib['height'], 'y')

            if (type == self.cell_type_column):
                if (idx != -1):
                    x += width
                self.newCell(x, y, width, height, tableId, i, idx + 1, transform)
            else:
                if (idx != -1):
                    y += height
                self.newCell(x, y, width, height, tableId, idx + 1, i, transform)

        self.moveCells(tableId, idx + 1, delta, type)
        self.updateMergedPoints(tableId, idx + 1, 1, type)
        self.incrementCoordonate(tableId, idx + 1, 1, type)
        self.getTable(tableId)
        self.tablesTexts[tableId] = self.getTableText(tableId)

    def addColumns(self, count, where):
        for id in self.svg.selected.ids:
            el = self.svg.getElementById(id)
            if (self.isTableCell(id)):
                tableId = el.attrib[inkex.addNS('table-id', 'inkex')]
                idx = self.getColumnIndex(id)
                if (where == 'before'):
                    idx -= 1

                for i in range(count):
                    self.addCell(tableId, idx, self.cell_type_column)

    def addRows(self, count, where):
        for id in self.svg.selected.ids:
            el = self.svg.getElementById(id)
            if (self.isTableCell(id)):
                tableId = el.attrib[inkex.addNS('table-id', 'inkex')]
                idx = self.getRowIndex(id)
                if (where == 'before'):
                    idx -= 1

                for i in range(count):
                    self.addCell(tableId, idx, self.cell_type_row)
                    
                break

    def removeCell(self, tableId, idx, type):
        table = self.selectedTables[tableId]
        texts = self.tablesTexts[tableId]
        if (type == self.cell_type_column):
            delta = [-self.sizeToPx(self.svg.getElementById(table[0][idx]).attrib['width'], 'x'), 0, 1]
        else:
            delta = [0, -self.sizeToPx(self.svg.getElementById(table[idx][0]).attrib['height'], 'y'), 1]

        count = len(table)
        if type == self.cell_type_row:
            count = len(table[idx])
            
        for i in range(count):
            if (type == self.cell_type_column):
                cell = self.svg.getElementById(table[i][idx])
                text = self.svg.getElementById(texts[i][idx])
            else:
                cell = self.svg.getElementById(table[idx][i])
                text = self.svg.getElementById(texts[idx][i])

            if (cell != None):
                cell.getparent().remove(cell)
                if (text != None):
                    text.getparent().remove(text)

        self.moveCells(tableId, idx + 1, delta, type)
        self.updateMergedPoints(tableId, idx, -1, type)
        self.incrementCoordonate(tableId, idx + 1, -1, type)
        self.getTable(tableId)
        self.tablesTexts[tableId] = self.getTableText(tableId)

    def removeRowsColumns(self, type):
        for id in self.svg.selected.ids:
            el = self.svg.getElementById(id)
            if (el != None):
                if (self.isTableCell(id)):
                    tableId = el.attrib[inkex.addNS('table-id', 'inkex')]
                    if (type == self.cell_type_column):
                        idx = self.getColumnIndex(id)
                    else:
                        idx = self.getRowIndex(id)

                    self.removeCell(tableId, idx, type)

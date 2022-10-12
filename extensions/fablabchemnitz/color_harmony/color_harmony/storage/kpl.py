
from os.path import join, basename
from PyQt4 import QtGui
from lxml import etree as ET
from zipfile import ZipFile, ZIP_DEFLATED

from color.colors import *
from color import mixers
from palette.storage.storage import *

MIMETYPE = "application/x-krita-palette"
DEFAULT_GROUP_NAME = "Default (root)"

class KplPalette(Storage):
    name = 'kpl'
    title = _("Krita 4.0+ palette format")
    filters = ["*.kpl"]
    can_load = True
    can_save = True

    @staticmethod
    def check(filename):
        try:
            with ZipFile(filename, 'r') as zf:
                mimetype = zf.read("mimetype")
                return (mimetype == MIMETYPE)
        except Exception as e:
            print(e)
            return False

    @staticmethod
    def get_group_names(filename):
        result = [DEFAULT_GROUP_NAME]

        with ZipFile(filename, 'r') as zf:
            colorset_str = zf.read("colorset.xml")
            colorset = ET.fromstring(colorset_str)

            for xmlgrp in colorset.xpath("//Group"):
                name = xmlgrp.attrib['name']
                if name is not None:
                    result.append(name)

        return result

    @staticmethod
    def get_options_widget(dialog, filename):

        dialog.options = DEFAULT_GROUP_NAME

        def on_group_changed(selector):
            def handler():
                dialog.options = selector.currentText()
                dialog.on_current_changed(filename)
            return handler

        widget = QtGui.QWidget()
        box = QtGui.QHBoxLayout()
        label = QtGui.QLabel(_("Group: "))
        selector = QtGui.QComboBox()

        for group_name in KplPalette.get_group_names(filename):
            selector.addItem(group_name)

        selector.currentIndexChanged.connect(on_group_changed(selector))
        selector.setCurrentIndex(0)

        box.addWidget(label)
        box.addWidget(selector)
        widget.setLayout(box)
        return widget

    def load(self, mixer, file_r, group_name):

        if group_name is None:
            group_name = DEFAULT_GROUP_NAME
        
        def find_group(xml):
            if group_name == DEFAULT_GROUP_NAME:
                return xml
            for xmlgrp in xml.xpath("//Group"):
                if xmlgrp.attrib['name'] == group_name:
                    return xmlgrp
            return None

        self.palette = Palette(mixer)

        with ZipFile(file_r, 'r') as zf:
            mimetype = zf.read("mimetype")
            if mimetype != MIMETYPE:
                raise Exception("This is not a valid Krita palette file")

            colorset_str = zf.read("colorset.xml")
            colorset = ET.fromstring(colorset_str)
            self.palette.ncols = int( colorset.attrib['columns'] )
            self.palette.name = colorset.attrib.get('name', "Untitled")

            group = find_group(colorset)
            if group is None:
                print(u"Cannot find group by name {}".format(group_name).encode('utf-8'))
                return None
            else:
                self.palette.name = self.palette.name + " - " + group.attrib.get('name', 'Untitled')

            all_slots = []
            n_colors = 0
            for xmlclr in group.findall('ColorSetEntry'):
                name = xmlclr.attrib['name']
                if xmlclr.attrib['bitdepth'] != 'U8':
                    print("Skip color {}: unsupported bitdepth".format(name))
                    continue
                rgb = xmlclr.find('RGB')
                if rgb is None:
                    rgb = xmlclr.find('sRGB')
                if rgb is None:
                    print("Skip color {}: no RGB representation".format(name))
                    continue

                r = float(rgb.attrib['r'].replace(',', '.'))
                g = float(rgb.attrib['g'].replace(',', '.'))
                b = float(rgb.attrib['b'].replace(',', '.'))
                clr = Color()
                clr.setRGB1((r,g,b))
                clr.name = name
                slot = Slot(clr)
                slot.mode = USER_DEFINED

                all_slots.append(slot)
                n_colors += 1

            if n_colors < DEFAULT_GROUP_SIZE:
                self.palette.ncols = n_colors
            if not self.palette.ncols:
                if n_colors > MAX_COLS:
                    self.palette.ncols = MAX_COLS
                else:
                    self.palette.ncols = n_colors
            #print("Loaded colors: {}".format(len(all_slots)))
            self.palette.setSlots(all_slots)
            self.palette.meta["SourceFormat"] = "KRITA KPL"
            print("Loaded palette: {}x{}".format( self.palette.nrows, self.palette.ncols ))
            return self.palette

    def save(self, file_w=None):
        with ZipFile(file_w, 'w', ZIP_DEFLATED) as zf:
            zf.writestr("mimetype", MIMETYPE)

            xml = ET.Element("Colorset")
            xml.attrib['version'] = '1.0'
            xml.attrib['columns'] = str(self.palette.ncols)
            xml.attrib['name'] = self.palette.name
            xml.attrib['comment'] = self.palette.meta.get("Comment", "Generated by Palette Editor")

            for i,row in enumerate(self.palette.slots):
                for j,slot in enumerate(row):
                    color = slot.color
                    name = color.name
                    default_name = "Swatch-{}-{}".format(i,j)
                    if not name:
                        name = default_name
                    
                    elem = ET.SubElement(xml, "ColorSetEntry")
                    elem.attrib['spot'] = color.meta.get("Spot", "false")
                    elem.attrib['id'] = default_name
                    elem.attrib['name'] = name
                    elem.attrib['bitdepth'] = 'U8'

                    r,g,b = color.getRGB1()
                    srgb = ET.SubElement(elem, "sRGB")
                    srgb.attrib['r'] = str(r)
                    srgb.attrib['g'] = str(g)
                    srgb.attrib['b'] = str(b)

            tree = ET.ElementTree(xml)
            tree_str = ET.tostring(tree, encoding='utf-8', pretty_print=True, xml_declaration=False)

            zf.writestr("colorset.xml", tree_str)


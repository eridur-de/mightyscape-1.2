
from os.path import join, basename
from PyQt4 import QtGui
from lxml import etree as ET

from color.colors import *
from color import mixers
from palette.storage.storage import *

class XmlPalette(Storage):
    name = 'xml'
    title = _("CREATE palette format")
    filters = ["*.xml"]
    can_load = True
    can_save = True

    @staticmethod
    def check(filename):
        return ET.parse(filename).getroot().tag == 'colors'

    @staticmethod
    def get_options_widget(dialog, filename):

        def on_group_changed(selector):
            def handler():
                dialog.options = selector.currentText()
                dialog.on_current_changed(filename)
            return handler

        widget = QtGui.QWidget()
        box = QtGui.QHBoxLayout()
        label = QtGui.QLabel(_("Group: "))
        selector = QtGui.QComboBox()

        xml = ET.parse(filename)
        for xmlgrp in xml.xpath("//group"):
            xml_label = xmlgrp.find('label')
            if xml_label is not None:
                selector.addItem(xml_label.text)

        selector.currentIndexChanged.connect(on_group_changed(selector))
        selector.setCurrentIndex(0)

        box.addWidget(label)
        box.addWidget(selector)
        widget.setLayout(box)
        return widget

    @staticmethod
    def get_group_names(filename):
        result = []
        xml = ET.parse(filename)
        for xmlgrp in xml.xpath("//group"):
            xml_label = xmlgrp.find('label')
            if xml_label is not None:
                result.append(xml_label.text)
        return result

    def save(self, file_w=None):
        xml = ET.Element("colors")
        root_group = ET.SubElement(xml, "group")
        group = ET.SubElement(root_group, "group")
        label = ET.SubElement(group, "label")
        label.text = self.palette.name
        layout = ET.SubElement(group, "layout", columns=str(self.palette.ncols), expanded="True")

        for key,value in self.palette.meta.items():
            if key != "Name":
                meta = ET.SubElement(group, "meta", name=key)
                meta.text = value

        for i,row in enumerate(self.palette.slots):
            for j,slot in enumerate(row):
                color = slot.color
                name = color.name
                if not name:
                    name = "Swatch-{}-{}".format(i,j)
                elem = ET.SubElement(group, "color")
                label = ET.SubElement(elem, "label")
                label.text = name
                if slot.mode == USER_DEFINED:
                    meta = ET.SubElement(elem, "meta", name="user_chosen")
                    meta.text = "True"
                for key,value in color.meta.items():
                    if key != "Name":
                        meta = ET.SubElement(elem, "meta", name=key)
                        meta.text = value
                rgb = ET.SubElement(elem, "sRGB")
                r,g,b = color.getRGB1()
                rgb.attrib["r"] = str(r)
                rgb.attrib["g"] = str(g)
                rgb.attrib["b"] = str(b)

        ET.ElementTree(xml).write(file_w, encoding="utf-8", pretty_print=True, xml_declaration=True)

    def load(self, mixer, file_r, group_name):

        def get_label(grp):
            xml_label = grp.find('label')
            if xml_label is None:
                return None
            return xml_label.text


        def find_group(xml):
            #print("Searching {}".format(group_name))
            grp = None
            for xmlgrp in xml.xpath("//group"):
                label = get_label(xmlgrp)
                if label is None:
                    continue
                #print("Found: {}".format(label))
                if group_name is None or label == group_name:
                    grp = xmlgrp
                    break
            return grp

        self.palette = Palette(mixer)
        self.palette.ncols = None
        xml = ET.parse(file_r)
        grp = find_group(xml)
        if grp is None:
            print(u"Cannot find group by name {}".format(group_name).encode('utf-8'))
            return None
        self.palette.name = get_label(grp)

        layout = grp.find('layout')
        if layout is not None:
            self.palette.ncols = int( layout.attrib['columns'] )

        metas = grp.findall('meta')
        if metas is not None:
            for meta in metas:
                key = meta.attrib['name']
                value = meta.text
                if key != 'Name':
                    self.palette.meta[key] = value

        all_slots = []
        n_colors = 0
        for xmlclr in grp.findall('color'):
            sRGB = xmlclr.find('sRGB')
            if sRGB is None:
                continue
            attrs = sRGB.attrib
            r = float(attrs['r'].replace(',','.'))
            g = float(attrs['g'].replace(',','.'))
            b = float(attrs['b'].replace(',','.'))
            clr = Color()
            clr.setRGB1((r,g,b))
            slot = Slot(clr)
            metas = xmlclr.findall('meta')
            if metas is not None:
                for meta in metas:
                    key = meta.attrib['name']
                    value = meta.text
                    if key == 'user_chosen' and value == 'True':
                        slot.mode = USER_DEFINED
                    else:
                        clr.meta[key] = value
            label = xmlclr.find('label')
            if label is not None:
                clr.name = label.text
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
        self.palette.meta["SourceFormat"] = "CREATE XML"
        print("Loaded palette: {}x{}".format( self.palette.nrows, self.palette.ncols ))
        return self.palette


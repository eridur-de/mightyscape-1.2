#! /usr/bin/env python3

# OS modules
import os
import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

# inkscape extension files
import cairo
from lxml import etree
import inkex  # required
from inkex.elements import NSS
from inkex.utils import errormsg as show_errormsg
from inkex.styles import Style
from inkex.colors import Color

__version__ = '1.0.0'

saved_gradient_path = "../my-gradients.svg"

def create_new_file(gradient_data):
    root = etree.Element("svg", nsmap=NSS)
    def_tree = etree.SubElement(root, "defs")
    for i, item in enumerate(gradient_data):
        gradient = etree.SubElement(def_tree, item.tag, attrib=item.attrib)
        for j, gradient_stop in enumerate(item):
            etree.SubElement(gradient, gradient_stop.tag, attrib=gradient_stop.attrib, id="stop%d%d" % (i, j))
    with open(saved_gradient_path, "w") as f:
        f.write(etree.tostring(
            root, encoding="utf-8", xml_declaration=True, pretty_print=True).decode("utf-8"))

def save_to_file(data):
    """ Wrapper for saving gradients to file. """
    if len(data) == 0:
        return 1
    else:
        try:
            # read previous data then append it with current data
            if os.path.exists(saved_gradient_path):
                previous_data = load_gradients_from_file()
                data = previous_data + data
            create_new_file(data)
            return 0
        except Exception as e:
            import traceback
            show_errormsg(e)
            show_errormsg(traceback.print_exc())
            return -1

def load_gradients_from_file():
    """ Load gradients from saved gradient, returned as List """
    if os.path.exists(saved_gradient_path) and os.stat(saved_gradient_path).st_size != 0:
        root = etree.parse(saved_gradient_path)
        mygradients = root.xpath("//linearGradient", namespaces=NSS)
    else:
        mygradients = []
    return mygradients

def read_stop_gradient(gradient):
    stop_data = {
        "id": gradient.attrib.get("id"),
        "stops": []
    }
    for stop in gradient:
        offset = stop.attrib.get("offset")
        style = Style(Style.parse_str(stop.attrib['style']))
        color = Color.parse_str(style.get("stop-color"))[1]
        opacity = style.get("stop-opacity")
        stop_data.get("stops").append(
            tuple([float(offset)] + [x/256.0 for x in color] + [float(opacity)]))
    return stop_data

class MainWindow(Gtk.Builder):
    def __init__(self, gradientSaver):
        Gtk.Builder.__init__(self)
        self.gradientSaver = gradientSaver
        self.add_from_file("GUI.glade")
        self.window = self.get_object("window")
        self.app_version = self.get_object("extension_version")
        self.app_version.set_label(self.app_version.get_label().replace("$VERSION",__version__))
        self.information_dialog = self.get_object("information_dialog")
        # parsing components
        # save gradient components
        self.save_container = self.get_object("save_gradients_container")
        save_template = self.get_object("save_gradient1")
        self.save_container.remove(save_template)
        for idx, item in enumerate(self.gradientSaver.doc_selected_gradients):
            new_save_template = self.SaveGradientTemplate(item)
            new_save_template.set_name("gradient%d" % idx)
            self.save_container.add(new_save_template)
            self.save_container.show_all()
        # - end save gradient components
        # load gradient components
        self.load_container = self.get_object("load_gradients_container")
        load_template = self.get_object("load_gradient1")
        self.load_container.remove(load_template)
        # - end load gradient components
        # show the GUI
        self.connect_signals(self.Handler(self))
        self.window.show()

    class SaveGradientTemplate(Gtk.HBox):
        """
        Template for generating gradient name 
        and preview of selected object in the save page.
        """

        def __init__(self, gradient_data):
            Gtk.HBox.__init__(self)
            self.gradient_data = gradient_data
            self.set_spacing(20)
            preview = Gtk.DrawingArea()
            preview.set_size_request(150, 42)
            preview.set_app_paintable(True)
            preview.connect("draw", self.on_draw, gradient_data)
            self.pack_start(preview, False, True, 0)
            self.input_entry = Gtk.Entry()
            self.input_entry.set_placeholder_text("e.g Beautiful Color")
            self.input_entry.set_size_request(250, 42)
            self.input_entry.set_text(gradient_data.get("id"))
            self.input_entry.set_max_length(25)
            self.pack_start(self.input_entry, False, True, 1)

        def on_draw(self, wid, cr, data):
            """
            Calllback for draw signal for rendering gradient.
            params:
                - wid :GtkWidget
                - cr :Cairo
                - data :list -> gradient data
            """
            lg = cairo.LinearGradient(0.0, 20.0, 150.0, 20.0)
            for stop in data["stops"]:
                lg.add_color_stop_rgba(
                    stop[0], stop[1], stop[2], stop[3], stop[4])
            cr.rectangle(10.0, 0.0, 150.0, 42.0)
            cr.set_source(lg)
            cr.fill()

        def get_save_gradient_text(self):
            return self.input_entry.get_text()

        def get_compiled_gradient(self, new_id):
            # compiling gradient stops
            root = etree.Element("linearGradient", id=new_id)
            for idx, stop in enumerate(self.gradient_data["stops"]):
                stop_id = self.get_name() + str(idx)
                offset = stop[0]
                color = Color([stop[1], stop[2], stop[3]],"rgb")
                opacity = stop[4]
                tmp_stops = {
                    "id": stop_id,
                    "offset": str(offset),
                    "style": Style({
                                "stop-color": str(color), 
                                "stop-opacity": str(opacity)
                            }).to_str()
                }
                current_stop = etree.SubElement(root, "stop", attrib=tmp_stops)
            return root

    class LoadGradientTemplate(Gtk.FlowBoxChild):
        """
        Template for generating gradient name 
        and preview of saved gradient in the load page.
        """
        def __init__(self, gradient_data):
            Gtk.FlowBoxChild.__init__(self)
            self.gradient_data = gradient_data
            self.set_size_request(60,32)
            self.set_halign(Gtk.Align.START)
            self.set_valign(Gtk.Align.START)
            container = Gtk.HBox()
            container.set_spacing(5)
            container.set_baseline_position(Gtk.BaselinePosition.TOP)
            self.checkbox = Gtk.CheckButton()
            self.checkbox.draw_indicator = True
            container.pack_start(self.checkbox,False,True,0)
            preview = Gtk.DrawingArea()
            preview.set_size_request(100, 32)
            preview.set_app_paintable(True)
            preview.connect("draw", self.on_draw, gradient_data)
            container.pack_start(preview,False,True,0)
            self.text_gradient = Gtk.Label()
            self.text_gradient.set_text(gradient_data.get("id"))
            self.text_gradient.set_line_wrap(True)
            self.text_gradient.set_line_wrap_mode(1)
            self.text_gradient.set_max_width_chars(25)
            container.pack_start(self.text_gradient,False,True,0)
            self.add(container)
        
        def on_draw(self, wid, cr, data):
            """
            Calllback for draw signal for rendering gradient.
            params:
                - wid :GtkWidget
                - cr :Cairo
                - data :list -> gradient data
            """
            lg = cairo.LinearGradient(0.0, 20.0, 100.0, 20.0)
            for stop in data["stops"]:
                lg.add_color_stop_rgba(
                    stop[0], stop[1], stop[2], stop[3], stop[4])
            cr.rectangle(10.0, 0.0, 110.0, 32.0)
            cr.set_source(lg)
            cr.fill()

    class Handler:
        """ Signal Handler for GUI """

        def __init__(self, main_window):
            self.main_window = main_window

        def onDestroy(self, *args):
            Gtk.main_quit()
        
        def onSwitchPage(self, notebook, page, page_num):
            if page_num == 0: # save tab
                pass
            elif page_num == 1: # load/remove tab
                self.main_window.gradients_to_load = []
                for children in self.main_window.load_container.get_children():
                    self.main_window.load_container.remove(children)
                loaded_gradients = load_gradients_from_file()
                # TODO render with disabled checkbox if it already exists in current project doc
                for idx,gradient in enumerate(loaded_gradients):
                    # parse gradient stops
                    stop_data = read_stop_gradient(gradient)
                    gradient_info = self.main_window.LoadGradientTemplate(stop_data)
                    gradient_info.checkbox.connect("toggled",self.onLoadGradientToggled, gradient)
                    gradient_info.set_name("gradient%d" % idx)
                    self.main_window.load_container.add(gradient_info)
                self.main_window.load_container.show_all()
            else:
                pass

        def onSaveGradientClicked(self, button):
            text = ""
            gradient_to_save = []
            # get all gradient data in save_container
            for item in self.main_window.save_container.get_children():
                # get new gradient name
                new_name_gradient = item.get_save_gradient_text()
                # strip all special chars
                if not new_name_gradient.isalnum():
                    new_name_gradient = ''.join(e for e in new_name_gradient if e.isalnum())
                # get gradient data
                gradient_data = item.get_compiled_gradient(new_name_gradient)
                text += "{0}\n-----\n".format(etree.tostring(gradient_data))
                gradient_to_save.append(gradient_data)
            # save to file
            status = save_to_file(gradient_to_save)
            if status == 0:
                info = "%d gradients saved successfully!" % len(gradient_to_save)
                # reload current document info with saved gradients
                self.main_window.gradientSaver.reload_current_gradients(gradient_to_save)
            elif status == 1:
                info = "Nothing to save, there is no object with gradient selected. Exiting..."
            elif status == -1:
                info = "Internal Error (-1)! "
            # showing popup information
            self.main_window.get_object("information_text").set_text(info)
            self.main_window.information_dialog.set_title("Save Gradient Information")
            self.main_window.information_dialog.show_all()
        
        def onLoadGradientToggled(self, togglebutton, gradient):
            # if active, queue gradient, otherwise pop it
            if togglebutton.get_active():
                self.main_window.gradients_to_load.append(gradient)
            else:
                self.main_window.gradients_to_load.remove(gradient)

        def onLoadGradientClicked(self, button):
            if len(self.main_window.gradients_to_load) > 0:
                self.main_window.gradientSaver.insert_new_gradients_to_current_doc(self.main_window.gradients_to_load)
                teks = "Successfully loading these gradients:\n"
                teks += "".join(["- "+gradient.attrib["id"]+"\n" for gradient in self.main_window.gradients_to_load])
            else:
                teks = "No gradient(s) selected to load. Exiting..."
            self.main_window.get_object("information_text").set_text(teks)
            self.main_window.information_dialog.set_title("Load Gradient Information")
            self.main_window.information_dialog.show_all()

        def onRemoveGradientClicked(self, button):
            loaded_gradients = load_gradients_from_file()
            if len(self.main_window.gradients_to_load) > 0:
                gradient_to_remove = [gradient.attrib["id"] for gradient in self.main_window.gradients_to_load]
                new_gradient_after = [gradient for gradient in loaded_gradients if gradient.attrib["id"] not in gradient_to_remove]
                create_new_file(new_gradient_after)
                teks = "Successfully removing these gradients:\n"
                teks += "".join(["- "+gradient+"\n" for gradient in gradient_to_remove])
            else:
                teks = "No gradient(s) selected to load. Exiting..."
            self.main_window.get_object("information_text").set_text(teks)
            self.main_window.information_dialog.set_title("Remove Gradient Information")
            self.main_window.information_dialog.show_all()


class GradientSaver(inkex.Effect):
    def __init__(self):
        " define how the options are mapped from the inx file "
        inkex.Effect.__init__(self)  # initialize the super class
        try:
            self.tty = open("/dev/tty", 'w')
        except:
            self.tty = open(os.devnull, 'w')
        self.doc_selected_gradients = []
    
    def insert_new_gradients_to_current_doc(self, gradients):
        defs_node = self.svg.getElement("//svg:defs")
        for item in gradients:
            gradient = etree.SubElement(defs_node,item.tag,attrib=item.attrib)
            for stop in item:
                etree.SubElement(gradient,stop.tag,attrib=stop.attrib)

    def reload_current_gradients(self, new_data):
        " reload gradients information in current project with stored gradient "
        for idx,gradient in enumerate(self.doc_selected_gradients):
            # set old gradient id to new id
            real_node = self.svg.getElement("//*[@id='%s']" % gradient["id"])
            # remove inkscape collect first
            real_node.attrib.pop("{"+NSS["inkscape"]+"}collect", None)
            real_node.attrib["id"] = new_data[idx].attrib["id"]
            # set old xlink:href to new id
            node_href = self.svg.getElement("//*[@xlink:href='#%s']" % gradient["id"])
            node_href.attrib["{"+NSS["xlink"]+"}href"] = "#"+new_data[idx].attrib["id"]
            # last set up inkscape collect again
            real_node.attrib["{"+NSS["inkscape"]+"}collect"] = "always"

    def get_all_doc_gradients(self):
        """TODO
        retrieve all gradient sources of current project document
        """
        pass

    def get_selected_gradients_data(self):
        selected_objects = self.svg.selected
        gradient_list = []
        if len(selected_objects) > 0:
            for item in selected_objects.values():
                style = Style(Style.parse_str(item.get('style')))
                fill = stroke = "None"
                if style.get("fill"):
                    fill = style.get("fill")[5:-1] if "url" in style.get("fill") else "None"
                if style.get("stroke"):
                    stroke = style("stroke")[5:-1] if "url" in style.get("stroke") else "None"
                if fill == "None" and stroke == "None":
                    continue
                # read fill data
                if "radialGradient" in fill or "linearGradient" in fill:
                    real_fill = self.svg.getElementById(fill).attrib["{"+NSS["xlink"]+"}href"][1:]
                    real_fill_node = self.svg.getElementById(real_fill)
                    if real_fill_node not in gradient_list:
                        gradient_list.append(real_fill_node)
                # read stroke data
                if "radialGradient" in stroke or "linearGradient" in stroke:
                    real_stroke = self.svg.getElementById(stroke).attrib["{"+NSS["xlink"]+"}href"][1:]
                    real_stroke_node = self.svg.getElementById(real_stroke)
                    if real_stroke_node not in gradient_list:
                        gradient_list.append(real_stroke_node)
        data = []
        # read gradients data
        for gradient in gradient_list:
            # parse gradient stops
            stop_data = read_stop_gradient(gradient)
            inkex.utils.debug(gradient)
            data.append(stop_data)
        return data

    # called when the extension is running.
    def effect(self):
        self.doc_selected_gradients = self.get_selected_gradients_data()
        try:
            app = MainWindow(self)
            Gtk.main()
        except Exception as e:
            import traceback
            show_errormsg(e)
            show_errormsg(traceback.print_exc())


if __name__ == '__main__':
    GradientSaver().run()

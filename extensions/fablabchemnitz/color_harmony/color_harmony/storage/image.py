
from os.path import join, basename, splitext
from math import sqrt, floor
from PyQt4 import QtGui

from color.colors import *
from color import spaces
from color import mixers
from palette.image import PaletteImage
from palette.palette import *
from palette.storage.storage import *
from palette.storage.cluster import *
from palette.storage.table import parse_color_table
from matching.transform import rho, get_center

LOAD_MORE = 1
LOAD_LESS_COMMON = 2
LOAD_LESS_FAREST = 3
LOAD_TABLE = 4

print("Ok")

class DialogOptions(object):
    def __init__(self, method):
        self.method = method
        self.border_x = 10
        self.border_y = 10
        self.gap_x = 10
        self.gap_y = 10
        self.size_x = 5
        self.size_y = 5

class Image(Storage):
    name = 'image'
    title = _("Raster image")
    filters = ["*.jpg", "*.png", "*.gif"]
    can_load = image_loading_supported
    can_save = True

    @staticmethod
    def check(filename):
        return True

    @staticmethod
    def get_options_widget(dialog, filename):
        if use_sklearn:
            return None

        def dependencies():
            if dialog.options is None or dialog.options.method != LOAD_TABLE:
                table_w.setVisible(False)
            else:
                table_w.setVisible(True)

        def on_method_changed(checked):
            method = None
            if dialog._more_button.isChecked():
                method = LOAD_MORE
            elif dialog._less_button.isChecked():
                method = LOAD_LESS_COMMON
            elif dialog._less_farest.isChecked():
                method = LOAD_LESS_FAREST
            elif dialog._table.isChecked():
                method = LOAD_TABLE
            dialog.options = DialogOptions(method)
            if method == LOAD_TABLE:
                dialog.options.border_x = dialog._border_x.value()
                dialog.options.border_y = dialog._border_y.value()
                dialog.options.gap_x = dialog._gap_x.value()
                dialog.options.gap_y = dialog._gap_y.value()
                dialog.options.size_x = dialog._size_x.value()
                dialog.options.size_y = dialog._size_y.value()
            dependencies()
            dialog.on_current_changed(filename)

        group_box = QtGui.QGroupBox(_("Loading method"))
        dialog._more_button = more = QtGui.QRadioButton(_("Use 49 most used colors"))
        dialog._less_button = less = QtGui.QRadioButton(_("Use 9 most used colors and mix them"))
        dialog._less_farest = less_farest = QtGui.QRadioButton(_("Use 9 most different colors and mix them"))
        dialog._table = table = QtGui.QRadioButton(_("Load table of colors"))

        table_w = QtGui.QWidget(dialog)
        table_form = QtGui.QFormLayout(table_w)
        dialog._border_x = QtGui.QSpinBox(table_w)
        dialog._border_x.valueChanged.connect(on_method_changed)
        table_form.addRow(_("Border from right/left side, px"), dialog._border_x)
        dialog._border_y = QtGui.QSpinBox(table_w)
        dialog._border_y.valueChanged.connect(on_method_changed)
        table_form.addRow(_("Border from top/bottom side, px"), dialog._border_y)
        dialog._gap_x = QtGui.QSpinBox(table_w)
        dialog._gap_x.valueChanged.connect(on_method_changed)
        table_form.addRow(_("Width of gap between cells, px"), dialog._gap_x)
        dialog._gap_y = QtGui.QSpinBox(table_w)
        dialog._gap_y.valueChanged.connect(on_method_changed)
        table_form.addRow(_("Height of gap between cells, px"), dialog._gap_y)
        dialog._size_x = QtGui.QSpinBox(table_w)
        dialog._size_x.setValue(5)
        dialog._size_x.valueChanged.connect(on_method_changed)
        table_form.addRow(_("Number of columns in the table"), dialog._size_x)
        dialog._size_y = QtGui.QSpinBox(table_w)
        dialog._size_y.setValue(5)
        dialog._size_y.valueChanged.connect(on_method_changed)
        table_form.addRow(_("Number of rows in the table"), dialog._size_y)
        table_w.setLayout(table_form)

        dependencies()

        more.toggled.connect(on_method_changed)
        less.toggled.connect(on_method_changed)
        less_farest.toggled.connect(on_method_changed)
        table.toggled.connect(on_method_changed)

        if dialog.options is None or dialog.options.method == LOAD_MORE:
            more.setChecked(True)
        elif dialog.options.method == LOAD_LESS_COMMON:
            less.setChecked(True)
        elif dialog.options.method == LOAD_TABLE:
            table.setChecked(True)
        else:
            less_farest.setChecked(True)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(more)
        vbox.addWidget(less)
        vbox.addWidget(less_farest)
        vbox.addWidget(table)
        vbox.addWidget(table_w)
        group_box.setLayout(vbox)
        return group_box

    def save(self, file_w):
        w,h = self.palette.ncols * 48, self.palette.nrows * 48
        image = PaletteImage( self.palette ).get(w,h)
        print("Writing image: " + file_w)
        res = image.save(file_w)
        if not res:
            image.save(file_w, format='PNG')

    def load(self, mixer, file_r, options=None):
        def _cmp(clr1,clr2):
            h1,s1,v1 = clr1.getHSV()
            h2,s2,v2 = clr2.getHSV()
            x = cmp(h1,h2)
            if x != 0:
                return x
            x = cmp(v1,v2)
            if x != 0:
                return x
            return cmp(s1,s2)

        def get_farest(space, colors, n=9):
            points = [space.getCoords(c) for c in colors]
            center = get_center(points)
            srt = sorted(points, key = lambda c: -rho(center, c))
            farest = srt[:n]
            return [space.fromCoords(c) for c in farest]

        if use_sklearn or options is None or options.method is None or options.method == LOAD_MORE:
            colors = get_common_colors(file_r)
            colors.sort(cmp=_cmp)
            self.palette = create_palette(colors, mixer)
            return self.palette
        
        elif options.method == LOAD_TABLE:
            self.palette = palette = Palette(mixer, nrows=options.size_y, ncols=options.size_x)
            colors = parse_color_table(file_r, options)

            for i in range(0, options.size_y):
                for j in range(0, options.size_x):
                    palette.paint(i, j, colors[i][j])

            return palette

        else:
            if options.method == LOAD_LESS_FAREST:
                colors = get_common_colors(file_r)
                colors = get_farest(spaces.RGB, colors)
            else:
                colors = get_common_colors(file_r, n_clusters=9)

            self.palette = palette = Palette(mixer, nrows=7, ncols=7)

            palette.paint(0, 0, colors[0])
            palette.paint(0, 3, colors[1])
            palette.paint(0, 6, colors[2])
            palette.paint(3, 0, colors[3])
            palette.paint(3, 3, colors[4])
            palette.paint(3, 6, colors[5])
            palette.paint(6, 0, colors[6])
            palette.paint(6, 3, colors[7])
            palette.paint(6, 6, colors[8])

            palette.need_recalc_colors = True
            palette.recalc()

            name,ext = splitext(basename(file_r))
            self.palette.meta["SourceFormat"] = ext

            return palette



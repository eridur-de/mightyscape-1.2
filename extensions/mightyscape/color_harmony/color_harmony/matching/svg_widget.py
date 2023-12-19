
from string import Template
from PyQt4 import QtGui, QtSvg, QtCore

from color.colors import *
from color.spaces import *
import svg, transform, matching

class SvgTemplateWidget(QtSvg.QSvgWidget):
    template_loaded = QtCore.pyqtSignal()
    colors_matched = QtCore.pyqtSignal()
    file_dropped = QtCore.pyqtSignal(unicode)

    def __init__(self, *args):
        QtSvg.QSvgWidget.__init__(self, *args)
        self.setAcceptDrops(True)
        self._colors = [Color(i*10,i*10,i*10) for i in range(20)]
        self._template = None
        self._template_filename = None
        self._svg = None
        self._need_render = True
        self._svg_colors = None
        self._dst_colors = None
        self._last_size = None

    def sizeHint(self):
        if self.renderer().isValid():
            return self.renderer().defaultSize()
        elif self._last_size:
            return self._last_size
        else:
            return QtCore.QSize(300,300)
            

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            path = unicode( urls[0].path() )
            self.file_dropped.emit(path)

    def _get_color(self, i):
        if i < len(self._colors):
            return self._colors[i]
        else:
            return Color(i*10, i*10, i*10)
    
    def _update(self):
        arr = QtCore.QByteArray.fromRawData(self.get_svg())
        print("Data loaded: {} bytes".format(arr.length()))
        self.load(arr)
        if self.renderer().isValid():
            self._last_size = self.renderer().defaultSize()
        self.update()

    def _get_image(self):
        w,h = self.size().width(), self.size().height()
        image = QtGui.QImage(w, h,  QtGui.QImage.Format_ARGB32_Premultiplied)
        image.fill(0)
        qp = QtGui.QPainter()
        qp.begin(image)
        self.renderer().render(qp, QtCore.QRectF(0.0, 0.0, w, h))
        qp.end()
        return image

    def loadTemplate(self, filename):
        self._template_filename = filename
        self._svg_colors, self._template = svg.read_template(filename)
        print("Source SVG colors:")
        for c in self._svg_colors:
            print str(c)
        print("Template loaded: {}: {} bytes".format(filename, len(self._template)))
        self._need_render = True
        self._update()
        self.template_loaded.emit()

    def set_color(self, idx, color):
        self._colors[idx] = color
        self._need_render = True
        self._update()

    def setColors(self, dst_colors, space=HCY):
        if not dst_colors:
            return
        print("Matching colors in space: {}".format(space))
        self._dst_colors = dst_colors
        self._colors = transform.match_colors(space, self._svg_colors, dst_colors)
        #self._colors = matching.match_colors(self._svg_colors, dst_colors)
        self._need_render = True
        self._update()
        self.colors_matched.emit()

    def resetColors(self):
        self.load(self._template_filename)
        self.repaint()

    def get_svg_colors(self):
        return self._svg_colors
    
    def get_dst_colors(self):
        return self._colors

    def get_svg(self):
        if self._svg is not None and not self._need_render:
            return self._svg
        else:
            self._svg = self._render()
            self._need_render = False
            return self._svg

    def _render(self):
        #d = dict([("color"+str(i), color.hex() if color is not None else Color(255,255,255)) for i, color in enumerate(self._colors)])
        d = ColorDict(self._colors)
        #self._image = self._get_image()
        return Template(self._template).substitute(d)

class ColorDict(object):
    def __init__(self, colors):
        self._colors = colors

    def __getitem__(self, key):
        if key.startswith("color"):
            n = int( key[5:] )
            if n < len(self._colors):
                return self._colors[n].hex()
            else:
                return "#ffffff"
        else:
            raise KeyError(key)


        

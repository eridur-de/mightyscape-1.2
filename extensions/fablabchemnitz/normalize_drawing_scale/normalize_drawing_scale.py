#!/usr/bin/env python3

import inkex
from inkex import Transform
from lxml import etree

class NormalizeDrawingScale(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument('--target_scale', type=float, default=100.0)

    def effect(self):
        format_units = inkex.units.parse_unit(self.svg.get('width'))[1] #get the "Format:" unit at "Display tab"
        namedView = self.document.getroot().find(inkex.addNS('namedview', 'sodipodi'))
        display_units = namedView.get('inkscape:document-units') #means the "Display units:" at "Display tab"
        docScale = self.svg.scale
        inkscapeScale = self.svg.inkscape_scale #this is the "Scale:" value at "Display tab"

        docWidth = self.svg.get('width')
        docHeight = self.svg.get('height')

        docWidth_fin = inkex.units.parse_unit(docWidth)[0]
        docHeight_fin = inkex.units.parse_unit(docHeight)[0]

        vxMin, vyMin, vxMax, vyMax = self.svg.get_viewbox()
        vxTotal = vxMax - vxMin
        targetScale = self.options.target_scale / 100

        if display_units is None:
            display_units = format_units #assume same unit ad format_units if "inkscape:document-units" does not exist
            namedView.set('inkscape:document-units', format_units)

        visualScaleX = self.svg.unittouu(str(vxTotal / self.svg.viewport_width) + display_units)
        formatScaleX = self.svg.unittouu(str(vxTotal / self.svg.viewport_width) + format_units)

        docWidth_new = docWidth_fin * visualScaleX * inkscapeScale
        docHeight_new = docHeight_fin * visualScaleX * inkscapeScale

        docWidth_new = docWidth_fin * targetScale / inkscapeScale
        docHeight_new = docHeight_fin * targetScale / inkscapeScale

        #inkex.errormsg("format_units: " + str(format_units))
        #inkex.errormsg("display_units: " + str(display_units))
        #inkex.errormsg("docScale: {:0.6f}".format(docScale))
        #inkex.errormsg("inkscapeScale: {:0.6f}".format(inkscapeScale))
        #inkex.errormsg("docWidth_fin: {:0.3f}{}".format(docWidth_fin, format_units))
        #inkex.errormsg("docHeight_fin: {:0.3f}{}".format(docHeight_fin, format_units))
        #inkex.errormsg("vxTotal: " + str(vxTotal))
        #inkex.errormsg("docWidth_new: {:0.3f}{} ({:0.3f}px)".format(docWidth_new, format_units, self.svg.unittouu(str(docWidth_new) + format_units)))
        #inkex.errormsg("docHeight_new: {:0.3f}{} ({:0.3f}px)".format(docHeight_new, format_units, self.svg.unittouu(str(docHeight_new) + format_units)))
        #inkex.errormsg("targetScale: {:0.6f}".format(targetScale))
        #inkex.errormsg("visualScaleX: {:0.6f}".format(visualScaleX))
        #inkex.errormsg("formatScaleX: {:0.6f}".format(formatScaleX))

        #if inkscapeScale == targetScale: #strange rule. might break sth.
        #    inkex.utils.debug("Nothing to do. Scale is already 100%")
        #    return

        if visualScaleX == 0.0: #seems there is no viewBox attribute, then ...
            #inkex.errormsg("viewBox attribute is missing in svg:svg. Applying new one ...")
            visualScaleX = 1.0 #this is the case we deal with px as display unit and we removed the viewBox
            self.svg.set('viewBox', '0 0 {} {}'.format(targetScale * docWidth_fin, targetScale * docHeight_fin))
        if inkscapeScale != targetScale:
            #set scale to 100% (we adjust viewBox)
            sc = (1 / (targetScale / inkscapeScale))
            viewBoxNew = '0 0 {} {}'.format(docWidth_fin / targetScale, docHeight_fin / targetScale)
            #inkex.errormsg("viewBox modifying to: {}".format(viewBoxNew))
            #inkex.errormsg("width modifying to: {}{}".format(docWidth_fin, format_units))
            #inkex.errormsg("height modifying to: {}{}".format(docHeight_fin, format_units))
            self.svg.set('viewBox', viewBoxNew)
            self.svg.set('width', "{}{}".format(docWidth_fin, format_units))
            self.svg.set('height', "{}{}".format(docHeight_fin, format_units))

            translation_matrix = [[sc, 0.0, 0.0], [0.0, sc, 0.0]]
            #select each top layer and apply the transformation to scale
            processed = []
            for element in self.document.getroot().iter(tag=etree.Element):
                if element != self.document.getroot():
                    if element.tag == inkex.addNS('g','svg'):
                        parent = element.getparent()
                        if parent.get('inkscape:groupmode') != 'layer' and element.get('inkscape:groupmode') == 'layer':
                            element.transform = Transform(translation_matrix) @ element.composed_transform()
                            processed.append(element)

            #do the same for all elements which lay on first level and which are not a layer
            for element in self.document.getroot().getchildren():
                if isinstance(element, inkex.ShapeElement) and element not in processed:
                    element.transform = Transform(translation_matrix) @ element.composed_transform()

        else:
            inkex.utils.debug("Nothing to do. Scale is already {:.3f}%".format(self.options.target_scale))
            return


if __name__ == '__main__':
    NormalizeDrawingScale().run()
#!/usr/bin/env python3

import re
import inkex
from inkex import TextElement, TextPath, Tspan
from inkex.bezier import csparea, cspcofm, csplength
from inkex.colors import Color

class IdsToText(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--fontsize', type = int, default = '10', help = 'Font Size')
        pars.add_argument('--color', type=Color, default = 255, help = 'Color')
        pars.add_argument('--font', default = 'Roboto', help = 'Font Family')
        pars.add_argument('--fontweight', default = 'bold', help = 'Font Weight')
        pars.add_argument('--replaced', default = '', help = 'Text to replace')
        pars.add_argument('--replacewith', default = '', help = 'Replace with this text')
        pars.add_argument('--angle', type = float, dest = 'angle', default = 0, help = 'Rotation angle')
        pars.add_argument('--capitals', type = inkex.Boolean, default = False, help = 'Capitalize')
        pars.add_argument('--path_attribute', default='id', help='Path attribute to show')
        pars.add_argument('--matchre', default='', help='Match regular expression')
        pars.add_argument('--group', type=inkex.Boolean, default=False, help='Group paths with generated text elements')

    def extract_path_attribute(self, attr, node):
        ret = ''
        if attr == 'id':
            ret = node.get(attr)
        elif attr == 'label':
            value = node.get(attr)
            ret = str(value) if value else (node.get("inkscape:label") or "")
        elif attr == 'width':
            ret = format(node.bounding_box().width, '.2f')
        elif attr == 'height':
            ret = format(node.bounding_box().height, '.2f')
        elif attr == 'fill' or attr == 'stroke':
            if 'style' in node.attrib:
                style = node.attrib.get('style')
                style = dict(inkex.styles.Style.parse_str(style))
                if attr in style:
                    ret = style.get(attr)
                elif attr in node.attrib:
                    ret = node.attrib.get(attr)
        return ret

    def effect(self):
        if len(self.svg.selection.filter(inkex.PathElement)) == 0:
            inkex.errormsg("Please select some paths first.")
            exit()

        path_attribute = self.options.path_attribute
        is_text_attribute = path_attribute in ['id', 'label']
        for id, node in self.svg.selection.filter(inkex.PathElement).items():
            to_show = self.extract_path_attribute(path_attribute, node)

            node.path.transform(node.composed_transform()).to_superpath()
            bbox = node.bounding_box()
            tx, ty = bbox.center

            if self.options.group:
                group_element = node.getparent().add(inkex.Group())
                group_element.add(node)
                group_element.set('id', node.get('id') + "_group")
                text_element = group_element.add(inkex.TextElement())
            else:
                text_element = node.getparent().add(inkex.TextElement())

            tspan_element = text_element.add(inkex.Tspan())
            tspan_element.set('sodipodi:role', 'line')
            styles = {'text-align': 'center',
                      'vertical-align': 'bottom',
                      'text-anchor': 'middle',
                      'font-size': str(self.options.fontsize) + 'px',
                      'font-weight': self.options.fontweight,
                      'font-style': 'normal',
                      'font-family': self.options.font,
                      'fill': str(self.options.color)
                      }
            tspan_element.set('style', str(inkex.Style(styles)))
            tspan_element.set('dy', '0')

            if is_text_attribute:
                if self.options.capitals:
                    to_show = to_show.upper()

                if self.options.matchre != '':
                    matches = re.findall(self.options.matchre, to_show)
                    if len(matches) > 0:
                        to_show = matches[0]

                if self.options.replaced != '':
                    to_show = to_show.replace(
                        self.options.replaced, self.options.replacewith)

            tspan_element.text = to_show
            tspan_element.set('id', node.get('id') + "_tspan")
            text_element.set('id', node.get('id') + "_text")
            text_element.set('x', str(tx))
            text_element.set('y', str(ty))
            text_element.set('transform', 'rotate(%s, %s, %s)' %
                             (-int(self.options.angle), tx, ty))

if __name__ == '__main__':
    IdsToText().run()
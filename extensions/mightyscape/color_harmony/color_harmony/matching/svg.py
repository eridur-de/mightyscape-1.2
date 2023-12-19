
import re
from lxml import etree

from color import colors

SVG_NS="http://www.w3.org/2000/svg"

color_re = re.compile("#[0-9a-fA-F]+")

def walk(processor, element):
     for child in element.iter():
         processor(child)

class Collector(object):
     def __init__(self):
         self.colors = {}
         self.n = 0

     def _parse(self, string):
        xs = string.split(";")
        single = len(xs) == 1

        result = {}
        for x in xs:
            ts = x.split(":")
            if len(ts) < 2:
                if single:
                    return None
                else:
                    continue
            key, value = ts[0], ts[1]
            result[key] = value
        return result

     def _merge(self, attr):
         if type(attr) == str:
             return attr
         result = ""
         for key in attr:
             value = attr[key]
             result += key + ":" + value + ";"
         return result

     def _is_color(self, val):
         return color_re.match(val) is not None

     def _remember_color(self, color):
         if color not in self.colors:
             self.colors[color] = self.n
             self.n += 1
         n = self.colors[color]
         return "${color%s}" % n

     def _process_attr(self, value):
         d = self._parse(value)
         if d is None:
             if self._is_color(value):
                 return self._remember_color(value)
             else:
                 return value
         elif type(d) == dict:
             for attr in ['fill', 'stroke', 'stop-color']:
                 if (attr in d) and self._is_color(d[attr]):
                     color = d[attr]
                     d[attr] = self._remember_color(color)
             return self._merge(d)
         else:
             if self._is_color(value):
                 return self._remember_color(value)
             else:
                 return value

     def process(self, element):
         for attr in ['fill', 'stroke', 'style', 'pagecolor', 'bordercolor']:
             if attr in element.attrib:
                 value = element.get(attr)
                 element.set(attr, self._process_attr(value))

     def result(self):
         return self.colors

def read_template(filename):
    xml = etree.parse(filename)
    collector = Collector()
    walk(collector.process, xml.getroot())
    svg = etree.tostring(xml, encoding='utf-8', xml_declaration=True, pretty_print=True)
    #open("last_template.svg",'w').write(svg)
    color_dict = collector.result()
    colors_inv = dict((v,k) for k, v in color_dict.iteritems())
    svg_colors = []
    for key in range(len(colors_inv.keys())):
        clr = colors_inv[key]
        svg_colors.append( colors.fromHex(clr) )
    return svg_colors, svg


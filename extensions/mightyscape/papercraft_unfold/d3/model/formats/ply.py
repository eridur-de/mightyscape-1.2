import os
import sys
import struct
from ..basemodel import ModelParser, TextModelParser, Exporter, Vertex, Face, Color, FaceVertex, TexCoord, Material

class UnkownTypeError(Exception):
    def __init__(self, message):
        self.message  = message

def is_ply(filename):
    """Checks that the file is a .ply file

    Only checks the extension of the file
    :param filename: path to the file
    """
    return filename[-4:] == '.ply'

# List won't work with this function
def _ply_type_size(type):
    """Returns the size of a ply property

    :param type: a string that is in a ply element
    """
    if type == 'char' or type == 'uchar':
        return 1
    elif type == 'short' or type == 'ushort':
        return 2
    elif type == 'int' or type == 'uint':
        return 4
    elif type == 'float':
        return 4
    elif type == 'double':
        return 8
    else:
        raise UnkownTypeError('Type ' + type + ' is unknown')

def ply_type_size(type):
    """Returns the list containing the sizes of the elements

    :param type: a string that is in a ply element
    """
    split = type.split()

    if len(split) == 1:
        return [_ply_type_size(type)]
    else:
        if split[0] != 'list':
            print('You have multiple types but it\'s not a list...', file=sys.stderr)
            sys.exit(-1)
        else:
            return list(map(lambda a: _ply_type_size(a), split[1:]))


def bytes_to_element(type, bytes, byteorder = 'little'):
    """Returns a python object parsed from bytes

    :param type: the type of the object to parse
    :param bytes: the bytes to read
    :param byteorder: little or big endian
    """
    if type == 'char':
        return ord(struct.unpack('<b', bytes)[0])
    if type == 'uchar':
        return ord(struct.unpack('<c', bytes)[0])
    elif type == 'short':
        return struct.unpack('<h', bytes)[0]
    elif type == 'ushort':
        return struct.unpack('<H', bytes)[0]
    elif type == 'int':
        return struct.unpack('<i', bytes)[0]
    elif type == 'uint':
        return struct.unpack('<I', bytes)[0]
    elif type == 'float':
        return struct.unpack('<f', bytes)[0]
    elif type == 'double':
        return struct.unpack('<d', bytes)[0]
    else:
        raise UnkownTypeError('Type ' + type + ' is unknown')

class PLYParser(ModelParser):
    """Parser that parses a .ply file
    """

    def __init__(self, up_conversion = None):
        super().__init__(up_conversion)
        self.counter = 0
        self.elements = []
        self.inner_parser = PLYHeaderParser(self)
        self.beginning_of_line = ''
        self.header_finished = False

    def parse_bytes(self, bytes, byte_counter):
        """Parses bytes of a .ply file
        """
        if self.header_finished:
            self.inner_parser.parse_bytes(self.beginning_of_line + bytes, byte_counter - len(self.beginning_of_line))
            self.beginning_of_line = b''
            return

        # Build lines for header and use PLYHeaderParser
        current_line = self.beginning_of_line
        for (i, c) in enumerate(bytes):
            char = chr(c)
            if char == '\n':
                self.inner_parser.parse_line(current_line)
                if  current_line == 'end_header':
                    self.header_finished = True
                    self.beginning_of_line = bytes[i+1:]
                    return
                current_line = ''
            else:
                current_line += chr(c)
        self.beginning_of_line = current_line

class PLYHeaderParser:
    """Parser that parses the header of a .ply file
    """
    def __init__(self, parent):
        self.current_element = None
        self.parent = parent
        self.content_parser = None

    def parse_line(self, string):
        split = string.split()
        if string == 'ply':
            return

        elif split[0] == 'format':
            if split[2] != '1.0':
                print('Only format 1.0 is supported', file=sys.stderr)
                sys.exit(-1)

            if split[1] == 'ascii':
                self.content_parser = PLY_ASCII_ContentParser(self.parent)
            elif split[1] == 'binary_little_endian':
                self.content_parser = PLYLittleEndianContentParser(self.parent)
            elif split[1] == 'binary_big_endian':
                self.content_parser = PLYBigEndianContentParser(self.parent)
            else:
                print('Only ascii, binary_little_endian and binary_big_endian are supported', \
                      file=sys.stderr)
                sys.exit(-1)

        elif split[0] == 'element':
            self.current_element = PLYElement(split[1], int(split[2]))
            self.parent.elements.append(self.current_element)

        elif split[0] == 'property':
            self.current_element.add_property(split[-1], ' '.join(split[1:-1]))

        elif split[0] == 'end_header':
            self.parent.inner_parser = self.content_parser

        elif split[0] == 'comment' and split[1] == 'TextureFile':
            material = Material('mat' + str(len(self.parent.materials)))
            self.parent.materials.append(material)
            material.relative_path_to_texture = split[2]
            material.absolute_path_to_texture = os.path.join(os.path.dirname(self.parent.path), split[2])

class PLYElement:
    def __init__(self, name, number):
        self.name = name
        self.number = number
        self.properties = []

    def add_property(self, name, type):
        self.properties.append((name, type))

class PLY_ASCII_ContentParser:
    def __init__(self, parent):
        self.parent = parent
        self.element_index = 0
        self.counter = 0
        self.current_element = None
        self.beginning_of_line = ''

    def parse_bytes(self, bytes, byte_counter):
        current_line = self.beginning_of_line
        for (i, c) in enumerate(bytes):
            char = chr(c)
            if char == '\n':
                self.parse_line(current_line)
                current_line = ''
            else:
                current_line += chr(c)
        self.beginning_of_line = current_line


    def parse_line(self, string):

        if string == '':
            return

        if self.current_element is None:
            self.current_element = self.parent.elements[0]

        split = string.split()
        color = None

        if self.current_element.name == 'vertex':

            vertex = Vertex()
            red = None
            blue = None
            green = None
            alpha = None

            offset = 0
            for property in self.current_element.properties:

                if property[0] == 'x':
                    vertex.x = float(split[offset])
                elif property[0] == 'y':
                    vertex.y = float(split[offset])
                elif property[0] == 'z':
                    vertex.z = float(split[offset])
                elif property[0] == 'red':
                    red = float(split[offset]) / 255
                elif property[0] == 'green':
                    green = float(split[offset]) / 255
                elif property[0] == 'blue':
                    blue = float(split[offset]) / 255
                elif property[0] == 'alpha':
                    alpha = float(split[offset]) / 255

                offset += 1

            self.parent.add_vertex(vertex)

            if red is not None:
                color = Color(red, blue, green)
                self.parent.add_color(color)

        elif self.current_element.name == 'face':

            faceVertexArray = []
            current_material = None

            # Analyse element
            offset = 0
            for property in self.current_element.properties:

                if property[0] == 'vertex_indices':
                    for i in range(int(split[offset])):
                        faceVertexArray.append(FaceVertex(int(split[i+offset+1])))
                    offset += int(split[0]) + 1

                elif property[0] == 'texcoord':
                    offset += 1
                    for i in range(3):
                        # Create corresponding tex_coords
                        tex_coord = TexCoord().from_array(split[offset:offset+2])
                        offset += 2
                        self.parent.add_tex_coord(tex_coord)
                        faceVertexArray[i].tex_coord = len(self.parent.tex_coords) - 1

                elif property[0] == 'texnumber':
                    current_material = self.parent.materials[int(split[offset])]
                    offset += 1

            face = Face(*faceVertexArray)
            face.material = current_material
            self.parent.add_face(face)

        self.counter += 1

        if self.counter == self.current_element.number:
            self.next_element()

    def next_element(self):
        self.element_index += 1
        if self.element_index < len(self.parent.elements):
            self.current_element = self.parent.elements[self.element_index]

class PLYLittleEndianContentParser:
    def __init__(self, parent):
        self.parent = parent
        self.previous_bytes = b''
        self.element_index = 0
        self.counter = 0
        self.current_element = None
        self.started = False

        # Serves for debugging purposes
        # self.current_byte = 0

    def parse_bytes(self, bytes, byte_counter):

        if not self.started:
            # self.current_byte = byte_counter
            self.started = True

        if self.current_element is None:
            self.current_element = self.parent.elements[0]

        bytes = self.previous_bytes + bytes
        current_byte_index = 0

        while True:
            property_values = []

            beginning_byte_index = current_byte_index

            for property in self.current_element.properties:

                size = ply_type_size(property[1])

                if current_byte_index + size[0] > len(bytes):
                    self.previous_bytes = bytes[beginning_byte_index:]
                    # self.current_byte -= len(self.previous_bytes)
                    return

                if len(size) == 1:

                    size = size[0]

                    current_property_bytes = bytes[current_byte_index:current_byte_index+size]
                    property_values.append(bytes_to_element(property[1], current_property_bytes))
                    current_byte_index += size
                    # self.current_byte += size

                elif len(size) == 2:

                    types = property[1].split()[1:]
                    current_property_bytes = bytes[current_byte_index:current_byte_index+size[0]]
                    number_of_elements = bytes_to_element(types[0], current_property_bytes)
                    current_byte_index += size[0]
                    # self.current_byte += size[0]

                    property_values.append([])

                    # Parse list
                    for i in range(number_of_elements):

                        if current_byte_index + size[1] > len(bytes):

                            self.previous_bytes = bytes[beginning_byte_index:]
                            # self.current_byte -= len(self.previous_bytes)
                            return

                        current_property_bytes = bytes[current_byte_index:current_byte_index+size[1]]
                        property_values[-1].append(bytes_to_element(types[1], current_property_bytes))
                        current_byte_index += size[1]
                        # self.current_byte += size[1]


                else:
                    print('I have not idea what this means', file=sys.stderr)

            # Add element
            if self.current_element.name == 'vertex':

                vertex = Vertex()
                red = None
                green = None
                blue = None
                alpha = None
                offset = 0

                for property in self.current_element.properties:

                    if property[0] == 'x':
                        vertex.x = property_values[offset]
                    elif property[0] == 'y':
                        vertex.y = property_values[offset]
                    elif property[0] == 'z':
                        vertex.z = property_values[offset]
                    elif property[0] == 'red':
                        red = property_values[offset] / 255
                    elif property[0] == 'green':
                        green = property_values[offset] / 255
                    elif property[0] == 'blue':
                        blue = property_values[offset] / 255
                    elif property[0] == 'alpha':
                        alpha = property_values[offset] / 255

                    offset += 1

                self.parent.add_vertex(vertex)

                if red is not None:
                    self.parent.add_color(Color(red, blue, green))

            elif self.current_element.name == 'face':

                vertex_indices = []
                tex_coords = []
                material = None

                for (i, property) in enumerate(self.current_element.properties):

                    if property[0] == 'vertex_indices':
                        vertex_indices.append(property_values[i][0])
                        vertex_indices.append(property_values[i][1])
                        vertex_indices.append(property_values[i][2])

                    elif property[0] == 'texcoord':
                        # Create texture coords
                        for j in range(0,6,2):
                            tex_coord = TexCoord(*property_values[i][j:j+2])
                            tex_coords.append(tex_coord)

                    elif property[0] == 'texnumber':
                        material = self.parent.materials[property_values[i]]

                for tex_coord in tex_coords:
                    self.parent.add_tex_coord(tex_coord)

                face = Face(*list(map(lambda x: FaceVertex(x), vertex_indices)))

                counter = 3
                if len(tex_coords) > 0:
                    for face_vertex in [face.a, face.b, face.c]:
                        face_vertex.tex_coord = len(self.parent.tex_coords) - counter
                        counter -= 1

                if material is None and len(self.parent.materials) == 1:
                    material = self.parent.materials[0]

                face.material = material

                self.parent.add_face(face)

            self.counter += 1

            if self.counter == self.current_element.number:
                self.next_element()

    def next_element(self):
        self.counter = 0
        self.element_index += 1
        if self.element_index < len(self.parent.elements):
            self.current_element = self.parent.elements[self.element_index]



class PLYBigEndianContentParser(PLYLittleEndianContentParser):
    def __init__(self, parent):
        super().__init__(self, parent)

    def parse_bytes(self, bytes):
        # Reverse bytes, and then
        super().parse_bytes(self, bytes)

class PLYExporter(Exporter):
    def __init__(self, model):
        super().__init__(model)

    def __str__(self):

        faces = sum([part.faces for part in self.model.parts], [])

        # Header
        string = "ply\nformat ascii 1.0\ncomment Automatically gnerated by model-converter\n"

        for material in self.model.materials:
            string += "comment TextureFile " + (material.relative_path_to_texture or 'None') + "\n"

        # Types : vertices
        string += "element vertex " + str(len(self.model.vertices)) +"\n"
        string += "property float x\nproperty float y\nproperty float z\n"

        # Types : faces
        string += "element face " + str(len(faces)) + "\n"
        string += "property list uchar int vertex_indices\n"

        if len(self.model.tex_coords) > 0:
            string += "property list uchar float texcoord\n"
            string += "property int texnumber\n"

        # End header
        string += "end_header\n"

        # Content of the model
        for vertex in self.model.vertices:
            string += str(vertex.x) + " " + str(vertex.y) + " " + str(vertex.z) + "\n"

        for face in faces:
            string += "3 " + str(face.a.vertex) + " " + str(face.b.vertex) + " " + str(face.c.vertex)

            if len(self.model.tex_coords) > 0:
                string += " 6 " \
                       + str(self.model.tex_coords[face.a.tex_coord].x) + " " \
                       + str(self.model.tex_coords[face.a.tex_coord].y) + " " \
                       + str(self.model.tex_coords[face.b.tex_coord].x) + " " \
                       + str(self.model.tex_coords[face.b.tex_coord].y) + " " \
                       + str(self.model.tex_coords[face.c.tex_coord].x) + " " \
                       + str(self.model.tex_coords[face.c.tex_coord].y) + " " \
                       + str(self.model.get_material_index(face.material))

            string += "\n"

        return string


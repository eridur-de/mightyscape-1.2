from ..basemodel import TextModelParser, Exporter, Vertex, TexCoord, Normal, FaceVertex, Face
from ..mesh import Material, MeshPart
from functools import reduce
import os.path
import sys


def is_obj(filename):
    """Checks that the file is a .obj file

    Only checks the extension of the file
    :param filename: path to the file
    """
    return filename[-4:] == '.obj'

class OBJParser(TextModelParser):
    """Parser that parses a .obj file
    """

    def __init__(self, up_conversion = None):
        super().__init__(up_conversion)
        self.current_material = None
        self.mtl = None
        self.vertex_offset = 0

    def parse_line(self, string):
        """Parses a line of .obj file

        :param string: the line to parse
        """
        if string == '':
            return

        split = string.split()
        first = split[0]
        split = split[1:]

        if first == 'usemtl' and self.mtl is not None:
            self.current_material = self.mtl[split[0]]
        elif first == 'mtllib':
            path = os.path.join(os.path.dirname(self.path), ' '.join(split[:]))
            if os.path.isfile(path):
                self.mtl = MTLParser(self)
                self.mtl.parse_file(path)
            else:
                print('Warning : ' + path + ' not found ', file=sys.stderr)
        elif first == 'v':
            self.add_vertex(Vertex().from_array(split))
        elif first == 'vn':
            self.add_normal(Normal().from_array(split))
        elif first == 'vt':
            self.add_tex_coord(TexCoord().from_array(split))
        elif first == 'f':
            splits = list(map(lambda x: x.split('/'), split))

            for i in range(len(splits)):
                for j in range(len(splits[i])):
                    if splits[i][j] != '':
                        splits[i][j] = int(splits[i][j])
                        if splits[i][j] > 0:
                            splits[i][j] -= 1
                        else:
                            splits[i][j] = len(self.vertices) + splits[i][j]

            # if Face3
            if len(split) == 3:
                face = Face().from_array(splits)
                face.material = self.current_material
                self.add_face(face)

            #  Face4 are well supported with the next stuff
            # elif len(split) == 4:
            #     face = Face().from_array(splits[:3])
            #     face.material = self.current_material
            #     self.add_face(face)

            #     face = Face().from_array([splits[0], splits[2], splits[3]])
            #     face.material = self.current_material
            #     self.add_face(face)

            else:
                # Bweeee
                # First, lets compute all the FaceVertex for each vertex
                face_vertices = []
                for face_vertex in splits[:]:
                    face_vertices.append(FaceVertex(*face_vertex))

                # Then, we build the faces 0 i i+1 for each 1 <= i < len - 1
                for i in range(1, len(face_vertices) - 1):

                    # Create face with barycenter, i and i + 1
                    face = Face(face_vertices[0], face_vertices[i], face_vertices[i+1])
                    face.material = self.current_material
                    self.add_face(face)






class MTLParser:
    """Parser that parses a .mtl material file
    """
    def __init__(self, parent):
        """Creates a MTLParser bound to the OBJParser

        :param parent: the OBJParser this MTLParser refers to
        """
        self.parent = parent
        self.current_mtl = None

    def parse_line(self, string):
        """Parses a line of .mtl file

        :param string: line to  parse
        """

        if string == '':
            return

        split = string.split()
        first = split[0]
        split = split[1:]

        if first == 'newmtl':
            self.current_mtl = Material(' '.join(split[:]))
            self.parent.materials.append(self.current_mtl)
        elif first == 'Ka':
            self.current_mtl.Ka = Vertex().from_array(split)
        elif first == 'Kd':
            self.current_mtl.Kd = Vertex().from_array(split)
        elif first == 'Ks':
            self.current_mtl.Ks = Vertex().from_array(split)
        elif first == 'map_Kd':
            self.current_mtl.relative_path_to_texture = ' '.join(split)
            self.current_mtl.absolute_path_to_texture = os.path.join(os.path.dirname(self.parent.path), ' '.join(split))


    def parse_file(self, path):
        with open(path) as f:
            for line in f.readlines():
                line = line.rstrip()
                self.parse_line(line)

    def __getitem__(self, key):
        for material in self.parent.materials:
            if material.name == key:
                return material


class OBJExporter(Exporter):
    """Exporter to .obj format
    """

    def __init__(self, model):
        """Creates an exporter from the model

        :param model: Model to export
        """
        super().__init__(model)

    def __str__(self):
        """Exports the model
        """
        current_material = ''
        string = ""

        for vertex in self.model.vertices:
            string += "v " + ' '.join([str(vertex.x), str(vertex.y), str(vertex.z)]) + "\n"

        string += "\n"

        if len(self.model.tex_coords) > 0:
            for tex_coord in self.model.tex_coords:
                string += "vt " + ' '.join([str(tex_coord.x), str(tex_coord.y)]) + "\n"

            string += "\n"

        if len(self.model.normals) > 0:
            for normal in self.model.normals:
                string += "vn " + ' '.join([str(normal.x), str(normal.y), str(normal.z)]) + "\n"

            string += "\n"

        faces = sum(map(lambda x: x.faces, self.model.parts), [])

        for face in faces:
            if face.material is not None and face.material.name != current_material:
                current_material = face.material.name
                string += "usemtl " + current_material + "\n"
            string += "f "
            arr = []
            for v in [face.a, face.b, face.c]:
                sub_arr = []
                sub_arr.append(str(v.vertex + 1))
                if v.normal is None:
                    if v.tex_coord is not None:
                        sub_arr.append('')
                        sub_arr.append(str(v.tex_coord + 1))
                elif v.tex_coord is not None:
                    sub_arr.append(str(v.tex_coord + 1))
                    if v.normal is not None:
                        sub_arr.append(str(v.normal + 1))
                arr.append('/'.join(sub_arr))

            string += ' '.join(arr) + '\n'
        return string


from ..basemodel import TextModelParser, Exporter, Vertex, TexCoord, Normal, FaceVertex, Face
from ..mesh import Material, MeshPart

def is_off(filename):
    """Checks that the file is a .off file

    Only checks the extension of the file
    :param filename: path to the file
    """
    return filename[-4:] == '.off'

class OFFParser(TextModelParser):
    """Parser that parses a .off file
    """
    def __init__(self, up_conversion = None):
        super().__init__(up_conversion)
        self.vertex_number = None
        self.face_number = None
        self.edge_number = None

    def parse_line(self, string):
        """Parses a line of .off file

        :param string: the line to parse
        """
        split = string.split()

        if string == '' or string == 'OFF':
            pass
        elif self.vertex_number is None:
            # The first will be the header
            self.vertex_number = int(split[0])
            self.face_number = int(split[1])
            self.edge_number = int(split[2])
        elif len(self.vertices) < self.vertex_number:
            self.add_vertex(Vertex().from_array(split))
        else:
            self.add_face(Face(FaceVertex(int(split[1])), FaceVertex(int(split[2])), FaceVertex(int(split[3]))))



class OFFExporter(Exporter):
    """Exporter to .off format
    """
    def __init__(self, model):
        """Creates an exporter from the model

        :param model: Model to export
        """
        super().__init__(model)

    def __str__(self):
        """Exports the model
        """
        faces = sum(map(lambda x: x.faces, self.model.parts), [])
        string = "OFF\n{} {} {}".format(len(self.model.vertices), len(faces), 0) + '\n'

        for vertex in self.model.vertices:
            string += ' '.join([str(vertex.x), str(vertex.y), str(vertex.z)]) + '\n'

        for face in faces:
            string += '3 ' + ' '.join([str(face.a.vertex), str(face.b.vertex), str(face.c.vertex)]) + '\n'

        return string


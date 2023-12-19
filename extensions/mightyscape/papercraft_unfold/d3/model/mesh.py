class Material:
    """Represents a material

    It contains its constants and its texturess. It is also usable with OpenGL
    """
    def __init__(self, name):
        """ Creates an empty material

        :param name: name of the material:
        """
        self.name = name
        self.Ka = None
        self.Kd = None
        self.Ks = None
        self.relative_path_to_texture = None
        self.absolute_path_to_texture = None
        self.im = None
        self.id = None

    def init_texture(self):
        """ Initializes the OpenGL texture of the current material

        To be simple, calls glGenTextures and stores the given id
        """

        import OpenGL.GL as gl

        # Already initialized
        if self.id is not None:
            return

        # If no map_Kd, nothing to do
        if self.im is None:

            if self.absolute_path_to_texture is None:
                return

            try:
                import PIL.Image
                self.im = PIL.Image.open(self.absolute_path_to_texture)
            except ImportError:
                return

        try:
            ix, iy, image = self.im.size[0], self.im.size[1], self.im.tobytes("raw", "RGBA", 0, -1)
        except:
            ix, iy, image = self.im.size[0], self.im.size[1], self.im.tobytes("raw", "RGBX", 0, -1)

        self.id = gl.glGenTextures(1)

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.id)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT,1)

        gl.glTexImage2D(
            gl.GL_TEXTURE_2D, 0, 3, ix, iy, 0,
            gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, image
        )

    def bind(self):
        """Binds the material to OpenGL
        """
        from OpenGL import GL as gl

        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_DECAL)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.id)

    def unbind(self):
        """Disables the GL_TEXTURE_2D flag of OpenGL
        """
        from OpenGL import GL as gl

        gl.glDisable(gl.GL_TEXTURE_2D)

Material.DEFAULT_MATERIAL=Material('')
"""Material that is used when no material is specified
"""
Material.DEFAULT_MATERIAL.Ka = 1.0
Material.DEFAULT_MATERIAL.Kd = 0.0
Material.DEFAULT_MATERIAL.Ks = 0.0

try:
    import PIL.Image
    Material.DEFAULT_MATERIAL.im = PIL.Image.new("RGBA", (1,1), "white")
except ImportError:
    pass

class MeshPart:
    """A part of a 3D model that is bound to a single material
    """
    def __init__(self, parent):
        """Creates a mesh part

        :param parent: the global model with all the information
        """
        self.parent = parent
        self.material = None
        self.vertex_vbo = None
        self.tex_coord_vbo = None
        self.normal_vbo = None
        self.color_vbo = None
        self.faces = []

    def init_texture(self):
        """Initializes the material of the current parent
        """
        if self.material is not None:
            self.material.init_texture()

    def add_face(self, face):
        """Adds a face to this MeshPart

        :param face: face to add
        """
        self.faces.append(face)

    def generate_vbos(self):
        """Generates the vbo for this MeshPart

        Creates the arrays that are necessary for smooth rendering
        """

        from OpenGL.arrays import vbo
        from numpy import array

        # Build VBO
        v = []
        n = []
        t = []
        c = []

        for face in self.faces:
            v1 = self.parent.vertices[face.a.vertex]
            v2 = self.parent.vertices[face.b.vertex]
            v3 = self.parent.vertices[face.c.vertex]
            v += [[v1.x, v1.y, v1.z], [v2.x, v2.y, v2.z], [v3.x, v3.y, v3.z]]

            if face.a.normal is not None:
                n1 = self.parent.normals[face.a.normal]
                n2 = self.parent.normals[face.b.normal]
                n3 = self.parent.normals[face.c.normal]
                n += [[n1.x, n1.y, n1.z], [n2.x, n2.y, n2.z], [n3.x, n3.y, n3.z]]

            if face.a.tex_coord is not None:
                t1 = self.parent.tex_coords[face.a.tex_coord]
                t2 = self.parent.tex_coords[face.b.tex_coord]
                t3 = self.parent.tex_coords[face.c.tex_coord]
                t += [[t1.x, t1.y], [t2.x, t2.y], [t3.x, t3.y]]

            if len(self.parent.colors) > 0: # face.a.color is not None:
                c1 = self.parent.colors[face.a.vertex]
                c2 = self.parent.colors[face.b.vertex]
                c3 = self.parent.colors[face.c.vertex]
                c += [[c1.x, c1.y, c1.z], [c2.x, c2.y, c2.z], [c3.x, c3.y, c3.z]]

        self.vertex_vbo  = vbo.VBO(array(v, 'f'))

        if len(n) > 0:
            self.normal_vbo  = vbo.VBO(array(n, 'f'))

        if len(t) > 0:
            self.tex_coord_vbo = vbo.VBO(array(t, 'f'))

        if len(c) > 0:
            self.color_vbo = vbo.VBO(array(c, 'f'))

    def draw(self):
        """Draws the current MeshPart

        Binds the material, and draws the model
        """
        if self.material is not None:
            self.material.bind()

        if self.vertex_vbo is not None:
            self.draw_from_vbos()
        else:
            self.draw_from_arrays()

        if self.material is not None:
            self.material.unbind()

    def draw_from_vbos(self):
        """Simply calls the OpenGL drawArrays function

        Sets the correct vertex arrays and draws the part
        """

        import OpenGL.GL as gl

        self.vertex_vbo.bind()
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY);
        gl.glVertexPointerf(self.vertex_vbo)
        self.vertex_vbo.unbind()

        if self.normal_vbo is not None:
            self.normal_vbo.bind()
            gl.glEnableClientState(gl.GL_NORMAL_ARRAY)
            gl.glNormalPointerf(self.normal_vbo)
            self.normal_vbo.unbind()

        if self.tex_coord_vbo is not None:

            if self.material is not None:
                self.material.bind()

            self.tex_coord_vbo.bind()
            gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)
            gl.glTexCoordPointerf(self.tex_coord_vbo)
            self.tex_coord_vbo.unbind()

        if self.color_vbo is not None:
            self.color_vbo.bind()
            gl.glEnableClientState(gl.GL_COLOR_ARRAY)
            gl.glColorPointerf(self.color_vbo)
            self.color_vbo.unbind()

        gl.glDrawArrays(gl.GL_TRIANGLES, 0, len(self.vertex_vbo.data) * 9)

        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glDisableClientState(gl.GL_NORMAL_ARRAY)
        gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
        gl.glDisableClientState(gl.GL_COLOR_ARRAY)


    def draw_from_arrays(self):
        pass


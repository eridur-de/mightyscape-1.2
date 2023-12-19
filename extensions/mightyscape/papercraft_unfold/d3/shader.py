import os
dir_path = os.path.dirname(os.path.realpath(__file__))

import OpenGL.GL as gl
import OpenGL.GL.shaders as sh

default_vertex_path = dir_path + '/../assets/shaders/shader.vert'
default_fragment_path = dir_path + '/../assets/shaders/shader.frag'

class Shader:
    """Shader

    Loads, compile and binds the shader that are in the assets/shaders
    directory
    """

    def __init__(self, vertex_path = default_vertex_path, fragment_path = default_fragment_path):
        """Creates a shader object, and compile it

        :param vertex_path: path to the vertex shader
        :param fragment_path: path to the fragment shader
        """
        with open(vertex_path) as f:
            self.vertex_src = f.read()

        with open(fragment_path) as f:
            self.fragment_src = f.read()

        self.compile_shaders()
        self.compile_program()

    def compile_shaders(self):
        """ Compiles the shader
        """
        self.vertex_shader = sh.compileShader(self.vertex_src, gl.GL_VERTEX_SHADER)
        self.fragment_shader = sh.compileShader(self.fragment_src, gl.GL_FRAGMENT_SHADER)

    def compile_program(self):
        """Compile the shader program

        The shaders must be compiled
        """
        self.program = sh.compileProgram(self.vertex_shader, self.fragment_shader)

    def bind(self):
        """Bind the current shader to the OpenGL context
        """
        gl.glUseProgram(self.program)

    def unbind(self):
        """Reset OpenGL shader to 0
        """
        gl.glUseProgram(0)

from .geometry import Vector

import OpenGL.GLU as glu

class Camera:
    """Simple 3D camera
    """
    def __init__(self, position = Vector(1.0,0.0,0.0), target = Vector(), up = Vector(0.0,1.0,0.0)):
        """Creates a simple camera

        :param position: center of the camera
        :param target: point where the camera is looking
        :param up: up vector of the camera
        """
        self.position = position
        self.target = target
        self.up = up

    def look(self):
        """Sets the model view matrix of OpenGL

        Simply calls the gluLookAt function
        """
        glu.gluLookAt(
            self.position.x, self.position.y, self.position.z,
            self.target.x, self.target.y, self.target.z,
            self.up.x, self.up.y, self.up.z)

from .geometry import Vector

import pygame
import OpenGL.GL as gl
import math

class Controls:
    """Abstract class for controls
    """
    def __init__(self):
        pass

    def apply(self):
        """Apply the controls modification to the model view matrix
        """
        pass

    def update(self, time = 10):
        """Update according to the user's inputs
        """
        pass

class TrackBallControls(Controls):
    """Trackball controls

    Simple trackball controls"""

    def __init__(self):
        """Creates a TrackBallControls

        The trackball is centered at the origin
        """
        super().__init__()
        self.vertex = Vector()
        self.theta = 0

    def apply(self):
        """Apply the rotation of the current trackball
        """
        gl.glRotatef(self.theta * 180 / math.pi, self.vertex.x, self.vertex.y, self.vertex.z)

    def update(self, time = 10):
        """Checks the keyboard inputs and update the angle
        """
        if not pygame.mouse.get_pressed()[0]:
            return

        coeff = 0.001
        move = pygame.mouse.get_rel()

        dV = Vector(move[1] * time * coeff, move[0] * time * coeff, 0)
        dTheta = dV.norm2()

        if abs(dTheta) < 0.00001:
            return

        dV.normalize()

        cosT2 = math.cos(self.theta / 2)
        sinT2 = math.sin(self.theta / 2)
        cosDT2 = math.cos(dTheta / 2)
        sinDT2 = math.sin(dTheta / 2)

        A = cosT2 * sinDT2 * dV + cosDT2 * sinT2 * self.vertex + sinDT2 * sinT2 * Vector.cross_product(dV, self.vertex)

        self.theta = 2 * math.acos(cosT2 * cosDT2 - sinT2 * sinDT2 * Vector.dot(dV, self.vertex))

        self.vertex = A
        self.vertex.normalize()

class OrbitControls(Controls):
    """Simple OrbitControls

    Similar to TrackBallControls but the up vector is preserved"""

    def __init__(self):
        """Creates an OrbitControls with null angles
        """
        super().__init__()
        self.phi = 0
        self.theta = 0
        self.scale_log = 0

    def apply(self):
        scale = math.exp(self.scale_log)
        gl.glScalef(scale, scale, scale)
        gl.glRotatef(self.theta * 180 / math.pi, 1.0, 0.0, 0.0)
        gl.glRotatef(self.phi * 180 / math.pi, 0.0, 1.0, 0.0)

    def apply_event(self, event):
        """Manages the wheel event

        :param event: a pyevent
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Wheel up
            if event.button == 4:
                self.scale_log += 0.1
            # Wheel down
            elif event.button == 5:
                self.scale_log -= 0.1

    def update(self, time = 10):

        if not pygame.mouse.get_pressed()[0]:
            return

        move = pygame.mouse.get_rel()
        self.theta += move[1] * 0.01
        self.phi += move[0] * 0.01

        self.theta = max(min(self.theta, math.pi / 2), -math.pi / 2)

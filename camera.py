import math

from vector import Vector
from matrix import Matrix


class Camera:
    def __init__(self, width, height, position, rotation):
        self.height = height
        self.width = width
        self.position = position
        self.rotation = rotation

        self.translate = Matrix.identity()
        self.rotate = Matrix.identity()
        self.project = Matrix.identity()

    def update(self, dt, input_vector):
        s = dt * 5

        rotY = self.rotation.y / 180 * math.pi
        dx, dz = math.cos(rotY), math.sin(rotY)

        self.position += s * Vector(
            input_vector.x * dx + input_vector.z * dz,
            0,
            input_vector.x * dz - input_vector.z * dx,
        )

    def update_mouse(self, input_vector):
        self.rotation += input_vector

    @property
    def mvp_matrix(self):
        return self.translate @ self.rotate @ self.project

    def compute_matrices(self):
        self.project = Matrix.perspective(60, float(self.width) / self.height, 0.1, 500)
        self.rotate = Matrix.rotate_2d(2 * math.pi * self.rotation[1] / 360, 2 * math.pi * self.rotation[0] / 360)
        self.translate = Matrix.translate(-self.position)

import math

from vector import Vector
import matrix


class Camera:
    def __init__(self, shader, width, height, position, rotation):
        self.shader = shader
        self.height = height
        self.width = width
        self.position = position
        self.rotation = rotation

        self.mv_matrix = matrix.Matrix()
        self.r_matrix = matrix.Matrix()
        self.p_matrix = matrix.Matrix()

        # shaders
        self.shader = shader

    def update(self, dt, input_vector):
        s = dt * 5

        rotY = self.rotation.y / 180 * math.pi
        dx, dz = math.cos(rotY), math.sin(rotY)

        self.position += s * Vector(
                input_vector.x * dx + input_vector.z * dz,
                0,
                input_vector.x * dz - input_vector.z * dx)

    def update_mouse(self, input_vector):
        self.rotation += input_vector

    def apply(self):
        # create projection matrix

        self.p_matrix.load_identity()
        self.p_matrix.perspective(60, float(self.width) / self.height, 0.1, 500)

        # create modelview matrix

        self.r_matrix.load_identity()
        self.r_matrix.rotate_2d(
            2 * math.pi * self.rotation[1] / 360, 2 * math.pi * self.rotation[0] / 360
        )

        self.mv_matrix.load_identity()
        self.mv_matrix.rotate_2d(
            2 * math.pi * self.rotation[1] / 360, 2 * math.pi * self.rotation[0] / 360
        )
        self.mv_matrix.translate(
            -self.position[0], -self.position[1], -self.position[2]
        )

        # modelviewprojection matrix

        mvp_matrix = self.mv_matrix * self.p_matrix

        self.shader["matrix"] = mvp_matrix
        self.shader["camera"] = self.position

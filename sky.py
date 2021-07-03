import math

from texture_manager import TextureManager
from scene import Scene, Quad
from shader import Shader
from vector import Vector
from matrix import Matrix
import sun

# Bridge St
LONGITUDE = sun.radians(-73.985)
LATITUDE = sun.radians(40.6913)

class Sky:
    def __init__(self, show_grid):
        texture_manager = TextureManager(4096, 2048, 1)
        texture_manager.add_texture("starmap")

        self.show_grid = show_grid

        self.shader = Shader("sky")

        self.scene = Scene(texture_manager, max_vertices=13)
        self.scene.add_cube(1, Quad())

    @staticmethod
    def sun_position(utctime):
        return sun.position(LONGITUDE, LATITUDE, utctime)

    def draw(self, camera, utctime):
        self.shader.use()
        self.shader["rotation_matrix"] = camera.r_matrix
        self.shader["projection_matrix"] = camera.p_matrix

        declination_matrix = Matrix.rotate(math.pi/2 - LATITUDE, Vector(1.0, 0.0, 0.0))
        # TODO: This is totally inaccurate, but gives the correct effect.
        rotation_matrix = Matrix.rotate(2 * math.pi * sun.time_of_day(utctime) / (24 * 3600), Vector(0.0, 1.0, 0.0))

        matrix = declination_matrix @ rotation_matrix

        self.shader["celestial_matrix"] = matrix
        self.shader["sun_position"] = self.sun_position(utctime)
        self.shader["show_grid"] = self.show_grid
        self.scene.draw(self.shader)

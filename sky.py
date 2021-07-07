import math

from texture_manager import TextureManager
from scene import Scene, Quad
from shader import Shader
from vector import Vector
from matrix import Matrix
import sun

from pyglet import gl

# Bridge St
LONGITUDE = sun.radians(-73.985)
LATITUDE = sun.radians(40.6913)


class Sky:
    def __init__(self, show_grid, show_atmosphere):
        self.starmap_texture = TextureManager(4096, 2048, 1)
        self.starmap_texture.add_texture("starmap")

        self.moon_texture = TextureManager(1024, 512, 1)
        self.moon_texture.add_texture("moon")

        self.show_grid = show_grid
        self.show_atmosphere = show_atmosphere

        self.shader = Shader("sky")

        self.scene = Scene(max_vertices=13)
        self.scene.add_cube(1, Quad())

    @staticmethod
    def sun_position(utctime):
        return sun.position(LONGITUDE, LATITUDE, utctime)

    def draw(self, camera, utctime):
        self.shader.use()
        self.shader["rotation_matrix"] = camera.rotate
        self.shader["projection_matrix"] = camera.project

        declination_matrix = Matrix.rotate(math.pi / 2 - LATITUDE, Vector(1.0, 0.0, 0.0))
        # TODO: This is totally inaccurate, but gives the correct effect.
        rotation_matrix = Matrix.rotate(2 * math.pi * sun.time_of_day(utctime) / (24 * 3600), Vector(0.0, 1.0, 0.0))

        moon_matrix, moon_position = sun.moon_position(LONGITUDE, LATITUDE, utctime)
        matrix = declination_matrix @ rotation_matrix

        gl.glActiveTexture(gl.GL_TEXTURE0)
        self.starmap_texture.bind()
        self.shader["stars_array_sampler"] = 0

        gl.glActiveTexture(gl.GL_TEXTURE1)
        self.moon_texture.bind()
        self.shader["moon_array_sampler"] = 1

        self.shader["celestial_matrix"] = matrix
        self.shader["sun_position"] = self.sun_position(utctime)
        self.shader["moon_position"] = moon_position
        self.shader["moon_matrix"] = moon_matrix
        self.shader["show_grid"] = self.show_grid
        self.shader["show_atmosphere"] = self.show_atmosphere
        self.scene.draw(self.shader)

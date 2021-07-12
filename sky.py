from math import cos, sin, radians
from collections import namedtuple

from skyfield import api

from textures import Texture
from scene import Scene, Quad
from shader import Shader
from vector import Vector
from matrix import Matrix

# Bridge St
LONGITUDE = -73.985
LATITUDE = 39.6913

TS = api.load.timescale()
PLANETS = api.load("de421.bsp")
SUN, EARTH, MOON = PLANETS['sun'], PLANETS['earth'], PLANETS['moon']
BROOKLYN = EARTH + api.wgs84.latlon(LATITUDE, LONGITUDE)

def to_cartesian(alt, az, _distance=None):
    x = sin(az.radians) * cos(alt.radians)
    z = -cos(az.radians) * cos(alt.radians)
    y = sin(alt.radians)

    return Vector(x, y, z)

Astronomy = namedtuple('Astronomy', ('sun_position', 'moon_matrix', 'moon_position', 'celestial_matrix'))

def astronomy(utctime):
    t = TS.from_datetime(utctime.replace(tzinfo=api.utc))
    observer = BROOKLYN.at(t)

    declination_matrix = Matrix.rotate(radians(90 - LATITUDE), Vector(1.0, 0.0, 0.0))
    rotation_matrix = Matrix.rotate(radians(LONGITUDE + (360 * t.gmst / 24)), Vector(0.0, 1.0, 0.0))
    celestrial_matrix = declination_matrix @ rotation_matrix

    (moon_alt, moon_az, _) = observer.observe(MOON).apparent().altaz()
    moon_matrix = Matrix.rotate_2d(moon_az.radians, moon_alt.radians)
    moon_position = to_cartesian(moon_alt, moon_az)
    sun_position = to_cartesian(*observer.observe(SUN).apparent().altaz())
    return Astronomy(sun_position, moon_matrix, moon_position, celestrial_matrix)

class Sky:
    def __init__(self, show_grid, show_atmosphere):
        self.starmap_texture = Texture("starmap")
        self.moon_texture = Texture("moon")

        self.show_grid = show_grid
        self.show_atmosphere = show_atmosphere

        self.shader = Shader("sky")

        self.scene = Scene(max_vertices=13)
        self.scene.add_entity(1, Quad())

    def draw(self, camera, astro):
        self.shader.use()
        self.shader["rotation_matrix"] = camera.rotate
        self.shader["projection_matrix"] = camera.project

        self.starmap_texture.activate(0)
        self.shader["stars_array_sampler"] = 0

        self.moon_texture.activate(1)
        self.shader["moon_array_sampler"] = 1

        self.shader["celestial_matrix"] = astro.celestial_matrix
        self.shader["sun_position"] = astro.sun_position
        self.shader["moon_position"] = astro.moon_position
        self.shader["moon_matrix"] = astro.moon_matrix
        self.shader["show_grid"] = self.show_grid
        self.shader["show_atmosphere"] = self.show_atmosphere
        self.scene.draw()

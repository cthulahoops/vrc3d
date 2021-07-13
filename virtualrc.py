import queue
import pyglet

from vector import Vector
from scene import Scene, tex_coords, Cube, Mesh
from textures import TextureCube
from shader import Shader

COLORS = {
    "gray": "#919c9c",
    "pink": "#d95a88",
    "orange": "#e6a56e",
    "green": "#3dc06c",
    "blue": "#66bdff",
    "purple": "#956bc3",
    "yellow": "#e7dd6f",
}

WALL_COLORS = list(COLORS.keys())

PHOTOS = {}


def floor(textures):
    texture_index = textures.index("grid")

    x0, x1 = (0.5, 1000.5)
    y0, y1 = (0.5, 1000.5)

    return Cube(
        Vector(500, -1, 500),
        Vector(1000, 1, 1000),
        color="#eeeeee",
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def get_mesh(entity_type, entity, texture):
    position = Vector(entity["pos"]["x"], 0, entity["pos"]["y"])

    if entity["type"] == "Wall":
        return Cube(position, color=COLORS[entity["color"]])
    if entity["type"] == "Desk":
        leg_color = "#333333"
        mesh = Mesh()
        mesh += Cube(position, Vector(0.9, 0.04, 0.9), color=COLORS["orange"], offset=Vector(0, 0.35, 0))
        mesh += Cube(position, Vector(0.04, 0.35, 0.04), color=leg_color, offset=Vector(-0.4, 0, -0.4))
        mesh += Cube(position, Vector(0.04, 0.35, 0.04), color=leg_color, offset=Vector(-0.4, 0, 0.4))
        mesh += Cube(position, Vector(0.04, 0.35, 0.04), color=leg_color, offset=Vector(0.4, 0, -0.4))
        mesh += Cube(position, Vector(0.04, 0.35, 0.04), color=leg_color, offset=Vector(0.4, 0, 0.4))
        return mesh
    if entity["type"] == "Avatar":
        return Cube(position, Vector(0.05, 0.8, 0.4), color="#ffffff", texture=texture)
    if entity["type"] == "ZoomLink":
        return Cube(position, Vector(0.6, 0.6, 0.6), color="#0000ff", texture=texture)
    if entity["type"] == "Bot":
        return None
    if entity["type"] == "Link":
        return Cube(position, Vector(0.8, 0.8, 0.8), texture=texture)
    if entity["type"] == "Note":
        return Cube(position, color=COLORS["yellow"], texture=texture)
    if entity["type"] == "AudioBlock":
        return Cube(position, Vector(0.6, 0.6, 0.6), texture=texture)
    if entity["type"] == "RC::Calendar":
        return Cube(position, Vector(0.6, 0.6, 0.6), texture=texture)
    if entity["type"] == "AudioRoom":
        return Cube(position, Vector(entity["width"], 0.002, entity["height"]), texture=texture)
    return None


class VirtualRc:
    def __init__(self, camera, entity_queue):
        self.entity_queue = entity_queue

        self.shader = Shader("world")
        self.shader.use()

        self.building_textures = TextureCube(128, 128, 8)
        for name in [
            "empty",
            "audio_block",
            "calendar",
            "grid",
            "link",
            "microphone",
            "note",
            "zoom",
        ]:
            self.building_textures.add_texture(name)

        self.building = Scene()
        self.building.add_entity("floor", floor(self.building_textures))

        self.avatar_textures = TextureCube(150, 150, 50)
        self.avatar_textures.clamp_border(Vector(0.8, 0.8, 0.8))

        self.avatars = Scene(max_vertices=10_000)
        self.camera = camera

    def draw(self, sun_position, shadow_map):
        self.shader.use()
        self.shader["sun_position"] = sun_position
        self.shader["matrix"] = self.camera.mvp_matrix
        self.shader["camera"] = self.camera.position
        self.shader["light_space_matrix"] = shadow_map.light_space_matrix

        self.building_textures.activate(0)
        shadow_map.activate(1)
        self.shader["texture_array_sampler"] = 0
        self.shader["shadow_map"] = 1
        self.building.draw()

        self.avatar_textures.activate(0)
        shadow_map.activate(1)
        self.shader["texture_array_sampler"] = 0
        self.shader["shadow_map"] = 1
        self.avatars.draw()

    def update(self):
        try:
            while True:
                self.handle_entity(self.entity_queue.get_nowait())
        except queue.Empty:
            pass

    def add_entity(self, entity):
        entity_id = entity["id"]
        entity_type = entity["type"]

        if entity_type == "Avatar":
            scene = self.avatars
        else:
            scene = self.building

        texture = self.get_texture(entity_type, entity)
        mesh = get_mesh(entity_type, entity, texture)

        if mesh:
            scene.add_entity(entity_id, mesh)

    def get_texture(self, entity_type, entity):
        x0, x1 = (0.0, 1.0)
        y0, y1 = (0.0, 1.0)

        if entity_type == "Avatar":
            entity_id = entity["id"]
            x0, x1 = (-0.0, 1.0)
            y0, y1 = (-1.0, 1.0)

            try:
                self.avatar_textures.add_texture(entity_id, PHOTOS[entity_id])
                texture_index = self.avatar_textures.index(entity_id)
            except pyglet.gl.lib.GLException:
                return None
        elif entity_type == "ZoomLink":
            texture_index = self.building_textures.index("zoom")
        elif entity_type == "Link":
            texture_index = self.building_textures.index("link")
        elif entity_type == "AudioBlock":
            texture_index = self.building_textures.index("audio_block")
        elif entity_type == "RC::Calendar":
            texture_index = self.building_textures.index("calendar")
        elif entity["type"] == "AudioRoom":
            texture_index = self.building_textures.index("microphone")

            x0, x1 = (0.0, entity["width"])
            y0, y1 = (0.0, entity["height"])
        else:
            return None

        return tex_coords(x0, x1, y0, y1, texture_index)

    def handle_entity(self, entity):
        if entity.get("deleted"):
            if entity["type"] == "Avatar":
                self.avatars.delete_entity(entity["id"])
            else:
                self.building.delete_entity(entity["id"])
        else:
            self.add_entity(entity)

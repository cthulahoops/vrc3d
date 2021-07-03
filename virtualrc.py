import queue
import pyglet

from vector import Vector
from scene import Scene, tex_coords, Cube
from texture_manager import TextureManager
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


def add_wall(batch, entity):
    add_cube(batch, entity["id"], entity["pos"], color=COLORS[entity["color"]])


def add_note(batch, entity):
    add_cube(batch, entity["id"], entity["pos"], color=COLORS["yellow"])


def add_desk(batch, entity):
    add_cube(
        batch,
        (entity["id"], 5),
        entity["pos"],
        Vector(0.9, 0.04, 0.9),
        color=COLORS["orange"],
        offset=Vector(0, 0.35, 0),
    )
    add_cube(
        batch,
        (entity["id"], 0),
        entity["pos"],
        Vector(0.04, 0.35, 0.04),
        color="#33333",
        offset=Vector(-0.4, 0, -0.4),
    )
    add_cube(
        batch,
        (entity["id"], 1),
        entity["pos"],
        Vector(0.04, 0.35, 0.04),
        color="#33333",
        offset=Vector(-0.4, 0, 0.4),
    )
    add_cube(
        batch,
        (entity["id"], 2),
        entity["pos"],
        Vector(0.04, 0.35, 0.04),
        color="#33333",
        offset=Vector(0.4, 0, -0.4),
    )
    add_cube(
        batch,
        (entity["id"], 3),
        entity["pos"],
        Vector(0.04, 0.35, 0.04),
        color="#33333",
        offset=Vector(0.4, 0, 0.4),
    )


def add_calendar(batch, entity):
    texture_index = batch.texture_manager.textures.index("calendar")

    x0, x1 = (0.0, 1.0)
    y0, y1 = (0.0, 1.0)

    add_cube(
        batch,
        entity["id"],
        entity["pos"],
        Vector(0.6, 0.6, 0.6),
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def add_link(batch, entity):
    texture_index = batch.texture_manager.textures.index("link")

    x0, x1 = (0.0, 1.0)
    y0, y1 = (0.0, 1.0)

    add_cube(
        batch,
        entity["id"],
        entity["pos"],
        Vector(0.8, 0.8, 0.8),
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def add_zoomlink(batch, entity):
    texture_index = batch.texture_manager.textures.index("zoom")

    x0, x1 = (0.0, 1.0)
    y0, y1 = (0.0, 1.0)

    add_cube(
        batch,
        entity["id"],
        entity["pos"],
        Vector(0.6, 0.6, 0.6),
        color="#0000ff",
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def add_audioblock(batch, entity):
    texture_index = batch.texture_manager.textures.index("audio_block")

    x0, x1 = (0.0, 1.0)
    y0, y1 = (0.0, 1.0)

    add_cube(
        batch,
        entity["id"],
        entity["pos"],
        Vector(0.6, 0.6, 0.6),
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def add_audioroom(batch, entity):
    texture_index = batch.texture_manager.textures.index("microphone")

    x0, x1 = (0.0, entity["width"])
    y0, y1 = (0.0, entity["height"])

    pos = entity["pos"]
    pos["x"] += entity["width"] / 2 - 0.5
    pos["y"] += entity["height"] / 2 - 0.5

    add_cube(
        batch,
        entity["id"],
        pos,
        Vector(entity["width"], 0.002, entity["height"]),
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def add_avatar(batch, entity):
    entity_id = entity["id"]

    try:
        batch.texture_manager.add_texture(entity_id, PHOTOS[entity_id])
        texture_index = batch.texture_manager.textures.index(entity_id)
    except pyglet.gl.lib.GLException:
        texture_index = -1

    x0, x1 = (-0.0, 1.0)
    y0, y1 = (-1.0, 1.0)

    pos = entity["pos"]

    add_cube(
        batch,
        entity["id"],
        pos,
        Vector(0.05, 0.8, 0.4),
        color="#ffffff",
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def add_floor(batch):
    texture_index = batch.texture_manager.textures.index("grid")

    x0, x1 = (0.5, 1000.5)
    y0, y1 = (0.5, 1000.5)

    add_cube(
        batch,
        "floor",
        {"x": 500, "y": 500},
        Vector(1000, 0.0001, 1000),
        color="#eeeeee",
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def add_cube(scene, entity_id, entity_position, *a, **k):
    position = Vector(entity_position["x"], 0, entity_position["y"])
    cube = Cube(position, *a, **k)
    scene.add_cube(entity_id, cube)


class VirtualRc:
    def __init__(self, camera, entity_queue):
        self.entity_queue = entity_queue

        self.shader = Shader("world")
        self.shader.use()

        texture_manager = TextureManager(128, 128, 8)
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
            texture_manager.add_texture(name)

        self.building = Scene(texture_manager)
        add_floor(self.building)

        texture_manager = TextureManager(150, 150, 50)

        self.avatars = Scene(texture_manager, max_vertices=10_000)
        self.camera = camera

    def draw(self, sun_position):
        self.shader.use()
        self.shader["sun_position"] = sun_position
        self.shader["matrix"] = self.camera.mvp_matrix
        self.shader["camera"] = self.camera.position

        self.shader["tile_texture"] = 1
        self.building.draw(self.shader)
        self.shader["tile_texture"] = 0
        self.avatars.draw(self.shader)

    def update(self):
        try:
            while True:
                self.handle_entity(self.entity_queue.get_nowait())
        except queue.Empty:
            pass

    def add_entity(self, entity):
        entity_id = entity["id"]
        position = Vector(entity["pos"]["x"], 0, entity["pos"]["y"])

        if entity["type"] == "Wall":
            add_wall(self.building, entity)
        elif entity["type"] == "Desk":
            mesh = (
                Cube(position, Vector(0.9, 0.04, 0.9), color=COLORS["orange"], offset=Vector(0, 0.35, 0))
                + Cube(position, Vector(0.04, 0.35, 0.04), color="#33333", offset=Vector(-0.4, 0, -0.4))
                + Cube(position, Vector(0.04, 0.35, 0.04), color="#33333", offset=Vector(-0.4, 0, 0.4))
                + Cube(position, Vector(0.04, 0.35, 0.04), color="#33333", offset=Vector(0.4, 0, -0.4))
                + Cube(position, Vector(0.04, 0.35, 0.04), color="#33333", offset=Vector(0.4, 0, 0.4))
            )

            self.building.add_cube(entity_id, mesh)
        elif entity["type"] == "Avatar":
            add_avatar(self.avatars, entity)
        elif entity["type"] == "ZoomLink":
            add_zoomlink(self.building, entity)
        elif entity["type"] == "Bot":
            pass
        elif entity["type"] == "Link":
            add_link(self.building, entity)
        elif entity["type"] == "Note":
            add_note(self.building, entity)
        elif entity["type"] == "AudioBlock":
            add_audioblock(self.building, entity)
        elif entity["type"] == "RC::Calendar":
            add_calendar(self.building, entity)
        elif entity["type"] == "AudioRoom":
            add_audioroom(self.building, entity)
        else:
            print(entity["type"], entity)

    def handle_entity(self, entity):
        if entity.get("deleted"):
            if entity["type"] == "Avatar":
                self.avatars.delete_cube(entity["id"])
            else:
                self.building.delete_cube(entity["id"])
        else:
            self.add_entity(entity)

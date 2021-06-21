import io
import math
import threading
import asyncio
import queue
import functools
import aiohttp
import ctypes

import rctogether

from pyglet import gl
from pyglet.window import key
import pyglet

from camera import Camera
from vector import Vector
import shader
import texture_manager

COLORS = {
    "gray": "#919c9c",
    "pink": "#d95a88",
    "orange": "#e6a56e",
    "green": "#3dc06c",
    "blue": "#66bdff",
    "purple": "#956bc3",
    "yellow": "#e7dd6f",
}


# @functools.lru_cache(maxsize=None)
# def load_image(filename, file=None):
#     return pyglet.image.load(filename, file=file)


# @functools.lru_cache(maxsize=None)
# def get_texture(filename, file=None):
#     image = load_image(filename, file=file)
#     gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
#     gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
#     return pyglet.graphics.TextureGroup(image.get_texture())


def tex_coords(x0, x1, y0, y1, texture_index):
    return [ x0, y0, texture_index, x1, y0, texture_index, x1, y1, texture_index, x0, y1, texture_index ]

def color_to_rgb(color):
    return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))


def add_wall(batch, entity):
    add_cube(batch, entity["pos"], [1, 1, 1], color=COLORS[entity["color"]])


def add_note(batch, entity):
    add_cube(batch, entity["pos"], [1, 1, 1], color=COLORS["yellow"])


def add_desk(batch, entity):
    add_cube(batch, entity["pos"], [0.9, 0.04, 0.9], color=COLORS["orange"], y_offset=0.35)
    add_cube(batch, entity["pos"], [0.04, 0.35, 0.04], color="#33333", x_offset=-0.4, z_offset=-0.4)
    add_cube(batch, entity["pos"], [0.04, 0.35, 0.04], color="#33333", x_offset=-0.4, z_offset=0.4)
    add_cube(batch, entity["pos"], [0.04, 0.35, 0.04], color="#33333", x_offset=0.4, z_offset=-0.4)
    add_cube(batch, entity["pos"], [0.04, 0.35, 0.04], color="#33333", x_offset=0.4, z_offset=0.4)


def add_calendar(batch, entity):
    texture_index = batch.texture_manager.textures.index("calendar")

    x0, x1 = (0.0, 1.0)
    y0, y1 = (0.0, 1.0)

    add_cube(
        batch,
        entity["pos"],
        [0.6, 0.6, 0.6],
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def add_link(batch, entity):
    texture_index = batch.texture_manager.textures.index("link")

    x0, x1 = (0.0, 1.0)
    y0, y1 = (0.0, 1.0)

    add_cube(
        batch,
        entity["pos"],
        [0.8, 0.8, 0.8],
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def add_zoomlink(batch, entity):
    texture_index = batch.texture_manager.textures.index("zoom")

    x0, x1 = (0.0, 0.9)
    y0, y1 = (-0.1, 0.9)

    add_cube(
        batch,
        entity["pos"],
        [0.6, 0.6, 0.6],
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def add_audioblock(batch, entity):
    texture_index = batch.texture_manager.textures.index("audio_block")

    x0, x1 = (0.0, 1.0)
    y0, y1 = (0.0, 1.0)

    add_cube(
        batch,
        entity["pos"],
        [0.6, 0.6, 0.6],
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )

def add_audioroom(batch, entity):
    texture_index = batch.texture_manager.textures.index("microphone")

    x0, x1 = (0.0, entity["width"])
    y0, y1 = (0.0, entity["height"])

    pos = entity["pos"]
    pos['x'] += entity["width"] / 2 - 0.5
    pos['y'] += entity["height"] / 2 - 0.5

    add_cube(batch, pos, [entity["width"], 0.002, entity["height"]],
        texture=tex_coords(x0, x1, y0, y1, texture_index),
        )


def add_avatar(batch, entity):
    entity_id = entity['id']
    batch.texture_manager.add_texture(entity_id, PHOTOS[entity_id])
    texture_index = batch.texture_manager.textures.index(entity_id)
  #  texture = get_texture("avatar.png", file=io.BytesIO())
    texture_index = 0

    x0, x1 = (-0.0, 0.6)
    y0, y1 = (-0.4, 0.6)

    pos = entity['pos']

    add_cube(
        batch,
        pos,
        [0.05, 0.8, 0.4],
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def add_floor(batch):
    texture_index = batch.texture_manager.textures.index("grid")

    x0, x1 = (0.5, 1000.5)
    y0, y1 = (0.5, 1000.5)

    add_cube(
        batch,
        {"x": 500, "y": 500},
        [1000, 0.001, 1000],
        color = "#eeeeee",
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def add_cube(batch, *a, **k):
    batch.add_cube(*a, **k)

class Scene:
    def __init__(self, texture_manager):
        self.vertices = []
        self.colors = []
        self.normals = []
        self.tex_coords = []
        self.dirty = True

        self.texture_manager = texture_manager

    def add_cube(self, pos, size, texture=None, color=None, group=None, x_offset=0, y_offset=0, z_offset=0):
        pos = [pos["x"], 0, pos["y"]]
        x0, y0, z0 = x_offset + pos[0] - size[0] / 2, y_offset + pos[1], z_offset + pos[2] - size[2] / 2
        x1, y1, z1 = x_offset + pos[0] + size[0] / 2, y_offset + pos[1] + size[1], z_offset + pos[2] + size[2] / 2

        color = color or "#114433"

        (r, g, b) = color_to_rgb(color)
        colors = (r / 256, g / 256, b / 256) * 4

        if not texture:
            texture = tex_coords(0, 0, 1, 1, 0)

        vertices = [
            (x1, y0, z0, x0, y0, z0, x0, y1, z0, x1, y1, z0), # Back
            (x0, y0, z1, x1, y0, z1, x1, y1, z1, x0, y1, z1), # Front
            (x0, y0, z0, x0, y0, z1, x0, y1, z1, x0, y1, z0), # Left
            (x1, y0, z1, x1, y0, z0, x1, y1, z0, x1, y1, z1), # Right
            (x0, y0, z0, x1, y0, z0, x1, y0, z1, x0, y0, z1), # Bottom
            (x0, y1, z1, x1, y1, z1, x1, y1, z0, x0, y1, z0), # Top
        ]

        normals = [
            (0, 0, -1),
            (0, 0, 1),
            (-1, 0, 0),
            (1, 0, 0),
            (0, -1, 0),
            (0, 1, 0)
        ]

        for (v, n) in zip(vertices, normals):
            self.vertices.extend(v)
            self.colors.extend(colors)
            self.normals.extend(n * 4)
            self.tex_coords.extend(texture)

        self.dirty = True

#            batch.add(4, gl.GL_QUADS, group, ("v3f", v), tex_coords)

    def draw(self):
        if self.dirty:
            print("Required to regen buffers!")

            # Create a vertex array
            self.vao = gl.GLuint(0)
            gl.glGenVertexArrays(1, ctypes.byref(self.vao))
            gl.glBindVertexArray(self.vao)

            # create vertex position vbo
            self.vertex_position_vbo = gl.GLuint(0)
            gl.glGenBuffers(1, ctypes.byref(self.vertex_position_vbo))
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertex_position_vbo)

            gl.glBufferData(
                    gl.GL_ARRAY_BUFFER,
                    ctypes.sizeof(gl.GLfloat * len(self.vertices)),
                    (gl.GLfloat * len(self.vertices))(*self.vertices),
                    gl.GL_STATIC_DRAW)
            gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
            gl.glEnableVertexAttribArray(0)

            # create color data vbo
            self.color_vbo = gl.GLuint(0)
            gl.glGenBuffers(1, ctypes.byref(self.color_vbo))
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.color_vbo)

            gl.glBufferData(
                    gl.GL_ARRAY_BUFFER,
                    ctypes.sizeof(gl.GLfloat * len(self.colors)),
                    (gl.GLfloat * len(self.colors))(*self.colors),
                    gl.GL_STATIC_DRAW)

            gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
            gl.glEnableVertexAttribArray(1)

            # create normal data vbo
            normal_vbo = gl.GLuint(0)
            gl.glGenBuffers(1, ctypes.byref(normal_vbo))
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, normal_vbo)

            gl.glBufferData(
                    gl.GL_ARRAY_BUFFER,
                    ctypes.sizeof(gl.GLfloat * len(self.normals)),
                    (gl.GLfloat * len(self.normals))(*self.normals),
                    gl.GL_STATIC_DRAW)

            gl.glVertexAttribPointer(2, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
            gl.glEnableVertexAttribArray(2)

            # create tex_coords data vbo
            tex_coords_vbo = gl.GLuint(0)
            gl.glGenBuffers(1, ctypes.byref(tex_coords_vbo))
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, tex_coords_vbo)

            gl.glBufferData(
                    gl.GL_ARRAY_BUFFER,
                    ctypes.sizeof(gl.GLfloat * len(self.tex_coords)),
                    (gl.GLfloat * len(self.tex_coords))(*self.tex_coords),
                    gl.GL_STATIC_DRAW)

            gl.glVertexAttribPointer(3, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
            gl.glEnableVertexAttribArray(3)

            self.dirty = False

        gl.glDrawArrays(gl.GL_QUADS, 0, len(self.vertices))

class World:
    def __init__(self, queue):
        self.queue = queue

        self.window = pyglet.window.Window(
            caption="VRC3D", resizable=True, fullscreen=True
        )
        self.window.set_mouse_visible(False)
        self.window.set_exclusive_mouse(True)
        (r, g, b) = color_to_rgb("#87ceeb")
        gl.glClearColor(r / 255, g / 255, b / 255, 1)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glShadeModel(gl.GL_SMOOTH)

        self.window.event(self.on_draw)
        self.window.event(self.on_mouse_motion)
        self.window.event(self.on_key_press)
        pyglet.clock.schedule(self.update)

        self.shader = shader.Shader("vert.glsl", "frag.glsl")
        self.shader_sampler_location = self.shader.find_uniform(b"texture_array_sampler")
        self.shader.use()


        tm = texture_manager.TextureManager(128, 128, 8)
        for name in ["empty", "audio_block", "calendar", "grid", "link", "microphone", "note", "zoom"]:
            tm.add_texture(name)
        tm.generate_mipmaps()

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, tm.texture_array)

        self.batch = Scene(tm)
        add_floor(self.batch)

        tm = texture_manager.TextureManager(150, 150, 50)

        tm.generate_mipmaps()
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, tm.texture_array)

        self.avatars = Scene(tm)

        self.camera = Camera(
                self.shader,
                self.window.width,
                self.window.height,
                Vector([45, 0.6, 53]),
                Vector([0, 90])
            )

        self.keys = key.KeyStateHandler()
        self.window.push_handlers(self.keys)

    def on_key_press(self, KEY, MOD):
        if KEY == key.ESCAPE:
            print(self.camera.position)
            self.window.close()

    def on_mouse_motion(self, x, y, dx, dy):
        self.camera.update_mouse(Vector([dy/6, dx/6]))

    def on_draw(self):
        self.window.clear()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.gluPerspective(60, self.window.width / self.window.height, 0.05, 1000)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        self.camera.apply()

        gl.glUniform1i(self.shader_sampler_location, 0)
        self.batch.draw()
#        gl.glUniform1i(self.shader_sampler_location, 1)
#        self.avatars.draw()

    def update(self, dt):
        try:
            while True:
                entity = self.queue.get_nowait()
                if entity["type"] == "Wall":
                    add_wall(self.batch, entity)
                elif entity["type"] == "Desk":
                    add_desk(self.batch, entity)
                elif entity["type"] == "Avatar":
                    add_avatar(self.avatars, entity)
                elif entity["type"] == "ZoomLink":
                    add_zoomlink(self.batch, entity)
                elif entity["type"] == "Bot":
                    pass
                elif entity["type"] == "Link":
                    add_link(self.batch, entity)
                elif entity["type"] == "Note":
                    add_note(self.batch, entity)
                elif entity["type"] == "AudioBlock":
                    add_audioblock(self.batch, entity)
                elif entity["type"] == "RC::Calendar":
                    add_calendar(self.batch, entity)
                elif entity["type"] == "AudioRoom":
                    add_audioroom(self.batch, entity)
                else:
                    print(entity["type"], entity)

        except queue.Empty:
            pass

        input_vector = Vector([0, 0, 0])
        if self.keys[key.COMMA] or self.keys[key.UP]:
            input_vector += Vector([0, 0, 1])
        if self.keys[key.O] or self.keys[key.DOWN]:
            input_vector += Vector([0, 0, -1])
        if self.keys[key.A] or self.keys[key.LEFT]:
            input_vector += Vector([-1, 0, 0])
        if self.keys[key.E] or self.keys[key.RIGHT]:
            input_vector += Vector([1, 0, 0])

        self.camera.update(dt, input_vector)


# async def async_2d_avatar():
# 👾

PHOTOS = {}


def photo_path(avatar_id, extension):
    return "photos/%d.%s" % (avatar_id, extension)

def get_photo_ext(avatar_id, extension):
    try:
        with open(photo_path(avatar_id, extension), "rb") as fh:
            return fh.read()
    except FileNotFoundError:
        return None

async def get_photo(session, avatar_id, image_path):
    image_data = (
        get_photo_ext(avatar_id, "jpeg")
        or get_photo_ext(avatar_id, "png") \
        or await download_photo(session, avatar_id, image_path))

    PHOTOS[avatar_id] = image_data
    return image_data


async def download_photo(session, avatar_id, image_path):
    print("FETCH: ", image_path)
    async with session.get(image_path) as response:
        image_data = await response.read()

        if response.content_type == 'image/jpeg':
            extension = 'jpeg'
        elif response.content_type == 'image/png':
            extension = 'png'

        with open(photo_path(avatar_id, extension), 'wb') as fh:
            fh.write(image_data)

    return image_data




async def async_thread_main(queue):
    async with aiohttp.ClientSession() as session:
        async for entity in rctogether.WebsocketSubscription():
            if entity["type"] == "Avatar" and entity["id"] not in PHOTOS:
                await get_photo(session, entity["id"], entity["image_path"])
            queue.put(entity)

def main():
    entity_queue = queue.Queue()

    async_thread = threading.Thread(
        target=lambda: asyncio.run(async_thread_main(entity_queue)), daemon=True
    )
    async_thread.start()

    world = World(entity_queue)

    pyglet.app.run()


if __name__ == "__main__":
    main()

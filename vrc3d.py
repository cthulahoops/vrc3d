import ctypes
import threading
import asyncio
import queue
from queue import Queue
import traceback
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

import aiohttp

import rctogether
from rctogether import walls

from pyglet import gl
from pyglet.window import key
import pyglet


from camera import Camera
from vector import Vector
from shader import Shader
from texture_manager import TextureManager
import photos

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

def tex_coords(x0, x1, y0, y1, texture_index):
    return [
        x0,
        y0,
        texture_index,
        x1,
        y0,
        texture_index,
        x1,
        y1,
        texture_index,
        x0,
        y1,
        texture_index,
    ]


def color_to_rgb(color):
    return (int(color[1:3], 16) / 255, int(color[3:5], 16) / 255, int(color[5:7], 16) / 255)


def add_wall(batch, entity):
    add_cube(batch, entity['id'], entity["pos"], color=COLORS[entity["color"]])


def add_note(batch, entity):
    add_cube(batch, entity['id'], entity["pos"], color=COLORS["yellow"])


def add_desk(batch, entity):
    add_cube(
        batch,
        (entity['id'], 5),
        entity["pos"],
        Vector(0.9, 0.04, 0.9),
        color=COLORS["orange"],
        offset=Vector(0, 0.35, 0)
    )
    add_cube(
        batch,
        (entity['id'], 0),
        entity["pos"],
        Vector(0.04, 0.35, 0.04),
        color="#33333",
        offset=Vector(-0.4, 0, -0.4)
    )
    add_cube(
        batch,
        (entity['id'], 1),
        entity["pos"],
        Vector(0.04, 0.35, 0.04),
        color="#33333",
        offset=Vector(-0.4, 0, 0.4)
    )
    add_cube(
        batch,
        (entity['id'], 2),
        entity["pos"],
        Vector(0.04, 0.35, 0.04),
        color="#33333",
        offset=Vector(0.4, 0, -0.4)
    )
    add_cube(
        batch,
        (entity['id'], 3),
        entity["pos"],
        Vector(0.04, 0.35, 0.04),
        color="#33333",
        offset=Vector(0.4, 0, 0.4)
    )


def add_calendar(batch, entity):
    texture_index = batch.texture_manager.textures.index("calendar")

    x0, x1 = (0.0, 1.0)
    y0, y1 = (0.0, 1.0)

    add_cube(
        batch,
        entity['id'],
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
        entity['id'],
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
        entity['id'],
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
        entity['id'],
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
        entity['id'],
        pos,
        Vector(entity["width"], 0.002, entity["height"]),
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def add_avatar(batch, entity):
    entity_id = entity["id"]
    batch.texture_manager.add_texture(entity_id, PHOTOS[entity_id])
    texture_index = batch.texture_manager.textures.index(entity_id)
    print("Texture index: ", texture_index)
    #  texture = get_texture("avatar.png", file=io.BytesIO())

    x0, x1 = (-0.0, 1.0)
    y0, y1 = (-1.0, 1.0)

    pos = entity["pos"]

    add_cube(
        batch,
        entity['id'],
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
        -1,
        {"x": 500, "y": 500},
        Vector(1000, 0.001, 1000),
        color="#eeeeee",
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def add_cube(scene, entity_id, entity_position, *a, **k):
    position = Vector(entity_position["x"], 0, entity_position["y"])
    cube = Cube(position, *a, **k)
    scene.add_cube(entity_id, cube)


class VertexArrayObject:
    def __init__(self):
        self._id = gl.GLuint(0)
        gl.glGenVertexArrays(1, ctypes.byref(self._id))

    def __enter__(self):
        gl.glBindVertexArray(self._id)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        gl.glBindVertexArray(0)


class VertexBufferObject:
    def __init__(self):
        self._id = gl.GLuint(0)
        gl.glGenBuffers(1, ctypes.byref(self._id))

    def __enter__(self):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._id)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def write_slice(self, offset, data):
        print("WRITE: ", offset, len(data))
        with self:
            gl.glBufferSubData(
                gl.GL_ARRAY_BUFFER,
                ctypes.sizeof(gl.GLfloat) * offset,
                ctypes.sizeof(gl.GLfloat) * len(data),
                (gl.GLfloat * len(data))(*data),
            )

    def write(self, data):
        with self:
            gl.glBufferData(
                gl.GL_ARRAY_BUFFER,
                ctypes.sizeof(gl.GLfloat) * len(data),
                (gl.GLfloat * len(data))(*data),
                gl.GL_DYNAMIC_DRAW,
            )

class Cube:
    def __init__(self, pos, size=Vector(1, 1, 1), texture=None, color=None, offset=Vector(0, 0, 0)):

        a = pos + offset - Vector(size.x, 0, size.z) / 2
        b = a + size

        colors = color_to_rgb(color or "#114433") * 4

        if not texture:
            texture = tex_coords(0, 0, 1, 1, -1)

        vertices = [
            (b.x, a.y, a.z, a.x, a.y, a.z, a.x, b.y, a.z, b.x, b.y, a.z),  # Back
            (a.x, a.y, b.z, b.x, a.y, b.z, b.x, b.y, b.z, a.x, b.y, b.z),  # Front
            (a.x, a.y, a.z, a.x, a.y, b.z, a.x, b.y, b.z, a.x, b.y, a.z),  # Left
            (b.x, a.y, b.z, b.x, a.y, a.z, b.x, b.y, a.z, b.x, b.y, b.z),  # Right
            (a.x, a.y, a.z, b.x, a.y, a.z, b.x, a.y, b.z, a.x, a.y, b.z),  # Bottom
            (a.x, b.y, b.z, b.x, b.y, b.z, b.x, b.y, a.z, a.x, b.y, a.z),  # Top
        ]

        normals = [(0, 0, -1), (0, 0, 1), (-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0)]

        self.vertices = []
        self.colors = []
        self.normals = []
        self.tex_coords = []

        for (v, n) in zip(vertices, normals):
            self.vertices.extend(v)
            self.colors.extend(colors)
            self.normals.extend(n * 4)
            self.tex_coords.extend(texture)


Mesh = namedtuple('Mesh', ('vertices', 'colors', 'normals', 'tex_coords'))

class Scene:
    def __init__(self, texture_manager):
        self.entities = {}

        self.texture_manager = texture_manager

        self.data_size = 0
        self.buffer_size = 0

        self.vao = VertexArrayObject()
        with self.vao:
            self.buffers = Mesh(
                VertexBufferObject(),
                VertexBufferObject(),
                VertexBufferObject(),
                VertexBufferObject()
            )

            self.allocate_buffers(500_000)

    def delete_cube(self, entity_id):
        offset = self.entities[entity_id]
        print("Handling deletion: ", entity_id, " at ", offset)

        size = 72

        self.buffers.tex_coords.write_slice(offset, [-2] * size)

    def add_cube(self, entity_id, cube):
        if entity_id in self.entities:
            offset = self.entities[entity_id]

            print("Creating at: ", offset, len(cube.vertices))

            for (vbo, data) in [
                    (self.buffers.vertices, cube.vertices),
                    (self.buffers.colors, cube.colors),
                    (self.buffers.normals, cube.normals),
                    (self.buffers.tex_coords, cube.tex_coords)]:
                vbo.write_slice(offset, data)

        elif self.data_size + len(cube.vertices) < self.buffer_size:
            offset = self.entities[entity_id] = self.data_size
            print(f"Adding new at: {entity_id} at  {self.data_size}")
            self.data_size += len(cube.vertices)

            for (vbo, data) in [
                    (self.buffers.vertices, cube.vertices),
                    (self.buffers.colors, cube.colors),
                    (self.buffers.normals, cube.normals),
                    (self.buffers.tex_coords, cube.tex_coords)]:

                vbo.write_slice(offset, data)
        else:
            raise Exception("Ooops!")

    def allocate_buffers(self, size):
        self.buffer_size = size
        self.data_size = 0

        for (vbo, layout_offset) in [
            (self.buffers.vertices, 0),
            (self.buffers.colors, 1),
            (self.buffers.normals, 2),
            (self.buffers.tex_coords, 3),
        ]:
            vbo.write([0] * self.buffer_size)
            with vbo:
                gl.glVertexAttribPointer(
                    layout_offset, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, 0
                )
                gl.glEnableVertexAttribArray(layout_offset)

    def draw(self, shader):
        with self.vao:
            gl.glBindTexture(
                gl.GL_TEXTURE_2D_ARRAY, self.texture_manager.texture_array
            )
            shader["texture_array_sampler"] = 1
            gl.glDrawArrays(gl.GL_QUADS, 0, self.data_size)


class World:
    def __init__(self, entity_queue, avatar_update_queue):
        self.entity_queue = entity_queue
        self.avatar_update_queue = avatar_update_queue

        self.window = pyglet.window.Window(
            caption="VRC3D", resizable=True, fullscreen=False
        )
        self.window.set_mouse_visible(False)
        self.window.set_exclusive_mouse(True)
        (r, g, b) = color_to_rgb("#87ceeb")
        gl.glClearColor(r, g, b, 1)

        gl.glEnable(gl.GL_DEPTH_TEST)

        self.window.event(self.on_draw)
        self.window.event(self.on_mouse_motion)
        self.window.event(self.on_key_press)
        pyglet.clock.schedule(self.update)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glActiveTexture(gl.GL_TEXTURE1)

        self.shader = Shader("vert.glsl", "frag.glsl")
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


        self.batch = Scene(texture_manager)
        add_floor(self.batch)

        texture_manager = TextureManager(150, 150, 50)


        self.avatars = Scene(texture_manager)

        self.camera = Camera(
            self.shader,
            self.window.width,
            self.window.height,
            Vector(45, 0.6, 53),
            Vector(0, 90),
        )
        self.pos = None

        self.keys = key.KeyStateHandler()
        self.window.push_handlers(self.keys)

        self.active_color = 0

    def on_key_press(self, KEY, MOD):
        if KEY == key.ESCAPE:
            print(self.camera.position)
            self.window.close()
        elif KEY == key.X:
            self.avatar_update_queue.put({'type': 'wall', 'payload': {'action': 'create', 'color': WALL_COLORS[self.active_color % len(WALL_COLORS)]}})
        elif KEY == key.C:
            self.active_color += 1
            self.avatar_update_queue.put({'type': 'wall', 'payload': {'action': 'update', 'color': WALL_COLORS[self.active_color % len(WALL_COLORS)]}})


    def on_mouse_motion(self, x, y, dx, dy):
        self.camera.update_mouse(Vector(dy / 6, dx / 6))

    def on_draw(self):
        self.window.clear()
        self.camera.apply()
        self.shader["tile_texture"] = 1
        self.batch.draw(self.shader)
        self.shader["tile_texture"] = 0
        self.avatars.draw(self.shader)

    def handle_entity(self, entity):
        if entity.get('deleted'):
            if entity["type"] == "Avatar":
                self.avatars.delete_cube(entity["id"])
            else:
                self.batch.delete_cube(entity["id"])
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

    def update(self, dt):
        try:
            while True:
                self.handle_entity(self.entity_queue.get_nowait())
        except queue.Empty:
            pass

        input_vector = Vector(0, 0, 0)
        if self.keys[key.COMMA] or self.keys[key.UP]:
            input_vector += Vector(0, 0, 1)
        if self.keys[key.O] or self.keys[key.DOWN]:
            input_vector += Vector(0, 0, -1)
        if self.keys[key.A] or self.keys[key.LEFT]:
            input_vector += Vector(-1, 0, 0)
        if self.keys[key.E] or self.keys[key.RIGHT]:
            input_vector += Vector(1, 0, 0)

        self.camera.update(dt, input_vector)
        pos = {
            'x': round(self.camera.position.x),
            'y': round(self.camera.position.z),
            'direction': ['up', 'right', 'down', 'left'][round(self.camera.rotation.y / 90) % 4]
        }

        self.camera.update(dt, input_vector)

        pos = avatar_position(self.camera)

        if pos != self.pos:
            self.avatar_update_queue.put({'type': 'pos', 'payload': pos})
            self.pos = pos


def avatar_position(camera):
    return {
        'x': round(camera.position.x),
        'y': round(camera.position.z),
        'direction': ['up', 'right', 'down', 'left'][round(camera.rotation.y / 90) % 4]
    }

async def space_avatar_worker(avatars_update_queue):
    async with rctogether.RestApiSession() as session:
        bot_id = None
        for bot in await rctogether.bots.get(session):
            if bot['emoji'] == "👾":
                bot_id = bot['id']

        with ThreadPoolExecutor(max_workers=1) as executor:
            loop = asyncio.get_event_loop()
            while message := await loop.run_in_executor(executor, avatars_update_queue.get):
                try:
                    if message['type'] == 'pos':
                        pos = message['payload']

                        if bot_id:
                            await rctogether.bots.update(session, bot_id, pos)
                        else:
                            bot = await rctogether.bots.create(
                                    session,
                                    name="Extra-dimensional Avatar",
                                    emoji="👾",
                                    x=pos['x'],
                                    y=pos['y'])
                            bot_id = bot['id']
                    elif message['type'] == 'wall':
                        if message['payload']['action'] == 'create':
                            await walls.create(session, bot_id=bot_id, color=message['payload']['color'])
                        elif message['payload']['action'] == 'upload':
                            pass # Not supported without getting the wall id.
                            # await walls.update(session, bot_id=bot_id, color=message['payload']['color'])
                except rctogether.api.HttpError:
                    traceback.print_exc()


async def async_thread_main(entity_queue, avatar_update_queue_future):
    asyncio.create_task(space_avatar_worker(avatar_update_queue_future))

    async with aiohttp.ClientSession() as session:
        async for entity in rctogether.WebsocketSubscription():
            if entity["type"] == "Avatar" and entity["id"] not in PHOTOS:
                image_data = await photos.get_photo(session, entity["id"], entity["image_path"])
                PHOTOS[entity["id"]] = image_data
            entity_queue.put(entity)


def main():
    entity_queue = Queue()
    avatar_update_queue = Queue()

    async_thread = threading.Thread(
            target=lambda: asyncio.run(async_thread_main(entity_queue, avatar_update_queue))
    )
    async_thread.start()

    World(entity_queue, avatar_update_queue)
    pyglet.app.run()
    avatar_update_queue.put(None)



if __name__ == "__main__":
    main()

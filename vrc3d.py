import ctypes
import threading
import asyncio
import queue
from queue import Queue
import aiohttp
from concurrent.futures import ThreadPoolExecutor

import rctogether
from rctogether import walls
import traceback

from pyglet import gl
from pyglet.window import key
import pyglet

from camera import Camera
from vector import Vector
from shader import Shader
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

WALL_COLORS = list(COLORS.keys())


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
    return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))


def add_wall(batch, entity):
    add_cube(batch, entity['id'], entity["pos"], [1, 1, 1], color=COLORS[entity["color"]])


def add_note(batch, entity):
    add_cube(batch, entity['id'], entity["pos"], [1, 1, 1], color=COLORS["yellow"])


def add_desk(batch, entity):
    add_cube(
        batch, (entity['id'], 5), entity["pos"], [0.9, 0.04, 0.9], color=COLORS["orange"], y_offset=0.35
    )
    add_cube(
        batch,
        (entity['id'], 0),
        entity["pos"],
        [0.04, 0.35, 0.04],
        color="#33333",
        x_offset=-0.4,
        z_offset=-0.4,
    )
    add_cube(
        batch,
        (entity['id'], 1),
        entity["pos"],
        [0.04, 0.35, 0.04],
        color="#33333",
        x_offset=-0.4,
        z_offset=0.4,
    )
    add_cube(
        batch,
        (entity['id'], 2),
        entity["pos"],
        [0.04, 0.35, 0.04],
        color="#33333",
        x_offset=0.4,
        z_offset=-0.4,
    )
    add_cube(
        batch,
        (entity['id'], 3),
        entity["pos"],
        [0.04, 0.35, 0.04],
        color="#33333",
        x_offset=0.4,
        z_offset=0.4,
    )


def add_calendar(batch, entity):
    texture_index = batch.texture_manager.textures.index("calendar")

    x0, x1 = (0.0, 1.0)
    y0, y1 = (0.0, 1.0)

    add_cube(
        batch,
        entity['id'],
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
        entity['id'],
        entity["pos"],
        [0.8, 0.8, 0.8],
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
        [0.6, 0.6, 0.6],
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
        [0.6, 0.6, 0.6],
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
        [entity["width"], 0.002, entity["height"]],
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
        [0.05, 0.8, 0.4],
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
        [1000, 0.001, 1000],
        color="#eeeeee",
        texture=tex_coords(x0, x1, y0, y1, texture_index),
    )


def add_cube(scene, entity_id, *a, **k):
    cube = Cube(*a, **k)
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

class Cube:
    def __init__(self, pos, size, texture=None, color=None, x_offset=0, y_offset=0, z_offset=0):
        pos = [pos["x"], 0, pos["y"]]
        x0, y0, z0 = (
            x_offset + pos[0] - size[0] / 2,
            y_offset + pos[1],
            z_offset + pos[2] - size[2] / 2,
        )
        x1, y1, z1 = (
            x_offset + pos[0] + size[0] / 2,
            y_offset + pos[1] + size[1],
            z_offset + pos[2] + size[2] / 2,
        )

        color = color or "#114433"

        (r, g, b) = color_to_rgb(color)
        colors = (r / 256, g / 256, b / 256) * 4

        if not texture:
            texture = tex_coords(0, 0, 1, 1, -1)

        vertices = [
            (x1, y0, z0, x0, y0, z0, x0, y1, z0, x1, y1, z0),  # Back
            (x0, y0, z1, x1, y0, z1, x1, y1, z1, x0, y1, z1),  # Front
            (x0, y0, z0, x0, y0, z1, x0, y1, z1, x0, y1, z0),  # Left
            (x1, y0, z1, x1, y0, z0, x1, y1, z0, x1, y1, z1),  # Right
            (x0, y0, z0, x1, y0, z0, x1, y0, z1, x0, y0, z1),  # Bottom
            (x0, y1, z1, x1, y1, z1, x1, y1, z0, x0, y1, z0),  # Top
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

class Scene:
    def __init__(self, texture_manager):
        self.vertices = []
        self.colors = []
        self.normals = []
        self.tex_coords = []
        self.dirty = True

        self.entities = {}

        self.texture_manager = texture_manager

        self.vao = VertexArrayObject()
        with self.vao:
            self.vertex_position_vbo = VertexBufferObject()
            self.color_vbo = VertexBufferObject()
            self.normal_vbo = VertexBufferObject()
            self.tex_coords_vbo = VertexBufferObject()

    def add_cube(self, entity_id, cube):
        if entity_id in self.entities:
            offset = self.entities[entity_id]

            print("Replacing at: ", offset)

            self.vertices[offset:offset+len(cube.vertices)] = cube.vertices
            self.colors[offset:offset+len(cube.colors)] = cube.colors
            self.normals[offset:offset+len(cube.normals)] = cube.normals
            self.tex_coords[offset:offset+len(cube.tex_coords)] = cube.tex_coords

            if self.dirty:
                return

            for (vbo, data) in [
                    (self.vertex_position_vbo, cube.vertices),
                    (self.color_vbo, cube.colors),
                    (self.normal_vbo, cube.normals),
                    (self.tex_coords_vbo, cube.tex_coords)]:
                with vbo:
                    try:
                        gl.glBufferSubData(
                            gl.GL_ARRAY_BUFFER,
                            ctypes.sizeof(gl.GLfloat * offset),
                            ctypes.sizeof(gl.GLfloat * len(data)),
                            (gl.GLfloat * len(data))(*data),
                        )
                    except:
                        print(offset, len(data), data, self.dirty, len(self.vertices))
                        raise
        else:
            self.entities[entity_id] = len(self.vertices)

            self.vertices.extend(cube.vertices)
            self.colors.extend(cube.colors)
            self.normals.extend(cube.normals)
            self.tex_coords.extend(cube.tex_coords)

            self.dirty = True

    def regenerate_buffers(self):
        print("Required to regen buffers!")

        for (vbo, data, layout_offset) in [
            (self.vertex_position_vbo, self.vertices, 0),
            (self.color_vbo, self.colors, 1),
            (self.normal_vbo, self.normals, 2),
            (self.tex_coords_vbo, self.tex_coords, 3),
        ]:
            with vbo:
                gl.glBufferData(
                    gl.GL_ARRAY_BUFFER,
                    ctypes.sizeof(gl.GLfloat * len(data)),
                    (gl.GLfloat * len(self.vertices))(*data),
                    gl.GL_STATIC_DRAW,
                )
                gl.glVertexAttribPointer(
                    layout_offset, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, 0
                )
                gl.glEnableVertexAttribArray(layout_offset)

    def draw(self, shader):
        with self.vao:
            if self.dirty:
                self.regenerate_buffers()
                self.dirty = False

            if self.vertices:
                gl.glBindTexture(
                    gl.GL_TEXTURE_2D_ARRAY, self.texture_manager.texture_array
                )
                shader["texture_array_sampler"] = 1
                gl.glDrawArrays(gl.GL_QUADS, 0, len(self.vertices))


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
        gl.glClearColor(r / 255, g / 255, b / 255, 1)

        gl.glEnable(gl.GL_DEPTH_TEST)

        self.window.event(self.on_draw)
        self.window.event(self.on_mouse_motion)
        self.window.event(self.on_key_press)
        pyglet.clock.schedule(self.update)

        self.shader = Shader("vert.glsl", "frag.glsl")
        self.shader.use()

        tm = texture_manager.TextureManager(128, 128, 8)
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
            tm.add_texture(name)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, tm.texture_array)

        self.batch = Scene(tm)
        add_floor(self.batch)

        tm = texture_manager.TextureManager(150, 150, 50)

        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, tm.texture_array)

        self.avatars = Scene(tm)

        self.camera = Camera(
            self.shader,
            self.window.width,
            self.window.height,
            Vector([45, 0.6, 53]),
            Vector([0, 90]),
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
        self.camera.update_mouse(Vector([dy / 6, dx / 6]))

    def on_draw(self):
        self.window.clear()
        self.camera.apply()
        self.shader["tile_texture"] = 1
        self.batch.draw(self.shader)
        self.shader["tile_texture"] = 0
        self.avatars.draw(self.shader)

    def update(self, dt):
        try:
            while True:
                entity = self.entity_queue.get_nowait()
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
        pos = {
            'x': round(self.camera.position.x),
            'y': round(self.camera.position.z),
            'direction': ['up', 'right', 'down', 'left'][round(self.camera.rotation.y / 90) % 4]
        }

        self.camera.update(dt, input_vector)

        pos = avatar_position(self.camera)

        if pos != self.pos:
            print("Updating pos: ", pos)
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
                            await walls.update(session, bot_id=bot_id, color=message['payload']['color'])
                except rctogether.api.HttpError:
                    traceback.print_exc()
                    pass

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
        or get_photo_ext(avatar_id, "png")
        or await download_photo(session, avatar_id, image_path)
    )

    PHOTOS[avatar_id] = image_data
    return image_data


async def download_photo(session, avatar_id, image_path):
    print("FETCH: ", image_path)
    async with session.get(image_path) as response:
        image_data = await response.read()

        if response.content_type == "image/jpeg":
            extension = "jpeg"
        elif response.content_type == "image/png":
            extension = "png"

        with open(photo_path(avatar_id, extension), "wb") as fh:
            fh.write(image_data)

    return image_data


async def async_thread_main(entity_queue, avatar_update_queue_future):
    asyncio.create_task(space_avatar_worker(avatar_update_queue_future))

    async with aiohttp.ClientSession() as session:
        async for entity in rctogether.WebsocketSubscription():
            if entity["type"] == "Avatar" and entity["id"] not in PHOTOS:
                await get_photo(session, entity["id"], entity["image_path"])
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

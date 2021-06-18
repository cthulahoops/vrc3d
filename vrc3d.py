import io
import math
import threading
import asyncio
import queue
import functools
import aiohttp

import rctogether

from pyglet import gl
from pyglet.window import key
import pyglet

COLORS = {
    "gray": "#919c9c",
    "pink": "#d95a88",
    "orange": "#e6a56e",
    "green": "#3dc06c",
    "blue": "#66bdff",
    "purple": "#956bc3",
    "yellow": "#e7dd6f",
}


@functools.lru_cache(maxsize=None)
def load_image(filename, file=None):
    return pyglet.image.load(filename, file=file)


def get_texture(filename, file=None):
    image = load_image(filename, file=file)
    gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    return pyglet.graphics.TextureGroup(image.get_texture())

def tex_coords(x0, x1, y0, y1):
    return (
        "t2f",
        (
            x0,
            y0,
            x1,
            y0,
            x1,
            y1,
            x0,
            y1,
        ),
    )

def color_to_rgb(color):
    return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))


def add_wall(batch, entity):
    pos = [entity["pos"]["x"], 0, entity["pos"]["y"]]

    add_cube(batch, pos, [1, 1, 1], color=COLORS[entity["color"]])


def add_note(batch, entity):
    pos = [entity["pos"]["x"], 0, entity["pos"]["y"]]
    add_cube(batch, pos, [1, 1, 1], color=COLORS["yellow"])


def add_desk(batch, entity):
    pos = [entity["pos"]["x"], 0, entity["pos"]["y"]]
    add_cube(batch, pos, [0.9, 0.4, 0.9], color=COLORS["orange"])


def add_link(batch, entity):
    texture = get_texture('link.png')
    pos = [entity["pos"]["x"], 0, entity["pos"]["y"]]

    x0, x1 = (0.0, 1.0)
    y0, y1 = (0.0, 1.0)

    add_cube(batch, pos, [0.4, 0.4, 0.4], tex_coords=tex_coords(x0, x1, y0, y1), group=texture)

def add_zoomlink(batch, entity):
    texture = get_texture('zoom.jpeg')
    pos = [entity["pos"]["x"], 0, entity["pos"]["y"]]

    x0, x1 = (0.0, 0.9)
    y0, y1 = (-0.1, 0.9)

    add_cube(batch, pos, [0.6, 0.6, 0.6], tex_coords=tex_coords(x0, x1, y0, y1), group=texture)

def add_audioblock(batch, entity):
    texture = get_texture('audio_block.jpeg')
    pos = [entity["pos"]["x"], 0, entity["pos"]["y"]]

    x0, x1 = (0.0, 1.0)
    y0, y1 = (0.0, 1.0)

    add_cube(batch, pos, [0.6, 0.6, 0.6], tex_coords=tex_coords(x0, x1, y0, y1), group=texture)

def add_avatar(batch, entity):
    texture = get_texture('avatar.png', file=io.BytesIO(PHOTOS[entity['id']]))
    pos = [entity["pos"]["x"], 0, entity["pos"]["y"]]

    x0, x1 = (-0.0, 0.6)
    y0, y1 = (-0.4, 0.6)

    add_cube(batch, pos, [0.05, 0.8, 0.4], tex_coords=tex_coords(x0,x1,y0,y1), group=texture)


def add_cube(batch, pos, size, tex_coords=None, color=None, group=None):
    x0, y0, z0 = pos[0] - size[0] / 2, pos[1], pos[2] - size[2] / 2
    x1, y1, z1 = pos[0] + size[0] / 2, pos[1] + size[1], pos[2] + size[2] / 2

    if color:
        (r, g, b) = color_to_rgb(color)
        tex_coords = ("c3B", (r, g, b, r, g, b, r, g, b, r, g, b))

    batch.add(
        4,
        gl.GL_QUADS,
        group,
        (
            "v3f",
            (
                x1,
                y0,
                z0,
                x0,
                y0,
                z0,
                x0,
                y1,
                z0,
                x1,
                y1,
                z0,
            ),
        ),
        tex_coords,
    )  # back
    batch.add(
        4,
        gl.GL_QUADS,
        group,
        (
            "v3f",
            (
                x0,
                y0,
                z1,
                x1,
                y0,
                z1,
                x1,
                y1,
                z1,
                x0,
                y1,
                z1,
            ),
        ),
        tex_coords,
    )  # front
    batch.add(
        4,
        gl.GL_QUADS,
        group,
        (
            "v3f",
            (
                x0,
                y0,
                z0,
                x0,
                y0,
                z1,
                x0,
                y1,
                z1,
                x0,
                y1,
                z0,
            ),
        ),
        tex_coords,
    )  # left
    batch.add(
        4,
        gl.GL_QUADS,
        group,
        (
            "v3f",
            (
                x1,
                y0,
                z1,
                x1,
                y0,
                z0,
                x1,
                y1,
                z0,
                x1,
                y1,
                z1,
            ),
        ),
        tex_coords,
    )  # right
    batch.add(
        4,
        gl.GL_QUADS,
        group,
        (
            "v3f",
            (
                x0,
                y0,
                z0,
                x1,
                y0,
                z0,
                x1,
                y0,
                z1,
                x0,
                y0,
                z1,
            ),
        ),
        tex_coords,
    )  # bottom
    batch.add(
        4,
        gl.GL_QUADS,
        group,
        (
            "v3f",
            (
                x0,
                y1,
                z1,
                x1,
                y1,
                z1,
                x1,
                y1,
                z0,
                x0,
                y1,
                z0,
            ),
        ),
        tex_coords,
    )  # top


class World:
    def __init__(self, queue):
        self.queue = queue

        self.window = pyglet.window.Window(
            caption="VRC3D", resizable=True, fullscreen=True
        )
        self.window.set_mouse_visible(False)
        self.window.set_exclusive_mouse(True)
        gl.glClearColor(0.1, 0.2, 0.3, 1)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glShadeModel(gl.GL_SMOOTH)

        self.window.event(self.on_draw)
        self.window.event(self.on_mouse_motion)
        self.window.event(self.on_key_press)
        pyglet.clock.schedule(self.update)

        self.batch = pyglet.graphics.Batch()

        self.player_pos = [71, 0.6, 43]
        self.player_rot = [0, 270]

        self.keys = key.KeyStateHandler()
        self.window.push_handlers(self.keys)

    def push(self, pos, rot):
        gl.glPushMatrix()
        gl.glRotatef(-rot[0], 1, 0, 0)
        gl.glRotatef(-rot[1], 0, 1, 0)
        gl.glTranslatef(-pos[0], -pos[1], -pos[2])

    def on_key_press(self, KEY, MOD):
        if KEY == key.ESCAPE:
            print(self.player_pos)
            self.window.close()

    def on_mouse_motion(self, x, y, dx, dy):
        self.player_rot[0] += dy / 6
        self.player_rot[1] -= dx / 6

    def on_draw(self):
        self.window.clear()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.gluPerspective(60, self.window.width / self.window.height, 0.05, 1000)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        self.push(self.player_pos, self.player_rot)
        self.batch.draw()
        gl.glPopMatrix()

    def update(self, dt):
        try:
            while True:
                entity = self.queue.get_nowait()
                if entity["type"] == "Wall":
                    add_wall(self.batch, entity)
                elif entity["type"] == "Desk":
                    add_desk(self.batch, entity)
                elif entity["type"] == "Avatar":
                    add_avatar(self.batch, entity)
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
                else:
                    print(entity['type'], entity)

        except queue.Empty:
            pass

        s = dt * 5
        rotY = -self.player_rot[1] / 180 * math.pi
        dx, dz = s * math.sin(rotY), s * math.cos(rotY)

        if self.keys[key.UP]:
            self.player_pos[0] += dx
            self.player_pos[2] -= dz
        elif self.keys[key.DOWN]:
            self.player_pos[0] -= dx
            self.player_pos[2] += dz
        elif self.keys[key.LEFT]:
            self.player_pos[0] -= dz
            self.player_pos[2] -= dx
        elif self.keys[key.RIGHT]:
            self.player_pos[0] += dz
            self.player_pos[2] += dx


# async def async_2d_avatar():
# 👾

PHOTOS = {}

async def download_photo(session, avatar_id, image_path):
    async with session.get(image_path) as response:
        PHOTOS[avatar_id] = await response.read()

async def async_thread_main(queue):
    async with aiohttp.ClientSession() as session:
        async for entity in rctogether.WebsocketSubscription():
            if entity['type'] == 'Avatar' and entity['id'] not in PHOTOS:
                await download_photo(session, entity['id'], entity['image_path'])
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

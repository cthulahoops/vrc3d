import math
import threading
import asyncio
import queue

from pyglet import gl
from pyglet.window import key
import pyglet

import rctogether


def add_cube(batch, pos):
    tex_coords = (
        "t2f",
        (
            0,
            0,
            1,
            0,
            1,
            1,
            0,
            1,
        ),
    )
    # texture coordinates

    x, y, z = 0, 0, -1
    X, Y, Z = x + 1, y + 1, z + 1

    batch.add(
        4,
        gl.GL_QUADS,
        None,
        (
            "v3f",
            (
                X + pos[0],
                y + pos[1],
                z + pos[2],
                x + pos[0],
                y + pos[1],
                z + pos[2],
                x + pos[0],
                Y + pos[1],
                z + pos[2],
                X + pos[0],
                Y + pos[1],
                z + pos[2],
            ),
        ),
        tex_coords,
    )  # back
    batch.add(
        4,
        gl.GL_QUADS,
        None,
        (
            "v3f",
            (
                x + pos[0],
                y + pos[1],
                Z + pos[2],
                X + pos[0],
                y + pos[1],
                Z + pos[2],
                X + pos[0],
                Y + pos[1],
                Z + pos[2],
                x + pos[0],
                Y + pos[1],
                Z + pos[2],
            ),
        ),
        tex_coords,
    )  # front
    batch.add(
        4,
        gl.GL_QUADS,
        None,
        (
            "v3f",
            (
                x + pos[0],
                y + pos[1],
                z + pos[2],
                x + pos[0],
                y + pos[1],
                Z + pos[2],
                x + pos[0],
                Y + pos[1],
                Z + pos[2],
                x + pos[0],
                Y + pos[1],
                z + pos[2],
            ),
        ),
        tex_coords,
    )  # left
    batch.add(
        4,
        gl.GL_QUADS,
        None,
        (
            "v3f",
            (
                X + pos[0],
                y + pos[1],
                Z + pos[2],
                X + pos[0],
                y + pos[1],
                z + pos[2],
                X + pos[0],
                Y + pos[1],
                z + pos[2],
                X + pos[0],
                Y + pos[1],
                Z + pos[2],
            ),
        ),
        tex_coords,
    )  # right
    batch.add(
        4,
        gl.GL_QUADS,
        None,
        (
            "v3f",
            (
                x + pos[0],
                y + pos[1],
                z + pos[2],
                X + pos[0],
                y + pos[1],
                z + pos[2],
                X + pos[0],
                y + pos[1],
                Z + pos[2],
                x + pos[0],
                y + pos[1],
                Z + pos[2],
            ),
        ),
        tex_coords,
    )  # bottom
    batch.add(
        4,
        gl.GL_QUADS,
        None,
        (
            "v3f",
            (
                x + pos[0],
                Y + pos[1],
                Z + pos[2],
                X + pos[0],
                Y + pos[1],
                Z + pos[2],
                X + pos[0],
                Y + pos[1],
                z + pos[2],
                x + pos[0],
                Y + pos[1],
                z + pos[2],
            ),
        ),
        tex_coords,
    )  # top


class World:
    def __init__(self, queue):
        self.queue = queue

        self.window = pyglet.window.Window(
            caption="VRC3D", resizable=True, fullscreen=False
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

        self.player_pos = [0.5, 0.5, 0]
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
                add_cube(self.batch, [entity['pos']['x'], 0, entity['pos']['y']])
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


async def async_thread_main(queue):
    async for entity in rctogether.WebsocketSubscription():
        if entity['type'] == 'Wall':
            queue.put(entity)
#            add_cube(world.batch, [entity['pos']['x'], 0, entity['pos']['y']])
#            print(entity)


def main():
    entity_queue = queue.Queue()

    async_thread = threading.Thread(target=lambda: asyncio.run(async_thread_main(entity_queue)))
    async_thread.start()

    world = World(entity_queue)

    pyglet.app.run()


if __name__ == "__main__":
    main()

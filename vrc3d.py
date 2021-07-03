import threading
import asyncio
import queue
import time
from queue import Queue
import traceback
from concurrent.futures import ThreadPoolExecutor
import datetime
import argparse

import aiohttp

import rctogether
from rctogether import walls

from pyglet import gl
from pyglet.window import key
import pyglet


from camera import Camera
from vector import Vector
from shader import Shader
from scene import Scene, tex_coords, color_to_rgb, Cube
from texture_manager import TextureManager
import photos
from sky import Sky

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





class World:
    def __init__(self, entity_queue, avatar_update_queue, speed=None, show_grid=False):
        self.entity_queue = entity_queue
        self.avatar_update_queue = avatar_update_queue

        self.window = pyglet.window.Window(
            caption="VRC3D", resizable=True, fullscreen=False
        )
        pyglet.gl.Config(major_version=3, minor_version=3)
        self.exclusive_mouse = True
        self.window.set_mouse_visible(not self.exclusive_mouse)
        self.window.set_exclusive_mouse(self.exclusive_mouse)
        (r, g, b) = color_to_rgb("#87ceeb")
        gl.glClearColor(r, g, b, 1)

        gl.glEnable(gl.GL_DEPTH_TEST)

        self.window.event(self.on_draw)
        self.window.event(self.on_mouse_motion)
        self.window.event(self.on_key_press)
        pyglet.clock.schedule(self.update)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glActiveTexture(gl.GL_TEXTURE1)

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


        self.batch = Scene(texture_manager)
        add_floor(self.batch)

        texture_manager = TextureManager(150, 150, 50)

        self.avatars = Scene(texture_manager, max_vertices=10_000)

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

        texture_manager = TextureManager(4096, 2048, 1)
        texture_manager.add_texture("starmap")

        self.sky = Sky(show_grid)

        self.t0 = time.time()
        self.speed = speed

    def on_key_press(self, KEY, MOD):
        if KEY == key.ESCAPE:
            self.window.close()
        elif KEY == key.SPACE:
            self.exclusive_mouse = not self.exclusive_mouse
            self.window.set_exclusive_mouse(self.exclusive_mouse)
            self.window.set_mouse_visible(not self.exclusive_mouse)
        elif KEY == key.ENTER:
            self.window.set_fullscreen(not self.window.fullscreen)
        elif KEY == key.X:
            self.avatar_update_queue.put({'type': 'wall', 'payload': {'action': 'create', 'color': WALL_COLORS[self.active_color % len(WALL_COLORS)]}})
        elif KEY == key.C:
            self.active_color += 1
            self.avatar_update_queue.put({'type': 'wall', 'payload': {'action': 'update', 'color': WALL_COLORS[self.active_color % len(WALL_COLORS)]}})
        elif KEY == key.P:
            print(pyglet.clock.get_fps())


    def on_mouse_motion(self, x, y, dx, dy):
        if self.exclusive_mouse:
            self.camera.update_mouse(Vector(dy / 6, dx / 6))

    def on_draw(self):
        self.window.clear()

        utctime = datetime.datetime.utcnow()
        if self.speed:
            utctime += datetime.timedelta(seconds=self.speed * (time.time() - self.t0))

        sun_position = self.sky.sun_position(utctime)

        self.shader.use()
        self.camera.apply()
        self.shader["tile_texture"] = 1
        self.batch.draw(self.shader)
        self.shader["tile_texture"] = 0
        self.shader["sun_position"] = sun_position
        self.avatars.draw(self.shader)

        self.sky.draw(self.camera, utctime)


    def add_entity(self, entity):
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

    def handle_entity(self, entity):
        if entity.get('deleted'):
            if entity["type"] == "Avatar":
                self.avatars.delete_cube(entity["id"])
            else:
                self.batch.delete_cube(entity["id"])
        else:
            self.add_entity(entity)

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


async def avatar_updates(avatars_update_queue):
    with ThreadPoolExecutor(max_workers=1) as executor:
        loop = asyncio.get_event_loop()
        while message := await loop.run_in_executor(executor, avatars_update_queue.get):
            yield message

async def space_avatar_worker(avatar_queue):
    async with rctogether.RestApiSession() as session:
        bot_id = None
        for bot in await rctogether.bots.get(session):
            if bot['emoji'] == "👾":
                bot_id = bot['id']

        async for message in avatar_updates(avatar_queue):
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

        if bot_id:
            await rctogether.bots.delete(session, bot_id)

async def websocket_subscription(entity_queue):
    async with aiohttp.ClientSession() as session:
        async for entity in rctogether.WebsocketSubscription():
            if entity["type"] == "Avatar" and entity["id"] not in PHOTOS:
                image_data = await photos.get_photo(session, entity["id"], entity["image_path"])
                PHOTOS[entity["id"]] = image_data
            entity_queue.put(entity)


async def async_thread_main(entity_queue, avatar_update_queue_future):
    subscription = asyncio.create_task(websocket_subscription(entity_queue))
    await space_avatar_worker(avatar_update_queue_future)
    subscription.cancel()
    try:
        await subscription
    except asyncio.exceptions.CancelledError:
        pass


def main(args):
    entity_queue = Queue()
    avatar_update_queue = Queue()

    if args.connect:
        async_thread = threading.Thread(
                target=lambda: asyncio.run(async_thread_main(entity_queue, avatar_update_queue))
        )
        async_thread.start()

    try:
        World(entity_queue, avatar_update_queue, speed=args.speed, show_grid=args.grid)
        pyglet.app.run()
    finally:
        if args.connect:
            avatar_update_queue.put(None)
            async_thread.join()

if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser("Virtual RC 3D")
    argument_parser.add_argument("--no-connect", action='store_false', dest='connect')
    argument_parser.add_argument("--grid", action='store_true')
    argument_parser.add_argument("--speed", type=int)

    main(argument_parser.parse_args())

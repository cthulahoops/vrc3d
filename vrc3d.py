import threading
import asyncio
import time
from queue import Queue
import traceback
from concurrent.futures import ThreadPoolExecutor
import datetime
import argparse

import aiohttp

import rctogether
from rctogether import walls

from pyglet import gl, window
import pyglet

from camera import Camera
from vector import Vector
import photos
from sky import Sky, astronomy
from virtualrc import WALL_COLORS, VirtualRc, PHOTOS


class World:
    def __init__(self, entity_queue, avatar_update_queue, offset=0, speed=None, show_grid=False, show_atmosphere=True):
        self.avatar_update_queue = avatar_update_queue

        self.window = pyglet.window.Window(caption="VRC3D", resizable=True, fullscreen=False)
        pyglet.gl.Config(major_version=3, minor_version=3)
        self.exclusive_mouse = True
        self.window.set_mouse_visible(not self.exclusive_mouse)
        self.window.set_exclusive_mouse(self.exclusive_mouse)

        gl.glEnable(gl.GL_DEPTH_TEST)

        self.window.event(self.on_draw)
        self.window.event(self.on_mouse_motion)
        self.window.event(self.on_key_press)
        self.window.event(self.on_resize)
        pyglet.clock.schedule(self.update)
        pyglet.clock.schedule_interval(self.update_astro, 0.5)

        self.camera = Camera(
            self.window.width,
            self.window.height,
            Vector(45, 0.6, 53),
            Vector(0, 90),
        )

        self.keys = window.key.KeyStateHandler()
        self.window.push_handlers(self.keys)

        # self.active_color = 0

        self.virtual_rc = VirtualRc(self.camera, entity_queue)
        self.sky = Sky(show_grid, show_atmosphere)

        self.offset = offset
        self.t0 = time.time()
        self.speed = speed

        self.astro = None

    def on_resize(self, width, height):
        self.camera.resize(width, height)

    def on_key_press(self, KEY, MOD):
        if KEY == window.key.ESCAPE:
            self.window.close()
        elif KEY == window.key.SPACE:
            self.exclusive_mouse = not self.exclusive_mouse
            self.window.set_exclusive_mouse(self.exclusive_mouse)
            self.window.set_mouse_visible(not self.exclusive_mouse)
        elif KEY == window.key.ENTER:
            self.window.set_fullscreen(not self.window.fullscreen)
        elif KEY == window.key.X:
            self.avatar_update_queue.put(
                {
                    "type": "wall",
                    "payload": {
                        "action": "create",
                        "color": WALL_COLORS[self.active_color % len(WALL_COLORS)],
                    },
                }
            )
        elif KEY == window.key.C:
            self.active_color += 1
            self.avatar_update_queue.put(
                {
                    "type": "wall",
                    "payload": {
                        "action": "update",
                        "color": WALL_COLORS[self.active_color % len(WALL_COLORS)],
                    },
                }
            )
        elif KEY == window.key.P:
            print(pyglet.clock.get_fps())

    def on_mouse_motion(self, x, y, dx, dy):
        if self.exclusive_mouse:
            self.camera.update_mouse(Vector(dy / 6, dx / 6))

    def update_astro(self, dt):
        utctime = datetime.datetime.utcnow()
        if self.offset:
            utctime += datetime.timedelta(seconds=self.offset)
        if self.speed:
            utctime += datetime.timedelta(seconds=self.speed * (time.time() - self.t0))

        self.astro = astronomy(utctime)

    def on_draw(self):
        self.window.clear()

        self.camera.compute_matrices()
        self.virtual_rc.draw(self.astro.sun_position)
        self.sky.draw(self.camera, self.astro)

    def update(self, dt):
        self.virtual_rc.update()

        input_vector = Vector(0, 0, 0)
        if self.keys[window.key.COMMA] or self.keys[window.key.UP]:
            input_vector += Vector(0, 0, 1)
        if self.keys[window.key.O] or self.keys[window.key.DOWN]:
            input_vector += Vector(0, 0, -1)
        if self.keys[window.key.A] or self.keys[window.key.LEFT]:
            input_vector += Vector(-1, 0, 0)
        if self.keys[window.key.E] or self.keys[window.key.RIGHT]:
            input_vector += Vector(1, 0, 0)

        self.camera.update(dt, input_vector)
        self.avatar_update_queue.put({"type": "pos", "payload": self.avatar_position()})

    def avatar_position(self):
        return {
            "x": round(self.camera.position.x),
            "y": round(self.camera.position.z),
            "direction": ["up", "right", "down", "left"][round(self.camera.rotation.y / 90) % 4],
        }


class DeduplicatingQueue(Queue):
    def __init__(self):
        super().__init__()
        self.last_item = object()

    def put(self, item, block=True, timeout=None):
        if item != self.last_item:
            self.last_item = item
            super().put(item, block=block, timeout=timeout)


async def avatar_updates(avatars_update_queue):
    with ThreadPoolExecutor(max_workers=1) as executor:
        loop = asyncio.get_event_loop()
        while message := await loop.run_in_executor(executor, avatars_update_queue.get):
            yield message


async def space_avatar_worker(avatar_queue):
    async with rctogether.RestApiSession() as session:
        bot_id = None
        for bot in await rctogether.bots.get(session):
            if bot["emoji"] == "👾":
                bot_id = bot["id"]

        async for message in avatar_updates(avatar_queue):
            try:
                if message["type"] == "pos":
                    pos = message["payload"]

                    if bot_id:
                        await rctogether.bots.update(session, bot_id, pos)
                    else:
                        bot = await rctogether.bots.create(
                            session,
                            name="Extra-dimensional Avatar",
                            emoji="👾",
                            x=pos["x"],
                            y=pos["y"],
                        )
                        bot_id = bot["id"]
                elif message["type"] == "wall":
                    if message["payload"]["action"] == "create":
                        await walls.create(session, bot_id=bot_id, color=message["payload"]["color"])
                    elif message["payload"]["action"] == "upload":
                        pass  # Not supported without getting the wall id.
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
    avatar_update_queue = DeduplicatingQueue()

    if args.connect:
        async_thread = threading.Thread(
            target=lambda: asyncio.run(async_thread_main(entity_queue, avatar_update_queue))
        )
        async_thread.start()

    try:
        World(entity_queue, avatar_update_queue, offset=args.offset, speed=args.speed, show_grid=args.grid, show_atmosphere=args.atmosphere)
        pyglet.app.run()
    finally:
        if args.connect:
            avatar_update_queue.put(None)
            async_thread.join()


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser("Virtual RC 3D")
    argument_parser.add_argument("--no-connect", action="store_false", dest="connect")
    argument_parser.add_argument("--no-atmosphere", action="store_false", dest="atmosphere")
    argument_parser.add_argument("--grid", action="store_true")
    argument_parser.add_argument("--speed", type=int)
    argument_parser.add_argument("--offset", type=int, default=0)

    main(argument_parser.parse_args())

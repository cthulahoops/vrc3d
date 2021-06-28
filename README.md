# Virtual RC 3D

A 3d interface to Virtual RC with Python and OpenGL.

## Usage

You can install deps with `poetry install` or directly with `pip install pyglet rctogether aiohttp`.

Create an application key at https://recurse.rctogether.com/apps/ (or the appropiate non-RC endpoint) and configure:

```
export RC_APP_ID=<app_id>
export RC_APP_SECRET=<app_id>
```

(Configure RC_APP_ENDPOINT too, if you're not a non-RC endpoint.)


Run:

```
python vrc3d.py
```

## Code

Much of the OpenGL code is adapted from a python minecraft clone tutorial found here: https://github.com/obiwac/python-minecraft-clone/

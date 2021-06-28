# Virtual RC 3D

A 3d interface to Virtual RC with Python and OpenGL.

# Dependencies

You can install deps with `poetry install` or directly with `pip install pyglet rctogether aiohttp`.

Create an application key at https://recurse.rctogether.com/apps/ (or the appropiate non-RC endpoint) and configure:

```
export RC_APP_ID=<app_id>
export RC_APP_SECRET=<app_id>
```

(Configure RC_APP_ENDPOINT too, if needed.)

Create a directory to cache user photos:

```
mkdir photos
```

Run:

```
python vrc3d.py
```

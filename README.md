# Virtual RC 3D

A 3d interface to Virtual RC with Python and OpenGL.

## Usage

Virtual RC 3D was developed and works on Linux. Mac OS isn't supported due to graphics driver issues.
AFAIK, it hasn't ever been tried on Window.

Python 3.8 is required. Python 3.10 isn't supported due to a change in the asyncio api.

Use [poetry](https://python-poetry.org/) to install dependencies with `poetry install`.

Create an application key at https://recurse.rctogether.com/apps/ (or the appropiate non-RC endpoint) and configure:

```
export RC_APP_ID=<app_id>
export RC_APP_SECRET=<app_id>
```

(Configure RC_APP_ENDPOINT too, if you're using a non-RC endpoint.)


Run:

```
poetry shell
python vrc3d.py
```

## Code

Much of the OpenGL code is adapted from a python minecraft clone tutorial found here: https://github.com/obiwac/python-minecraft-clone/

The star map is from NASA: https://svs.gsfc.nasa.gov/4851

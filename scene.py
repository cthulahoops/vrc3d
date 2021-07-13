import ctypes
from pyglet import gl

from vector import Vector


class Scene:
    def __init__(self, max_vertices=500_000):
        self.entities = {}

        self.data_size = 0
        self.buffer_size = 0

        self.vao = VertexArrayObject()
        with self.vao:
            self.vertices = VertexBufferObject()
            self.colors = VertexBufferObject()
            self.normals = VertexBufferObject()
            self.tex_coords = VertexBufferObject()

            self.allocate_buffers(max_vertices)

    def delete_entity(self, entity_id):
        (offset, size) = self.entities[entity_id]
        self.buffers.tex_coords.write_slice(offset, [-2] * size)

    def add_entity(self, entity_id, cube):
        if entity_id in self.entities:
            (offset, size) = self.entities[entity_id]

            for (vbo, data) in [
                (self.vertices, cube.vertices),
                (self.colors, cube.colors),
                (self.normals, cube.normals),
                (self.tex_coords, cube.tex_coords),
            ]:
                vbo.write_slice(offset, data)

        elif self.data_size + len(cube.vertices) < self.buffer_size:
            (offset, size) = self.entities[entity_id] = (self.data_size, len(cube))
            self.data_size += size

            for (vbo, data) in [
                (self.vertices, cube.vertices),
                (self.colors, cube.colors),
                (self.normals, cube.normals),
                (self.tex_coords, cube.tex_coords),
            ]:

                vbo.write_slice(offset, data)
        else:
            raise ValueError("Exceeded available size of vertex buffer.")

    def allocate_buffers(self, size):
        self.buffer_size = size
        self.data_size = 0

        for (vbo, layout_offset) in [
            (self.vertices, 0),
            (self.colors, 1),
            (self.normals, 2),
            (self.tex_coords, 3),
        ]:
            vbo.write([0] * self.buffer_size)
            with vbo:
                gl.glVertexAttribPointer(layout_offset, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
                gl.glEnableVertexAttribArray(layout_offset)

    def draw(self):
        with self.vao:
            gl.glDrawArrays(gl.GL_QUADS, 0, self.data_size)


class VertexArrayObject:
    def __init__(self):
        self._id = gl.GLuint()
        gl.glGenVertexArrays(1, ctypes.byref(self._id))

    def __enter__(self):
        gl.glBindVertexArray(self._id)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        gl.glBindVertexArray(0)


class VertexBufferObject:
    def __init__(self):
        self._id = gl.GLuint()
        gl.glGenBuffers(1, ctypes.byref(self._id))

    def __enter__(self):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._id)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def write_slice(self, offset, data):
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


def color_to_rgb(color):
    return (
        int(color[1:3], 16) / 255,
        int(color[3:5], 16) / 255,
        int(color[5:7], 16) / 255,
    )


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


class Mesh:
    def __init__(self):
        self.vertices = []
        self.colors = []
        self.normals = []
        self.tex_coords = []

    def __iadd__(self, other):
        self.vertices.extend(other.vertices)
        self.colors.extend(other.colors)
        self.normals.extend(other.normals)
        self.tex_coords.extend(other.tex_coords)

        return self

    def __len__(self):
        return len(self.vertices)


class Cube(Mesh):
    def __init__(
        self,
        pos,
        size=Vector(1, 1, 1),
        texture=None,
        color=None,
        offset=Vector(0, 0, 0),
    ):

        a = pos + offset - Vector(size.x, 0, size.z) / 2
        b = a + size

        colors = color_to_rgb(color or "#114433") * 4

        if not texture:
            texture = tex_coords(0, 1, 0, 1, -1)

        vertices = [
            (b.x, a.y, a.z, a.x, a.y, a.z, a.x, b.y, a.z, b.x, b.y, a.z),  # Back
            (a.x, a.y, b.z, b.x, a.y, b.z, b.x, b.y, b.z, a.x, b.y, b.z),  # Front
            (a.x, a.y, a.z, a.x, a.y, b.z, a.x, b.y, b.z, a.x, b.y, a.z),  # Left
            (b.x, a.y, b.z, b.x, a.y, a.z, b.x, b.y, a.z, b.x, b.y, b.z),  # Right
            (a.x, a.y, a.z, b.x, a.y, a.z, b.x, a.y, b.z, a.x, a.y, b.z),  # Bottom
            (a.x, b.y, b.z, b.x, b.y, b.z, b.x, b.y, a.z, a.x, b.y, a.z),  # Top
        ]

        normals = [(0, 0, -1), (0, 0, 1), (-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0)]

        super().__init__()
        self.vertices = []
        self.colors = []
        self.normals = []
        self.tex_coords = []

        for (v, n) in zip(vertices, normals):
            self.vertices.extend(v)
            self.colors.extend(colors)
            self.normals.extend(n * 4)
            self.tex_coords.extend(texture)


class Quad:
    def __init__(self, x0=-1, x1=1, y0=-1, y1=1, depth=-1):
        self.vertices = [
            x0,
            y0,
            depth,
            x1,
            y0,
            depth,
            x1,
            y1,
            depth,
            x0,
            y1,
            depth,
        ]
        self.normals = [0] * 12
        self.colors = [1.0] * 12
        self.tex_coords = [0] * 12

    def __len__(self):
        return len(self.vertices)

import io
import pyglet
import pyglet.gl as gl


class Texture:
    def __init__(self, texture, texture_image=None):
        if texture_image:
            texture_image = io.BytesIO(texture_image)

        texture_image = pyglet.image.load(f"textures/{texture}.png", file=texture_image)

        self.width = texture_image.width
        self.height = texture_image.height
        image_data = texture_image.get_image_data()

        self._id = gl.GLuint()
        gl.glGenTextures(1, self._id)
        self.bind()

        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RGBA,
            self.width,
            self.height,
            0,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            image_data.get_data("RGBA", self.width * 4),
        )
        gl.glGenerateMipmap(gl.GL_TEXTURE_2D)

    def bind(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._id)

    def activate(self, sampler_id):
        gl.glActiveTexture(gl.GL_TEXTURE0 + sampler_id)
        self.bind()


class TextureCube:
    def __init__(self, width, height, max_textures):
        self.width = width
        self.height = height
        self.max_textures = max_textures

        self.next_index = 0
        self.textures = {}

        self._id = gl.GLuint()
        gl.glGenTextures(1, self._id)

        self.bind()

        gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)

        gl.glTexImage3D(
            gl.GL_TEXTURE_2D_ARRAY,
            0,
            gl.GL_RGBA,
            self.width,
            self.height,
            self.max_textures,
            0,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            None,
        )

    def clamp_border(self, color):
        self.bind()

        gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameterfv(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_BORDER_COLOR, (gl.GLfloat * 3)(*color))

    def index(self, texture):
        return self.textures[texture]

    def add_texture(self, texture, texture_image=None):
        if not texture in self.textures:
            self.textures[texture] = index = self.next_index
            self.next_index += 1

            if texture_image:
                texture_image = io.BytesIO(texture_image)

            texture_image = pyglet.image.load(f"textures/{texture}.png", file=texture_image).get_image_data()

            assert texture_image.width == self.width
            assert texture_image.height == self.height

            self.bind()
            gl.glTexSubImage3D(
                gl.GL_TEXTURE_2D_ARRAY,
                0,
                0,
                0,
                index,
                self.width,
                self.height,
                1,
                gl.GL_RGBA,
                gl.GL_UNSIGNED_BYTE,
                texture_image.get_data("RGBA", self.width * 4),
            )
            gl.glGenerateMipmap(gl.GL_TEXTURE_2D_ARRAY)

    def bind(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self._id)

    def activate(self, sampler_id):
        gl.glActiveTexture(gl.GL_TEXTURE0 + sampler_id)
        self.bind()

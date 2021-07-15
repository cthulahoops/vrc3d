from copy import copy
import io
import pyglet
import pyglet.gl as gl

import freetype2
from freetype2 import FT

EMOJI_FACE = freetype2.get_default_lib().find_face("NotoColorEmoji")
EMOJI_FACE.set_pixel_sizes(109, 109)

TEXT_FACE = freetype2.get_default_lib().find_face("Ubuntu")
TEXT_FACE.set_pixel_sizes(109, 109)


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
            gl.GL_RGB,
            self.width,
            self.height,
            0,
            gl.GL_RGB,
            gl.GL_UNSIGNED_BYTE,
            image_data.get_data("RGB", self.width * 4),
        )
        gl.glGenerateMipmap(gl.GL_TEXTURE_2D)

    def bind(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._id)

    def activate(self, sampler_id):
        gl.glActiveTexture(gl.GL_TEXTURE0 + sampler_id)
        self.bind()


class TextureCube:
    def __init__(self, width, height, max_textures, pixel_format=gl.GL_RGBA):
        self.width = width
        self.height = height
        self.max_textures = max_textures
        self.pixel_format = pixel_format

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
            self.pixel_format,
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

    def add_texture_png(self, texture, texture_image=None):
        if not texture in self.textures:
            if texture_image:
                texture_image = io.BytesIO(texture_image)

            texture_image = pyglet.image.load(f"textures/{texture}.png", file=texture_image).get_image_data()
            self.add_texture(texture, texture_image)

    def add_texture_glyph(self, character):
        if not character in self.textures:
            glyph = Glyph(character)
            self.add_texture(character, glyph)

    def add_texture(self, texture_id, texture_image):
        if not texture_id in self.textures:
            self.textures[texture_id] = index = self.next_index
            self.next_index += 1

            assert texture_image.width == self.width, f"Can't add: {texture_id!r}. Wrong texture width expected {self.width} got {texture_image.width}"
            assert texture_image.height == self.height, f"Can't add: {texture_id!r}. Wrong texture height expected {self.height} got {texture_image.height}"

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
                self.pixel_format,
                gl.GL_UNSIGNED_BYTE,
                texture_image.get_data("RGBA", self.width * 4),
            )
            gl.glGenerateMipmap(gl.GL_TEXTURE_2D_ARRAY)

    def bind(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self._id)

    def activate(self, sampler_id):
        gl.glActiveTexture(gl.GL_TEXTURE0 + sampler_id)
        self.bind()


class Glyph:
    def __init__(self, character):
        if len(character) != 1:
            print("Not a single character: ", repr(character))
            raise ValueError("Not a single character.")

        # if ord(character) < 256:
        #     TEXT_FACE.load_char(ord(character))
        #     TEXT_FACE.glyph.render_glyph(FT.RENDER_MODE_NORMAL)
        #     bitmap = TEXT_FACE.glyph.bitmap
        # else:
        EMOJI_FACE.load_char(ord(character), FT.LOAD_COLOR)
        EMOJI_FACE.glyph.render_glyph(FT.RENDER_MODE_NORMAL)
        bitmap = EMOJI_FACE.glyph.bitmap

        if bitmap.width == 0:
            raise ValueError(f"Can't generate glyph for: {character!r}")

        self.width = bitmap.width
        self.height = bitmap.rows
        array = bitmap.to_array()
        array2 = copy(array)
        array2[::4] = array[2::4]
        array2[2::4] = array[::4]
        self.image_data = bytes(array2)

    def get_data(self, _format, _size):
        return self.image_data

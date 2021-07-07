import io
import pyglet
import pyglet.gl as gl


class TextureCube:
    def __init__(self, texture_width, texture_height, max_textures):
        self.texture_width = texture_width
        self.texture_height = texture_height

        self.max_textures = max_textures

        self.next_index = 0
        self.textures = {}

        self.texture_array = gl.GLuint(0)
        gl.glGenTextures(1, self.texture_array)
        print("::: ", texture_width, texture_height, self.texture_array)
        gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.texture_array)

        gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)

        gl.glTexImage3D(
            gl.GL_TEXTURE_2D_ARRAY,
            0,
            gl.GL_RGBA,
            self.texture_width,
            self.texture_height,
            self.max_textures,
            0,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            None,
        )

    def index(self, texture):
        return self.textures[texture]

    def add_texture(self, texture, texture_image=None):
        if not texture in self.textures:
            self.textures[texture] = index = self.next_index
            self.next_index += 1

            if texture_image:
                texture_image = io.BytesIO(texture_image)

            texture_image = pyglet.image.load(f"textures/{texture}.png", file=texture_image).get_image_data()

            self.bind()
            gl.glTexSubImage3D(
                gl.GL_TEXTURE_2D_ARRAY,
                0,
                0,
                0,
                index,
                self.texture_width,
                self.texture_height,
                1,
                gl.GL_RGBA,
                gl.GL_UNSIGNED_BYTE,
                texture_image.get_data("RGBA", texture_image.width * 4),
            )
            gl.glGenerateMipmap(gl.GL_TEXTURE_2D_ARRAY)

    def bind(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.texture_array)

    def activate(self, sampler_id):
        gl.glActiveTexture(gl.GL_TEXTURE0 + sampler_id)
        self.bind()

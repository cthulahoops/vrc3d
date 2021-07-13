import math
import pyglet.gl as gl

from vector import Vector
from matrix import Matrix
from shader import Shader
from scene import Scene, Quad

SHADOW_WIDTH = 2 * 1024
SHADOW_HEIGHT = 2 * 1024


class ShadowQuad:
    def __init__(self):
        self.shader = Shader("shadow_quad")
        self.scene = Scene(max_vertices=13)
        self.scene.add_entity(1, Quad(0.0, 1, 0, 1))

    def draw(self, shadow_map):
        self.shader.use()

        shadow_map.activate(0)
        self.shader["depthMap"] = 0

        self.scene.draw()


class ShadowMap:
    def __init__(self):
        self.buffer_id = gl.GLuint()
        gl.glGenFramebuffers(1, self.buffer_id)

        self.texture_id = gl.GLuint()
        gl.glGenTextures(1, self.texture_id)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_DEPTH_COMPONENT,
            SHADOW_WIDTH,
            SHADOW_HEIGHT,
            0,
            gl.GL_DEPTH_COMPONENT,
            gl.GL_FLOAT,
            gl.GL_NONE,
        )

        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameterfv(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_BORDER_COLOR, (gl.GLfloat * 3)(1.0, 1.0, 1.0))

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.buffer_id)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_TEXTURE_2D, self.texture_id, 0)
        gl.glDrawBuffer(gl.GL_NONE)
        gl.glReadBuffer(gl.GL_NONE)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        self.shader = Shader("shadows")

        self.shadow_quad = ShadowQuad()
        self.light_space_matrix = None

    def render(self, camera, sun, meshes):
        d = 10
        ortho_matrix = Matrix.orthographic(-d, d, -d, d, -20, 20)
        model_matrix = camera.translate
        rotate_matrix = Matrix.rotate(sun.az.radians, Vector(0, 1, 0)) @ Matrix.rotate(
            sun.alt.radians, Vector(-1, 0, 0)
        )

        self.light_space_matrix = model_matrix @ rotate_matrix @ ortho_matrix
        self.shader.use()
        self.shader["light_space_matrix"] = self.light_space_matrix

        gl.glViewport(0, 0, SHADOW_WIDTH, SHADOW_HEIGHT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.buffer_id)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT)

        gl.glCullFace(gl.GL_FRONT)
        for mesh in meshes:
            mesh.draw()
        gl.glCullFace(gl.GL_BACK)

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def activate(self, offset):
        gl.glActiveTexture(gl.GL_TEXTURE0 + offset)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)

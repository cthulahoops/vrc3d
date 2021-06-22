import functools
import ctypes
import pyglet.gl as gl

from matrix import Matrix
from vector import Vector


class Shader_error(Exception):
    def __init__(self, message):
        self.message = message


def create_shader(target, source_path):
    # read shader source

    source_file = open(source_path, "rb")
    source = source_file.read()
    source_file.close()

    source_length = ctypes.c_int(len(source) + 1)
    source_buffer = ctypes.create_string_buffer(source)

    buffer_pointer = ctypes.cast(
        ctypes.pointer(ctypes.pointer(source_buffer)),
        ctypes.POINTER(ctypes.POINTER(ctypes.c_char)),
    )

    # compile shader

    gl.glShaderSource(target, 1, buffer_pointer, ctypes.byref(source_length))
    gl.glCompileShader(target)

    # handle potential errors

    log_length = gl.GLint(0)
    gl.glGetShaderiv(target, gl.GL_INFO_LOG_LENGTH, ctypes.byref(log_length))

    log_buffer = ctypes.create_string_buffer(log_length.value)
    gl.glGetShaderInfoLog(target, log_length, None, log_buffer)

    if log_length:
        raise Shader_error(str(log_buffer.value))


class Shader:
    def __init__(self, vert_path, frag_path):
        self.program = gl.glCreateProgram()

        # create vertex shader

        self.vert_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        create_shader(self.vert_shader, vert_path)
        gl.glAttachShader(self.program, self.vert_shader)

        # create fragment shader

        self.frag_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        create_shader(self.frag_shader, frag_path)
        gl.glAttachShader(self.program, self.frag_shader)

        # link program and clean up

        gl.glLinkProgram(self.program)

        gl.glDeleteShader(self.vert_shader)
        gl.glDeleteShader(self.frag_shader)

    def __del__(self):
        gl.glDeleteProgram(self.program)

    @functools.lru_cache
    def find_uniform(self, name):
        location = gl.glGetUniformLocation(self.program, ctypes.create_string_buffer(name.encode('utf-8')))
        if location < 0:
            raise ValueError("Invalid uniform: %r" % (name,))
        return location

    def __setitem__(self, key, value):
        location = self.find_uniform(key)
        if isinstance(value, Matrix):
            gl.glUniformMatrix4fv(
                location, 1, gl.GL_FALSE, (gl.GLfloat * 16)(*sum(value.data, []))
            )
        elif isinstance(value, Vector):
            gl.glUniform3f(location, value.x, value.y, value.z)
        else:
            gl.glUniform1i(location, value)


    def uniform_matrix(self, location, matrix):
        gl.glUniformMatrix4fv(
            location, 1, gl.GL_FALSE, (gl.GLfloat * 16)(*sum(matrix.data, []))
        )

    def uniform_vec3(self, location, vec):
        gl.glUniform3f(location, vec.x, vec.y, vec.z)

    def use(self):
        gl.glUseProgram(self.program)

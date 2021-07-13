import functools
import ctypes
import pyglet.gl as gl

from matrix import Matrix
from vector import Vector


def create_shader(shader_type, source_path):
    target = gl.glCreateShader(shader_type)

    with open(source_path, "rb") as source_file:
        source = source_file.read()

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
        raise SyntaxError(f"SHADER ERROR: {source_path}\n{log_buffer.value.decode()}")

    return target


class Shader:
    def __init__(self, name=None, vert_path=None, frag_path=None):
        vert_path = vert_path or name + ".vert.glsl"
        frag_path = frag_path or name + ".frag.glsl"

        self.program = gl.glCreateProgram()

        self.vert_shader = create_shader(gl.GL_VERTEX_SHADER, vert_path)
        gl.glAttachShader(self.program, self.vert_shader)

        self.frag_shader = create_shader(gl.GL_FRAGMENT_SHADER, frag_path)
        gl.glAttachShader(self.program, self.frag_shader)

        gl.glLinkProgram(self.program)

        gl.glDeleteShader(self.vert_shader)
        gl.glDeleteShader(self.frag_shader)

    # def __del__(self):
    # gl.glDeleteProgram(self.program)

    @functools.lru_cache
    def find_uniform(self, name):
        location = gl.glGetUniformLocation(self.program, ctypes.create_string_buffer(name.encode("utf-8")))
        if location < 0:
            print("WARNING: Undefined or unused uniform: %r" % (name,))
        return location

    def __setitem__(self, key, value):
        location = self.find_uniform(key)
        if isinstance(value, Matrix):
            gl.glUniformMatrix4fv(location, 1, gl.GL_FALSE, (gl.GLfloat * 16)(*value))
        elif isinstance(value, Vector):
            gl.glUniform3f(location, *value)
        elif isinstance(value, float):
            gl.glUniform1f(location, gl.GLfloat(value))
        else:
            gl.glUniform1i(location, value)

    def use(self):
        gl.glUseProgram(self.program)

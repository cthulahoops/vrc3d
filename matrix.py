import operator
import math

from vector import Vector


def dot(xs, ys):
    return sum(x * y for (x, y) in zip(xs, ys))


class Matrix:
    def __init__(self, *rows):
        self._data = rows

    def __matmul__(self, other):
        contents = tuple(
            tuple(
                dot((self[row, i] for i in range(4)), (other[i, column] for i in range(4)))
                for column in range(4))
            for row in range(4))
        return Matrix(*contents)

    def __getitem__(self, row_column):
        (row, column) = row_column
        return self._data[row][column]

    @classmethod
    def identity(cls):
        return cls(
            (1, 0, 0, 0),
            (0, 1, 0, 0),
            (0, 0, 1, 0),
            (0, 0, 0, 1),
        )

    @classmethod
    def scale(cls, vector):
        return cls(
            (vector.x, 0, 0, 0),
            (0, vector.y, 0, 0),
            (0, 0, vector.z, 0),
            (0, 0, 0, 1),
        )

    @classmethod
    def translate(cls, vector):
        return cls(
            (1, 0, 0, 0),
            (0, 1, 0, 0),
            (0, 0, 1, 0),
            (vector.x, vector.y, vector.z, 1),
        )

    @classmethod
    def rotate(cls, angle, vector):
        unit = vector.unit()
        x, y, z = (unit.x, unit.y, unit.z)

        sin_angle = math.sin(angle)
        cos_angle = math.cos(angle)
        one_minus_cos = 1.0 - cos_angle

        return cls(
            (one_minus_cos * x * x + cos_angle, one_minus_cos * x * y + sin_angle * z, one_minus_cos * z * x - sin_angle * y, 0),
            (one_minus_cos * x * y - sin_angle * z, one_minus_cos * y * y + cos_angle, one_minus_cos * y * z + sin_angle * x, 0),
            (one_minus_cos * z * x + sin_angle * y, one_minus_cos * y * z - sin_angle * x, one_minus_cos * z * z + cos_angle, 0),
            (0, 0, 0, 1)
        )

    @classmethod
    def rotate_2d(cls, x, y):
        turn = cls.rotate(x, Vector(0, 1, 0))
        elevation = cls.rotate(-y, Vector(1, 0, 0))
        return turn @ elevation

    @classmethod
    def frustum(cls, left, right, bottom, top, near, far):
        return cls(
            (2 * near / (right - left), 0, 0, 0),
            (0, 2 * near / (top - bottom), 0, 0),
            ((right + left) / (right - left), (top + bottom) / (top - bottom), -(far + near) / (far - near), -1.0),
            (0, 0, -2 * far * near / (far - near), 0),
        )


    @classmethod
    def perspective(cls, fovy, aspect, near, far):
        frustum_y = near * math.tan(math.radians(fovy) / 2)
        frustum_x = frustum_y * aspect

        return cls.frustum(-frustum_x, frustum_x, -frustum_y, frustum_y, near, far)

    def __eq__(self, other):
        return isinstance(other, type(self)) and all(self._pairwise(operator.eq, other))

    def __add__(self, other):
        return self._pairwise(operator.add, other)

    def __sub__(self, other):
        return self._pairwise(operator.sub, other)

    def _pairwise(self, f, other):
        return Matrix(*(tuple(f(a, b) for (a, b) in zip(row_a, row_b)) for (row_a, row_b) in zip(self.rows(), other.rows())))

    def rows(self):
        return iter(self._data)

    def values(self):
        return list(self)

    @classmethod
    def orthographic(cls, left, right, bottom, top, near, far):
        scale = cls.scale(Vector(2.0 / (right - left), 2.0 / (top - bottom), 2.0 / (far - near)))
        translate = cls.translate(Vector(-(right + left) / (right - left), -(top + bottom) / (top - bottom), -(near + far) / (far - near)))
        return scale @ translate

    def __iter__(self):
        for row in self._data:
            for value in row:
                yield value

    def __repr__(self):
        return "<Matrix %r>" % (self._data,)

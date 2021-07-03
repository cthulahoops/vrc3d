import math
import pytest

from matrix import Matrix
from vector import Vector


def approx_equal(a, b):
    r = a - b
    for row in r.rows():
        for v in row:
            if abs(v) > 1e-6:
                return False
    return True


def test_matmul():
    x = Matrix((1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16))
    y = x + x
    assert x @ y == Matrix((180, 200, 220, 240), (404, 456, 508, 560), (628, 712, 796, 880), (852, 968, 1084, 1200))


def test_rotation_simple():
    assert approx_equal(
        Matrix.rotate(math.pi / 2, Vector(1, 0, 0)), Matrix((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1))
    )


def test_rotation():
    expected = Matrix(
        (0.5357142857142858, 0.765793646257985, -0.3557671927434186, 0.0),
        (-0.6229365034008422, 0.642857142857143, 0.44574073922885216, 0.0),
        (0.5700529070291328, -0.01716931065742358, 0.8214285714285714, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )
    assert approx_equal(Matrix.rotate(math.pi / 3, Vector(1, 2, 3)), expected)


@pytest.mark.parametrize(
    "x,y,expected",
    [
        (
            math.pi / 4,
            0,
            (
                (0.7071067811865476, 0.0, -0.7071067811865475, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.7071067811865475, 0.0, 0.7071067811865476, 0.0),
                (0.0, 0.0, 0.0, 1.0),
            ),
        ),
        (
            0,
            math.pi / 4,
            (
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 0.7071067811865476, -0.7071067811865475, 0.0),
                (0.0, 0.7071067811865475, 0.7071067811865476, 0.0),
                (0.0, 0.0, 0.0, 1.0),
            ),
        ),
        (math.pi / 2, math.pi / 2, ((0, -1.0, 0, 0), (0, 0, -1.0, 0), (1.0, 0, 0, 0), (0, 0, 0, 1.0))),
        (
            math.pi / 6,
            math.pi / 7,
            (
                (0.8660254037844386, -0.21694186955877903, -0.4504844339512095, 0.0),
                (0.0, 0.9009688679024191, -0.4338837391175582, 0.0),
                (0.49999999999999994, 0.37575434036478533, 0.7802619276224012, 0.0),
                (0.0, 0.0, 0.0, 1.0),
            ),
        ),
    ],
)
def test_rotate_2d(x, y, expected):
    expected = Matrix(*expected)
    assert approx_equal(Matrix.rotate_2d(x, y), expected)


def test_translate():
    expected = Matrix((1.0, 0, 0, 0), (0, 1.0, 0, 0), (0, 0, 1.0, 0), (4.0, 5.0, 6.0, 1.0))
    assert approx_equal(Matrix.translate(Vector(4, 5, 6)), expected)


def test_orthographic():
    expected = Matrix((0.002, 0, 0, 0), (0, 0.005, 0, 0), (0, 0, 0.05, 0), (-1.0, -2.0, 0, 1.0))
    assert Matrix.orthographic(0, 1000, 200, 600, -20, 20) == expected

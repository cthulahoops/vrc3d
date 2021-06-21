import math

class Vector:
    def __init__(self, data):
        self._data = list(data)

    def __add__(self, other):
        return Vector(a + b for (a, b) in zip(self, other))

    def __sub__(self, other):
        return Vector(a - b for (a, b) in zip(self, other))

    def __getitem__(self, idx):
        return self._data[idx]

    def __setitem__(self, idx, value):
        self._data[idx] = value

    def __repr__(self):
        return f"<Vector {self._data}>"

    def mag(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def cross(self, other):
        return Vector([
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        ])

    def __rmul__(self, other):
        return Vector(other * x for x in self._data)

    @property
    def x(self):
        return self[0]

    @x.setter
    def x(self, value):
        self[0] = value

    @property
    def y(self):
        return self[1]

    @y.setter
    def y(self, value):
        self[1] = value

    @property
    def z(self):
        return self[2]

    @z.setter
    def z(self, value):
        self[2] = value

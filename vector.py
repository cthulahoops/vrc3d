import math


class Vector:
    def __init__(self, *data):
        self._data = data

    def __add__(self, other):
        return Vector(*(a + b for (a, b) in zip(self, other)))

    def __sub__(self, other):
        return Vector(*(a - b for (a, b) in zip(self, other)))

    def __getitem__(self, idx):
        return self._data[idx]

    def __repr__(self):
        return f"<Vector {self._data}>"

    def __truediv__(self, other):
        return Vector(*(a / other for a in self))

    def __neg__(self):
        return -1 * self

    def mag(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def unit(self):
        return self / self.mag()

    def cross(self, other):
        return Vector(
            *(
                self.y * other.z - self.z * other.y,
                self.z * other.x - self.x * other.z,
                self.x * other.y - self.y * other.x,
            )
        )

    def __rmul__(self, other):
        return Vector(*(other * x for x in self._data))

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    @property
    def z(self):
        return self[2]

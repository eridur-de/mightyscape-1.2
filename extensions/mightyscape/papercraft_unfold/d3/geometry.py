import math

class Vector:
    """ 3D Vector

    Simple class that represents a 3D vector
    """

    def __init__(self, x = 0.0, y = 0.0, z = 0.0):
        """
        Creates a vector from it's coordinates
        """
        self.x = x
        self.y = y
        self.z = z

    def from_array(self, arr):
        """
        Creates a vector from an array
        """
        self.x = float(arr[0]) if len(arr) > 0 else None
        self.y = float(arr[1]) if len(arr) > 1 else None
        self.z = float(arr[2]) if len(arr) > 2 else None
        return self

    def __add__(self, other):
        """
        Sums two vectors
        """
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        """
        Subs two vectors
        """
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        """
        Computes the product between a vector and a number
        """
        return Vector(self.x * other, self.y * other, self.z * other)

    def __truediv__(self, number):
        self.x /= number
        self.y /= number
        self.z /= number
        return self

    def __rmul__(self, other):
        """
        Computes the product between a vector and a number
        """
        return self.__mul__(other)

    def norm2(self):
        """
        Computes the square of the norm of a vector
        """
        return self.x * self.x + self.y * self.y + self.z * self.z

    def norm(self):
        """
        Compute the norm of a vector
        """
        return math.sqrt(self.norm2())

    def normalize(self):
        """
        Divides each coordinate of the vector by its norm
        """
        norm = self.norm()
        if abs(norm) > 0.0001:
            self.x /= norm
            self.y /= norm
            self.z /= norm

    def cross_product(v1, v2):
        """
        Computes the cross product between the two vectors
        """
        return Vector(
            v1.y * v2.z - v1.z * v2.y,
            v1.z * v2.x - v1.x * v2.z,
            v1.x * v2.y - v1.y * v2.x)

    def from_points(v1, v2):
        """
        Creates a vector from two points
        """
        return Vector(
            v2.x - v1.x,
            v2.y - v1.y,
            v2.z - v1.z)

    def __str__(self):
        """
        Prints the coordinates of the vector between partheses
        """
        return '(' + ", ".join([str(self.x), str(self.y), str(self.z)]) + ")"

    def dot(self, other):
        """
        Computes the dot product of two vectors
        """
        return self.x * other.x + self.y * other.y + self.z * other.z



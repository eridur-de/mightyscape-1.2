import math
from inkex import EffectExtension, PathElement, transforms as T

# https://en.wikipedia.org/wiki/Rotations_and_reflections_in_two_dimensions
def reflection_matrix(theta):
    theta2 = 2 * theta
    return [
        [math.cos(theta2),  math.sin(theta2), 0],
        [math.sin(theta2), -math.cos(theta2), 0],
    ]

def svg_matrix_order(mat):
    ((a, c, e), (b, d, f)) = mat
    return a, b, c, d, e, f

class Flip(EffectExtension):
    """Extension to flip a path about the line from the start to end node"""

    def effect(self):
        for node in self.svg.selection.filter(PathElement).values():
            points = list(node.path.end_points)
            if len(points) < 2 or points[0] == points[-1]:
                continue
            start = points[0]
            end = points[-1]
            v = end - start
            theta = math.atan2(v.y, v.x)

            # transforms go in reverse order
            mat = T.Transform()
            mat.add_translate(start)
            mat.add_matrix(*svg_matrix_order(reflection_matrix(theta)))
            mat.add_translate(-start)

            node.path = node.path.transform(mat)

if __name__ == '__main__':
    Flip().run()
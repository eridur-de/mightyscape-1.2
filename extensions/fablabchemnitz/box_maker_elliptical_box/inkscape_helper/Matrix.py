import copy

class Matrix(object):
    """
    Matrix class with some basic matrix operations
    """
    def __init__(self, array):
        columns = len(array[0])
        for r in array[1:]: #make sure each row has same number of columns
            assert len(r) == columns

        self.array = copy.copy(array)
        self.rows = len(array)
        self.columns = columns

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        a = ['[' + ', '.join([str(i) for i in r]) + ']' for r in self.array]
        return '[\n' + ',\n'.join(a) + '\n]'

    def minor(self, row, col):
        return Matrix([[self[r][c] for c in range(self.columns) if c != col] for r in range(self.rows) if r != row])

    def det(self):
        if self.rows != self.columns:
            raise TypeError, 'Can only calculate determinant for a square matrix'
        if self.rows == 1:
            return self[0][0]
        if self.rows == 2:
            return self[0][0] * self[1][1] - self[0][1] * self[1][0]
        det = 0
        for i in range(self.columns):
            det += (-1)**i * self.array[0][i] * self.minor(0, i).det()
        return det

    def __getitem__(self, index):
        return self.array[index]

    def __add__(self, other):
        if self.rows != other.rows or self.columns != other.columns:
            raise TypeError, 'Both matrices should have equal dimensions. Is ({} x {}) and ({} x {}).'.format(self.rows, self.columns, other.rows, other.columns)
        return Matrix([[self[r][c] + other[r][c] for c in range(self.columns)] for r in range(self.rows)])

    def __mul__(self, other):
        if self.columns != other.rows:
            raise TypeError, 'Left matrix should have same number of columns as right matrix has rows. Is ({} x {}) and ({} x {}).'.format(self.rows, self.columns, other.rows, other.columns)
        return Matrix([[sum([self[r][i] * other[i][c] for i in range(self.columns)]) for c in range(other.columns)] for r in range(self.rows)])

# Dumbp256k1: a stupid implementation of secp256k1
#
# Use this code only for prototyping
# -- putting this code into production would be dumb
# -- assuming this code is secure would also be dumb

import secrets
from hashlib import blake2s


# Curve parameters
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
cofactor = 1
b = 256   # bit length


# Internal helper methods
def invert(a, p):
    # Assumes `p` is prime
    return pow(a, p - 2, p)


def yfromx(x, even):
    # even determines even or odd y
    # this has no quadratic residue check
    y = pow(x * x * x + 7, (p + 1) // 4, p)
    if (y % 2 != 0 and even) or (y % 2 == 0 and not even):
        y = p - y
    return y


# An element of the main subgroup scalar field
class Scalar:
    def __init__(self, x):
        # Generated from an integer value
        if isinstance(x, int):
            self.x = x % n
        # Generated from a hex representation
        elif isinstance(x, str):
            try:
                self.x = int(x, 16) % n
            except:
                raise TypeError
        else:
            raise TypeError

    # Multiplicative inversion, with an option to let 1/0 = 0 if you're into that
    def invert(self, allow_zero=False):
        if self.x == 0:
            if allow_zero:
                return Scalar(0)
            else:
                raise ZeroDivisionError
        return Scalar(invert(self.x, n))

    # Addition
    def __add__(self, y):
        if isinstance(y, Scalar):
            return Scalar(self.x + y.x)
        return NotImplemented

    # Subtraction
    def __sub__(self, y):
        if isinstance(y, Scalar):
            return Scalar(self.x - y.x)
        return NotImplemented

    # Multiplication (possibly by an integer)
    def __mul__(self, y):
        if isinstance(y, int):
            return Scalar(self.x * y)
        if isinstance(y, Scalar):
            return Scalar(self.x * y.x)
        return NotImplemented

    def __rmul__(self, y):
        if isinstance(y, int):
            return self * y
        return NotImplemented

    # Truncated division (possibly by a positive integer)
    def __truediv__(self, y):
        if isinstance(y, int) and y >= 0:
            return Scalar(self.x // y)
        if isinstance(y, Scalar):
            return Scalar(self.x // y.x)
        raise NotImplemented

    # Integer exponentiation
    def __pow__(self, y):
        if isinstance(y, int) and y >= 0:
            return Scalar(self.x ** y)
        return NotImplemented

    # Equality
    def __eq__(self, y):
        if isinstance(y, Scalar):
            return self.x == y.x
        raise TypeError

    # Inequality
    def __ne__(self, y):
        if isinstance(y, Scalar):
            return self.x != y.x
        raise TypeError

    # Less-than comparison (does not account for overflow)
    def __lt__(self, y):
        if isinstance(y, Scalar):
            return self.x < y.x
        raise TypeError

    # Greater-than comparison (does not account for overflow)
    def __gt__(self, y):
        if isinstance(y, Scalar):
            return self.x > y.x
        raise TypeError

    # Less-than-or-equal comparison (does not account for overflow)
    def __le__(self, y):
        if isinstance(y, Scalar):
            return self.x <= y.x
        raise TypeError

    # Greater-than-or-equal comparison (does not account for overflow)
    def __ge__(self, y):
        if isinstance(y, Scalar):
            return self.x >= y.x
        raise TypeError

    # Hex representation (string)
    def __repr__(self):
        return f'{self.x:0{b // 4}x}'

    # Return underlying integer
    def __int__(self):
        return self.x

    # Modulus (possibly by an integer)
    def __mod__(self, mod):
        if isinstance(mod, int) and mod > 0:
            return Scalar(self.x % mod)
        if isinstance(mod, Scalar) and mod != Scalar(0):
            return Scalar(self.x % mod.x)
        return NotImplemented

    # Negation
    def __neg__(self):
        return Scalar(-self.x)


# An element of the curve group
class Point:
    def __init__(self, x, y=None):
        # Generated from integer values
        if isinstance(x, int) and isinstance(y, int) and y is not None:
            self.x = x % p
            self.y = y % p

            if not self.on_curve():
                raise ValueError
        # Generated from a hex representation (remove 0x first)
        elif isinstance(x, str) and y is None:
            try:
                if len(x) == b // 2 + 2 and x[:2] == '04':
                    self.x = int(x[2:b // 4 + 2], 16)
                    self.y = int(x[b // 4 + 2:], 16)
                elif len(x) == b // 4 + 2 and x[:2] == '03':
                    self.x = int(x[2:], 16)
                    self.y = yfromx(self.x, False)
                elif len(x) == b // 4 + 2 and x[:2] == '02':
                    self.x = int(x[2:], 16)
                    self.y = yfromx(self.x, True)
                elif x == '00':   # point at infinity
                    self.x = self.y = 0
                else:
                    raise TypeError
            except:
                raise TypeError

            if not self.x == self.y == 0 and not self.on_curve():
                raise ValueError
        else:
            raise TypeError

    # Equality
    def __eq__(self, Q):
        if isinstance(Q, Point):
            return self.x == Q.x and self.y == Q.y
        raise TypeError

    # Inequality
    def __ne__(self, Q):
        if isinstance(Q, Point):
            return self.x != Q.x or self.y != Q.y
        raise TypeError

    # Addition
    def __add__(self, Q):
        if isinstance(Q, Point):
            if self.x == self.y == 0:   # Z + Q = Q
                return Q
            elif Q.x == Q.y == 0:   # P + Z = P
                return self
            elif self.x == Q.x and self.y == p - Q.y:   # Q + (-Q) = Z
                return Point('00')
            else:
                x1 = self.x
                y1 = self.y
                x2 = Q.x
                y2 = Q.y
                if x1 == x2 and y1 == y2:
                    s = 3 * x1 * x1 * invert(2 * y1, p)
                else:
                    s = (y2 - y1) * invert(x2 - x1, p)
                x3 = s * s - x1 - x2
                y3 = s * (x1 - x3) - y1
                return Point(x3, y3)
        return NotImplemented

    # Subtraction
    def __sub__(self, Q):
        if isinstance(Q, Point):
            if self.x == self.y == 0:   # Z - Q = -Q
                return -Q
            elif Q.x == Q.y == 0:   # P - Z = P
                return self
            elif self == Q:   # Q - Q = Z
                return Point('00')
            else:
                x1 = self.x
                y1 = self.y
                x2 = Q.x
                y2 = p - Q.y
                if x1 == x2 and y1 == y2:
                    s = 3 * x1 * x1 * invert(2 * y1, p)
                else:
                    s = (y2 - y1) * invert(x2 - x1, p)
                x3 = s * s - x1 - x2
                y3 = s * (x1 - x3) - y1
                return Point(x3, y3)
        return NotImplemented

    # Multiplication
    def __mul__(self,y):
        # Point-Scalar: scalar multiplication
        if isinstance(y, Scalar):
            if y == Scalar(0):
                return Point('00')
            Q = self.__mul__(y / Scalar(2))
            Q = Q.__add__(Q)
            if y.x & 1:
                Q = self.__add__(Q)
            return Q
        return NotImplemented

    def __rmul__(self, y):
        # Scalar-Point
        if isinstance(y, Scalar):
            return self * y
        return NotImplemented

    # Hex representation
    def __repr__(self):
        # return compressed
        if self.x == self.y == 0:
            return '00'
        elif self.y % 2 == 0:
            return f'02{self.x:0{b // 4}x}'
        else:
            return f'03{self.x:0{b // 4}x}'

    # Curve membership
    def on_curve(self):
        x = self.x
        y = self.y
        return (y * y - x * x * x - 7) % p == 0

    # Negation
    def __neg__(self):
        if self.x == self.y == 0:
            return self
        return Point(self.x, -self.y)


# A vector of Points with superpowers
class PointVector:
    def __init__(self, points=None):
        if points is None:
            points = []
        for point in points:
            if not isinstance(point, Point):
                raise TypeError
        self.points = points

    # Equality
    def __eq__(self, W):
        if isinstance(W, PointVector):
            return self.points == W.points
        raise TypeError

    # Inequality
    def __ne__(self, W):
        if isinstance(W, PointVector):
            return self.points != W.points
        raise TypeError

    # Addition
    def __add__(self, W):
        if isinstance(W, PointVector) and len(self.points) == len(W.points):
            return PointVector([self.points[i] + W.points[i] for i in range(len(self.points))])
        return NotImplemented

    # Subtraction
    def __sub__(self, W):
        if isinstance(W, PointVector) and len(self.points) == len(W.points):
            return PointVector([self.points[i] - W.points[i] for i in range(len(self.points))])
        return NotImplemented

    # Multiplication
    def __mul__(self, s):
        # PointVector-Scalar: componentwise Point-Scalar multiplication
        if isinstance(s, Scalar):
            return PointVector([self.points[i] * s for i in range(len(self.points))])
        # PointVector-ScalarVector: Hadamard product
        if isinstance(s, ScalarVector) and len(self.points) == len(s.scalars):
            return PointVector([s[i] * self[i] for i in range(len(self))])
        return NotImplemented

    def __rmul__(self, s):
        # Scalar-PointVector
        if isinstance(s, Scalar):
            return self * s
        # ScalarVector-PointVector
        if isinstance(s, ScalarVector):
            return self * s
        return NotImplemented

    # Multiscalar multiplication
    def __pow__(self, s):
        if isinstance(s, ScalarVector) and len(self.points) == len(s.scalars):
            return multiexp(s, self)
        return NotImplemented

    # Length
    def __len__(self):
        return len(self.points)

    # Get slice
    def __getitem__(self, i):
        if not isinstance(i, slice):
            return self.points[i]
        return PointVector(self.points[i])

    # Set at index
    def __setitem__(self, i, P):
        if isinstance(P, Point):
            self.points[i] = P
        else:
            raise TypeError

    # Append
    def append(self, item):
        if isinstance(item, Point):
            self.points.append(item)
        else:
            raise TypeError

    # Extend
    def extend(self, items):
        if isinstance(items, PointVector):
            for item in items.points:
                self.points.append(item)
        else:
            raise TypeError

    # Hex representation of underlying Points
    def __repr__(self):
        return repr(self.points)

    # Negation
    def __neg__(self):
        return PointVector([-P for P in self.points])


# A vector of Scalars with superpowers
class ScalarVector:
    def __init__(self, scalars=None):
        if scalars is None:
            scalars = []
        for scalar in scalars:
            if not isinstance(scalar,Scalar):
                raise TypeError
        self.scalars = scalars

    # Equality
    def __eq__(self,s):
        if isinstance(s, ScalarVector):
            return self.scalars == s.scalars
        raise TypeError

    # Inequality
    def __ne__(self,s):
        if isinstance(s, ScalarVector):
            return self.scalars != s.scalars
        raise TypeError

    # Addition
    def __add__(self, s):
        if isinstance(s, ScalarVector) and len(self.scalars) == len(s.scalars):
            return ScalarVector([self.scalars[i] + s.scalars[i] for i in range(len(self.scalars))])
        return NotImplemented

    # Subtraction
    def __sub__(self,s):
        if isinstance(s, ScalarVector) and len(self.scalars) == len(s.scalars):
            return ScalarVector([self.scalars[i] - s.scalars[i] for i in range(len(self.scalars))])
        return NotImplemented

    # Multiplication
    def __mul__(self,s):
        # ScalarVector-Scalar: componentwise Scalar-Scalar multiplication 
        if isinstance(s, Scalar):
            return ScalarVector([self.scalars[i] * s for i in range(len(self.scalars))])
        # ScalarVector-ScalarVector: Hadamard product
        if isinstance(s, ScalarVector) and len(self.scalars) == len(s.scalars):
            return ScalarVector([self.scalars[i] * s.scalars[i] for i in range(len(self.scalars))])
        return NotImplemented

    def __rmul__(self, s):
        # Scalar-ScalarVector
        if isinstance(s,Scalar):
            return self * s
        return NotImplemented

    # Sum of all Scalars
    def sum(self):
        r = Scalar(0)
        for i in range(len(self.scalars)):
            r += self.scalars[i]
        return r

    # Inner product and multiscalar multiplication
    def __pow__(self, s):
        # ScalarVector**ScalarVector: inner product
        if isinstance(s, ScalarVector) and len(self.scalars) == len(s.scalars):
            r = Scalar(0)
            for i in range(len(self.scalars)):
                r += self.scalars[i] * s.scalars[i]
            return r
        # ScalarVector**PointVector: multiscalar multiplication
        if isinstance(s, PointVector):
            return s ** self
        return NotImplemented

    # Length
    def __len__(self):
        return len(self.scalars)

    # Get slice
    def __getitem__(self, i):
        if not isinstance(i, slice):
            return self.scalars[i]
        return ScalarVector(self.scalars[i])

    # Set at index
    def __setitem__(self, i, s):
        if isinstance(s, Scalar):
            self.scalars[i] = s
        else:
            raise TypeError

    # Append
    def append(self, item):
        if isinstance(item, Scalar):
            self.scalars.append(item)
        else:
            raise TypeError

    # Extend
    def extend(self, items):
        if isinstance(items, ScalarVector):
            for item in items.scalars:
                self.scalars.append(item)
        else:
            raise TypeError

    # Hex representation of underlying Scalars
    def __repr__(self):
        return repr(self.scalars)

    # Componentwise inversion (possibly with zero)
    def invert(self, allow_zero=False):
        # If we allow zero, the efficient method doesn't work
        if allow_zero:
            return ScalarVector([s.invert(allow_zero=True) for s in self.scalars])

        # Don't allow zero
        inputs = self.scalars[:]
        m = len(inputs)
        scratch = [Scalar(1)] * m
        acc = Scalar(1)

        for i in range(m):
            if inputs[i] == Scalar(0):
                raise ZeroDivisionError
            scratch[i] = acc
            acc *= inputs[i]
        acc = acc.invert()
        for i in range(m - 1, -1, -1):
            temp = acc * inputs[i]
            inputs[i] = acc * scratch[i]
            acc = temp

        return ScalarVector(inputs)

    # Negation
    def __neg__(self):
        return ScalarVector([-s for s in self.scalars])


# Try to make a point from a given x-coordinate
def make_point(x):
    if not x < p:   # stay in the field
        return None
    y = yfromx(x, secrets.randbits(1))
    try:
        P = Point(x, y)
    except ValueError:
        return None
    return P


# Hash data to get a Point in the main subgroup
def hash_to_point(*data):
    result = ''
    for datum in data:
        if datum is None:
            raise TypeError
        result += blake2s(str(datum).encode('utf-8')).hexdigest()

    # Continue hashing until we get a valid Point
    while True:
        result = blake2s(result.encode('utf-8')).hexdigest()
        test = make_point(int(result, 16))
        if test is not None:
            return test * Scalar(cofactor)


# Hash data to get a Scalar
def hash_to_scalar(*data):
    result = ''
    for datum in data:
        if datum is None:
            raise TypeError
        result += blake2s(str(datum).encode('utf-8')).hexdigest()

    # Continue hashing until we get a valid Scalar
    while True:
        result = blake2s(result.encode('utf-8')).hexdigest()
        test = int(result, 16)
        if test < n:
            return Scalar(test)


# Generate a random Scalar
def random_scalar(zero=True):
    value = Scalar(secrets.randbelow(n))
    if not zero and value == Scalar(0):
        raise ValueError('Random scalar unexpectedly returned zero!')
    return value


# Generate a random Point in the main subgroup
def random_point():
    return hash_to_point(secrets.randbits(b))


# The main subgroup default generator
G = Point('0279BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798')


# Point at infinity = identity/zero point of EC point addition
Z = Point('00')


# Perform a multiscalar multiplication using a simplified Pippenger algorithm
def multiexp(scalars, points):
    if not isinstance(scalars, ScalarVector) or not isinstance(points, PointVector):
        raise TypeError

    if len(scalars) != len(points):
        raise IndexError
    if len(scalars) == 0:
        return Z

    buckets = None
    result = Z   # zero point

    c = 4   # window parameter; NOTE: the optimal value actually depends on len(points) empirically

    # really we want to use the max bitlength to compute groups
    maxscalar = int(max(scalars))
    groups = 0
    while maxscalar >= 2 ** groups:
        groups += 1
    groups = int((groups + c - 1) / c)

    # loop is really (groups-1)..0
    for k in range(groups - 1, -1, -1):
        if result != Z:
            for i in range(c):
                result += result

        buckets = [Z] * (2 ** c)   # clear all buckets

        # partition scalars into buckets
        for i in range(len(scalars)):
            bucket = 0
            for j in range(c):
                if int(scalars[i]) & (1 << (k * c + j)):   # test for bit
                    bucket |= 1 << j

            if bucket == 0:   # zero bucket is never used
                continue

            if buckets[bucket] != Z:
                buckets[bucket] += points[i]
            else:
                buckets[bucket] = points[i]

        # sum the buckets
        pail = Z
        for i in range(len(buckets) - 1, 0, -1):
            if buckets[i] != Z:
                pail += buckets[i]
            if pail != Z:
                result += pail
    return result

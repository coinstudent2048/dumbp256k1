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
# cofactor = 1
b = 256   # bit length


# Internal helper methods
def invert(x, p):
    # Assumes `p` is prime
    return pow(x, p - 2, p)


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
            self.x = x
            self.y = y

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
            if self.x == self.y == 0:   # I + Q = Q
                return Q
            elif Q.x == Q.y == 0:   # P + I = P
                return self
            elif self.x == Q.x and self.y == p - Q.y:   # Q + (-Q) = I
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
                return Point(x3 % p, y3 % p)
        return NotImplemented

    # Subtraction
    def __sub__(self, Q):
        if isinstance(Q, Point):
            if self.x == self.y == 0:   # I - Q = -Q
                return -Q
            elif Q.x == Q.y == 0:   # P - I = P
                return self
            elif self == Q:   # Q - Q = I
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
                return Point(x3 % p, y3 % p)
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

    # Curve membership (not main subgroup!)
    def on_curve(self):
        x = self.x
        y = self.y
        return (y * y - x * x * x - 7) % p == 0

    # Negation
    def __neg__(self):
        return Point(self.x, p - self.y)


# The main subgroup default generator
G = Point('0279BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798')

# Point at infinity = identity element of EC point addition
I = Point('00')
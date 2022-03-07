# Testing Dumbp256k1

import pytest
import dumbp256k1


# parse test vectors
data = []
with open('test_vectors.txt','r') as fp:
    while True:
        line = fp.readline()
        if not line:
            break

        if line[:4] == 'k = ':
            k = int(line.strip()[4:])   # int
            line = fp.readline()
            x = line.strip()[4:]   # uppercase hex string
            line = fp.readline()
            y = line.strip()[4:]   # uppercase hex string

            data.append((k, x, y))


def test_keypair():
    for k, x, y in data:
        test = dumbp256k1.Scalar(k) * dumbp256k1.G
        hex_x = f'{test.x:0{dumbp256k1.b // 4}X}'
        hex_y = f'{test.y:0{dumbp256k1.b // 4}X}'
        assert (hex_x, hex_y) == (x, y)


def test_point_at_infinity():
    test = dumbp256k1.Scalar(dumbp256k1.n) * dumbp256k1.G
    assert str(test) == '00'


def test_addition():
    # test point at infinity
    assert dumbp256k1.Z + dumbp256k1.Z == dumbp256k1.Z
    assert dumbp256k1.Z + dumbp256k1.G == dumbp256k1.G
    assert dumbp256k1.G + dumbp256k1.Z == dumbp256k1.G
    assert dumbp256k1.G + (-dumbp256k1.G) == dumbp256k1.Z
    # randomized testing
    for i in range(50):
        a = dumbp256k1.random_scalar()
        b = dumbp256k1.random_scalar()
        c = a + b
        aG = a * dumbp256k1.G
        bG = b * dumbp256k1.G
        cG = c * dumbp256k1.G
        assert aG + bG == cG
        assert bG + aG == cG


def test_subtraction():
    # test point at infinity
    assert -dumbp256k1.Z == dumbp256k1.Z
    assert dumbp256k1.Z - dumbp256k1.Z == dumbp256k1.Z
    assert dumbp256k1.Z - dumbp256k1.G == -dumbp256k1.G
    assert dumbp256k1.G - dumbp256k1.Z == dumbp256k1.G
    assert dumbp256k1.G - dumbp256k1.G == dumbp256k1.Z
    # randomized testing
    for i in range(50):
        a = dumbp256k1.random_scalar()
        b = dumbp256k1.random_scalar()
        c = a - b
        aG = a * dumbp256k1.G
        bG = b * dumbp256k1.G
        cG = c * dumbp256k1.G
        assert aG - bG == cG
        assert bG - aG == -cG

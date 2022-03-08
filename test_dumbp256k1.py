# Testing Dumbp256k1
# Only "more complex" functions are tested because lazy

import pytest, secrets
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
    # test point at infinity
    test = dumbp256k1.Scalar(dumbp256k1.n) * dumbp256k1.G
    assert str(test) == '00'
    # test through test vectors
    for k, x, y in data:
        test = dumbp256k1.Scalar(k) * dumbp256k1.G
        hex_x = f'{test.x:0{dumbp256k1.b // 4}X}'
        hex_y = f'{test.y:0{dumbp256k1.b // 4}X}'
        assert (hex_x, hex_y) == (x, y)


def test_addition():
    # test point at infinity
    assert dumbp256k1.Z + dumbp256k1.Z == dumbp256k1.Z
    assert dumbp256k1.Z + dumbp256k1.G == dumbp256k1.G
    assert dumbp256k1.G + dumbp256k1.Z == dumbp256k1.G
    assert dumbp256k1.G + (-dumbp256k1.G) == dumbp256k1.Z
    # randomized testing
    for i in range(20):
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
    for i in range(20):
        a = dumbp256k1.random_scalar()
        b = dumbp256k1.random_scalar()
        c = a - b
        aG = a * dumbp256k1.G
        bG = b * dumbp256k1.G
        cG = c * dumbp256k1.G
        assert aG - bG == cG
        assert bG - aG == -cG


def test_scalarvector_invert():
    # test Scalar(0)
    svector = [dumbp256k1.Scalar(0), dumbp256k1.Scalar(1), dumbp256k1.Scalar(2)]
    svector = dumbp256k1.ScalarVector(svector)
    with pytest.raises(ZeroDivisionError):
        svector.invert()
    assert (svector.invert(allow_zero=True)).invert(allow_zero=True) == svector
    # randomized testing
    for i in range(20):
        svector = []
        for j in range(secrets.randbelow(4) + 1):
            svector.append(dumbp256k1.random_scalar())
        svector = dumbp256k1.ScalarVector(svector)
        assert (svector.invert()).invert() == svector


def test_vector_products():
    # test Scalar(0) and point at infinity
    svector1 = [dumbp256k1.Scalar(0)] * 3
    svector1 = dumbp256k1.ScalarVector(svector1)
    svector2 = [dumbp256k1.random_scalar(), dumbp256k1.random_scalar(), dumbp256k1.random_scalar()]
    svector2 = dumbp256k1.ScalarVector(svector2)
    pvector = dumbp256k1.PointVector([dumbp256k1.G] * 3)
    assert svector1 ** (svector2 * pvector) == dumbp256k1.Point('00')
    # randomized testing
    for i in range(20):
        svector1 = []
        svector2 = []
        length = secrets.randbelow(4) + 1
        pvector = dumbp256k1.PointVector([dumbp256k1.G] * length)
        for j in range(length):
            svector1.append(dumbp256k1.random_scalar(zero=True))
        svector1 = dumbp256k1.ScalarVector(svector1)
        for j in range(length):
            svector2.append(dumbp256k1.random_scalar(zero=True))
        svector2 = dumbp256k1.ScalarVector(svector2)
        assert svector1 ** (svector2 * pvector) == (svector1 ** svector2) * dumbp256k1.G

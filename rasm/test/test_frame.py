from unittest import TestCase
from rasm.model import W_Int, symbol
from rasm.error import OperationError
from rasm.frame import Frame
from rasm import code # Patch the frame

FRAME_SIZE = 1024

class TestFrame(TestCase):
    def setUp(self):
        self.frame = Frame(FRAME_SIZE, None)

    def test_ctor(self):
        self.assertEquals(self.frame.stacktop, 0)
        self.assertEquals(len(self.frame.local_w), FRAME_SIZE)

    def test_push(self):
        i = W_Int(1)
        self.frame.push(i)
        self.assertEquals(self.frame.stacktop, 1)

    def test_pop(self):
        i = W_Int(1)
        self.frame.push(i)
        i2 = self.frame.pop()
        self.assertEquals(self.frame.stacktop, 0)
        self.assertIs(i, i2)

    def test_pushsome(self):
        i1 = W_Int(1)
        i2 = W_Int(2)
        i3 = W_Int(3)
        self.frame.pushsome([i1, i2, i3])
        self.assertEquals(self.frame.stacktop, 3)
        self.assertIs(i3, self.frame.pop())
        self.assertIs(i2, self.frame.pop())
        self.assertIs(i1, self.frame.pop())

    def test_dropsome(self):
        i1 = W_Int(1)
        i2 = W_Int(2)
        i3 = W_Int(3)
        self.frame.pushsome([i1, i2, i3])
        self.frame.dropsome(3)
        self.assertEquals(self.frame.stacktop, 0)

    def test_dropto(self):
        i1 = W_Int(1)
        i2 = W_Int(2)
        i3 = W_Int(3)
        self.frame.pushsome([i1, i2, i3])
        self.frame.dropto(0)
        self.assertEquals(self.frame.stacktop, 0)

    def test_pop_error(self):
        self.assertRaises((OperationError, AssertionError), self.frame.pop)

    def test_push_error(self):
        [self.frame.push(symbol('x')) for _ in xrange(FRAME_SIZE)]
        self.assertRaises((OperationError, AssertionError),
                          self.frame.push, symbol('x'))

    def test_dropsome_empty(self):
        [self.frame.push(symbol('x')) for _ in xrange(FRAME_SIZE)]
        self.frame.dropsome(FRAME_SIZE)
        self.assertEquals(self.frame.stacktop, 0)

    def test_dropto_empty(self):
        [self.frame.push(symbol('x')) for _ in xrange(FRAME_SIZE)]
        self.frame.dropto(0)
        self.assertEquals(self.frame.stacktop, 0)

    def test_dropsome_error(self):
        [self.frame.push(symbol('x')) for _ in xrange(FRAME_SIZE)]
        self.assertRaises((AssertionError, OperationError),
                self.frame.dropsome, 1025)

    def test_dropto_error(self):
        [self.frame.push(symbol('x')) for _ in xrange(FRAME_SIZE)]
        self.assertRaises((AssertionError, OperationError), self.frame.dropto, -1)

    def test_pushsome_full(self):
        lst = [symbol('x') for _ in xrange(FRAME_SIZE)]
        self.frame.pushsome(lst)
        self.assertEquals(self.frame.stacktop, FRAME_SIZE)

    def test_pushsome_error(self):
        lst = [symbol('x') for _ in xrange(1025)]
        self.assertRaises((AssertionError, OperationError),
                          self.frame.pushsome, lst)


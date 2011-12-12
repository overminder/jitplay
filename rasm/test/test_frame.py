from unittest import TestCase
from rasm.model import W_Int, symbol
from rasm.error import OperationError
from rasm.frame import Stack

class TestStack(TestCase):
    def setUp(self):
        self.s = Stack(1024)

    def test_ctor(self):
        self.assertEquals(self.s.top, 0)
        self.assertEquals(len(self.s.item_w), 1024)

    def test_push(self):
        i = W_Int(1)
        self.s.push(i)
        self.assertEquals(self.s.top, 1)

    def test_ref(self):
        i = W_Int(1)
        self.s.push(i)
        self.assertIs(self.s.ref(0), i)

    def test_pop(self):
        i = W_Int(1)
        self.s.push(i)
        i2 = self.s.pop()
        self.assertEquals(self.s.top, 0)
        self.assertIs(i, i2)

    def test_pushsome(self):
        i1 = W_Int(1)
        i2 = W_Int(2)
        i3 = W_Int(3)
        self.s.pushsome([i1, i2, i3])
        self.assertEquals(self.s.top, 3)
        self.assertIs(i3, self.s.pop())
        self.assertIs(i2, self.s.pop())
        self.assertIs(i1, self.s.pop())

    def test_dropsome(self):
        i1 = W_Int(1)
        i2 = W_Int(2)
        i3 = W_Int(3)
        self.s.pushsome([i1, i2, i3])
        self.s.dropsome(3)
        self.assertEquals(self.s.top, 0)

    def test_dropto(self):
        i1 = W_Int(1)
        i2 = W_Int(2)
        i3 = W_Int(3)
        self.s.pushsome([i1, i2, i3])
        self.s.dropto(0)
        self.assertEquals(self.s.top, 0)

    def test_ref_error(self):
        self.assertRaises((OperationError, AssertionError), self.s.ref, 0)
        self.assertRaises((OperationError, AssertionError), self.s.ref, 1024)
        self.assertRaises((OperationError, AssertionError), self.s.ref, 1025)

    def test_pop_error(self):
        self.assertRaises((OperationError, AssertionError), self.s.pop)

    def test_push_error(self):
        [self.s.push(symbol('x')) for _ in xrange(1024)]
        self.assertRaises(OperationError, self.s.push, symbol('x'))

    def test_dropsome_empty(self):
        [self.s.push(symbol('x')) for _ in xrange(1024)]
        self.s.dropsome(1024)
        self.assertEquals(self.s.top, 0)

    def test_dropto_empty(self):
        [self.s.push(symbol('x')) for _ in xrange(1024)]
        self.s.dropto(0)
        self.assertEquals(self.s.top, 0)

    def test_dropsome_error(self):
        [self.s.push(symbol('x')) for _ in xrange(1024)]
        self.assertRaises((AssertionError, OperationError),
                self.s.dropsome, 1025)

    def test_dropto_error(self):
        [self.s.push(symbol('x')) for _ in xrange(1024)]
        self.assertRaises((AssertionError, OperationError), self.s.dropto, -1)

    def test_pushsome_full(self):
        lst = [symbol('x') for _ in xrange(1024)]
        self.s.pushsome(lst)
        self.assertEquals(self.s.top, 1024)

    def test_pushsome_error(self):
        lst = [symbol('x') for _ in xrange(1025)]
        self.assertRaises(OperationError, self.s.pushsome, lst)


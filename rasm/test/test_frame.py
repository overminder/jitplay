from unittest import TestCase
from rasm.model import W_Int, symbol
from rasm.error import OperationError
from rasm.frame import Frame
from rasm.code import W_Proto, W_Cont

class TestFrame(TestCase):
    def setUp(self):
        self.w_proto = W_Proto([], 0, 0, [], [], w_module=None)
        self.w_cont = W_Cont(self.w_proto, [])
        self.frame = Frame(self.w_cont, [self.w_proto])

    def test_ctor(self):
        self.assertEquals(self.frame.stacktop, 0)

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

    def test_peek(self):
        i = W_Int(1)
        self.frame.push(i)
        i2 = self.frame.peek()
        self.assertEquals(self.frame.stacktop, 1)
        self.assertIs(i, i2)

    def test_settop(self):
        i = W_Int(1)
        i2 = W_Int(2)
        self.frame.push(i)
        self.frame.settop(i2)
        i3 = self.frame.peek()
        self.assertEquals(self.frame.stacktop, 1)
        self.assertIs(i2, i3)


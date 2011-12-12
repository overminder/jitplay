from unittest import TestCase
from rasm.model import W_Int, symbol, w_nil, w_true, w_false, W_Array
from rasm.error import OperationError

class TestModel(TestCase):
    def test_int_ctor(self):
        i = W_Int(5)
        self.assertEquals(i.to_int(), 5)
        self.assertEquals(i.to_string(), '5')

    def test_symbol_ctor(self):
        s1 = symbol('s')
        s2 = symbol('s')
        self.assertIs(s1, s2)
        self.assertEquals(s1.to_string(), ':s')
        self.assertRaises(OperationError, s1.to_int)

    def test_nil(self):
        self.assertTrue(w_nil.to_bool())

    def test_false(self):
        self.assertFalse(w_false.to_bool())

    def test_aref(self):
        a = W_Array(1)
        self.assertIs(a.aref(0), w_nil)

    def test_aset(self):
        a = W_Array(1)
        a.aset(0, w_true)
        self.assertIs(a.aref(0), w_true)

    def test_alen(self):
        a = W_Array(1)
        self.assertIs(a.alen().to_int(), 1)


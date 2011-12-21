from unittest import TestCase
from rasm.lang.model import (W_Int, symbol, w_nil, w_true, w_false, W_Pair,
                             list_to_pair)
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

    def test_pair(self):
        s1 = symbol('s1')
        s2 = symbol('s2')
        p = W_Pair(s1, s2)
        self.assertEquals(p.car_w(), s1)
        self.assertEquals(p.cdr_w(), s2)

    def test_pair_from_list(self):
        s1 = symbol('s1')
        s2 = symbol('s2')
        p = list_to_pair([s1, s2])
        self.assertEquals(p.car_w(), s1)
        self.assertEquals(p.cdr_w().car_w(), s2)
        self.assertEquals(p.cdr_w().cdr_w(), w_nil)


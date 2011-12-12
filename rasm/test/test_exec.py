from unittest import TestCase
from rasm.model import W_Int, symbol, w_nil, w_true, w_false, W_Array
from rasm.error import OperationError
from rasm.frame import Stack
from rasm.code import CodeEnum, W_Function
from rasm.execution import W_Frame

def makecode(lst):
    return ''.join(map(chr, lst))

class TestExec(TestCase):
    def test_simple_add(self):
        simple_add = makecode([
            CodeEnum.INT, 1, 0,
            CodeEnum.INT, 2, 0,
            CodeEnum.IADD,
            CodeEnum.DUP,
            CodeEnum.PRINT,
            CodeEnum.FRET,
        ])
        s = Stack(2)
        f = W_Frame()
        f.stack = s
        f.code = simple_add
        w_ret = f.enter_dispatchloop()
        self.assertEquals(w_ret.to_int(), 3)

    def test_constpool(self):
        load_symbol = makecode([
            CodeEnum.SYMBOL, 0, 0,
            CodeEnum.DUP,
            CodeEnum.PRINT,
            CodeEnum.FRET,
        ])
        s = Stack(2)
        f = W_Frame()
        f.constpool = [symbol('hello')]
        f.stack = s
        f.code = load_symbol
        w_ret = f.enter_dispatchloop()
        self.assertEquals(w_ret.to_string(), ':hello')

    def test_simple_call(self):
        func_code = makecode([
            CodeEnum.INT, 1, 0,
            CodeEnum.FRET,
        ])
        main_code = makecode([
            CodeEnum.FLOAD, 0, 0,
            CodeEnum.FCALL, 0,
            CodeEnum.FRET,
        ])
        s = Stack(2)
        f = W_Frame()
        w_func = W_Function()
        w_func.code = func_code
        f.constpool = [w_func]
        f.stack = s
        f.code = main_code
        w_ret = f.enter_dispatchloop()
        self.assertEquals(w_ret.to_int(), 1)

    def test_goto(self):
        main_code = makecode([
            CodeEnum.INT, 12, 0,
            CodeEnum.GOTO, 3, 0,
            CodeEnum.INT, 6, 0,
            CodeEnum.FRET,
        ])
        s = Stack(2)
        f = W_Frame()
        f.stack = s
        f.code = main_code
        w_ret = f.enter_dispatchloop()
        self.assertEquals(w_ret.to_int(), 12)

    def test_lt(self):
        main_code = makecode([
            CodeEnum.INT, 12, 0,
            CodeEnum.INT, 6, 0,
            CodeEnum.LT,
            CodeEnum.FRET,
        ])
        s = Stack(2)
        f = W_Frame()
        f.stack = s
        f.code = main_code
        w_ret = f.enter_dispatchloop()
        self.assertFalse(w_ret.to_bool())

    def test_if(self):
        main_code = makecode([
            CodeEnum.INT, 6, 0,
            CodeEnum.FALSE,
            CodeEnum.BRANCHIFNOT, 3, 0,
            CodeEnum.INT, 12, 0,
            CodeEnum.FRET,
        ])
        s = Stack(2)
        f = W_Frame()
        f.stack = s
        f.code = main_code
        w_ret = f.enter_dispatchloop()
        self.assertEquals(w_ret.to_int(), 6)

    def test_call_with_arg(self):
        func_code = makecode([
            CodeEnum.LOAD, 0,
            CodeEnum.INT, 2, 0,
            CodeEnum.IADD,
            CodeEnum.FRET,
        ])
        main_code = makecode([
            CodeEnum.INT, 1, 0,
            CodeEnum.FLOAD, 0, 0,
            CodeEnum.FCALL, 1,
            CodeEnum.FRET,
        ])
        s = Stack(3)
        f = W_Frame()
        w_func = W_Function()
        w_func.nargs = 1
        w_func.code = func_code
        f.constpool = [w_func]
        f.stack = s
        f.code = main_code
        w_ret = f.enter_dispatchloop()
        self.assertEquals(w_ret.to_int(), 3)

    def test_call_with_recur(self):
        # fibonacci
        func_code = makecode([
            CodeEnum.LOAD, 0,
            CodeEnum.INT, 2, 0,
            CodeEnum.LT,
            CodeEnum.BRANCHIFNOT, 3, 0,
            CodeEnum.LOAD, 0,
            CodeEnum.FRET,

            CodeEnum.LOAD, 0,
            CodeEnum.INT, 1, 0,
            CodeEnum.ISUB,
            CodeEnum.FLOAD, 0, 0,
            CodeEnum.FCALL, 1,
            CodeEnum.LOAD, 0,
            CodeEnum.INT, 2, 0,
            CodeEnum.ISUB,
            CodeEnum.FLOAD, 0, 0,
            CodeEnum.FCALL, 1,
            CodeEnum.IADD,
            CodeEnum.FRET,
        ])
        main_code = makecode([
            CodeEnum.INT, 10, 0,
            CodeEnum.FLOAD, 0, 0,
            CodeEnum.FCALL, 1,
            CodeEnum.FRET,
        ])
        s = Stack(100)
        f = W_Frame()
        w_func = W_Function()
        w_func.nargs = 1
        w_func.code = func_code
        f.constpool = [w_func]
        f.stack = s
        f.code = main_code
        w_ret = f.enter_dispatchloop()
        self.assertEquals(w_ret.to_int(), 55)


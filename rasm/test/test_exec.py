from unittest import TestCase
from rasm.model import (W_Int, symbol, w_nil, w_true, w_false, W_Pair,
                        W_MPair)
from rasm.error import OperationError
from rasm.code import CodeEnum, W_Proto, W_Cont
from rasm.execution import Frame

def makecode(lst):
    return ''.join(map(chr, lst))

class TestExec(TestCase):
    def setUp(self):
        self.ctx = Context()

    def test_simple_add(self):
        simple_add = makecode([
            CodeEnum.INT, 1, 0,
            CodeEnum.INT, 2, 0,
            CodeEnum.IADD,
            CodeEnum.DUP,
            CodeEnum.PRINT,
            CodeEnum.FRET,
        ])
        f = Frame(2, simple_add, ctx=self.ctx)
        w_ret = f.run()
        self.assertEquals(w_ret.to_int(), 3)

    def test_constpool(self):
        load_symbol = makecode([
            CodeEnum.SYMBOL, 0, 0,
            CodeEnum.DUP,
            CodeEnum.PRINT,
            CodeEnum.FRET,
        ])
        f = Frame(2, load_symbol,
                  const_w=[symbol('hello')],
                  ctx=self.ctx)
        w_ret = f.run()
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
        w_func = W_Function()
        w_func.code = func_code
        w_func.framesize = 2
        f = Frame(2, main_code,
                  const_w=[w_func],
                  ctx=self.ctx)
        w_ret = f.run()
        self.assertEquals(w_ret.to_int(), 1)

    def test_goto(self):
        main_code = makecode([
            CodeEnum.INT, 12, 0,
            CodeEnum.GOTO, 3, 0,
            CodeEnum.INT, 6, 0,
            CodeEnum.FRET,
        ])
        f = Frame(2, main_code,
                  ctx=self.ctx)
        w_ret = f.run()
        self.assertEquals(w_ret.to_int(), 12)

    def test_lt(self):
        main_code = makecode([
            CodeEnum.INT, 12, 0,
            CodeEnum.INT, 6, 0,
            CodeEnum.LT,
            CodeEnum.FRET,
        ])
        f = Frame(2, main_code,
                  ctx=self.ctx)
        w_ret = f.run()
        self.assertFalse(w_ret.to_bool())

    def test_if(self):
        main_code = makecode([
            CodeEnum.INT, 6, 0,
            CodeEnum.FALSE,
            CodeEnum.BRANCHIFNOT, 3, 0,
            CodeEnum.INT, 12, 0,
            CodeEnum.FRET,
        ])
        f = Frame(2, main_code,
                  ctx=self.ctx)
        w_ret = f.run()
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
        w_func = W_Function()
        w_func.nb_args = 1
        w_func.code = func_code
        w_func.framesize = 3
        f = Frame(3, main_code,
                  const_w=[w_func],
                  ctx=self.ctx)
        w_ret = f.run()
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
        w_func = W_Function()
        w_func.nb_args = 1
        w_func.code = func_code
        w_func.const_w = [w_func]
        w_func.nb_args = 1
        w_func.nb_locals = 1
        w_func.framesize = 2
        f = Frame(4, main_code,
                  const_w=[w_func],
                  ctx=self.ctx)
        w_ret = f.run()
        self.assertEquals(w_ret.to_int(), 55)


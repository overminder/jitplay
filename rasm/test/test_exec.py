from unittest import TestCase
from rasm.model import (W_Int, symbol, w_nil, w_true, w_false, W_Pair,
                        W_MPair)
from rasm.error import OperationError
from rasm.code import Op, W_Proto, W_Cont
from rasm.execution import Frame

def makecode(lst):
    return ''.join(map(chr, lst))

class TestExec(TestCase):
    def test_simple_add(self):
        simple_add = makecode([
            Op.INT, 1, 0,
            Op.INT, 2, 0,
            Op.IADD,
            Op.DUP,
            Op.PRINT,
            Op.HALT,
        ])
        w_proto = W_Proto(simple_add, 0, 0, None, None)
        w_cont = W_Cont(w_proto, None)
        frame = Frame(w_cont, [w_proto])
        w_ret = frame.run()
        self.assertEquals(w_ret.to_int(), 3)

    def test_load_const(self):
        code = makecode([
            Op.LOADCONST, 0, 0,
            Op.DUP,
            Op.PRINT,
            Op.HALT,
        ])
        w_proto = W_Proto(code, 0, 0, None, [symbol('x')])
        w_cont = W_Cont(w_proto, None)
        frame = Frame(w_cont, [w_proto])
        w_ret = frame.run()
        self.assertEquals(w_ret.sval, 'x')

    def test_simple_call(self):
        maincode = makecode([
            Op.INT, 42, 0,
            Op.BUILDCONT, 0, 0,
            Op.CONT,
        ])
        callcode = makecode([
            Op.LOAD, 0,
            Op.HALT,
        ])
        w_mainproto = W_Proto(maincode, nb_args=0, nb_locals=0,
                              upval_descr=[], const_w=[])
        w_maincont = W_Cont(w_mainproto, upval_w=[])
        w_callproto = W_Proto(callcode, nb_args=1, nb_locals=1,
                              upval_descr=[], const_w=[])
        frame = Frame(w_maincont, [w_callproto])
        w_ret = frame.run()
        self.assertEquals(w_ret.to_int(), 42)

    def test_call_with_upval(self):
        maincode = makecode([
            Op.INT, 42, 0,
            Op.STORE, 0,
            Op.BUILDCONT, 0, 0,
            Op.CONT,
        ])
        callcode = makecode([
            Op.GETUPVAL, 0,
            Op.HALT,
        ])
        w_mainproto = W_Proto(maincode, nb_args=0, nb_locals=1,
                              upval_descr=[], const_w=[])
        w_maincont = W_Cont(w_mainproto, upval_w=[])
        w_callproto = W_Proto(callcode, nb_args=0, nb_locals=0,
                              upval_descr=[1], const_w=[])
        frame = Frame(w_maincont, [w_callproto])
        w_ret = frame.run()
        self.assertEquals(w_ret.to_int(), 42)

    def test_recur(self):
        maincode = makecode([
            Op.INT, 10, 0,
            Op.LOADCONST, 0, 0, # 'print-and-halt
            Op.LOADCONST, 1, 0, # 'fibo
            Op.CONT, # (fibo 10 print-and-halt)
        ])
        print_and_halt = makecode([
            Op.LOAD, 0,
            Op.DUP,
            Op.PRINT,
            Op.NEWLINE,
            Op.HALT,
        ])
        fibo_entry = makecode([
            Op.LOAD, 0,
            Op.DUP,
            Op.INT, 2, 0,
            Op.LT,
            Op.BRANCHIFNOT, 3, 0,
            # base case
            Op.LOAD, 1,
            Op.CONT,
            # recur case
            Op.INT, 1, 0,
            Op.ISUB,
            Op.BUILDCONT, 1, 0, # 'fibo-k0, with upval[0] = n, upval[1] = k
            Op.LOADCONST, 0, 0, # 'fibo
            Op.CONT,
        ])
        fibo_k0 = makecode([
            Op.GETUPVAL, 0,
            Op.INT, 2, 0,
            Op.ISUB,
            Op.BUILDCONT, 2, 0, # 'fibo-k1, with upval[0] = $Rv_0, upval[1] = k
            Op.LOADCONST, 0, 0, # 'fibo
            Op.CONT,
        ])
        fibo_k1 = makecode([
            Op.GETUPVAL, 0, # $Rv_0
            Op.LOAD, 0, # $Rv_1
            Op.IADD,
            Op.GETUPVAL, 1, # k
            Op.CONT,
        ])
        const_w0 = [None, None]
        const_w1 = [None]
        proto_w = [None, None, None, None, None]
        proto_w[0] = W_Proto(maincode, nb_args=0, nb_locals=0,
                             upval_descr=[], const_w=const_w0)
        w_maincont = W_Cont(proto_w[0], upval_w=[])
        proto_w[1] = W_Proto(fibo_k0, nb_args=1, nb_locals=1,
                             upval_descr=[(0 << 1) | 1, (1 << 1) | 1],
                             const_w=const_w1)
        proto_w[2] = W_Proto(fibo_k1, nb_args=1, nb_locals=1,
                             upval_descr=[(0 << 1) | 1, (1 << 1) | 0],
                             const_w=const_w1)
        proto_w[3] = W_Proto(fibo_entry, nb_args=2, nb_locals=2,
                             upval_descr=[],
                             const_w=const_w1)
        w_fibocont = W_Cont(proto_w[3], upval_w=[])
        proto_w[4] = W_Proto(print_and_halt, nb_args=1, nb_locals=1,
                             upval_descr=[],
                             const_w=[])
        w_printcont = W_Cont(proto_w[4], upval_w=[])
        const_w0[0] = w_printcont
        const_w0[1] = w_fibocont
        const_w1[0] = w_fibocont
        frame = Frame(w_maincont, proto_w)
        w_ret = frame.run()
        self.assertEquals(w_ret.to_int(), 55)

class Foo(object):
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
            CodeEnum.LOAD, 0, 0,
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


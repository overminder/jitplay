from unittest import TestCase
from rasm.model import (W_Int, symbol, w_nil, w_true, w_false, W_Pair,
                        W_MPair)
from rasm.module import ModuleDict
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
        w_proto = W_Proto(simple_add, 0, 0, [], [])
        w_cont = W_Cont(w_proto, [])
        frame = Frame(w_cont, [w_proto])
        w_ret = frame.run()
        self.assertEquals(w_ret.to_int(), 3)

    def test_load_const(self):
        code = makecode([
            Op.LOADCONST, 0,
            Op.DUP,
            Op.PRINT,
            Op.HALT,
        ])
        w_proto = W_Proto(code, 0, 0, [], [symbol('x')])
        w_cont = W_Cont(w_proto, [])
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
                              upval_descr=[chr(0)], const_w=[])
        frame = Frame(w_maincont, [w_callproto])
        w_ret = frame.run()
        self.assertEquals(w_ret.to_int(), 42)

    def test_recur(self):
        maincode = makecode([
            Op.INT, 10, 0,
            Op.GETGLOBAL, 1, # 'display-and-halt
            Op.GETGLOBAL, 0, # 'fibo
            Op.CONT, # (fibo 10 display-and-halt)
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
            Op.GETGLOBAL, 0, # 'fibo
            Op.CONT,
        ])
        fibo_k0 = makecode([
            Op.GETUPVAL, 0,
            Op.INT, 2, 0,
            Op.ISUB,
            Op.BUILDCONT, 2, 0, # 'fibo-k1, with upval[0] = $Rv_0, upval[1] = k
            Op.GETGLOBAL, 0, # 'fibo
            Op.CONT,
        ])
        fibo_k1 = makecode([
            Op.GETUPVAL, 0, # $Rv_0
            Op.LOAD, 0, # $Rv_1
            Op.IADD,
            Op.GETUPVAL, 1, # k
            Op.CONT,
        ])
        fibo_sym = symbol('fibo')
        dah_sym = symbol('display-and-halt')
        const_w0 = [fibo_sym, dah_sym]
        const_w1 = [fibo_sym]
        proto_w = [None, None, None, None, None]
        w_module = ModuleDict()
        proto_w[0] = W_Proto(maincode, nb_args=0, nb_locals=0,
                             upval_descr=[], const_w=const_w0,
                             w_module=w_module)
        w_maincont = W_Cont(proto_w[0], upval_w=[])
        proto_w[1] = W_Proto(fibo_k0, nb_args=1, nb_locals=1,
                             upval_descr=[chr(0), chr(1)],
                             const_w=const_w1, w_module=w_module)
        proto_w[2] = W_Proto(fibo_k1, nb_args=1, nb_locals=1,
                             upval_descr=[chr(0), chr(2)],
                             const_w=const_w1, w_module=w_module)
        proto_w[3] = W_Proto(fibo_entry, nb_args=2, nb_locals=2,
                             upval_descr=[],
                             const_w=const_w1, w_module=w_module)
        w_fibocont = W_Cont(proto_w[3], upval_w=[])
        proto_w[4] = W_Proto(print_and_halt, nb_args=1, nb_locals=1,
                             upval_descr=[],
                             const_w=[], w_module=w_module)
        w_printcont = W_Cont(proto_w[4], upval_w=[])

        w_module.setitem(fibo_sym, w_fibocont)
        w_module.setitem(dah_sym, w_printcont)

        frame = Frame(w_maincont, proto_w)

        w_ret = frame.run()
        self.assertEquals(w_ret.to_int(), 55)


from rasm.lang.model import (W_Root, W_Int, W_Boolean, W_Unspecified,
                             W_Pair, W_Nil, W_Symbol,
                             symbol, list_to_pair, gensym,
                             w_nil, w_true, w_false, w_unspec,
                             W_ValueError, W_TypeError)
from rasm.compiler.ast import (Node, If, Seq, Apply, Def, Sete, Lambda,
                               Var, Const)
from rasm.lang.model import symbol
from rasm.lang.env import ModuleDict
from rasm.rt.code import Op, W_Proto, W_Cont

class AbstractFrame(object):
    def __init__(self):
        self.stacktop = 0
        self.localmap = {}

class AbstractInterpreter(object):
    def __init__(self, node):
        self.node = node
        self.frame = AbstractFrame()
        self.code = []

    def run(self):
        self.visit(self.node)

    def visit(self, node):
        node.accept_interp(self)

    def emitbyte(self, u8):
        self.code.append(chr(u8))

    def emitshort(self, i16):
        self.emitbyte(i16 & 0xff)
        self.emitbyte((i16 >> 8) & 0xff)

    def dummyshort(self):
        res = len(self.code)
        self.emitbyte(0)
        self.emitbyte(0)
        return res, res + 2

    def codeptr(self):
        return len(self.code)

    def patchshort(self, index, i16):
        self.code[index] = chr(i16 & 0xff)
        self.code[index + 1] = chr((i16 >> 8) & 0xff)


class __extend__(Node):
    def accept_interp(self, interp):
        raise NotImplementedError


class __extend__(If):
    def accept_interp(self, interp):
        interp.visit(self.fst)
        interp.emitbyte(Op.BRANCHIFNOT)
        patch_index, jump_from = interp.dummyshort()
        interp.visit(self.snd)
        interp.patchshort(patch_index, interp.codeptr() - jump_from)
        interp.visit(self.trd)

class __extend__(Seq):
    def accept_interp(self, interp):
        for node in self.nodelist:
            interp.visit(node)

class __extend__(Apply):
    def accept_interp(self, interp):
        for arg in self.args:
            interp.visit(arg)
        interp.visit(self.proc)
        interp.emitbyte(Op.CONT)

class __extend__(Def):
    def accept_interp(self, interp):
        w_name = self.name.w_form
        assert isinstance(w_name, W_Symbol)
        raise NotImplementedError

class __extend__(Sete):
    def accept_interp(self, interp):
        w_name = self.name.w_form
        assert isinstance(w_name, W_Symbol)
        raise NotImplementedError

class __extend__(Var):
    def accept_interp(self, interp):
        pass


def main2(argv):
    try:
        fibo_arg = int(argv[1])
    except (IndexError, ValueError):
        fibo_arg = 30

    try:
        stacksize = int(argv[2])
    except (IndexError, ValueError):
        stacksize = 16

    maincode = makecode([
        Op.INT, fibo_arg, 0,
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

    frame = Frame(w_maincont, proto_w, stacksize)

    w_ret = frame.run()
    return 0

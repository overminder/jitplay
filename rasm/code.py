from pypy.rlib.jit import hint, unroll_safe, dont_look_inside
from pypy.rlib.debug import check_nonneg
from rasm.util import load_descr_file
from rasm.frame import Frame, W_ExecutionError
from rasm.model import (W_Root, W_Int, W_Pair, W_MPair,
                        w_nil, w_true, w_false,
                        W_Error, W_TypeError, W_ValueError)

def load_code_descr():
    namelist = load_descr_file('code.txt')

    last_i16 = namelist.index('_last_i16_')
    del namelist[last_i16]
    last_i16 -= 1

    last_u8 = namelist.index('_last_u8_')
    del namelist[last_u8]
    last_u8 -= 1

    namemap = dict((name, i) for (i, name) in enumerate(namelist))
    return namelist, namemap, last_i16, last_u8

codenames, codemap, last_i16, last_u8 = load_code_descr()

class Op(object):
    vars().update(codemap)

# For debug's purpose and for dispatching.
def argwidth(opcode):
    if opcode > last_u8:
        return 0
    elif opcode > last_i16:
        return 1
    else:
        return 2

class HaltContinuation(Exception):
    def __init__(self, w_retval):
        self.w_retval = w_retval

class W_ArgError(W_Error):
    def __init__(self, expected, got, w_cont):
        self.expected = expected
        self.got = got
        self.w_cont = w_cont

    def to_string(self):
        return '<ArgError: expecting %d arguments, but got %d at %s>' % (
                self.expected, self.got, self.w_cont.w_proto.name)

class W_Proto(W_Root):
    _immutable_ = True
    name = '#f'

    def __init__(self, code, nb_args, nb_locals, upval_descr, const_w):
        self.code = code
        check_nonneg(nb_args)
        self.nb_args = nb_args
        check_nonneg(nb_locals)
        self.nb_locals = nb_locals
        self.upval_descr = upval_descr
        self.const_w = const_w

    def to_string(self):
        return '<proto>'


class W_Cont(W_Root):
    _immutable_ = True

    def __init__(self, w_proto, upval_w):
        self.w_proto = w_proto
        self.upval_w = upval_w

    def to_string(self):
        return '<continuation>'


class __extend__(Frame):
    """ Extended Frame object that can interpret bytecode.
    """
    _virtualizable2_ = [
        'stacktop',
        'pc',
        'code',
        'local_w',
        'upval_w',
        'const_w',
        'proto_w',
        'stack_w[*]',
    ]
    _immutable_fields_ = ['proto_w[*]']

    def __init__(self, w_cont, proto_w):
        self = hint(self, promote=True,
                    access_directly=True,
                    fresh_virtualizable=True)
        self.stacktop = 0
        self.apply_continuation(w_cont)
        self.proto_w = proto_w
        self.stack_w = [None] * 32

    @unroll_safe
    def apply_continuation(self, w_cont):
        self.pc = 0
        self.code = w_cont.w_proto.code
        self.local_w = [None] * w_cont.w_proto.nb_locals
        self.upval_w = w_cont.upval_w
        self.const_w = w_cont.w_proto.const_w

    def nextbyte(self):
        pc = self.pc
        assert pc >= 0
        code = self.code[pc]
        self.pc = pc + 1
        return ord(code)

    def nextshort(self):
        b0 = self.nextbyte()
        b1 = self.nextbyte()
        return (b1 << 8) | b0

    def INT(self, ival):
        self.push(W_Int(ival))

    def LOADCONST(self, index):
        assert index >= 0
        w_val = self.const_w[index]
        self.push(w_val)

    @unroll_safe
    def BUILDCONT(self, index):
        assert index >= 0
        w_proto = self.proto_w[index]
        upval_w = [None] * len(w_proto.upval_descr)
        for i, descr in enumerate(w_proto.upval_descr):
            upval_index, is_fresh = descr >> 1, descr & 1
            assert upval_index >= 0
            if is_fresh:
                upval_w[i] = self.local_w[upval_index]
            else:
                upval_w[i] = self.upval_w[upval_index]
        w_cont = W_Cont(w_proto, upval_w)
        self.push(w_cont)

    def BRANCHIF(self, offset):
        if self.pop().to_bool():
            self.pc += offset

    def BRANCHIFNOT(self, offset):
        if not self.pop().to_bool():
            self.pc += offset

    def LOAD(self, index):
        assert index >= 0
        w_val = self.local_w[index]
        if w_val is None:
            # This is essential... And will not result in
            # a big performance hit.
            raise W_ExecutionError('unbound local variable',
                                   'load(%d)' % index).wrap()
        self.push(w_val)

    def STORE(self, index):
        assert index >= 0
        self.local_w[index] = self.pop()

    def GETUPVAL(self, index):
        assert index >= 0
        w_val = self.upval_w[index]
        self.push(w_val)

    def SETUPVAL(self, index):
        self.upval_w[index] = self.pop()

    @unroll_safe
    def CONT(self, _):
        w_cont = self.pop()
        if not isinstance(w_cont, W_Cont):
            raise W_TypeError('Continuation', w_cont, 'cont()').wrap()

        nb_args = self.stacktop
        w_proto = w_cont.w_proto
        # Argument count checking. (We currently don't consider complex
        # calling conventions like varargs...)
        if nb_args != w_proto.nb_args:
            raise W_ArgError(w_proto.nb_args, nb_args, w_cont).wrap()

        # Switch to this continuation.
        self.apply_continuation(w_cont)

        # Set arguments to local variables
        i = nb_args - 1
        while i >= 0:
            self.local_w[i] = self.pop()
            i -= 1

    def HALT(self, _):
        raise HaltContinuation(self.pop())

    def POP(self, _):
        self.pop()

    def DUP(self, _):
        self.push(self.peek())

    def ROT(self, _):
        w_x = self.pop()
        w_y = self.peek()
        self.settop(w_x)
        self.push(w_y)

    def NIL(self, _):
        self.push(w_nil)

    def TRUE(self, _):
        self.push(w_true)

    def FALSE(self, _):
        self.push(w_false)

    # Missing some cons operations

    def IADD(self, _):
        w_y = self.pop()
        w_x = self.peek()
        self.settop(W_Int(w_x.to_int() + w_y.to_int()))

    def ISUB(self, _):
        w_y = self.pop()
        w_x = self.peek()
        self.settop(W_Int(w_x.to_int() - w_y.to_int()))

    def IMUL(self, _):
        w_y = self.pop()
        w_x = self.peek()
        self.settop(W_Int(w_x.to_int() * w_y.to_int()))

    def IDIV(self, _):
        w_y = self.pop()
        w_x = self.peek()
        y = w_y.to_int()
        if y == 0:
            raise W_ValueError('divide by zero', w_x, 'idiv()').wrap()
        self.settop(W_Int(w_x.to_int() * y))

    def IS(self, _):
        w_x = self.pop()
        w_y = self.peek()
        self.settop(w_x.is_w(w_y))

    def EQUAL(self, _):
        w_x = self.pop()
        w_y = self.peek()
        self.settop(w_x.equal_w(w_y))

    def LT(self, _):
        y = self.pop().to_int()
        x = self.peek().to_int()
        self.settop(w_true if x < y else w_false)

    def NOT(self, _):
        x = self.pop().to_bool()
        self.settop(w_false if x else w_true)

    def OR(self, _):
        y = self.pop().to_bool()
        x = self.peek().to_bool()
        self.settop(w_true if x or y else w_false)

    def AND(self, _):
        y = self.pop().to_bool()
        x = self.peek().to_bool()
        self.settop(w_true if x and y else w_false)

    def PRINT(self, _):
        w_x = self.pop()
        print w_x.to_string(),

    def NEWLINE(self, _):
        print


def patching_ophandlers():
    def noimpl(self, _):
        raise NotImplementedError
    for name in codemap:
        meth = getattr(Frame, name, None)
        if meth is None:
            print 'Stub implementation for %s' % name
            setattr(Frame, name, noimpl)

patching_ophandlers()


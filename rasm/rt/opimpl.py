from pypy.rlib.jit import hint, unroll_safe, elidable, dont_look_inside
from rasm.rt.frame import Frame, W_ExecutionError
from rasm.rt.code import codemap, W_Cont
from rasm.rt.prelude import reify_callcc
from rasm.lang.model import (W_Root, W_Int, W_Pair,
                             w_nil, w_true, w_false, w_unspec,
                             W_Error, W_TypeError, W_ValueError, W_NameError)

DEBUG = False

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

class __extend__(Frame):
    """ Extended Frame object that can interpret bytecode.
        A typical stack consist of three parts:
        [frame_locals] [upvals] [temporaries]
        0 .. nb_locals - 1
                       nb_locals .. nb_locals + len(upval) - 1
                                nb_locals + len(upval) .. len(stack_w)
    """
    _virtualizable2_ = [
        'stacktop',
        'pc',
        'w_proto',
        'proto_w',
        'stack_w[*]',
    ]
    _immutable_fields_ = ['proto_w[*]']

    # XXX: stacksize would largely affect the efficiency.
    def __init__(self, w_cont, proto_w, stacksize=32):
        self = hint(self, promote=True,
                    access_directly=True,
                    fresh_virtualizable=True)
        self.stacktop = 0
        self.stack_w = [None] * stacksize
        self.proto_w = proto_w
        self.apply_continuation(w_cont)

    @unroll_safe
    def apply_continuation(self, w_cont):
        self.w_proto = w_cont.w_proto
        old_stacktop = self.stacktop
        self.stacktop = self.w_proto.nb_locals
        self.pc = 0
        if w_cont.upval_w:
            for w_upval in w_cont.upval_w:
                self.push(w_upval)
        # In case some old upvals/locals are left on the stack...
        if self.stacktop < old_stacktop:
            for i in xrange(self.stacktop, old_stacktop + 1):
                self.stackclear(i)

    def nextbyte(self, code):
        pc = self.pc
        assert pc >= 0
        c = code[pc]
        self.pc = pc + 1
        return ord(c)

    def nextshort(self, code):
        b0 = self.nextbyte(code)
        b1 = self.nextbyte(code)
        return (b1 << 8) | b0

    def INT(self, ival):
        self.push(W_Int(ival))

    @unroll_safe
    def BUILDCONT(self, index):
        assert index >= 0
        w_proto = self.proto_w[index]
        upval_w = [None] * len(w_proto.upval_descr)
        for i, descr in enumerate(w_proto.upval_descr):
            upval_w[i] = self.stackref(ord(descr))
        w_cont = W_Cont(w_proto, upval_w)
        self.push(w_cont)

    def BRANCHIF(self, offset):
        if self.pop().to_bool():
            self.pc += offset

    def BRANCHIFNOT(self, offset):
        if not self.pop().to_bool():
            self.pc += offset

    def LOADCONST(self, index):
        assert index >= 0
        w_val = self.w_proto.const_w[index]
        self.push(w_val)

    def GETGLOBAL(self, index):
        w_key = self.w_proto.const_w[index]
        w_val = self.w_proto.w_module.getitem(w_key)
        if w_val is None:
            raise W_NameError(w_key).wrap()
        self.push(w_val)

    def SETGLOBAL(self, index):
        w_key = self.w_proto.const_w[index]
        w_val = self.pop()
        self.w_proto.w_module.setitem(w_key, w_val)

    def LOAD(self, index):
        assert index >= 0
        w_val = self.stackref(index)
        if w_val is None:
            # This is essential... And will not result in
            # a big performance hit.
            raise W_ExecutionError(
                    'unbound local variable in %s' % self.w_proto.to_string(),
                    'load(%d)' % index).wrap()
        self.push(w_val)

    def STORE(self, index):
        assert index >= 0
        self.stackset(index, self.pop())

    def GETUPVAL(self, index):
        assert index >= 0
        w_val = self.stackref(index + self.w_proto.nb_locals)
        self.push(w_val)

    def SETUPVAL(self, index):
        assert index >= 0
        self.stackset(index + self.w_proto.nb_locals, self.pop())

    @unroll_safe
    def CONT(self, _):
        w_cont = self.pop()
        if DEBUG:
            print 'enter cont %s' % w_cont.to_string()
        if not isinstance(w_cont, W_Cont):
            raise W_TypeError('Continuation', w_cont, 'cont()').wrap()

        nb_args = (self.stacktop - self.w_proto.nb_locals -
                   self.w_proto.nb_upvals())
        # Argument count checking. (We currently don't consider complex
        # calling conventions like varargs...)
        if nb_args != w_cont.w_proto.nb_args:
            raise W_ArgError(w_cont.w_proto.nb_args, nb_args, w_cont).wrap()

        # Move arguments to local variables.
        offset = self.w_proto.nb_locals + self.w_proto.nb_upvals()
        for i in xrange(nb_args):
            self.stackset(i, self.stackref(i + offset))

        i = nb_args
        while i < w_cont.w_proto.nb_locals:
            self.stackclear(i)
            i += 1

        # Switch to this continuation (adjust/clear stack, push upvals,
        # set w_proto, etc...)
        self.apply_continuation(w_cont)

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

    def UNSPEC(self, _):
        self.push(w_unspec)

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
        x = self.peek().to_bool()
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

    def CAR(self, _):
        w_pair = self.peek()
        self.settop(w_pair.car_w())

    def CDR(self, _):
        w_pair = self.peek()
        self.settop(w_pair.cdr_w())

    def CONS(self, _):
        w_cdr = self.pop()
        w_car = self.peek()
        self.settop(W_Pair(w_car, w_cdr))

    def SETCAR(self, _):
        w_car = self.pop()
        w_pair = self.pop()
        w_pair.set_car(w_car)

    def SETCDR(self, _):
        w_cdr = self.pop()
        w_pair = self.pop()
        w_pair.set_cdr(w_cdr)

    def REIFYCC(self, _):
        w_cont = self.peek()
        self.settop(reify_callcc(w_cont))

    def READ(self, _):
        from rasm.rt.prelude import read_stdin
        self.push(read_stdin()[0]) # with values?

def patching_ophandlers():
    def noimpl(self, _):
        raise NotImplementedError
    for name in codemap:
        meth = getattr(Frame, name, None)
        if meth is None:
            print 'Stub implementation for %s' % name
            setattr(Frame, name, noimpl)

patching_ophandlers()

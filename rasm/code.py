from pypy.rlib.jit import hint, we_are_jitted, unroll_safe
from rasm.frame import Frame, W_ExecutionError
from rasm.model import (W_Root, W_Error, W_Int, W_Array, w_nil,
        w_true, w_false, W_TypeError, W_ValueError)
from rasm.jit import driver
from rasm import config

codenames = '''
LOAD STORE
POP DUP ROT
INT SYMBOL NIL TRUE FALSE
ARRAY AREF ASET ALEN
IADD ISUB IMUL IDIV
FLOAD FCALL FRET FTAILCALL
GOTO BRANCHIFNOT
TRY THROW CATCH
IS EQ LT NOT OR AND
PRINT NEWLINE
'''.split()

codemap = dict((name, i) for (i, name) in enumerate(codenames))

class CodeEnum(object):
    vars().update(codemap)

shortarg_op = '''
INT SYMBOL
ARRAY
FLOAD
GOTO BRANCHIFNOT
TRY THROW CATCH
'''.split()

bytearg_op = '''
LOAD STORE
FCALL FTAILCALL
'''.split()

# For debug's purpose.
def argwidth(opcode):
    name = codenames[opcode]
    if name in shortarg_op:
        return 2
    elif name in bytearg_op:
        return 1
    else:
        return 0

class W_ArgError(W_Error):
    def __init__(self, expected, got, w_func):
        self.expected = expected
        self.got = got
        self.w_func = w_func

    def to_string(self):
        return '<ArgError: expecting %d arguments, but got %d at %s>' % (
                self.expected, self.got, self.w_func.name)

class W_ReturnFromTopLevel(W_Error):
    def __init__(self, w_val):
        self.w_val = w_val

    def to_string(self):
        return '<ReturnFromTopLevel: %s>' % self.w_val.to_string()


class W_Function(W_Root):
    _immutables_ = ['name', 'code', 'framesize', 'nb_args',
                    'nb_locals', 'const_w']
    def __init__(self, name=None, code=None, framesize=0, nb_args=0,
                 nb_locals=0, const_w=0):
        self.name = name
        self.code = code
        self.framesize = framesize
        self.nb_args = nb_args
        self.nb_locals = nb_locals
        self.const_w = const_w
                

class __extend__(Frame):
    """ Extended Frame object that can interpret bytecode.
    """
    _virtualizable2_ = [
        'pc',
        'stacktop',
        'f_prev',
        'code',
        'ctx',
        'const_w',
        'local_w',
    ]
    _immutable_fields_ = ['const_w', 'code[*]', 'ctx', 'local_w']

    const_w = None # Shared constant pool.
    code = None # Code object.
    ctx = None
    pc = 0 # Program counter.

    def __init__(self, size, code, nb_locals=0,
                 const_w=None, ctx=None):
        self = hint(self, access_directly=True,
                          fresh_virtualizable=True)
        self.stacktop = nb_locals
        self.local_w = [None] * (size + nb_locals)
        self.nb_locals= nb_locals

        self.const_w = const_w
        self.code = code
        self.ctx = ctx

    def nextbyte(self):
        b = self.code[self.pc]
        self.pc += 1
        return ord(b)

    def nextshort(self):
        b0 = self.nextbyte()
        b1 = self.nextbyte()
        return b0 | (b1 << 8)

    def LOAD(self):
        index = self.nextbyte()
        w_val = self.local_w[index]
        if w_val is None:
            raise W_ExecutionError('unbound local variable', 'load()').wrap()
        self.push(w_val)

    def STORE(self):
        index = self.nextbyte()
        self.local_w[index] = self.pop()

    def POP(self):
        self.pop()

    def DUP(self):
        self.push(self.peek())

    def ROT(self):
        w_x = self.pop()
        w_y = self.peek()
        self.settop(w_x)
        self.push(w_y)

    def INT(self):
        ival = self.nextshort()
        self.push(W_Int(ival))

    def SYMBOL(self):
        index = self.nextshort()
        w_symbol = self.const_w[index]
        self.push(w_symbol)

    def NIL(self):
        self.push(w_nil)

    def TRUE(self):
        self.push(w_true)

    def FALSE(self):
        self.push(w_false)

    def ARRAY(self):
        size = self.nextshort()
        self.push(W_Array(size))

    def AREF(self):
        w_index = self.pop()
        w_array = self.peek()
        w_val = w_array.aref(w_index.to_int())
        self.settop(w_val)

    def ASET(self):
        w_val = self.pop()
        w_index = self.pop()
        w_array = self.pop()
        w_array.aset(w_index.to_int(), w_val)

    def ALEN(self):
        w_array = self.peek()
        self.settop(w_array.alen())

    def IADD(self):
        w_y = self.pop()
        w_x = self.peek()
        self.settop(W_Int(w_x.to_int() + w_y.to_int()))

    def ISUB(self):
        w_y = self.pop()
        w_x = self.peek()
        self.settop(W_Int(w_x.to_int() - w_y.to_int()))

    def IMUL(self):
        w_y = self.pop()
        w_x = self.peek()
        self.settop(W_Int(w_x.to_int() * w_y.to_int()))

    def IDIV(self):
        w_y = self.pop()
        w_x = self.peek()
        y = w_y.to_int()
        if y == 0:
            raise W_ValueError('divide by zero', w_x, 'idiv()').wrap()
        self.settop(W_Int(w_x.to_int() * y))

    def FLOAD(self):
        index = self.nextshort()
        w_func = self.const_w[index]
        self.push(w_func)

    @unroll_safe
    def FCALL(self):
        w_func = self.pop()
        if not isinstance(w_func, W_Function):
            raise W_TypeError('Function', w_func, 'fcall()').wrap()

        nb_args = self.nextbyte()
        # Argument count checking. (We currently don't consider complex
        # calling conventions like varargs...)
        if nb_args != w_func.nb_args:
            raise W_ArgError(w_func.nb_args, nb_args, w_func).wrap()

        # Create a new frame and link its back to self.
        frame = Frame(size=w_func.framesize + nb_args,
                      code=w_func.code,
                      nb_locals=w_func.nb_locals,
                      const_w=w_func.const_w,
                      ctx=self.ctx)
        # Pop arguments from self frame to that frame.
        i = nb_args - 1
        local_w = frame.local_w
        while i >= 0:
            local_w[i] = self.pop()
            i -= 1
        self.ctx.enter(frame)
        return frame

    def FRET(self):
        w_val = self.pop()
        f_prev = self.ctx.leave(self)
        if f_prev is None:
            # Return from toplevel.
            raise W_ReturnFromTopLevel(w_val).wrap()

        f_prev.push(w_val)
        return f_prev

    def FTAILCALL(self):
        raise NotImplementedError

    def GOTO(self):
        offset = self.nextshort()
        self.pc += offset

    def BRANCHIFNOT(self):
        offset = self.nextshort()
        if not self.pop().to_bool():
            self.pc += offset
        #driver.can_enter_jit(pc=self.pc, code=self.code,
        #                     frame=self)

    def TRY(self):
        raise NotImplementedError

    def THROW(self):
        raise NotImplementedError

    def CATCH(self):
        raise NotImplementedError

    def IS(self):
        w_x = self.pop()
        w_y = self.peek()
        self.settop(w_x.is_w(w_y))

    def EQ(self):
        w_x = self.pop()
        w_y = self.peek()
        self.settop(w_x.eq_w(w_y))

    def LT(self):
        y = self.pop().to_int()
        x = self.peek().to_int()
        self.settop(w_true if x < y else w_false)

    def NOT(self):
        x = self.pop().to_bool()
        self.settop(w_false if x else w_true)

    def OR(self):
        y = self.pop().to_bool()
        x = self.peek().to_bool()
        self.settop(w_true if x or y else w_false)

    def AND(self):
        y = self.pop().to_bool()
        x = self.peek().to_bool()
        self.settop(w_true if x and y else w_false)

    def PRINT(self):
        w_x = self.pop()
        print w_x.to_string(),

    def NEWLINE(self):
        print


def patching_ophandlers():
    def noimpl(self):
        raise NotImplementedError
    for name in codemap:
        meth = getattr(Frame, name, None)
        if meth is None:
            print 'Stub implementation for %s' % name
            setattr(Frame, name, noimpl)
        else:
            if config.INLINE_OPCODE:
                meth.im_func._always_inline_ = True

patching_ophandlers()


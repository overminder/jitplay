from pypy.rlib.jit import hint, we_are_jitted
from rasm.frame import W_Frame, LAST_FRAME, W_ExecutionError
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
    name = None # function name
    code = None # list of bytecodes
    nargs = 0

    def buildlocals(self, stack, nargs):
        if nargs != self.nargs:
            raise W_ArgError(self.nargs, nargs, self).wrap()
        f_local = stack.popsome(nargs)
        return f_local

class __extend__(W_Frame):
    #_virtualizable2_ = [
    #    'pc',
    #    'prev',
    #    'constpool',
    #    'code',
    #    'f_local',
    #    'stack',
    #]
    _immutable_fields_ = ['constpool', 'code', 'f_local', 'prev', 'stack']
    constpool = None # Shared constant pool.
    code = None # Code object.
    f_local = None # Frame locals, consider flatten this
                    # into the stack as well?
    pc = 0 # Program counter.

    def __init__(self, stack, code, f_local=None, prev=LAST_FRAME,
                 constpool=None):
        self.stack = stack
        self.prev = prev
        self.code = code
        self.f_local = f_local
        self.constpool = constpool

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
        w_val = self.f_local[index]
        if w_val is None:
            raise W_ExecutionError('unbound local variable', 'load()').wrap()
        self.stack.push(w_val)

    def STORE(self):
        index = self.nextbyte()
        self.f_local[index] = self.stack.pop()

    def POP(self):
        self.stack.pop()

    def DUP(self):
        self.stack.push(self.stack.peek())

    def ROT(self):
        w_x = self.stack.pop()
        w_y = self.stack.peek()
        self.stack.settop(w_x)
        self.stack.push(w_y)

    def INT(self):
        ival = self.nextshort()
        self.stack.push(W_Int(ival))

    def SYMBOL(self):
        index = self.nextshort()
        w_symbol = self.constpool[index]
        self.stack.push(w_symbol)

    def NIL(self):
        self.stack.push(w_nil)

    def TRUE(self):
        self.stack.push(w_true)

    def FALSE(self):
        self.stack.push(w_false)

    def ARRAY(self):
        size = self.nextshort()
        self.stack.push(W_Array(size))

    def AREF(self):
        w_index = self.stack.pop()
        w_array = self.stack.peek()
        w_val = w_array.aref(w_index.to_int())
        self.stack.settop(w_val)

    def ASET(self):
        w_val = self.stack.pop()
        w_index = self.stack.pop()
        w_array = self.stack.pop()
        w_array.aset(w_index.to_int(), w_val)

    def ALEN(self):
        w_array = self.stack.peek()
        self.stack.settop(w_array.alen())

    def IADD(self):
        w_y = self.stack.pop()
        w_x = self.stack.peek()
        self.stack.settop(W_Int(w_x.to_int() + w_y.to_int()))

    def ISUB(self):
        w_y = self.stack.pop()
        w_x = self.stack.peek()
        self.stack.settop(W_Int(w_x.to_int() - w_y.to_int()))

    def IMUL(self):
        w_y = self.stack.pop()
        w_x = self.stack.peek()
        self.stack.settop(W_Int(w_x.to_int() * w_y.to_int()))

    def IDIV(self):
        w_y = self.stack.pop()
        w_x = self.stack.peek()
        y = w_y.to_int()
        if y == 0:
            raise W_ValueError('divide by zero', w_x, 'idiv()').wrap()
        self.stack.settop(W_Int(w_x.to_int() * y))

    def FLOAD(self):
        index = self.nextshort()
        w_func = self.constpool[index]
        self.stack.push(w_func)

    def FCALL(self):
        s = self.stack
        w_func = s.pop()
        if not isinstance(w_func, W_Function):
            raise W_TypeError('Function', w_func, 'fcall()').wrap()

        nargs = self.nextbyte()
        # This will pop arguments from the frame.
        f_local = w_func.buildlocals(s, nargs)
        index = s.top
        s.push(self)
        return W_Frame(s, w_func.code, f_local, index, self.constpool)

    def FRET(self):
        s = self.stack
        p = self.prev

        w_val = s.peek()
        if p == LAST_FRAME:
            raise W_ReturnFromTopLevel(w_val).wrap()

        w_prevframe = s.ref(p)
        assert isinstance(w_prevframe, W_Frame)

        s.dropto(p + 1)
        s.settop(w_val)
        return w_prevframe

    def FTAILCALL(self):
        raise NotImplementedError

    def GOTO(self):
        offset = self.nextshort()
        self.pc += offset

    def BRANCHIFNOT(self):
        offset = self.nextshort()
        if not self.stack.pop().to_bool():
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
        w_x = self.stack.pop()
        w_y = self.stack.peek()
        self.stack.settop(w_x.is_w(w_y))

    def EQ(self):
        w_x = self.stack.pop()
        w_y = self.stack.peek()
        self.stack.settop(w_x.eq_w(w_y))

    def LT(self):
        y = self.stack.pop().to_int()
        x = self.stack.peek().to_int()
        self.stack.settop(w_true if x < y else w_false)

    def NOT(self):
        x = self.stack.pop().to_bool()
        self.stack.settop(w_false if x else w_true)

    def OR(self):
        y = self.stack.pop().to_bool()
        x = self.stack.peek().to_bool()
        self.stack.settop(w_true if x or y else w_false)

    def AND(self):
        y = self.stack.pop().to_bool()
        x = self.stack.peek().to_bool()
        self.stack.settop(w_true if x and y else w_false)

    def PRINT(self):
        w_x = self.stack.pop()
        print w_x.to_string(),

    def NEWLINE(self):
        print


def patching_ophandlers():
    def noimpl(self):
        raise NotImplementedError
    for name in codemap:
        meth = getattr(W_Frame, name, None)
        if meth is None:
            print 'Stub implementation for %s' % name
            setattr(W_Frame, name, noimpl)
        else:
            if config.INLINE_OPCODE:
                meth.im_func._always_inline_ = True

patching_ophandlers()


import __pypy_path__
from pypy.rlib.unroll import unrolling_iterable
from pypy.rlib.jit import JitDriver, hint
from frame import Frame
from model import W_Int, W_Bool

codenames = '''
LOAD STORE
POP DUP
HALT
FIXNUM
ADD SUB LSH LT
BIFZ B
PRINT
'''.split()

witharg = '''
LOAD STORE FIXNUM BIFZ B
'''.split()

class Enum(object):
    vars().update(dict((name, i) for (i, name) in enumerate(codenames)))

def op2name(op):
    return codenames[op]

def get_location(pc, code):
    assert pc >= 0
    op = ord(code[pc])
    name = op2name(op)
    if name in witharg:
        arg = '%d' % ord(code[pc + 1])
    else:
        arg = ''
    return '%d:%s(%s)' % (pc, name, arg)

driver = JitDriver(greens=['pc', 'code'],
                   reds=['frame'],
                   virtualizables=['frame'],
                   get_printable_location=get_location)


class __extend__(Frame):
    # XXX: seems code could not be virtualized.
    _virtualizable2_ = ['pc', 'code', 'stack[*]', 'top', 'f_local[*]']
    _immutable_fields_ = ['code[*]', 'f_local', 'stack']

    def dispatch(self):
        self = hint(self, access_directly=True)
        try:
            while True:
                #print get_location(self.pc, self.code)
                driver.jit_merge_point(pc=self.pc, code=self.code,
                                       frame=self)
                nextop = self.nextbyte()
                for op, dispatcher in unrolled_dispatchers:
                    if op == nextop:
                        dispatcher(self)
                        break
        except SystemExit:
            return

    def LOAD(self):
        idx = self.nextbyte()
        assert idx >= 0
        w_val = self.f_local[idx]
        self.push(w_val)

    def STORE(self):
        w_val = self.pop()
        idx = self.nextbyte()
        assert idx >= 0
        self.f_local[idx] = w_val

    def DUP(self):
        w_val = self.pop()
        self.push(w_val)
        self.push(w_val)

    def POP(self):
        self.pop()

    def HALT(self):
        raise SystemExit

    def FIXNUM(self):
        val = self.nextbyte()
        self.push(W_Int.wrap(val))
    
    def ADD(self):
        y = self.pop().to_int()
        x = self.pop().to_int()
        self.push(W_Int.wrap(x + y))

    def SUB(self):
        y = self.pop().to_int()
        x = self.pop().to_int()
        self.push(W_Int.wrap(x - y))

    def LSH(self):
        y = self.pop().to_int()
        x = self.pop().to_int()
        self.push(W_Int.wrap(x << y))

    def LT(self):
        y = self.pop().to_int()
        x = self.pop().to_int()
        self.push(W_Bool.wrap(x < y))

    def B(self):
        offset = self.nextbyte()
        self.pc += offset
        driver.can_enter_jit(pc=self.pc, code=self.code,
                             frame=self)

    def BIFZ(self):
        offset = self.nextbyte()
        w_val = self.pop()
        if not w_val.to_bool():
            self.pc += offset
            driver.can_enter_jit(pc=self.pc, code=self.code,
                                 frame=self)

    def PRINT(self):
        w_val = self.pop()
        print w_val.to_string()

unrolled_dispatchers = unrolling_iterable([(i, getattr(Frame, name))
                                           for (i, name)
                                           in enumerate(codenames)])

#for _, meth in unrolled_dispatchers:
#    meth.im_func._always_inline_ = True


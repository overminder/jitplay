from pypy.tool.pairtype import extendabletype
from pypy.rlib.jit import hint
from pypy.rlib.debug import check_nonneg
from pypy.rlib.rarithmetic import r_uint

class Frame(object):
    __metaclass__ = extendabletype
    top = 0
    pc = 0

    def __init__(self, size, code, f_local):
        self = hint(self, access_directly=True,
                          fresh_virtualizable=True)
        self.stack = [None] * size
        self.code = code
        self.f_local = f_local

    def nextbyte(self):
        co = self.code
        pc = self.pc 
        assert pc >= 0
        b = co[pc]
        self.pc = pc + 1
        val = ord(b)
        if val > 127:
            val -= 256
        return val

    def push(self, val):
        self.stack[self.top] = val
        self.top += 1

    def pop(self):
        s = self.stack
        t = self.top - 1
        assert t >= 0
        self.top = t # XXX: fixed
        return s[t]


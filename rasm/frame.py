from pypy.tool.pairtype import extendabletype
from pypy.rlib.jit import hint, unroll_safe, vref_None
from rasm.error import OperationError
from rasm.model import W_Root, W_Error
from rasm import config

class W_ExecutionError(W_Error):
    def __init__(self, msg, where):
        self.msg = msg
        self.where = where

    def to_string(self):
        return '<ExecutionError: %s at %s>' % (self.msg, self.where)

""" Frame layout:
    {frame=(frame_0)
     stack=[arg0, arg1, arg2, f]
     insn=`call_3`} =>
    {frame=(frame_1, prev=0, code=f.code, locals=f.buildlocals())
     stack=[frame_0]
     insn=...}
"""

class Frame(object):
    """ Base frame object that knows how to interact with the stack.
    """
    __metaclass__ = extendabletype

    stacktop = 0 # Top of local_w stack.
    local_w = None # Local variables, stack + local variables.
    nb_locals = 0 # Number of local variables
    f_prev = vref_None # The previous frame that this frame will return to.

    def pop(self):
        t = self.stacktop - 1
        assert t >= self.nb_locals, 'accessing empty stack at stack.pop()'
        self.stacktop = t
        w_pop = self.local_w[t]
        self.local_w[t] = None
        if w_pop is None:
            raise W_ExecutionError('null pointer', 'stack.pop()').wrap()
        return w_pop

    @unroll_safe
    def popsome(self, n):
        n = hint(n, promote=True)
        return [self.pop() for _ in xrange(n)]

    def peek(self):
        t = self.stacktop - 1
        assert t >= self.nb_locals, 'accessing empty stack at stack.peek()'
        w_val = self.local_w[t]
        if w_val is None:
            raise W_ExecutionError('null pointer', 'stack.peek()').wrap()
        return w_val

    def settop(self, w_top):
        t = self.stacktop - 1
        assert t >= self.nb_locals, 'accessing empty stack at stack.settop(?)'
        self.local_w[t] = w_top

    @unroll_safe
    def dropsome(self, n):
        n = hint(n, promote=True)
        t = self.stacktop
        while n > 0:
            n -= 1
            t -= 1
            assert t >= self.nb_locals, ('accessing empty stack',
                                         'stack.dropsome(?)')
            self.local_w[t] = None
        self.stacktop = t

    def dropto(self, level):
        level = hint(level, promote=True)
        self.dropsome(self.stacktop - level)

    def push(self, w_push):
        t = self.stacktop
        assert t >= self.nb_locals
        assert t < len(self.local_w), 'stack overflow at stack.push(?)'
        self.local_w[t] = w_push
        self.stacktop = t + 1

    def pushsome(self, items_w):
        t = self.stacktop
        n = len(items_w)
        assert t + n <= len(self.local_w), 'stack overflow at stack.pushsome(?)'
        i = 0
        while i < n:
            # Workaround for virtualizable.
            self.local_w[t + i] = items_w[i]
            i += 1
        self.stacktop = t + n


if config.INLINE_STACKOP:
    for name in '''pop popsome peek settop dropsome dropto push
            pushsome'''.split():
        getattr(Frame, name).im_func._always_inline_ = True



from pypy.tool.pairtype import extendabletype
from rasm.error import OperationError
from rasm.model import W_Root, W_Error

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

LAST_FRAME = -1

class W_Frame(W_Root):
    """ Base frame object that knows how to interact with the stack.
    """
    __metaclass__ = extendabletype

    stack = None # Shared by all frames.
    prev = LAST_FRAME # The previous frame slot in the stack, and
                      # will be replaced by the return value of this
                      # procedure call.


class Stack(object):
    def __init__(self, size):
        self.top = 0
        self.item_w = [None] * size

    def ref(self, index):
        assert index >= 0
        try:
            w_val = self.item_w[index]
        except IndexError:
            raise W_ExecutionError('stack index out of bound',
                                   'stack.ref(%d)' % index).wrap()
        if w_val is None:
            raise W_ExecutionError('null pointer',
                                   'stack.ref(%d)' % index).wrap()
        return w_val

    def pop(self):
        t = self.top - 1
        assert t >= 0
        self.top = t
        try:
            w_pop = self.item_w[t]
            self.item_w[t] = None
        except IndexError:
            raise W_ExecutionError('accessing empty stack',
                                   'stack.pop()').wrap()
        if w_pop is None:
            raise W_ExecutionError('null pointer', 'stack.pop()').wrap()
        return w_pop

    def popsome(self, n):
        return [self.pop() for _ in xrange(n)]

    def peek(self):
        t = self.top - 1
        try:
            assert t >= 0
            w_val = self.item_w[t]
        except IndexError:
            raise W_ExecutionError('accessing empty stack',
                                   'stack.peek()').wrap()
        if w_val is None:
            raise W_ExecutionError('null pointer', 'stack.peek()').wrap()
        return w_val

    def settop(self, w_top):
        t = self.top - 1
        try:
            assert t >= 0
            self.item_w[t] = w_top
        except IndexError:
            raise W_ExecutionError('accessing empty stack',
                                   'stack.settop(%s)' %
                                   w_top.to_string()).wrap()

    def dropsome(self, n):
        t = self.top
        while n > 0:
            n -= 1
            t -= 1
            try:
                assert t >= 0
                self.item_w[t] = None
            except IndexError:
                raise W_ExecutionError('accessing empty stack',
                                       'stack.dropsome(%d)' % n).wrap()
        self.top = t

    def dropto(self, level):
        self.dropsome(self.top - level)

    def push(self, w_push):
        try:
            assert self.top >= 0
            self.item_w[self.top] = w_push
        except IndexError:
            raise W_ExecutionError('stack overflow',
                                   'stack.push(%s)' %
                                   w_push.to_string()).wrap()
        self.top += 1

    def pushsome(self, items_w):
        t = self.top
        n = len(items_w)
        if t + n <= len(self.item_w):
            self.item_w[t:t + n] = items_w
            self.top = t + n
        else:
            raise W_ExecutionError('stack overflow',
                                   'stack.pushsome(%d items)' % n).wrap()


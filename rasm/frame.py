from pypy.tool.pairtype import extendabletype
from pypy.rlib.jit import hint, unroll_safe, dont_look_inside
from rasm.error import OperationError
from rasm.model import W_Root, W_Error

class W_ExecutionError(W_Error):
    def __init__(self, msg, where):
        self.msg = msg
        self.where = where

    def to_string(self):
        return '<ExecutionError: %s at %s>' % (self.msg, self.where)

class Frame(object):
    """ Base frame object that knows how to interact with the stack.
        Since we are interpreting an CPS bytecode, there is only one
        frame.
    """
    __metaclass__ = extendabletype

    def pop(self):
        t = self.stacktop - 1
        assert t >= 0
        self.stacktop = t
        w_pop = self.stack_w[t]
        self.stack_w[t] = None
        assert w_pop is not None
        return w_pop

    def push(self, w_push):
        assert w_push is not None
        t = self.stacktop
        assert t >= 0
        self.stack_w[t] = w_push
        self.stacktop = t + 1

    def settop(self, w_top):
        t = self.stacktop - 1
        assert w_top is not None
        assert t >= 0
        self.stack_w[t] = w_top

    def peek(self):
        t = self.stacktop - 1
        assert t >= 0
        w_top = self.stack_w[t]
        return w_top

    def stackref(self, index):
        assert index >= 0
        w_ref = self.stack_w[index]
        return w_ref

    def stackset(self, index, w_val):
        assert w_val is not None
        assert index >= 0
        self.stack_w[index] = w_val

    def stackclear(self, index):
        assert index >= 0
        self.stack_w[index] = None


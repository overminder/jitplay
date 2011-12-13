from pypy.rlib.unroll import unrolling_iterable
from pypy.rlib.jit import hint, vref_None, virtual_ref, virtual_ref_finish
from rasm.error import OperationError
from rasm.code import Frame, codemap, W_ReturnFromTopLevel
from rasm.jit import driver
from rasm import config

unrolled_handlers = unrolling_iterable([(i, getattr(Frame, name))
    for (name, i) in codemap.iteritems()])

class __extend__(Frame):
    def run(self):
        self.ctx.enter(self)
        return self.enter_dispatchloop()

    def dispatch(self):
        opcode = self.nextbyte()
        for op, meth in unrolled_handlers:
            if op == opcode:
                return meth(self)
    if config.INLINE_DISPATCH:
        dispatch._always_inline_ = True

    def enter_dispatchloop(self):
        self = hint(self, access_directly=True)
        try:
            while True:
                driver.jit_merge_point(pc=self.pc, code=self.code,
                                       frame=self)
                w_retval = self.dispatch()
                if w_retval is not None:
                    # XXX: Is it the reason for crashing?
                    self = hint(w_retval, access_directly=True)
        except OperationError as e:
            # XXX: Finish vref on exception.
            if e.match(W_ReturnFromTopLevel):
                return e.unwrap().w_val
            else:
                print e.unwrap().to_string()
                return

class Context(object):
    def __init__(self):
        self.frameref = vref_None

    def enter(self, frame):
        frame.f_prev = self.frameref
        self.frameref = virtual_ref(frame)

    def leave(self, frame):
        """ Returns the previous frame.
        """
        frame_vref = self.frameref
        self.frameref = frame.f_prev
        virtual_ref_finish(frame_vref, frame)
        return self.frameref()


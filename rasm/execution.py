from pypy.rlib.unroll import unrolling_iterable
from rasm.error import OperationError
from rasm.code import W_Frame, codemap, W_ReturnFromTopLevel
from rasm.jit import driver
from rasm import config

unrolled_handlers = unrolling_iterable([(i, getattr(W_Frame, name))
    for (name, i) in codemap.iteritems()])

class __extend__(W_Frame):
    def dispatch(self):
        opcode = self.nextbyte()
        for op, meth in unrolled_handlers:
            if op == opcode:
                return meth(self)
    if config.INLINE_DISPATCH:
        dispatch._always_inline_ = True

    def enter_dispatchloop(self):
        try:
            while True:
                driver.jit_merge_point(pc=self.pc, code=self.code,
                                       frame=self)
                w_retval = self.dispatch()
                if w_retval is not None:
                    self = w_retval
        except OperationError as e:
            if e.match(W_ReturnFromTopLevel):
                return e.unwrap().w_val
            else:
                print e.unwrap().to_string()
                return


from pypy.rlib.unroll import unrolling_iterable
from pypy.rlib.jit import (hint, vref_None, virtual_ref, virtual_ref_finish,
        unroll_safe)
from rasm.error import OperationError
from rasm.code import Frame, codemap, ReturnFromTopLevel
from rasm.jit import driver
from rasm import config

unrolled_handlers = unrolling_iterable([(i, getattr(Frame, name))
                                        for (name, i) in codemap.iteritems()])

class __extend__(Frame):
    def dispatch(self):
        opcode = self.nextbyte()
        for op, meth in unrolled_handlers:
            if op == opcode:
                return meth(self)
    if config.INLINE_DISPATCH:
        dispatch._always_inline_ = True

    def enter_dispatchloop(self):
        # This could be recursive -- 5x faster than non-jitted code.
        self = hint(self, access_directly=True)
        try:
            while True:
                driver.jit_merge_point(pc=self.pc, code=self.code,
                                       frame=self)
                maybe_frame = self.dispatch()
                if maybe_frame:
                    self = maybe_frame
                    self = hint(self, access_directly=True)
        except ReturnFromTopLevel as ret:
            return ret.w_val
        except OperationError as err:
            print err.unwrap().to_string()
    run = enter_dispatchloop


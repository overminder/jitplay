from pypy.rlib.unroll import unrolling_iterable
from pypy.rlib.jit import (hint, vref_None, virtual_ref, virtual_ref_finish,
        unroll_safe)
from rasm.error import OperationError
from rasm.code import Frame, codemap, LeaveFrame
from rasm.jit import driver
from rasm import config

unrolled_handlers = unrolling_iterable([(i, getattr(Frame, name))
                                        for (name, i) in codemap.iteritems()])

class __extend__(Frame):
    @unroll_safe
    def dispatch(self):
        opcode = self.nextbyte()
        for op, meth in unrolled_handlers:
            if op == opcode:
                meth(self)
                return
    if config.INLINE_DISPATCH:
        dispatch._always_inline_ = True

    @unroll_safe
    def enter_dispatchloop(self):
        self = hint(self, access_directly=True)
        try:
            while True:
                driver.jit_merge_point(pc=self.pc, code=self.code,
                                       frame=self)
                self.dispatch()
        except LeaveFrame:
            return self.pop()
        except OperationError as e:
            print e.unwrap().to_string()
    run = enter_dispatchloop


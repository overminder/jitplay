from pypy.rlib.unroll import unrolling_iterable
from pypy.rlib.jit import hint, unroll_safe
from rasm.error import OperationError
from rasm.code import Frame, codemap, argwidth, HaltContinuation
from rasm.jit import driver

unrolled_handlers = unrolling_iterable([(i, getattr(Frame, name))
                                        for (name, i) in codemap.iteritems()])

class __extend__(Frame):
    @unroll_safe
    def dispatch(self):
        opcode = self.nextbyte()
        if argwidth(opcode) == 2:
            oparg = self.nextshort()
        elif argwidth(opcode) == 1:
            oparg = self.nextbyte()
        else:
            oparg = 0
        for someop, somemethod in unrolled_handlers:
            if someop == opcode:
                somemethod(self, oparg)

    @unroll_safe
    def execution_loop(self):
        # Simple recursive interpreter is 5x faster than non-jitted code,
        # What if we apply CPS?
        self = hint(self, promote=True,
                    access_directly=True)
        try:
            while True:
                driver.jit_merge_point(pc=self.pc, code=self.code,
                                       frame=self)
                self.dispatch()
        except HaltContinuation as ret:
            return
        except OperationError as err:
            print err.unwrap().to_string()


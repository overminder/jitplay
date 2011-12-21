from pypy.rlib.unroll import unrolling_iterable
from pypy.rlib.jit import hint, unroll_safe
from rasm.error import OperationError
from rasm.rt.code import codemap, argwidth
from rasm.rt.opimpl import Frame, HaltContinuation
from rasm.rt.jit import driver, get_location

unrolled_handlers = unrolling_iterable([(i, getattr(Frame, name))
                                        for (name, i) in codemap.iteritems()])

class __extend__(Frame):
    @unroll_safe
    def dispatch(self, code):
        opcode = self.nextbyte(code)
        if argwidth(opcode) == 2:
            oparg = self.nextshort(code)
        elif argwidth(opcode) == 1:
            oparg = self.nextbyte(code)
        else:
            oparg = 0
        for someop, somemethod in unrolled_handlers:
            if someop == opcode:
                somemethod(self, oparg)
                break

    @unroll_safe
    def run(self):
        # Simple recursive interpreter is 5x faster than non-jitted code,
        # What if we apply CPS? -> fibo: 3x, not too bad but still have
        # spaces to grow.
        # Now that since locals, upvals and temporaries are on one
        # virtualizable stack, we got 5x speed up back.
        self = hint(self, promote=True,
                    access_directly=True)
        try:
            while True:
                driver.jit_merge_point(pc=self.pc, w_proto=self.w_proto,
                                       frame=self)
                #print get_location(self.pc, self.w_proto)
                #print self.stack_w
                self.dispatch(self.w_proto.code)
        except HaltContinuation as ret:
            return ret.w_retval
        except OperationError as err:
            print err.unwrap().to_string()


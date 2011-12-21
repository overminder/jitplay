from pypy.rlib.jit import JitDriver
from rasm.compiler.codeviewer import dis_at_position

def get_location(pc, w_proto):
    return dis_at_position(pc, w_proto.code)

driver = JitDriver(greens=['pc', 'w_proto'],
                   reds=['frame'],
                   virtualizables=['frame'],
                   get_printable_location=get_location)


from pypy.rlib.jit import JitDriver

def get_location(pc, w_proto):
    from rasm.code import codenames, argwidth
    code = w_proto.code
    opcode = ord(code[pc])
    width = argwidth(opcode)
    if width == 0:
        arg = ''
    elif width == 1:
        arg = str(ord(code[pc + 1]))
    else:
        assert width == 2
        arg = str(ord(code[pc + 1]) | (ord(code[pc + 2]) << 8))
    return '%s:%s(%s)' % (pc, codenames[opcode], arg)

driver = JitDriver(greens=['pc', 'w_proto'],
                   reds=['frame'],
                   virtualizables=['frame'],
                   get_printable_location=get_location)


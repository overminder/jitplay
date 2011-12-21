from rasm.rt.code import codenames, argwidth

def dis_once(pc, code):
    opcode = ord(code[pc])
    width = argwidth(opcode)
    if width == 0:
        arg = ''
    elif width == 1:
        arg = str(ord(code[pc + 1]))
    else:
        assert width == 2
        arg = str(ord(code[pc + 1]) | (ord(code[pc + 2]) << 8))
    return width, '%s:%s(%s)' % (pc, codenames[opcode], arg)

def dis_at_position(pc, code):
    _, codedescr = dis_once(pc, code)
    return codedescr

def dis_proto(w_proto):
    code = w_proto.code
    pc = 0
    descrlist = []
    while pc < len(code):
        width, codedescr = dis_once(pc, code)
        pc += 1 + width
        descrlist.append(codedescr)
    return '\n'.join(descrlist)


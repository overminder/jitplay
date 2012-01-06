from pypy.rlib.debug import check_nonneg
from rasm.util import load_descr_file
from rasm.lang.model import W_Root

def load_code_descr():
    namelist = load_descr_file(__file__, 'code.txt')
    last_i16 = namelist.index('_last_i16_')
    del namelist[last_i16]
    last_i16 -= 1
    last_u8 = namelist.index('_last_u8_')
    del namelist[last_u8]
    last_u8 -= 1
    namemap = dict((name, i) for (i, name) in enumerate(namelist))
    return namelist, namemap, last_i16, last_u8

codenames, codemap, last_i16, last_u8 = load_code_descr()

class Op(object):
    vars().update(codemap)

# For debug's purpose and for dispatching.
def argwidth(opcode):
    if opcode > last_u8:
        return 0
    elif opcode > last_i16:
        return 1
    else:
        return 2

class W_Proto(W_Root):
    _immutable_ = True
    _immutable_fields_ = ['const_w[*]']
    name = '#f'

    def __init__(self, code, nb_args, nb_locals, upval_descr,
                 const_w, w_module=None):
        self.code = code
        check_nonneg(nb_args)
        self.nb_args = nb_args
        check_nonneg(nb_locals)
        self.nb_locals = nb_locals
        self.upval_descr = upval_descr
        self.const_w = const_w
        self.w_module = w_module

    def nb_upvals(self):
        if self.upval_descr:
            return len(self.upval_descr)
        return 0

    def to_string(self):
        return '#<proto %s>' % self.name


class W_Cont(W_Root):
    _immutable_ = True
    _immutable_fields_ = ['upval_w[*]']

    def __init__(self, w_proto, upval_w):
        self.w_proto = w_proto
        self.upval_w = upval_w

    def to_string(self):
        return '#<continuation %s>' % self.w_proto.name



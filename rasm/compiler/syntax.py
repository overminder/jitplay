""" syntax.py

    Doing macro transformation.
"""
from rasm.lang.model import (W_Root, W_Int, W_Boolean, W_Unspecified,
                             W_Pair, W_Nil, W_Symbol,
                             symbol, list_to_pair, gensym,
                             w_nil, w_true, w_false, w_unspec,
                             W_ValueError, W_TypeError)

class Transformer(object):
    def __init__(self):
        pass

    def expand(self, w_obj):
        return w_obj.expand_syntax(self)


class __extend__(W_Root):
    def expand_syntax(self, transformer):
        raise NotImplementedError

class __extend__(W_Int, W_Boolean, W_Nil, W_Symbol, W_Unspecified):
    def expand_syntax(self, transformer):
        return self

class __extend__(W_Pair):
    def expand_syntax(self, transformer):
        w_hd = self.w_car
        w_tl = self.w_cdr

        if isinstance(w_hd, W_Symbol):
            tag = w_hd.sval
            if tag == 'let':
                pass
            elif tag == 'letrec':
                pass
        
        return W_Pair(transformer.expand(w_hd),
                      transformer.expand(w_tl))



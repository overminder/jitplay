""" The whole file is copied from PyPy's celldict implementation.
    I must say this is very efficient... Global dictionary lookup basically
    becomes a nop, worship big god!
"""
from pypy.rlib.jit import hint, elidable
from rasm.lang.model import W_Root

class VersionTag(object):
    pass

class ModuleCell(W_Root):
    def __init__(self, w_value):
        self.w_value = w_value

    def to_string(self):
        return '<ModuleCell %s>' % self.w_value.to_string()

def unwrap_cell(maybecell):
    if isinstance(maybecell, ModuleCell):
        return maybecell.w_value
    return maybecell

class ModuleDict(W_Root):
    _immutable_fields_ = ['bindings_w', 'version?']

    def __init__(self):
        self.bindings_w = {}
        self.version = VersionTag()

    def mutated(self):
        self.version = VersionTag()

    def setitem(self, w_key, w_value):
        maybecell = self.getitem(w_key)
        if isinstance(maybecell, ModuleCell):
            maybecell.w_value = w_value
            return
        if w_value is maybecell:
            # They are the same.
            return
        if maybecell is not None:
            # Mutating an existing var: create a level of indirection.
            w_value = ModuleCell(w_value)
        self.mutated()
        self.bindings_w[w_key] = w_value

    def getitem(self, w_key):
        maybecell = self.rawgetitem(w_key)
        return unwrap_cell(maybecell)

    def rawgetitem(self, w_key):
        self = hint(self, promote=True)
        return self.pure_rawgetitem(w_key, self.version)

    @elidable
    def pure_rawgetitem(self, w_key, _):
        return self.bindings_w.get(w_key, None)


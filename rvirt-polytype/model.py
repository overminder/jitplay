from pypy.rlib.objectmodel import UnboxedValue

class W_Root(object):
    __slots__ = []
    def to_int(self):
        raise NotImplementedError

    def to_bool(self):
        return True

    def to_string(self):
        return '<object>'

# As an tagged pointer.
class W_Int(W_Root, UnboxedValue):
    _immutable_fields_ = ['ival']
    __slots__ = ['ival']

    def to_int(self):
        return self.ival

    def to_string(self):
        return '%d' % self.ival

    @staticmethod
    def wrap(i):
        return W_Int(i)


class W_Bool(W_Root):
    @staticmethod
    def wrap(bval):
        if bval:
            return w_true
        else:
            return w_false

class W_True(W_Bool):
    def to_string(self):
        return '#t'

class W_False(W_Bool):
    def to_string(self):
        return '#f'

    def to_bool(self):
        return False

w_true = W_True()
w_false = W_False()


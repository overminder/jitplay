from rasm.error import OperationError

class W_Root(object):
    def to_string(self):
        return '<root>'

    def to_int(self):
        raise W_TypeError('Int', self, 'to_int()').wrap()

    def to_bool(self):
        return True

    def is_w(self, w_x):
        if self is w_x:
            return w_true
        return w_false

    def eq_w(self, w_x):
        return self.is_w(w_x)

    def aref(self, index):
        raise W_TypeError('Array', self, 'aref(%d)' % index).wrap()

    def aset(self, index, w_val):
        raise W_TypeError('Array', self, 'aset(%d, %s)' %
                (index, w_val.to_string())).wrap()

    def alen(self):
        raise W_TypeError('Array', self, 'alen()').wrap()

class W_Int(W_Root):
    _immutable_fields_ = ['ival']

    def __init__(self, ival):
        self.ival = ival

    def to_string(self):
        return '%d' % self.ival

    def to_int(self):
        return self.ival

    def eq_w(self, w_x):
        if isinstance(w_x, W_Int):
            if self.ival == w_x.ival:
                return w_true
        return w_false

class W_Symbol(W_Root):
    interned_w = {}
    def __init__(self, sval):
        self.sval = sval

    def to_string(self):
        return ':' + self.sval

def symbol(sval):
    w_sym = W_Symbol.interned_w.get(sval, None)
    if w_sym is None:
        w_sym = W_Symbol(sval)
        W_Symbol.interned_w[sval] = w_sym
    return w_sym

class W_Nil(W_Root):
    def to_string(self):
        return '#nil'

w_nil = W_Nil()

class W_Boolean(W_Root):
    pass

class W_True(W_Boolean):
    def to_string(self):
        return '#t'

w_true = W_True()

class W_False(W_Boolean):
    def to_string(self):
        return '#f'

    def to_bool(self):
        return False

w_false = W_False()

class W_Array(W_Root):
    def __init__(self, size, w_fill=w_nil):
        self.item_w = [w_fill] * size

    def eq_w(self, w_x):
        if isinstance(w_x, W_Array):
            if self.item_w == w_x.item_w:
                return w_true
        return w_false

    def aref(self, index):
        assert index >= 0
        try:
            return self.item_w[index]
        except IndexError:
            raise W_IndexError(self, index, 'aref(%d)' % index).wrap()

    def aset(self, index, w_val):
        assert index >= 0
        try:
            self.item_w[index] = w_val
        except IndexError:
            raise W_IndexError(self, index, 'aset(%d, %s)' %
                    (index, w_val.to_string())).wrap()

    def alen(self):
        return W_Int(len(self.item_w))

    def to_string(self):
        return '[%s]' % ', '.join([w_o.to_string() for w_o in self.item_w])


class W_Error(W_Root):
    def to_string(self):
        return '<error>'

    def wrap(self):
        return OperationError(self)


class W_TypeError(W_Error):
    def __init__(self, expected, w_got, where):
        self.expected = expected
        self.w_got = w_got
        self.where = where

    def to_string(self):
        return '<TypeError: expecting %s, but got %s at %s>' % (
                self.expected, self.w_got.to_string(), self.where)


class W_IndexError(W_Error):
    def __init__(self, w_array, index, where):
        self.w_array = w_array
        self.index = index
        self.where = where

    def to_string(self):
        return '<IndexError: array index out of bound (%d) at %s>' % (
                self.index, self.where)

class W_ValueError(W_Error):
    def __init__(self, why, w_got, where):
        self.why = why
        self.w_got = w_got
        self.where = where

    def to_string(self):
        return '<ValueError: %s for %s at %s>' % (
                self.why, self.w_got.to_string(), self.where)


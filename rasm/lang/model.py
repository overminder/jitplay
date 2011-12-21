from pypy.rlib.objectmodel import UnboxedValue
from pypy.tool.pairtype import extendabletype
from rasm.error import OperationError

USING_SMALLINT = False

class W_Root(object):
    __slots__ = []
    __metaclass__ = extendabletype

    def to_string(self):
        return '#<object>'

    def to_int(self):
        raise W_TypeError('Int', self, 'to_int()').wrap()

    def to_bool(self):
        return True

    def to_list(self):
        items_w = []
        while isinstance(self, W_Pair):
            items_w.append(self.w_car)
            self = self.w_cdr
        return items_w, self

    def is_null(self):
        return self is w_nil

    # Pointer identity
    def is_w(self, w_x):
        if self is w_x:
            return w_true
        return w_false

    # Generic value equality.
    def equal_w(self, w_x):
        return self.is_w(w_x)

    def car_w(self):
        raise W_TypeError('Pair', self, 'car_w()').wrap()

    def cdr_w(self):
        raise W_TypeError('Pair', self, 'cdr_w()').wrap()

    def set_car(self, w_car):
        raise W_TypeError('Pair', self,
                          'set_car(%s)' % w_car.to_string()).wrap()

    def set_cdr(self, w_cdr):
        raise W_TypeError('Pair', self,
                          'set_cdr(%s)' % w_cdr.to_string()).wrap()


class W_Pair(W_Root):
    __slots__ = ['w_car', 'w_cdr']

    def __init__(self, w_car, w_cdr):
        self.w_car = w_car
        self.w_cdr = w_cdr

    def to_string(self):
        items_w, w_rest = self.to_list()
        head = '(' + ' '.join([w_x.to_string() for w_x in items_w])
        if w_rest.is_null():
            return head + ')'
        else:
            return head + ' . ' + w_rest.to_string() + ')'

    # Recursively compare equality
    def equal_w(self, w_x):
        if isinstance(w_x, W_Pair):
            return (self.w_car.equal_w(w_x.w_car) and
                    self.w_cdr.equal_w(w_x.w_cdr))
        return w_false

    def car_w(self):
        return self.w_car

    def cdr_w(self):
        return self.w_cdr

    def set_car(self, w_car):
        self.w_car = w_car

    def set_cdr(self, w_cdr):
        self.w_cdr = w_cdr


class W_SmallInt(W_Root, UnboxedValue):
    _immutable_fields_ = ['ival']
    __slots__ = ['ival']

    def to_string(self):
        return str(self.ival)

    def to_int(self):
        return self.ival

    def equal_w(self, w_x):
        if isinstance(w_x, W_Int):
            if self.ival == w_x.ival:
                return w_true
        return w_false

class W_Integer(W_Root):
    _immutable_fields_ = ['ival']
    __slots__ = ['ival']

    def __init__(self, ival):
        self.ival = ival

    def to_string(self):
        return '%d' % self.ival

    def to_int(self):
        return self.ival

    def equal_w(self, w_x):
        if isinstance(w_x, W_Int):
            if self.ival == w_x.ival:
                return w_true
        return w_false

if USING_SMALLINT:
    W_Int = W_SmallInt
else:
    W_Int = W_Integer

class W_Symbol(W_Root):
    interned_w = {}

    def __init__(self, sval):
        self.sval = sval

    def to_string(self):
        return self.sval

def symbol(sval):
    w_sym = W_Symbol.interned_w.get(sval, None)
    if w_sym is None:
        w_sym = W_Symbol(sval)
        W_Symbol.interned_w[sval] = w_sym
    return w_sym

class GensymCounter(object):
    i = 0
gensym_counter = GensymCounter()

def gensym(prefix='$Gensym_'):
    i = gensym_counter.i
    s = prefix + str(i)
    while s in W_Symbol.interned_w:                                             
        i += 1
        s = prefix + str(i)
    gensym_counter.i = i + 1
    return symbol(s)

class W_Nil(W_Root):
    def to_string(self):
        return '()'

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

class W_Unspecified(W_Root):
    def to_string(self):
        return '#<unspecified>'

w_unspec = W_Unspecified()

class W_Eof(W_Root):
    def to_string(self):
        return '#<eof>'

w_eof = W_Eof()

################################################################################
################################################################################

class W_Error(W_Root):
    def to_string(self):
        return '#<error>'

    def wrap(self):
        return OperationError(self)


class W_TypeError(W_Error):
    def __init__(self, expected, w_got, where):
        self.expected = expected
        self.w_got = w_got
        self.where = where

    def to_string(self):
        return '#<TypeError: expecting %s, but got %s at %s.>' % (
                self.expected, self.w_got.to_string(), self.where)


class W_IndexError(W_Error):
    def __init__(self, w_array, index, where):
        self.w_array = w_array
        self.index = index
        self.where = where

    def to_string(self):
        return '#<IndexError: array index out of bound (%d) at %s.>' % (
                self.index, self.where)


class W_ValueError(W_Error):
    def __init__(self, why, w_got, where):
        self.why = why
        self.w_got = w_got
        self.where = where

    def to_string(self):
        return '#<ValueError: %s for %s at %s.>' % (
                self.why, self.w_got.to_string(), self.where)

class W_NameError(W_Error):
    def __init__(self, w_name):
        self.w_name = w_name

    def to_string(self):
        return '#<NameError: name "%s" is not defined.>' % (
                self.w_name.to_string())


def list_to_pair(list_w, w_last=w_nil):
    for i in xrange(len(list_w) - 1, -1, -1):
        w_item = list_w[i]
        w_last = W_Pair(w_item, w_last)
    return w_last


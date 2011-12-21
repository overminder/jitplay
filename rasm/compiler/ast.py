""" The reason why we need an ast rather than directly operate on w_object
    is that we would like to be more readable and strict.
"""
from pypy.tool.pairtype import extendabletype
from rasm.lang.model import w_unspec

class Node(object):
    __metaclass__ = extendabletype

    def to_string(self):
        return '(Node)'

class If(Node):
    def __init__(self, fst, snd, trd=None):
        if trd is None:
            trd = Const(w_unspec)
        self.fst = fst
        self.snd = snd
        self.trd = trd

    def to_string(self):
        return '(If %s %s %s)' % (self.fst.to_string(), self.snd.to_string(),
                                                        self.trd.to_string())

class Seq(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def to_string(self):
        return '(Seq %s)' % show_list(self.nodelist, lparen='', rparen='')


class Apply(Node):
    def __init__(self, proc, args):
        self.proc = proc
        self.args = args

    def to_string(self):
        return '(Apply %s %s)' % (self.proc.to_string(),
                                  show_list(self.args, lparen='[', rparen=']'))

class PrimitiveOp(Node):
    def __init__(self, proc, args):
        self.proc = proc
        self.args = args

    def to_string(self):
        return '(PrimitiveOp %s %s)' % (self.proc.to_string(),
                                        show_list(self.args,
                                                  lparen='[', rparen=']'))

class Def(Node):
    def __init__(self, name, form):
        self.name = name
        self.form = form

    def to_string(self):
        return '(Def %s %s)' % (self.name.to_string(), self.form.to_string())

class Sete(Node):
    def __init__(self, name, form):
        self.name = name
        self.form = form

    def to_string(self):
        return '(Set! %s %s)' % (self.name.to_string(), self.form.to_string())

class Lambda(Node):
    def __init__(self, formals, body, name='#f'):
        self.name = name
        self.formals = formals
        self.body = body

    def to_string(self):
        return '(Lambda %s %s %s)' % (self.name, show_list(self.formals,
                                                           lparen='[',
                                                           rparen=']'),
                                                 show_list(self.body,
                                                           lparen='[',
                                                           rparen=']'))

class Var(Node):
    def __init__(self, w_form):
        self.w_form = w_form

    def to_string(self):
        return '(Var %s)' % self.w_form.to_string()

class Const(Node):
    def __init__(self, w_val):
        self.w_val = w_val

    def to_string(self):
        return self.w_val.to_string()


def show_list(nodelist, lparen='(', rparen=')'):
    return (lparen +
            ' '.join([node.to_string() for node in nodelist]) +
            rparen)


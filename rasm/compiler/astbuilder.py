from rasm.lang.model import (W_Root, W_Int, W_Boolean, W_Unspecified,
                             W_Pair, W_Nil, W_Symbol,
                             symbol, list_to_pair,
                             w_nil, w_true, w_false, w_unspec,
                             W_ValueError, W_TypeError)
from rasm.compiler.ast import (Node, If, Seq, Apply, Def, Sete, Lambda,
                               Var, Const)

class Builder(object):
    def __init__(self, exprs_w):
        self.exprs_w = exprs_w
        self.astlist = []

    def getast(self):
        for w_expr in self.exprs_w:
            self.astlist.append(w_expr.to_ast())
        self.exprs_w = None
        return self.astlist

class __extend__(W_Root):
    def to_ast(self):
        raise NotImplementedError

class __extend__(W_Int, W_Unspecified, W_Boolean):
    def to_ast(self):
        return Const(self)

class __extend__(W_Symbol):
    def to_ast(self):
        return Var(self)

class __extend__(W_Nil):
    def to_ast(self):
        raise W_ValueError('illegal empty application', self,
                           'to_ast()').wrap()

class __extend__(W_Pair):
    def to_ast(self):
        items_w, w_rest = self.to_list()
        if not w_rest.is_null():
            raise W_ValueError('not a proper-list', self, 'to_ast()').wrap()

        w_proc = items_w[0]
        w_args = items_w[1:]
        if isinstance(w_proc, W_Symbol):
            # special forms
            tagname = w_proc.sval
            if tagname == 'if':
                return build_if(self, w_args)
            elif tagname == 'define':
                return build_def(self, w_args)
            elif tagname == 'set!':
                return build_sete(self, w_args)
            elif tagname == 'quote':
                return build_quote(self, w_args)
            elif tagname == 'lambda':
                return build_lambda(self, w_args)
            elif tagname == 'begin':
                return build_seq(self, w_args)

        # normal application
        procnode = w_proc.to_ast()
        argnodes = [w_x.to_ast() for w_x in w_args]
        return Apply(procnode, argnodes)


################################################################################
# Implementations
################################################################################

def build_if(w_form, w_args):
    if not len(w_args) in (2, 3):
        raise W_ValueError('if requires 2 or 3 args',
                           w_form, 'build_if()').wrap()
    if len(w_args) == 2:
        w_fst, w_snd = w_args
        w_trd = w_unspec
    else:
        w_fst, w_snd, w_trd = w_args
    return If(w_fst.to_ast(), w_snd.to_ast(), w_trd.to_ast())

def build_def(w_form, w_args):
    if len(w_args) < 2:
        raise W_ValueError('define requires at least 2 args',
                           w_form, 'build_def()').wrap()
    w_first = w_args[0]
    if isinstance(w_first, W_Symbol): # is symbol, a normal define
        if len(w_args) != 2:
            raise W_ValueError('define variable requires 2 args',
                               w_form, 'build_def()').wrap()
        w_name = w_first
        form = w_args[1].to_ast()
    elif isinstance(w_first, W_Pair): # is pair, we are defining lambda
        name_formals_w, w_rest = w_first.to_list()
        w_name = name_formals_w[0]
        formals_w = list_to_pair(name_formals_w[1:], w_rest)
        w_lambda_form = [formals_w] + w_args[1:]
        form = build_lambda(w_form, w_lambda_form)
    else:
        raise W_TypeError('Pair or Symbol', w_first, 'build_def()').wrap()

    if not isinstance(w_name, W_Symbol):
        raise W_TypeError('Symbol', w_name, 'build_def()').wrap()
    if isinstance(form, Lambda):
        form.name = w_name.sval
    return Def(Var(w_name), form)

def build_sete(w_form, w_args):
    if len(w_args) != 2:
        raise W_ValueError('set! requires 2 args',
                           w_form, 'build_sete()').wrap()
    w_first = w_args[0]
    if not isinstance(w_first, W_Symbol):
        raise W_TypeError('Symbol', w_first, 'build_sete()').wrap()

    return Sete(Var(w_first), w_args[1].to_ast())

def build_quote(w_form, w_args):
    if len(w_args) != 1:
        raise W_ValueError('quote requires 1 argument',
                           w_form, 'build_quote()').wrap()
    return Const(w_args[0])

def build_lambda(w_form, w_args):
    w_formals = w_args[0]
    body_w = w_args[1:]
    posargs_w, w_rest = w_formals.to_list()
    if not w_rest.is_null():
        raise W_ValueError('variadic argument not supported (yet)',
                           w_form, 'build_lambda()').wrap()
    argnodes = [None] * len(posargs_w)
    for i in xrange(len(posargs_w)):
        w_arg = posargs_w[i] # XXX pypy hack
        if not isinstance(w_arg, W_Symbol):
            raise W_TypeError('Symbol', w_arg, 'build_lambda()').wrap()
        argnodes[i] = Var(w_arg)
    return Lambda(argnodes, [w_x.to_ast() for w_x in body_w])

def build_seq(w_form, w_args):
    return Seq([w_x.to_ast() for w_x in w_args])


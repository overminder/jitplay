from rasm.lang.model import (W_Root, W_Int, W_Boolean, W_Unspecified,
                             W_Pair, W_Nil, W_Symbol,
                             symbol, list_to_pair, gensym,
                             w_nil, w_true, w_false, w_unspec,
                             W_ValueError, W_TypeError)
from rasm.compiler.ast import (Node, If, Seq, Apply, Def, Sete, Lambda,
                               Var, Const, PrimitiveOp)
from rasm.lang.model import symbol
from rasm.lang.env import ModuleDict
from rasm.rt.code import Op, W_Proto, W_Cont

def compile_all(node, module_w):
    interp = AbstractInterpreter(args=None, node=node)
    interp.module_w = module_w
    toplevel = interp.interp()
    proto_w = [None] * len(interp.proto_w)
    for i in xrange(len(interp.proto_w)):
        proto_w[i] = interp.proto_w[i]
    return W_Cont(toplevel, None), proto_w

class AbstractInterpreter(object):
    def __init__(self, args, node, parent=None):
        self.parent = parent
        if parent:
            self.proto_w = parent.proto_w
            self.module_w = parent.module_w
        else:
            self.proto_w = []
            self.module_w = None
        self.args = args
        self.node = node
        self.localmap = {}
        self.nb_locals = 0
        self.upval_descr = []
        self.code = []
        self.const_w = []
        self.pending_lambdas = []
        # Set argument.
        if args:
            for argnode in args:
                w_name = argnode.w_form
                assert isinstance(w_name, W_Symbol)
                self.localmap[w_name] = self.nb_locals
                self.nb_locals += 1

    def emitbyte(self, u8):
        self.code.append(chr(u8))

    def emitshort(self, i16):
        self.emitbyte(i16 & 0xff)
        self.emitbyte((i16 >> 8) & 0xff)

    def dummyshort(self):
        res = len(self.code)
        self.emitbyte(0)
        self.emitbyte(0)
        return res, res + 2

    def codeptr(self):
        return len(self.code)

    def patchshort(self, index, i16):
        self.code[index] = chr(i16 & 0xff)
        self.code[index + 1] = chr((i16 >> 8) & 0xff)

    def intern_const(self, w_val):
        try:
            return self.const_w.index(w_val)
        except ValueError:
            self.const_w.append(w_val)
            return len(self.const_w) - 1

    def def_item(self, w_name, toplevel=False):
        if toplevel:
            const_index = self.intern_const(w_name)
            self.emitbyte(Op.SETGLOBAL)
            self.emitbyte(const_index)
            return
        if w_name not in self.localmap:
            self.localmap[w_name] = self.nb_locals
            self.nb_locals += 1
        local_index = self.localmap[w_name]
        self.emitbyte(Op.STORE)
        self.emitbyte(local_index)

    def set_item(self, w_name):
        # Is a local?
        if w_name in self.localmap:
            local_index = self.localmap[w_name]
            self.emitbyte(Op.STORE)
            self.emitbyte(local_index)
            return
        # Need to pull upval?
        if self.parent:
            upval_index = len(self.upval_descr)
            if self.parent.pull_upval(self, w_name):
                # Could pull the upval to here.
                self.emitbyte(Op.SETUPVAL)
                self.emitbyte(upval_index)
                return
        # No parent, or is global
        const_index = self.intern_const(w_name)
        self.emitbyte(Op.SETGLOBAL)
        self.emitbyte(const_index)

    def lookup_item(self, w_name):
        if w_name in self.localmap:
            local_index = self.localmap[w_name]
            self.emitbyte(Op.LOAD)
            self.emitbyte(local_index)
            return
        if self.parent:
            upval_index = len(self.upval_descr)
            if self.parent.pull_upval(self, w_name):
                self.emitbyte(Op.GETUPVAL)
                self.emitbyte(upval_index)
                return
        const_index = self.intern_const(w_name)
        self.emitbyte(Op.GETGLOBAL)
        self.emitbyte(const_index)

    def pull_upval(self, child, w_name):
        if w_name in self.localmap or (self.parent and
                self.parent.pull_upval(self, w_name)):
            from_index = self.localmap[w_name]
            to_index = len(child.upval_descr) + child.nb_locals # XXX
            child.upval_descr.append(from_index)
            child.localmap[w_name] = to_index
            return True
        return False # is global

    def visit(self, node):
        node.accept_interp(self)

    def interp(self, name=None):
        self.visit(self.node)
        for lambda_node, proto_index in self.pending_lambdas:
            new_interp = AbstractInterpreter(args=lambda_node.formals,
                                             node=lambda_node.body[0],
                                             parent=self)
            self.proto_w[proto_index] = new_interp.interp(name=lambda_node.name)
        self.pending_lambdas = None
        w_proto = build_proto(self)
        if w_proto.name == '#f' and name:
            w_proto.name = name
        return w_proto

def build_proto(interp):
    code = ''.join(interp.code)

    if interp.args:
        nb_args = len(interp.args)
    else:
        nb_args = 0

    upval_descr = ['\0'] * len(interp.upval_descr)
    for i, index in enumerate(interp.upval_descr):
        upval_descr[i] = chr(index)

    const_w = [None] * len(interp.const_w)
    for i in xrange(len(interp.const_w)): # XXX PyPy hack
        const_w[i] = interp.const_w[i]

    return W_Proto(code, nb_args, interp.nb_locals,
                   upval_descr, const_w, interp.module_w)


class __extend__(Node):
    def accept_interp(self, interp):
        raise NotImplementedError


class __extend__(If):
    def accept_interp(self, interp):
        interp.visit(self.fst)
        interp.emitbyte(Op.BRANCHIFNOT)
        patch_index, jump_from = interp.dummyshort()
        interp.visit(self.snd)
        interp.patchshort(patch_index, interp.codeptr() - jump_from)
        interp.visit(self.trd)

class __extend__(Seq):
    def accept_interp(self, interp):
        for node in self.nodelist:
            interp.visit(node)

class __extend__(Apply):
    def accept_interp(self, interp):
        for arg in self.args:
            interp.visit(arg)
        interp.visit(self.proc)
        interp.emitbyte(Op.CONT)

class __extend__(PrimitiveOp):
    def accept_interp(self, interp):
        for arg in self.args:
            interp.visit(arg)
        interp.emitbyte(primitivemap[self.proc.w_form.sval])

primitivemap = {
    '+': Op.IADD,
    '-': Op.ISUB,
    '*': Op.IMUL,
    '/': Op.IDIV,
    'cons': Op.CONS,
    'car': Op.CAR,
    'cdr': Op.CDR,
    '<': Op.LT,
    'eq?': Op.IS,
    'equal?': Op.EQUAL,
}

class __extend__(Def):
    def accept_interp(self, interp):
        w_name = self.name.w_form
        assert isinstance(w_name, W_Symbol)
        interp.visit(self.form)
        interp.def_item(w_name, self.toplevel)
        interp.emitbyte(Op.UNSPEC)

class __extend__(Sete):
    def accept_interp(self, interp):
        w_name = self.name.w_form
        assert isinstance(w_name, W_Symbol)
        interp.visit(self.form)
        interp.set_item(w_name)
        interp.emitbyte(Op.UNSPEC)

class __extend__(Var):
    def accept_interp(self, interp):
        w_form = self.w_form
        if not isinstance(self.w_form, W_Symbol):
            raise W_TypeError('Symbol', w_form, 'Var.accept_interp()').wrap()
        interp.lookup_item(self.w_form)

class __extend__(Const):
    def accept_interp(self, interp):
        w_val = self.w_val
        if w_val is w_nil:
            interp.emitbyte(Op.NIL)
            return
        elif w_val is w_true:
            interp.emitbyte(Op.TRUE)
            return
        elif w_val is w_false:
            interp.emitbyte(Op.FALSE)
            return
        elif w_val is w_unspec:
            interp.emitbyte(Op.UNSPEC)
            return
        elif isinstance(w_val, W_Int):
            ival = w_val.ival
            if 0 <= ival < (1 << 15):
                interp.emitbyte(Op.INT)
                interp.emitbyte(ival & 0xff)
                interp.emitbyte((ival >> 8) & 0xff)
                return
        const_index = interp.intern_const(w_val)
        interp.emitbyte(Op.LOADCONST)
        interp.emitbyte(const_index)

class __extend__(Lambda):
    def accept_interp(self, interp):
        proto_index = len(interp.proto_w)
        interp.proto_w.append(None) # hold a position for this lambda
        interp.emitbyte(Op.BUILDCONT)
        interp.emitshort(proto_index)
        interp.pending_lambdas.append((self, proto_index))


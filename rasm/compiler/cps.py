from rasm.lang.model import (W_Root, W_Int, W_Boolean, W_Unspecified,
                             W_Pair, W_Nil, W_Symbol,
                             symbol, list_to_pair, gensym,
                             w_nil, w_true, w_false, w_unspec,
                             W_ValueError, W_TypeError)
from rasm.compiler.ast import (Node, If, Seq, Apply, Def, Sete, Lambda,
                               Var, Const)

class Rewriter(object):
    def __init__(self, nodelist, lastcont=None):
        self.nodelist = nodelist
        self.lastcont = lastcont or Var(symbol('halt'))
        self.cpsform = None

    def run(self):
        if len(self.nodelist) == 0:
            return Const(w_unspec).rewrite_cps(self.lastcont)
        cont = self.lastcont
        nodelist_copy = self.nodelist[1:]
        nodelist_copy.reverse()
        for node in nodelist_copy:
            ignore = newvar('$Ignore_')
            cont = Lambda([ignore],
                          [node.rewrite_cps(cont)])
        self.cpsform = self.nodelist[0].rewrite_cps(cont)
        return self.cpsform


def newvar(prefix='$Var_'):
    return Var(gensym(prefix))

class __extend__(Node):
    def rewrite_cps(self, cont):
        raise NotImplementedError
    
    def to_cpsatom(self):
        raise NotImplementedError

    def is_cpsatom(self):
        raise NotImplementedError

class __extend__(If):
    def rewrite_cps(self, cont):
        fst, snd, trd = self.fst, self.snd, self.trd
        if isinstance(cont, Var):
            if fst.is_cpsatom():
                return If(fst.to_cpsatom(), snd.rewrite_cps(cont),
                                            trd.rewrite_cps(cont))
            else:
                fstval = newvar('$PredRv_')
                fstcont = Lambda([fstval],
                                 [If(fstval, snd.rewrite_cps(cont),
                                             trd.rewrite_cps(cont))])
                return fst.rewrite_cps(fstcont)
        else:
            contval = newvar('$Cont_')
            contdef = Def(contval, cont)
            if fst.is_cpsatom():
                return Seq([contdef, If(fst.to_cpsatom(),
                                        snd.rewrite_cps(contval),
                                        trd.rewrite_cps(contval))])
            else:
                fstval = newvar('$PredRv_')
                fstcont = Lambda([fstval],
                                 [If(fstval, snd.rewrite_cps(contval),
                                             trd.rewrite_cps(contval))])
                return Seq([contdef, fst.rewrite_cps(fstcont)])

    def to_cpsatom(self):
        return If(self.fst.to_cpsatom(), self.snd.to_cpsatom(),
                                         self.trd.to_cpsatom())

    def is_cpsatom(self):
        return (self.fst.is_cpsatom() and self.snd.to_cpsatom() and
                self.trd.is_cpsatom())

class __extend__(Seq):
    def rewrite_cps(self, cont):
        return Rewriter(self.nodelist, lastcont=cont).run()

    def is_cpsatom(self):
        return len(self.nodelist) == 1 and self.nodelist[0].is_cpsatom()

    def to_cpsatom(self):
        return self.nodelist[0].to_cpsatom()

class __extend__(Apply):
    def rewrite_cps(self, cont):
        proc, args = self.proc, self.args
        if proc.is_cpsatom():
            proc = proc.to_cpsatom()
        else:
            procrv = newvar('$ProcRv_')
            proccont = Lambda([procrv],
                              [Apply(procrv, args).rewrite_cps(cont)])
            return proc.rewrite_cps(proccont)

        atom_args = []
        for i in xrange(len(args)): # XXX pypy hack
            arg = args[i]
            if not arg.is_cpsatom():
                argrv = newvar('$ArgRv_')
                newapply = Apply(proc, args[:i] + [argrv] + args[i + 1:])
                argcont = Lambda([argrv],
                                 [newapply.rewrite_cps(cont)])
                return arg.rewrite_cps(argcont)
            else:
                atom_args.append(arg.to_cpsatom())
        return Apply(proc, atom_args + [cont])

    def is_cpsatom(self):
        return False

# XXX: define and set! need rethinking.
class __extend__(Def):
    def rewrite_cps(self, cont):
        formrv = newvar('$FormRv_')
        formcont = Lambda([formrv],
                          [Apply(cont, [Def(self.name, formrv)])])
        return self.form.rewrite_cps(formcont)

    def to_cpsatom(self):
        return Def(self.name, self.form.to_cpsatom())

    def is_cpsatom(self):
        return self.form.is_cpsatom()

class __extend__(Sete):
    def rewrite_cps(self, cont):
        formrv = newvar('$FormRv_')
        formcont = Lambda([formrv],
                          [Apply(cont, [Sete(self.name, formrv)])])
        return self.form.rewrite_cps(formcont)

    def to_cpsatom(self):
        return Sete(self.name, self.form.to_cpsatom())

    def is_cpsatom(self):
        return self.form.is_cpsatom()

class __extend__(Var, Const, Lambda):
    def rewrite_cps(self, cont):
        return Apply(cont, [self.to_cpsatom()])

    def to_cpsatom(self):
        return self

    def is_cpsatom(self):
        return True

class __extend__(Lambda):
    def to_cpsatom(self):
        cont = newvar('$LamK_')
        newbody = Rewriter(self.body, lastcont=cont).run()
        return Lambda(self.formals + [cont], [newbody], self.name)


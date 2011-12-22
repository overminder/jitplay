from rasm.rt.code import W_Proto, W_Cont, Op
from rasm.lang.env import ModuleDict, ModuleCell
from rasm.lang.model import symbol, w_eof, w_nil

def get_report_env():
    w_module = ModuleDict()
    for w_name, w_cont in prelude_impl.iteritems():
        w_module.setitem(w_name, w_cont)
    return w_module

prelude_impl = {}

def regimpl(w_cont):
    prelude_impl[symbol(w_cont.w_proto.name)] = w_cont

def buildproto(name, nb_args, raw_code, nb_locals=-1):
    if nb_locals == -1:
        nb_locals = nb_args
    code = ''.join(map(chr, raw_code))
    w_proto = W_Proto(code, nb_args, nb_locals, upval_descr=None,
                      const_w=None, w_module=None)
    w_proto.name = name
    return w_proto

def buildcont(name, nb_args, raw_code, nb_locals=-1):
    w_proto = buildproto(name, nb_args, raw_code, nb_locals)
    w_cont = W_Cont(w_proto, None)
    return w_cont

call_inplace = lambda x: x()

# Well, primitive op should be far more efficient than this..
@call_inplace
def populate_library():
    regimpl(buildcont('+', 3, [Op.LOAD, 0,
                               Op.LOAD, 1,
                               Op.IADD,
                               Op.LOAD, 2,
                               Op.CONT]))

    regimpl(buildcont('-', 3, [Op.LOAD, 0,
                               Op.LOAD, 1,
                               Op.ISUB,
                               Op.LOAD, 2,
                               Op.CONT]))

    regimpl(buildcont('*', 3, [Op.LOAD, 0,
                               Op.LOAD, 1,
                               Op.IMUL,
                               Op.LOAD, 2,
                               Op.CONT]))

    regimpl(buildcont('/', 3, [Op.LOAD, 0,
                               Op.LOAD, 1,
                               Op.IDIV,
                               Op.LOAD, 2,
                               Op.CONT]))

    regimpl(buildcont('<', 3, [Op.LOAD, 0,
                               Op.LOAD, 1,
                               Op.LT,
                               Op.LOAD, 2,
                               Op.CONT]))

    regimpl(buildcont('null?', 2, [Op.LOAD, 0,
                                   Op.NULLP,
                                   Op.LOAD, 1,
                                   Op.CONT]))

    regimpl(buildcont('pair?', 2, [Op.LOAD, 0,
                                   Op.PAIRP,
                                   Op.LOAD, 1,
                                   Op.CONT]))

    regimpl(buildcont('integer?', 2, [Op.LOAD, 0,
                                      Op.INTEGERP,
                                      Op.LOAD, 1,
                                      Op.CONT]))

    regimpl(buildcont('cons', 3, [Op.LOAD, 0,
                                  Op.LOAD, 1,
                                  Op.CONS,
                                  Op.LOAD, 2,
                                  Op.CONT]))

    regimpl(buildcont('car', 2, [Op.LOAD, 0,
                                 Op.CAR,
                                 Op.LOAD, 1,
                                 Op.CONT]))

    regimpl(buildcont('cdr', 2, [Op.LOAD, 0,
                                 Op.CDR,
                                 Op.LOAD, 1,
                                 Op.CONT]))

    regimpl(buildcont('display', 2, [Op.LOAD, 0,
                                     Op.PRINT,
                                     Op.UNSPEC,
                                     Op.LOAD, 1,
                                     Op.CONT]))

    regimpl(buildcont('newline', 1, [Op.NEWLINE,
                                     Op.UNSPEC,
                                     Op.LOAD, 0,
                                     Op.CONT]))

    '''
    (call/cc
      (lambda (k)
        (k 1)
        2)) =>

    (call/cc
      (lambda (k $LamK)
        (k 1 (lambda (_) ;; this lambda is never called.
               ($LamK 2))))
      cont)

    (define (call/cc func cont)
      (func (lambda (rv _)
              (cont rv))
        cont))
    '''

    regimpl(buildcont('call/cc', 2, [Op.LOAD, 1, # [cont]
                                     Op.REIFYCC, # [cc]
                                     Op.LOAD, 1, # [cc, cont]
                                     Op.LOAD, 0, # [cc, cont, func]
                                     Op.CONT]))

    regimpl(buildcont('read', 1, [Op.READ,
                                  Op.LOAD, 0,
                                  Op.CONT]))

    # XXX not finished yet.
    regimpl(buildcont('eval', 3, [Op.LOAD, 0, # [expr]
                                  Op.LOAD, 1, # [expr, w_module]
                                  Op.COMPILE, # [expr_cont]
                                  Op.LOAD, 2, # [expr_cont, cont]
                                  Op.CONT]))

    regimpl(buildcont('halt', 1, [Op.HALT]))

callcc_proto = buildproto('reified-continuation', 2, [Op.LOAD, 0,
                                                      Op.GETUPVAL, 0,
                                                      Op.CONT])
callcc_proto.upval_descr = ['\0'] # dummy

def reify_callcc(w_cont):
    return W_Cont(callcc_proto, [ModuleCell(w_cont)])

def read_stdin():
    from rasm.ffi.libreadline import getline
    from rasm.compiler.parser import parse_string, BacktrackException
    try:
        line = getline('> ')
    except EOFError:
        return [w_eof]
    try:
        exprs_w = parse_string(line)
    except BacktrackException as e:
        print e.error.nice_error_message('<stdin>', line)
        return [w_eof]
    return exprs_w


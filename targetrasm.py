import sys 
from rasm.model import symbol
from rasm.module import ModuleDict
from rasm.code import Op, W_Proto, W_Cont
from rasm.execution import Frame

EXE_NAME = "rasm-c"

def target(driver, argl):
    driver.exe_name = EXE_NAME
    return main, None

def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()

def makecode(lst):
    return ''.join([chr(ival) for ival in lst])

def main(argv):
    try:
        fibo_arg = int(argv[1])
    except (IndexError, ValueError):
        fibo_arg = 30

    try:
        stacksize = int(argv[2])
    except (IndexError, ValueError):
        stacksize = 16

    maincode = makecode([
        Op.INT, fibo_arg, 0,
        Op.GETGLOBAL, 1, # 'display-and-halt
        Op.GETGLOBAL, 0, # 'fibo
        Op.CONT, # (fibo 10 display-and-halt)
    ])
    print_and_halt = makecode([
        Op.LOAD, 0,
        Op.DUP,
        Op.PRINT,
        Op.NEWLINE,
        Op.HALT,
    ])
    fibo_entry = makecode([
        Op.LOAD, 0,
        Op.DUP,
        Op.INT, 2, 0,
        Op.LT,
        Op.BRANCHIFNOT, 3, 0,
        # base case
        Op.LOAD, 1,
        Op.CONT,
        # recur case
        Op.INT, 1, 0,
        Op.ISUB,
        Op.BUILDCONT, 1, 0, # 'fibo-k0, with upval[0] = n, upval[1] = k
        Op.GETGLOBAL, 0, # 'fibo
        Op.CONT,
    ])
    fibo_k0 = makecode([
        Op.GETUPVAL, 0,
        Op.INT, 2, 0,
        Op.ISUB,
        Op.BUILDCONT, 2, 0, # 'fibo-k1, with upval[0] = $Rv_0, upval[1] = k
        Op.GETGLOBAL, 0, # 'fibo
        Op.CONT,
    ])
    fibo_k1 = makecode([
        Op.GETUPVAL, 0, # $Rv_0
        Op.LOAD, 0, # $Rv_1
        Op.IADD,
        Op.GETUPVAL, 1, # k
        Op.CONT,
    ])
    fibo_sym = symbol('fibo')
    dah_sym = symbol('display-and-halt')
    const_w0 = [fibo_sym, dah_sym]
    const_w1 = [fibo_sym]
    proto_w = [None, None, None, None, None]
    w_module = ModuleDict()
    proto_w[0] = W_Proto(maincode, nb_args=0, nb_locals=0,
                         upval_descr=[], const_w=const_w0,
                         w_module=w_module)
    w_maincont = W_Cont(proto_w[0], upval_w=[])
    proto_w[1] = W_Proto(fibo_k0, nb_args=1, nb_locals=1,
                         upval_descr=[chr(0), chr(1)],
                         const_w=const_w1, w_module=w_module)
    proto_w[2] = W_Proto(fibo_k1, nb_args=1, nb_locals=1,
                         upval_descr=[chr(0), chr(2)],
                         const_w=const_w1, w_module=w_module)
    proto_w[3] = W_Proto(fibo_entry, nb_args=2, nb_locals=2,
                         upval_descr=[],
                         const_w=const_w1, w_module=w_module)
    w_fibocont = W_Cont(proto_w[3], upval_w=[])
    proto_w[4] = W_Proto(print_and_halt, nb_args=1, nb_locals=1,
                         upval_descr=[],
                         const_w=[], w_module=w_module)
    w_printcont = W_Cont(proto_w[4], upval_w=[])

    w_module.setitem(fibo_sym, w_fibocont)
    w_module.setitem(dah_sym, w_printcont)

    frame = Frame(w_maincont, proto_w, stacksize)

    w_ret = frame.run()
    return 0

if __name__ == '__main__':
    main(sys.argv)


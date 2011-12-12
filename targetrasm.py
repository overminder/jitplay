import sys 
from rasm.frame import Stack
from rasm.code import CodeEnum, W_Function
from rasm.execution import W_Frame

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

    func_code = makecode([
        CodeEnum.LOAD, 0,
        CodeEnum.INT, 2, 0,
        CodeEnum.LT,
        CodeEnum.BRANCHIFNOT, 3, 0,
        CodeEnum.LOAD, 0,
        CodeEnum.FRET,

        CodeEnum.LOAD, 0,
        CodeEnum.INT, 1, 0,
        CodeEnum.ISUB,
        CodeEnum.FLOAD, 0, 0,
        CodeEnum.FCALL, 1,
        CodeEnum.LOAD, 0,
        CodeEnum.INT, 2, 0,
        CodeEnum.ISUB,
        CodeEnum.FLOAD, 0, 0,
        CodeEnum.FCALL, 1,
        CodeEnum.IADD,
        CodeEnum.FRET,
    ])
    main_code = makecode([
        CodeEnum.INT, fibo_arg, 0,
        CodeEnum.FLOAD, 0, 0,
        CodeEnum.FCALL, 1,
        CodeEnum.PRINT,
        CodeEnum.NEWLINE,
        CodeEnum.NIL,
        CodeEnum.FRET,
    ])
    s = Stack(100)
    f = W_Frame()
    w_func = W_Function()
    w_func.nargs = 1
    w_func.code = func_code
    f.constpool = [w_func]
    f.stack = s
    f.code = main_code
    w_ret = f.enter_dispatchloop()
    if w_ret:
        print w_ret.to_string()
    return 0

if __name__ == '__main__':
    main(sys.argv)


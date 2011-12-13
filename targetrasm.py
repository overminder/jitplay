import sys 
from rasm.code import CodeEnum, W_Function
from rasm.execution import Frame, Context

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
    const_w = []
    w_func = W_Function(nb_args=1, nb_locals=1, framesize=4,
                        code=func_code, const_w=const_w)
    const_w.append(w_func)

    ctx = Context()
    f = Frame(10, main_code, const_w=const_w, ctx=ctx)
    w_ret = f.run()
    if w_ret:
        print w_ret.to_string()
    return 0

if __name__ == '__main__':
    main(sys.argv)


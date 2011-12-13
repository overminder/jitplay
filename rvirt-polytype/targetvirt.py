import sys
from code import Frame, Enum

def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()

def main(argv):
    try:
        loop_arg = int(argv[1])
    except (IndexError, ValueError):
        loop_arg = 25

    try:
        # lessthan 1k.
        stacksize = int(argv[2])
    except (IndexError, ValueError):
        stacksize = 5

    f_local = [None] * 4
    code = [chr(c) if c >= 0 else chr(c + 256) for c in [
        Enum.FIXNUM, 1,
        Enum.FIXNUM, loop_arg,
        Enum.LSH,
        Enum.STORE, 0,
        Enum.FIXNUM, 0,
        Enum.STORE, 1,

        Enum.LOAD, 1,
        Enum.LOAD, 0,
        Enum.LT,
        Enum.BIFZ, 9,
        Enum.FIXNUM, 1,
        Enum.LOAD, 1,
        Enum.ADD,
        Enum.STORE, 1,
        Enum.B, -16,

        Enum.LOAD, 1,
        Enum.PRINT,
        Enum.HALT
    ]]
    f = Frame(stacksize, code, f_local)
    f.dispatch()
    return 0

def target(driver, args):
    return main, None

if __name__ == '__main__':
    main(sys.argv)

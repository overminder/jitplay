import sys 
from rasm.error import OperationError
from rasm.ffi.libreadline import getline
from rasm.compiler.parser import parse_string, BacktrackException
from rasm.compiler.astbuilder import Builder
from rasm.compiler.cps import Rewriter

EXE_NAME = "interp-c"

def target(driver, argl):
    driver.exe_name = EXE_NAME
    return main, None

def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()

def main(argv):
    while True:
        try:
            line = getline('> ')
        except EOFError:
            break

        try:
            exprs_w = parse_string(line)
        except BacktrackException as e:
            print e.error.nice_error_message('<stdin>', line)
            continue

        try:
            nodelist = Builder(exprs_w).getast()
        except OperationError as e:
            print e.unwrap().to_string()
            continue

        cpsform = Rewriter(nodelist).run()
        print cpsform.to_string()

    return 0


if __name__ == '__main__':
    main(sys.argv)


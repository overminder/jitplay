import sys 
from rasm.error import OperationError
from rasm.ffi.libreadline import getline
from rasm.compiler.parser import parse_string, BacktrackException
from rasm.compiler.astbuilder import Builder
from rasm.compiler.cps import Rewriter
from rasm.compiler.codegen import compile_all
from rasm.compiler.codeviewer import dis_proto
from rasm.rt.prelude import get_report_env
from rasm.rt.execution import Frame
from rasm.lang.model import w_unspec

from pypy.jit.codewriter.policy import JitPolicy
from pypy.rlib.streamio import open_file_as_stream
from pypy.rlib.objectmodel import we_are_translated

EXE_NAME = "interp-c"

def target(driver, argl):
    driver.exe_name = EXE_NAME
    return main, None

def jitpolicy(driver):
    return JitPolicy()

def run_file(filename):
    fp = open_file_as_stream(filename)
    source = fp.readall()
    toplevel_env = get_report_env()
    try:
        exprs_w = parse_string(source)
    except BacktrackException as e:
        print e.error.nice_error_message('<file %s>' % filename, source)
        return 1
    try:
        nodelist = Builder(exprs_w).getast()
    except OperationError as e:
        print e.unwrap().to_string()
        return 1
    cpsform = Rewriter(nodelist, toplevel=True).run()
    try:
        w_maincont, proto_w = compile_all(cpsform, toplevel_env)
    except OperationError as e:
        print e.unwrap().to_string()
        return 1
    #print 'ast:', map(lambda o: o.to_string(), nodelist)
    #print cpsform.to_string()
    #print w_maincont, 'dis:'
    #print dis_proto(w_maincont.w_proto)
    #for w_proto in proto_w:
    #    print w_proto, 'dis:'
    #    print dis_proto(w_proto)
    #return 0
    frame = Frame(w_maincont, proto_w)
    frame.run()
    return 0

def repl():
    toplevel_env = get_report_env()
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

        cpsform = Rewriter(nodelist, toplevel=True).run()
        try:
            w_maincont, proto_w = compile_all(cpsform, toplevel_env)
        except OperationError as e:
            print e.unwrap().to_string()
            continue

        print 'cps:', cpsform.to_string()
        print w_maincont.to_string(), 'dis:'
        print dis_proto(w_maincont.w_proto)
        for w_proto in proto_w:
            print w_proto.to_string(), 'dis:'
            print dis_proto(w_proto)
        #frame = Frame(w_maincont, proto_w)
        #w_res = frame.run()
        #if w_res and w_res is not w_unspec:
        #    print w_res.to_string()

    return 0

def main(argv):
    try:
        filename = argv[1]
    except IndexError:
        if we_are_translated():
            print 'Usage: %s [filename]' % argv[0]
            return 1
        else:
            return repl()
    return run_file(filename)

if __name__ == '__main__':
    main(sys.argv)


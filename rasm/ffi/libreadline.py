import sys
sys.path.insert(0, '/home/overmind/src/rpy/lang-nativesanya/')

def getline(prompt='>>> '):
    from pypy.rlib.objectmodel import we_are_translated
    if we_are_translated():
        from sanya.ffi.rreadline import rreadline
        return rreadline(prompt)
    else:
        import readline
        return raw_input(prompt)


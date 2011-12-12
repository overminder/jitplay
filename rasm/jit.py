from pypy.rlib.jit import JitDriver

driver = JitDriver(greens=['pc', 'code'],
                   reds=['frame'])


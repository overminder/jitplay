from pypy.rlib.parsing.makepackrat import (PackratParser, Status,
                                           BacktrackException)
from rasm.lang.model import (W_Root, W_Int, W_Pair, w_nil, w_true, w_false,
                             symbol, w_unspec)

def parse_string(source):
    exprs_w = SchemeParser(source).program()
    assert isinstance(exprs_w[0], W_Root) # XXX pypy hack
    return exprs_w

def w_tag(s, w_x):
    return W_Pair(symbol(s), W_Pair(w_x, w_nil))

class SchemeParser(PackratParser):
    r'''
    IGNORE:
        `[ \t\n\r]`;

    NUMBER:
        `[+-]?[0-9]+`;

    IDENT:
        `[0-9a-zA-Z!@#$%&*+-/<>=]+`;

    EOF:
        !__any__;

    program:
        c = sexpr*
        EOF
        return {c};

    sexpr:
        IGNORE*
        '('
        c = pair
        IGNORE*
        ')'
        return {c}
      | IGNORE*
        c = NUMBER
        return {W_Int(int(c or 'ERR'))}
      | IGNORE*
        `'`
        c = sexpr
        return {w_tag('quote', c)}
      | IGNORE*
        c = IDENT
        return {symbol(c)};

    pair:
        car = sexpr
        IGNORE*
        '.'
        cdr = sexpr
        return {W_Pair(car, cdr)}
      | car = sexpr
        cdr = pair
        return {W_Pair(car, cdr)}
      | return {w_nil};
    '''
    noinit = True


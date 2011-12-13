# It seems that opcode switch should not be inlined..
# However, stack operations should always be inlined.
# Further more, opcode switch cannot be inlined in jitted code.
# ... Actually, in jitted code, it's better to let the jit engine to
# decide which part of the code to inline.

INLINE_OPCODE = False
INLINE_DISPATCH = False
INLINE_STACKOP = False


# It seems that OPCODE should not be inlined..
# However, stack operations should always be inlined.
INLINE_OPCODE = False
INLINE_DISPATCH = False
INLINE_STACKOP = True


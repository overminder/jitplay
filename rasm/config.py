# It seems that opcode switch should not be inlined..
# However, stack operations should always be inlined.
# Further more, opcode switch cannot be inlined in jitted code.
INLINE_OPCODE = False
INLINE_DISPATCH = False
INLINE_STACKOP = True


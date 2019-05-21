

class OpcodeLengthError(Exception):
    pass


class OpcodeBadFormat(Exception):
    pass


class OpcodeReserved(Exception):
    pass


class ParametersLengthError(Exception):
    pass


def check_opcode(opcode: bytes):
    if len(opcode) > 3:
        raise OpcodeLengthError

    opcode_int = opcode[0]
    prefix = (opcode_int & 0xC0) >> 6

    if opcode_int == 0x3f:
        raise OpcodeReserved
    elif (prefix == 0 or prefix == 1) and len(opcode) != 1:
        raise OpcodeBadFormat
    elif prefix == 2 and len(opcode) != 2:
        raise OpcodeBadFormat
    elif prefix == 3 and len(opcode) != 3:
        raise OpcodeBadFormat


def opcode_len(opcode: bytes) -> int:
    prefix = (opcode[0] & 0xC0) >> 6
    if prefix == 0:
        return 1
    else:
        return prefix


def check_parameters(opcode: bytes, parameters: bytes):
    prefix = (opcode[0] & 0xC0) >> 7

    if (prefix == 0 or prefix == 1) and len(parameters) > 379:
        raise ParametersLengthError
    elif prefix == 2 and len(parameters) > 378:
        raise ParametersLengthError
    elif prefix == 3 and len(parameters) > 377:
        raise ParametersLengthError

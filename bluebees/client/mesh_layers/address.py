
UNASSIGNED_ADDRESS = 0
UNICAST_ADDRESS = 1
VIRTUAL_ADDRESS = 2
GROUP_ADDRESS = 3


class AddressLengthError(Exception):
    pass


def address_type(address: bytes) -> int:
    if len(address) != 2:
        raise AddressLengthError

    addr_int = int.from_bytes(address, 'big')
    prefix = ((addr_int & 0xC000) >> 14)

    if addr_int == 0x0000:
        return UNASSIGNED_ADDRESS
    elif prefix == 0 or prefix == 1:
        return UNICAST_ADDRESS
    elif prefix == 2:
        return VIRTUAL_ADDRESS
    elif prefix == 3:
        return GROUP_ADDRESS

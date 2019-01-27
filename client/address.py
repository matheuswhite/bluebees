from enum import Enum


class MeshAddressType(Enum):
    UNASSIGNED_ADDRESS = 0x00
    UNICAST_ADDRESS = 0x01
    VIRTUAL_ADDRESS = 0x02
    GROUP_ADDRESS = 0x03
    ALL_PROXIES_ADDRESS = 0x04
    ALL_FRIENDS_ADDRESS = 0x05
    ALL_RELAYS_ADDRESS = 0x06
    ALL_NODES_ADDRESS = 0x07


def _int2type(value: int):
    if value == 0x0000:
        return MeshAddressType.UNASSIGNED_ADDRESS
    elif 0x0001 <= value <= 0x7fff:
        return MeshAddressType.UNICAST_ADDRESS
    elif 0x8000 <= value <= 0xbfff:
        return MeshAddressType.VIRTUAL_ADDRESS
    elif 0xff00 <= value <= 0xfffb:
        return MeshAddressType.GROUP_ADDRESS
    elif value == 0xfffc:
        return MeshAddressType.ALL_PROXIES_ADDRESS
    elif value == 0xfffd:
        return MeshAddressType.ALL_FRIENDS_ADDRESS
    elif value == 0xfffe:
        return MeshAddressType.ALL_RELAYS_ADDRESS
    elif value == 0xffff:
        return MeshAddressType.ALL_NODES_ADDRESS


class MeshAddress:

    def __init__(self, value):
        self.byte_value: bytes = value[0:2] if type(value) is bytes else int(value).to_bytes(2, 'big')
        self.int_value: int = value if type(value) is int else int.from_bytes(value[0:2], 'big')
        self.type: MeshAddressType = _int2type(self.int_value)


def address_is_valid_in_source(addr: MeshAddress):
    return addr.type == MeshAddressType.UNICAST_ADDRESS


def address_is_valid_in_control_messages(addr: MeshAddress):
    return addr.type == MeshAddressType.UNICAST_ADDRESS or addr.type == MeshAddressType.GROUP_ADDRESS or \
           addr.type == MeshAddressType.ALL_PROXIES_ADDRESS or addr.type == MeshAddressType.ALL_FRIENDS_ADDRESS or \
           addr.type == MeshAddressType.ALL_RELAYS_ADDRESS or addr.type == MeshAddressType.ALL_NODES_ADDRESS


def address_is_valid_in_access_messages(addr: MeshAddress):
    return addr.type == MeshAddressType.UNICAST_ADDRESS or addr.type == MeshAddressType.VIRTUAL_ADDRESS or \
           addr.type == MeshAddressType.GROUP_ADDRESS or addr.type == MeshAddressType.ALL_PROXIES_ADDRESS or \
           addr.type == MeshAddressType.ALL_FRIENDS_ADDRESS or addr.type == MeshAddressType.ALL_RELAYS_ADDRESS or \
           addr.type == MeshAddressType.ALL_NODES_ADDRESS


def address_is_valid_with_device_key(addr: MeshAddress):
    return addr.type == MeshAddressType.UNICAST_ADDRESS


def address_is_valid_with_app_key(addr: MeshAddress):
    return addr.type == MeshAddressType.UNICAST_ADDRESS or addr.type == MeshAddressType.VIRTUAL_ADDRESS or \
           addr.type == MeshAddressType.GROUP_ADDRESS or addr.type == MeshAddressType.ALL_PROXIES_ADDRESS or \
           addr.type == MeshAddressType.ALL_FRIENDS_ADDRESS or addr.type == MeshAddressType.ALL_RELAYS_ADDRESS or \
           addr.type == MeshAddressType.ALL_NODES_ADDRESS

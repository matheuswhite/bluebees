from dataclasses import dataclass
import json
from typing import List
from Crypto.Random import get_random_bytes

FORBIDDEN_ADDRESSES = [

]


@dataclass
class Net:
    name: str
    net_key: bytes
    net_key_index: int
    iv_index: int
    unicast_address_allocated: List[bytes]

    def next_unicast_address(self):
        if len(self.unicast_address_allocated) >= 2**16:
            return None

        addr = get_random_bytes(2)
        while addr in self.unicast_address_allocated or addr in FORBIDDEN_ADDRESSES:
            addr = get_random_bytes(2)
        return addr

    def save(self, json_file):
        with open(json_file, 'w') as write_file:
            data = {
                'name': self.name,
                'net_key': self.net_key,
                'net_key_index': self.net_key_index,
                'iv_index': self.iv_index,
                'unicast_address_allocated': self.unicast_address_allocated
            }
            json.dump(data, write_file)

    @classmethod
    def load(cls, json_file):
        with open(json_file, 'r') as read_file:
            data = json.load(read_file)
            net = cls(data['name'], data['net_key'], data['net_key_index'], data['iv_index'],
                      data['unicast_address_allocated'])
        return net

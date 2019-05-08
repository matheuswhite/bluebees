from dataclasses import dataclass
from common.serializable import Serializable
from typing import List
from client.data_paths import base_dir, node_dir


@dataclass
class NodeData(Serializable):
    name: str
    addr: bytes         # 2 bytes
    ecdh_secret: bytes  # 32 bytes
    device_uuid: bytes  # 16 bytes
    network: str
    apps: List[str]

    def __init__(self, name, addr, network, device_uuid, ecdh_secret, apps=[]):
        super().__init__(filename=base_dir + node_dir + name + '.yml')

        self.name = name
        self.addr = addr
        self.device_uuid = device_uuid
        self.ecdh_secret = ecdh_secret
        self.network = network
        self.apps = apps

    def __repr__(self):
        return f'Name: {self.name}\nAddress: {self.addr}\n' \
               f'Device UUID: {self.device_uuid}\n' \
               f'ECDH secret: {self.ecdh_secret}\nNetwork: {self.network}\n' \
               f'Apps: {self.apps}'

from dataclasses import dataclass
from common.serializable import Serializable
from typing import List
from client.data_paths import base_dir, net_dir


@dataclass
class NetworkData(Serializable):
    name: str
    key: bytes
    key_index: bytes
    iv_index: bytes
    nodes: List[str]

    def __init__(self, name, key, key_index, iv_index, nodes=[]):
        super().__init__(filename=base_dir + net_dir + name + '.yml')

        self.name = name
        self.key = key
        self.key_index = key_index
        self.iv_index = iv_index
        self.nodes = nodes

    def __repr__(self):
        return f'Name: {self.name}\nKey: {self.key}\nNodes: {self.nodes}'

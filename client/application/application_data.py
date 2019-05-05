from dataclasses import dataclass
from common.serializable import Serializable
from typing import List
from client.data_paths import base_dir, app_dir


@dataclass
class ApplicationData(Serializable):
    name: str
    key: bytes        # 16 bytes
    key_index: bytes  # 12 bits
    network: str
    nodes: List[str]

    def __init__(self, name, key, key_index, network, nodes=[]):
        super().__init__(filename=base_dir + app_dir + name + '.yml')

        self.name = name
        self.key = key
        self.key_index = key_index
        self.network = network
        self.nodes = nodes

    def __repr__(self):
        return f'Name: {self.name}\nKey: {self.key}\n' \
               f'Key Index: {self.key_index}\nNetwork: {self.network}\n' \
               f'Nodes: {self.nodes}'

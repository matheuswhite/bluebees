from dataclasses import dataclass
from common.serializable import Serializable
from typing import List
from client.data_paths import base_dir, net_dir


@dataclass
class NetworkData(Serializable):
    name: str
    key: bytes
    nodes: List[str]

    def __init__(self, name, key, nodes=[]):
        super().__init__(filename=base_dir + net_dir + name + '.yml')

        self.name = name
        self.key = key
        self.nodes = nodes

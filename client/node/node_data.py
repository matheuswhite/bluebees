from dataclasses import dataclass
from common.serializable import Serializable
from typing import List
from client.data_paths import base_dir, node_dir


@dataclass
class NodeData(Serializable):
    name: str
    addr: bytes
    network: str
    apps: List[str]

    def __init__(self, name, addr, network, apps=[]):
        super().__init__(filename=base_dir + node_dir + name + '.yml')

        self.name = name
        self.addr = addr
        self.network = network
        self.apps = apps

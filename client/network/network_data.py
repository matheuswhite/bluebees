from dataclasses import dataclass
from common.serializable import Serializable
from typing import List
from client.data_paths import base_dir, net_dir


@dataclass
class NetworkData(Serializable):
    name: str
    key: bytes        # 16 bytes
    key_index: bytes  # 12 bits
    iv_index: bytes   # 4 bytes
    seq: int          # 3 bytes
    apps: List[str]

    def __init__(self, name, key, key_index, iv_index, seq=-1, apps=[]):
        super().__init__(filename=base_dir + net_dir + name + '.yml')

        self.name = name
        self.key = key
        self.key_index = key_index
        self.iv_index = iv_index
        self.apps = apps
        self.seq = seq

    def __repr__(self):
        return f'Name: {self.name}\nKey: {self.key}\n' \
               f'Key Index: {self.key_index}\nIV Index: {self.iv_index}\n' \
               f'Seq number: {self.seq}\nApplications: {self.apps}'

from dataclasses import dataclass
from bluebees.common.serializable import Serializable
from typing import List
from bluebees.client.data_paths import base_dir, net_dir
from bluebees.common.file import file_helper


@dataclass
class NetworkData(Serializable):
    name: str
    key: bytes        # 16 bytes
    key_index: bytes  # 12 bits
    iv_index: bytes   # 4 bytes
    apps: List[str]
    nodes: List[str]

    def __init__(self, name, key, key_index, iv_index, apps=[], nodes=[]):
        super().__init__(filename=base_dir + net_dir + name + '.yml')

        self.name = name
        self.key = key
        self.key_index = key_index
        self.iv_index = iv_index
        self.apps = apps
        self.nodes = nodes

    def __repr__(self):
        return f'Name: {self.name}\nKey: {self.key.hex()}\n' \
               f'Key Index: {self.key_index.hex()}\n' \
               f'IV Index: {self.iv_index.hex()}\n' \
               f'Applications: {self.apps}\nNodes: {self.nodes}'


def net_name_list() -> list:
    filenames = file_helper.list_files(base_dir + net_dir)
    if not filenames:
        return False

    # remove file extension
    filenames_fmt = []
    for file in filenames:
        filenames_fmt.append(file[:-4])

    return filenames_fmt


def net_key_list() -> list:
    filenames = file_helper.list_files(base_dir + net_dir)
    if not filenames:
        return []

    netkeys = []
    for file in filenames:
        net = NetworkData.load(base_dir + net_dir + file)
        netkeys.append(net.key)
    return netkeys


def net_key_index_list() -> list:
    filenames = file_helper.list_files(base_dir + net_dir)
    if not filenames:
        return []

    net_key_indexes = []
    for file in filenames:
        net = NetworkData.load(base_dir + net_dir + file)
        net_key_indexes.append(net.key_index)
    return net_key_indexes

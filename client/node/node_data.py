from dataclasses import dataclass
from common.serializable import Serializable
from typing import List
from client.data_paths import base_dir, node_dir
from common.file import file_helper


@dataclass
class NodeData(Serializable):
    name: str
    addr: bytes         # 2 bytes
    devkey: bytes       # 16 bytes
    device_uuid: bytes  # 16 bytes
    network: str
    apps: List[str]

    def __init__(self, name, addr, network, device_uuid, devkey, apps=[]):
        super().__init__(filename=base_dir + node_dir + name + '.yml')

        self.name = name
        self.addr = addr
        self.device_uuid = device_uuid
        self.devkey = devkey
        self.network = network
        self.apps = apps

    def __repr__(self):
        return f'Name: {self.name}\nAddress: {self.addr}\n' \
               f'Device UUID: {self.device_uuid}\n' \
               f'Devkey: {self.devkey}\nNetwork: {self.network}\n' \
               f'Apps: {self.apps}'


def node_name_list() -> list:
    filenames = file_helper.list_files(base_dir + node_dir)
    if not filenames:
        return False

    # remove file extension
    filenames_fmt = []
    for file in filenames:
        filenames_fmt.append(file[:-4])

    return filenames_fmt


def node_addr_list() -> list:
    filenames = file_helper.list_files(base_dir + node_dir)
    if not filenames:
        return []

    node_addrs = []
    for file in filenames:
        node = NodeData.load(base_dir + node_dir + file)
        node_addrs.append(node.addr)
    return node_addrs

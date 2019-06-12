from dataclasses import dataclass
from bluebees.common.serializable import Serializable
from typing import List
from bluebees.client.data_paths import base_dir, node_dir
from bluebees.common.file import file_helper


@dataclass
class NodeData(Serializable):
    name: str
    addr: bytes         # 02 bytes
    devkey: bytes       # 16 bytes
    device_uuid: bytes  # 16 bytes
    seq: int            # 03 bytes
    network: str
    apps: List[str]

    def __init__(self, name, addr, network, device_uuid, devkey, seq=0, apps=[]):
        super().__init__(filename=base_dir + node_dir + name + '.yml')

        self.name = name
        self.addr = addr
        self.device_uuid = device_uuid
        self.devkey = devkey
        self.network = network
        self.apps = apps
        self.seq = seq

    def __repr__(self):
        return f'Name: {self.name}\nAddress: {self.addr.hex()}\n' \
               f'Device UUID: {self.device_uuid.hex()}\n' \
               f'Devkey: {self.devkey.hex()}\nNetwork: {self.network}\n' \
               f'SEQ: {self.seq}\nApps: {self.apps}'


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

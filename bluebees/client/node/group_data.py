from dataclasses import dataclass
from bluebees.common.serializable import Serializable
from typing import List
from bluebees.client.data_paths import base_dir, group_dir
from bluebees.common.file import file_helper


@dataclass
class GroupData(Serializable):
    name: str
    addr: bytes
    sub_addrs: List[bytes]

    def __init__(self, name, addr, sub_addrs=[]):
        super().__init__(filename=base_dir + group_dir + name + '.yml')

        self.name = name
        self.addr = addr
        self.sub_addrs = sub_addrs

    def __repr__(self):
        return f'Name: {self.name}\nAddress: {self.addr.hex()}\n' \
            f'Subscribers Addresses: {[a.hex() for a in self.addrs]}'


def group_name_list() -> list:
    filenames = file_helper.list_files(base_dir + group_dir)
    if not filenames:
        return False

    # remove file extension
    filenames_fmt = []
    for file in filenames:
        filenames_fmt.append(file[:-4])

    return filenames_fmt


def find_group_by_addr(target_addr: bytes) -> GroupData:
    filenames = file_helper.list_files(base_dir + group_dir)
    if not filenames:
        return False

    for file in filenames:
        group = GroupData.load(base_dir + group_dir + file)
        if target_addr == group.addr:
            return group

    return None

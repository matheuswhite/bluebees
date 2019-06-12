from dataclasses import dataclass
from bluebees.common.serializable import Serializable
from typing import List
from bluebees.client.data_paths import base_dir, app_dir
from bluebees.common.file import file_helper


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
        return f'Name: {self.name}\nKey: {self.key.hex()}\n' \
               f'Key Index: {self.key_index.hex()}\nNetwork: {self.network}\n'\
               f'Nodes: {self.nodes}'


def app_name_list() -> list:
    filenames = file_helper.list_files(base_dir + app_dir)
    if not filenames:
        return False

    # remove file extension
    filenames_fmt = []
    for file in filenames:
        filenames_fmt.append(file[:-4])

    return filenames_fmt


def app_key_list() -> list:
    filenames = file_helper.list_files(base_dir + app_dir)
    if not filenames:
        return []

    appkeys = []
    for file in filenames:
        app = ApplicationData.load(base_dir + app_dir + file)
        appkeys.append(app.key)
    return appkeys


def app_key_index_list() -> list:
    filenames = file_helper.list_files(base_dir + app_dir)
    if not filenames:
        return []

    app_key_indexes = []
    for file in filenames:
        app = ApplicationData.load(base_dir + app_dir + file)
        app_key_indexes.append(app.key_index)
    return app_key_indexes

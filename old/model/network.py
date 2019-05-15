from client.crypto import CRYPTO
from model.serializable import Serializable
from model.paths import *
import json


class Network(Serializable):

    def __init__(self, name: str, key: bytes, index: bytes, iv_index=b'\x00\x00\x00\x00'):
        super().__init__()

        self.name = name
        self.key = key
        self.index = index
        self.iv_index = iv_index

    def save(self):
        with open(BLUEBEES_DIR_PATH + f'{self.name}' + NETWORK_FILE_TYPE, 'w') as net_file:
            net_data = {
                'net_name': self.name,
                'key': bytes(self.key).hex(),
                'index': self.index.hex(),
                'iv_index': self.iv_index.hex()
            }
            json.dump(net_data, net_file)
        with open(BLUEBEES_DIR_PATH + NET_LIST_FILE_NAME + NETWORK_FILE_TYPE) as net_list_file_:
            net_list_ = json.load(net_list_file_)
        with open(BLUEBEES_DIR_PATH + NET_LIST_FILE_NAME + NETWORK_FILE_TYPE, 'w') as net_list_file_:
            net_list_['net_list'].append(self.name)
            json.dump(net_list_, net_list_file_)

    @classmethod
    def load(cls, name: str):
        with open(BLUEBEES_DIR_PATH + f'{name}' + NETWORK_FILE_TYPE) as net_file:
            net_data = json.load(net_file)
            return cls(net_data['net_name'], bytes.fromhex(net_data['key']), bytes.fromhex(net_data['index']),
                       bytes.fromhex(net_data['iv_index']))

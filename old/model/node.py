from model.serializable import Serializable
from model.paths import *
import json


class Node(Serializable):

    def __init__(self, name: str, net_name: str, unicast_address: bytes):
        super().__init__()

        self.name = name
        self.net_name = net_name
        self.unicast_address = unicast_address

    def save(self):
        with open(BLUEBEES_DIR_PATH + f'{self.name}' + NODE_FILE_TYPE, 'w') as node_file:
            node_data = {
                'name': self.name,
                'net_name': self.net_name,
                'unicast_address': self.unicast_address.hex()
            }
            json.dump(node_data, node_file)
        with open(BLUEBEES_DIR_PATH + NODE_LIST_FILE_NAME + NODE_FILE_TYPE) as node_list_file_:
            node_list_ = json.load(node_list_file_)
        with open(BLUEBEES_DIR_PATH + NODE_LIST_FILE_NAME + NODE_FILE_TYPE, 'w') as node_list_file_:
            node_list_['node_list'].append(self.name)
            json.dump(node_list_, node_list_file_)

    @classmethod
    def load(cls, name: str):
        with open(BLUEBEES_DIR_PATH + f'{name}' + NODE_FILE_TYPE) as node_file:
            node_data = json.load(node_file)
            return cls(node_data['name'], node_data['net_name'], bytes.fromhex(node_data['unicast_address']))

from random import randint
from model.network import Network
from model.paths import *
import json


class MeshManager:

    def __init__(self):
        self.networks = {}
        self._load_networks()

    def new_network(self, net_name: str):
        self.networks[net_name] = Network(net_name, self._gen_new_network_key())
        self.networks[net_name].save()
        return self.networks[net_name]

    def _gen_new_network_key(self):
        key_size = 16
        key = randint(0, 2**(key_size*8))
        keys_allocated = (n.key for n in list(self.networks.values()))
        while key.to_bytes(key_size, 'big') in keys_allocated:
            key = randint(0, 2**(key_size*8))
        return key.to_bytes(key_size, 'big')

    def _save_network(self, net_name: str):
        self.networks[net_name].save()

    def _load_networks(self):
        with open(BLUEBEES_DIR_PATH + NET_LIST_FILE_NAME + NETWORK_FILE_TYPE) as net_list_file_:
            net_list_ = json.load(net_list_file_)
            net_list_ = net_list_['net_list']
        for net in net_list_:
            self.networks[net] = Network.load(net)


mesh_manager = MeshManager()

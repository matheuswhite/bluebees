from client.network_layer import NetworkLayer
from random import randint
import json
import os


class Network:

    def __init__(self, key: bytes):
        self.key = key
        self.index = NetworkLayer.network_id(self.key)


class MeshManager:

    def __init__(self):
        self.bluebees_path = os.path.expanduser("~") + '/.bluebees/'
        self._create_bluebees_dir()

        self.networks = {}
        self._load_networks()

    def new_network(self, net_name: str):
        self.networks[net_name] = Network(self._gen_new_network_key())
        self._save_network(net_name)
        return self.networks[net_name]

    def _load_networks(self):
        if not os.path.exists(self.bluebees_path + 'net_list.json'):
            return

        with open(self.bluebees_path + 'net_list.json') as net_list_file:
            net_list = json.load(net_list_file)
            net_list = net_list['net_list']
        for net in net_list:
            with open(self.bluebees_path + f'{net}.json') as net_file:
                net_data = json.load(net_file)
                self.networks[net_data['net_name']] = Network(bytes.fromhex(net_data['key']))

    def _gen_new_network_key(self):
        key_size = 16
        key = randint(0, 2**(key_size*8))
        keys_allocated = (n.key for n in list(self.networks.values()))
        while key.to_bytes(key_size, 'big') in keys_allocated:
            key = randint(0, 2**(key_size*8))
        return key.to_bytes(key_size, 'big')

    def _create_bluebees_dir(self):
        if not os.path.exists(self.bluebees_path):
            os.mkdir(self.bluebees_path)

    def _create_net_list_file(self):
        if not os.path.exists(self.bluebees_path + 'net_list.json'):
            with open(self.bluebees_path + 'net_list.json', 'w') as net_list_file:
                net_list = {
                    'net_list': []
                }
                json.dump(net_list, net_list_file)

    def _save_network(self, net_name: str):
        with open(self.bluebees_path + f'{net_name}.json', 'w') as net_file:
            net_data = {
                'net_name': net_name,
                'key': bytes(self.networks[net_name].key).hex(),
                'index': self.networks[net_name].index.hex()
            }
            json.dump(net_data, net_file)
        self._create_net_list_file()
        with open(self.bluebees_path + 'net_list.json') as net_list_file:
            net_list = json.load(net_list_file)
        with open(self.bluebees_path + 'net_list.json', 'w') as net_list_file:
            net_list['net_list'].append(net_name)
            json.dump(net_list, net_list_file)


mesh_manager = MeshManager()

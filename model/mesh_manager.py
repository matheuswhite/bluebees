from random import randint
from model.network import Network
from model.device import Device
from model.node import Node
from model.paths import *
import json

"""
Zephyr Versions
    Dongle - v1.13.0-1442-g9c2c677da8
    Node - v1.13.0-1442-g9c2c677da8
"""


class MeshManager:

    def __init__(self):
        self.devices = {}
        self.networks = {}
        self.nodes = {}

        self._load_devices()
        self._load_networks()
        self._load_nodes()

    def remove_device(self, dev_name: str):
        del self.devices[dev_name]
        with open(BLUEBEES_DIR_PATH + DEVICE_LIST_FILE_NAME + DEVICE_FILE_TYPE) as device_list_file_:
            device_list_ = json.load(device_list_file_)
            device_list_ = device_list_['device_list']
            for x in range(len(device_list_)):
                if device_list_[x] == dev_name:
                    del device_list_[x]
                    break
        with open(BLUEBEES_DIR_PATH + DEVICE_LIST_FILE_NAME + DEVICE_FILE_TYPE, 'w') as device_list_file_:
            device_list_ = {'device_list': device_list_}
            json.dump(device_list_, device_list_file_)

    def new_device(self, dev_uuid: bytes):
        dev = Device(dev_uuid)
        self.devices[dev.name] = dev
        dev.save()
        return dev

    def new_network(self, net_name: str):
        self.networks[net_name] = Network(net_name, self._gen_new_network_key(), self._gen_new_network_key_index())
        self.networks[net_name].save()
        return self.networks[net_name]

    def new_node(self, node_name: str, net_name: str):
        if net_name not in list(self.networks.keys()):
            raise Exception('Net name unknown')
        node = Node(node_name, net_name, self._gen_new_unicast_address())
        self.nodes[node_name] = node
        # node.save()
        return node

    def _load_devices(self):
        with open(BLUEBEES_DIR_PATH + DEVICE_LIST_FILE_NAME + DEVICE_FILE_TYPE) as device_list_file_:
            device_list_ = json.load(device_list_file_)
            device_list_ = device_list_['device_list']
        for device in device_list_:
            self.devices[device] = Device.load(device)

    def _gen_new_network_key(self):
        key_size = 16
        key = randint(0, 2**(key_size*8))
        keys_allocated = (n.key for n in list(self.networks.values()))
        while key.to_bytes(key_size, 'big') in keys_allocated:
            key = randint(0, 2**(key_size*8))
        return key.to_bytes(key_size, 'big')

    def _gen_new_network_key_index(self):
        key_index_size = 2
        key_index = randint(0, 2 ** (key_index_size * 8))
        key_indexs_allocated = (n.index for n in list(self.networks.values()))
        while key_index.to_bytes(key_index_size, 'big') in key_indexs_allocated:
            key_index = randint(0, 2 ** (key_index_size * 8))
        return key_index.to_bytes(key_index_size, 'big')

    def _load_networks(self):
        with open(BLUEBEES_DIR_PATH + NET_LIST_FILE_NAME + NETWORK_FILE_TYPE) as net_list_file_:
            net_list_ = json.load(net_list_file_)
            net_list_ = net_list_['net_list']
        for net in net_list_:
            self.networks[net] = Network.load(net)

    def _gen_new_unicast_address(self):
        addr_size = 2
        addr = randint(0, 2 ** (addr_size * 8))
        addrs_allocated = (n.unicast_address for n in list(self.nodes.values()))
        while addr.to_bytes(addr_size, 'big') in addrs_allocated:
            addr = randint(0, 2 ** (addr_size * 8))
        return addr.to_bytes(addr_size, 'big')

    def _load_nodes(self):
        with open(BLUEBEES_DIR_PATH + NODE_LIST_FILE_NAME + NODE_FILE_TYPE) as node_list_file_:
            node_list_ = json.load(node_list_file_)
            node_list_ = node_list_['node_list']
        for node in node_list_:
            self.nodes[node] = Node.load(node)


mesh_manager = MeshManager()

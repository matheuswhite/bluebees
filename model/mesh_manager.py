from random import randint
from model.network import Network
from model.device import Device
from model.paths import *
import json


class MeshManager:

    def __init__(self):
        self.devices = {}
        self.networks = {}

        self._load_devices()
        self._load_networks()

    def new_device(self, dev_uuid: bytes):
        dev = Device(dev_uuid)
        self.devices[dev.name] = dev
        dev.save()
        return dev

    def new_network(self, net_name: str):
        self.networks[net_name] = Network(net_name, self._gen_new_network_key())
        self.networks[net_name].save()
        return self.networks[net_name]

    def _save_device(self, device_name: str):
        self.devices[device_name].save()

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

    def _save_network(self, net_name: str):
        self.networks[net_name].save()

    def _load_networks(self):
        with open(BLUEBEES_DIR_PATH + NET_LIST_FILE_NAME + NETWORK_FILE_TYPE) as net_list_file_:
            net_list_ = json.load(net_list_file_)
            net_list_ = net_list_['net_list']
        for net in net_list_:
            self.networks[net] = Network.load(net)


mesh_manager = MeshManager()

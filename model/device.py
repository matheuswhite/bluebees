from model.serializable import Serializable
from model.paths import *
import json


class Device(Serializable):

    def __init__(self, uuid: bytes):
        super().__init__()

        self.name = f'Device {uuid}'
        self.uuid = uuid

    def save(self):
        with open(BLUEBEES_DIR_PATH + f'{self.name}' + DEVICE_FILE_TYPE, 'w') as device_file:
            device_data = {
                'device_name': self.name,
                'uuid': bytes(self.uuid).hex(),
            }
            json.dump(device_data, device_file)
        with open(BLUEBEES_DIR_PATH + DEVICE_LIST_FILE_NAME + DEVICE_FILE_TYPE) as device_list_file_:
            device_list_ = json.load(device_list_file_)
        with open(BLUEBEES_DIR_PATH + DEVICE_LIST_FILE_NAME + DEVICE_FILE_TYPE, 'w') as device_list_file_:
            device_list_['device_list'].append(self.name)
            json.dump(device_list_, device_list_file_)

    @classmethod
    def load(cls, name: str):
        with open(BLUEBEES_DIR_PATH + f'{name}' + DEVICE_FILE_TYPE) as device_file:
            device_data = json.load(device_file)
            return cls(bytes.fromhex(device_data['uuid']))

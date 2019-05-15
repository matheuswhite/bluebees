from model.serializable import Serializable
from model.paths import *
import json


class Application(Serializable):

    def __init__(self, name: str, key: bytes, index: bytes):
        super().__init__()

        self.name = name
        self.key = key
        self.index = index

    def save(self):
        with open(BLUEBEES_DIR_PATH + f'{self.name}' + APPLICATION_FILE_TYPE, 'w') as app_file:
            app_data = {
                'app_name': self.name,
                'key': self.key.hex(),
                'index': self.index.hex(),
            }
            json.dump(app_data, app_file)
        with open(BLUEBEES_DIR_PATH + APPLICATION_LIST_FILE_NAME + APPLICATION_FILE_TYPE) as app_list_file_:
            app_list_ = json.load(app_list_file_)
        with open(BLUEBEES_DIR_PATH + APPLICATION_LIST_FILE_NAME + APPLICATION_FILE_TYPE, 'w') as app_list_file_:
            app_list_['application_list'].append(self.name)
            json.dump(app_list_, app_list_file_)

    @classmethod
    def load(cls, name: str):
        with open(BLUEBEES_DIR_PATH + f'{name}' + APPLICATION_FILE_TYPE) as app_file:
            app_data = json.load(app_file)
            return cls(app_data['app_name'], bytes.fromhex(app_data['key']), bytes.fromhex(app_data['index']))

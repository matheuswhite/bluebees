from dataclasses import dataclass
import json


@dataclass
class Device:
    name: str
    uuid: bytes

    def save(self, json_file):
        with open(json_file, 'w') as write_file:
            data = {
                'name': self.name,
                'uuid': self.uuid
            }
            json.dump(data, write_file)

    @classmethod
    def load(cls, json_file):
        with open(json_file, 'r') as read_file:
            data = json.load(read_file)
            dev = cls(data['name'], data['uuid'])
        return dev

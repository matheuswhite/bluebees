from dataclasses import dataclass
import json


@dataclass
class Net:
    name: str
    net_key: bytes

    def save(self, json_file):
        with open(json_file, 'w') as write_file:
            data = {
                'name': self.name,
                'net_key': self.net_key
            }
            json.dump(data, write_file)

    @classmethod
    def load(cls, json_file):
        with open(json_file, 'r') as read_file:
            data = json.load(read_file)
            net = cls(data['name'], data['net_key'])
        return net

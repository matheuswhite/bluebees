from dataclasses import dataclass
import json


@dataclass
class Node:
    name: str
    addr: bytes

    def save(self, json_file):
        with open(json_file, 'w') as write_file:
            data = {
                'name': self.name,
                'addr': self.addr
            }
            json.dump(data, write_file)

    @classmethod
    def load(cls, json_file):
        with open(json_file, 'r') as read_file:
            data = json.load(read_file)
            node = cls(data['name'], data['addr'])
        return node

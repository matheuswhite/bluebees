from dataclasses import dataclass
import json


@dataclass
class App:
    name: str
    app_key: bytes

    def save(self, json_file):
        with open(json_file, 'w') as write_file:
            data = {
                'name': self.name,
                'app_key': self.app_key
            }
            json.dump(data, write_file)

    @classmethod
    def load(cls, json_file):
        with open(json_file, 'r') as read_file:
            data = json.load(read_file)
            app = cls(data['name'], data['app_key'])
        return app

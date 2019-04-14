from random import randint


class Path:

    def __init__(self):
        self._complete_paths = {}
        self._base_path = {}

    def add(self, name: str, value):
        order = 0

        if name in self._base_path.keys():
            order = len(self._base_path[name])
            self._base_path[name].append(value)
        else:
            self._base_path[name] = [value]

        complete_path = f'{name}/{order}'
        self._complete_paths[complete_path] = value

        return order

    def get_values(self, base_path: str) -> list:
        return self._base_path[base_path]

    def get_val(self, complete_path: str):
        return self._complete_paths[complete_path]

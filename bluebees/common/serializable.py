from bluebees.common.file import file_helper
from dataclasses import asdict


class Serializable:

    def __init__(self, filename):
        self.filename = filename

    def save(self):
        file_helper.write(self.filename, asdict(self))

    @classmethod
    def load(cls, filename):
        return cls(**file_helper.read(filename))

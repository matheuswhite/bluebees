import os
import errno
from os import listdir
from os.path import isfile, join
import ruamel.yaml


class FileHelper:

    def __init__(self):
        self.yaml = ruamel.yaml.YAML()

    def read(self, filename):
        if not self.file_exist(filename):
            return {}

        with open(filename, 'r') as f:
            content = self.yaml.load(f)
        return content

    def list_files(self, dirpath):
        try:
            onlyfiles = [f for f in listdir(dirpath) if isfile(join(dirpath, f))]
            return onlyfiles
        except FileNotFoundError:
            return []

    def dir_exist(self, filename):
        dirname = os.path.dirname(filename)
        if dirname == '':
            return True
        else:
            return os.path.exists(dirname)

    def write(self, filename, content: dict):
        if not self.dir_exist(filename):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise Exception

        with open(filename, 'w') as f:
            self.yaml.dump(content, f)

    def file_exist(self, filename):
        return os.path.isfile(filename)

    def load(self, filename, default_content: dict):
        if self.file_exist(filename):
            return self.read(filename)
        else:
            self.write(filename, default_content)
            return self.read(filename)


file_helper = FileHelper()

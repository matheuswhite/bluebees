import os
import errno
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


class FileHelper:

    def __init__(self):
        pass

    def read(self, filename):
        if not self.file_exist(filename):
            print(f'File {filename} not found')
            return {}

        with open(filename, 'r') as f:
            content = ''.join(f.readlines())
        return yaml.load(content, Loader=Loader)

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
                    raise

        with open(filename, 'w') as f:
            stream = yaml.dump(content, Dumper=Dumper,
                               default_flow_style=False)
            f.write(stream)
            f.close()

    def file_exist(self, filename):
        return os.path.isfile(filename)

    def load(self, filename, default_content: dict):
        if self.file_exist(filename):
            return self.read(filename)
        else:
            self.write(filename, default_content)
            return self.read(filename)


file_helper = FileHelper()

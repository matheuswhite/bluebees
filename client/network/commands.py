from common.command import Command
from clint.textui import colored
from client.network.network_data import NetworkData
from common.file import file_helper
from random import randint
from client.data_paths import base_dir, net_dir


class NewCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py net new <-n|--name> [FLAGS]...

Flags:
  -n, --name <Network name>\tSpecify the name of network. This flag is mandatory
  -k, --key  <Network key> \tSpecify the key of network. This flag is not mandatory
  -h, --help               \tShow the help message'''

    def _net_name_exist(self, name: str) -> bool:
        filenames = file_helper.list_files(base_dir + net_dir)
        if not filenames:
            return False

        # remove file extension
        filenames_fmt = []
        for file in filenames:
            filenames_fmt.append(file[:-4])

        return name in filenames_fmt

    def _net_key_exist(self, key: bytes) -> bool:
        return key in self._net_key_list()

    def _net_key_list(self) -> list:
        filenames = file_helper.list_files(base_dir + net_dir)
        if not filenames:
            return []

        netkeys = []
        for file in filenames:
            net = NetworkData.load(base_dir + net_dir + file)
            netkeys.append(net.key)
        return netkeys

    def _generate_net_key(self) -> bytes:
        net_keys = self._net_key_list()

        key = randint(0, 2**128)
        for x in range(2**128):
            key = randint(0, 2**128)
            if key not in net_keys:
                return key.to_bytes(16, 'big')

        return None

    def _str2bytes(self, key: bytes) -> str:
        try:
            key_str = bytes.fromhex(key)
            return key_str
        except ValueError:
            return None

    def digest(self, flags, flags_values):
        name = None
        key = None

        for x in range(len(flags)):
            f = flags[x]
            fv = flags_values[x]
            if f == '-h' or f == '--help':
                print(self._help)
                return
            elif f == '-n' or f == '--name':
                name = fv
            elif f == '-k' or f == '--key':
                key = fv
            else:
                print(colored.red(f'Invalid flag {f}'))
                print(self._help)
                return

        # name processing
        if name is None:
            print(colored.red('Name is required'))
            return

        if self._net_name_exist(name):
            print(colored.red(f'The network name "{name}" already exist'))
            return

        # key handling
        if key is None:
            key = self._generate_net_key()
            if key is None:
                print(colored.red('The maxium number of network keys has '
                                  'already reached'))
                return
        else:
            key = self._str2bytes(key)
            if key is None:
                print(colored.red('Invalid key. Please enter with a string '
                                  'of hexadecimal digits'))
                return
            if self._net_key_exist(key):
                print(colored.red(f'The network key "{key.hex()}" already exist'))
                return

        net_data = NetworkData(name=name, key=key,
                               key_index=len(self._net_key_list()),
                               iv_index=0x0000_0000)
        net_data.save()

        print(colored.green('A new network was created.'))
        print(colored.green(net_data))


class ListCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py net list [FLAGS]...

Flags:
  -h, --help\tShow the help message'''

    def digest(self, flags, flags_values):

        for x in range(len(flags)):
            f = flags[x]
            if f == '-h' or f == '--help':
                print(self._help)
                return
            else:
                print(colored.red(f'Invalid flag {f}'))
                print(self._help)
                return

        print(colored.green('Listing networks...'))


class InfoCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py net info [FLAGS]...

Flags:
  -h, --help\tShow the help message
  -n, --name\tThe name of network'''

    def digest(self, flags, flags_values):

        for x in range(len(flags)):
            f = flags[x]
            fv = flags_values[x]
            if f == '-h' or f == '--help':
                print(self._help)
                return
            if f == '-n' or f == '--name':
                print(colored.green(f'Info about {fv} network'))
                return
            else:
                print(colored.red(f'Invalid flag {f}'))
                print(self._help)
                return

        print(colored.red('No network selected. Impossible obtain info...'))

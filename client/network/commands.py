from common.command import Command
from clint.textui import colored
from client.network.network_data import NetworkData
from common.file import file_helper
from common.template import template_helper
from random import randint
from client.data_paths import base_dir, net_dir


class NewCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py net new <-n|--name> [FLAGS]...

Flags:
  -n, --name <Network name>\tSpecify the name of network. This flag is mandatory
  -t, --template <filename>\tSpecify a template file. This template file can contain the keyworks:
                           \t  * name (The name of the network)
                           \t  * key  (The key of the network)
                           \tThis template file must contain the "name" keyword.
                           \tIf this flag is active, then the flag "-n|--name" is not mandatory
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

    def _net_key_index_list(self) -> list:
        filenames = file_helper.list_files(base_dir + net_dir)
        if not filenames:
            return []

        net_key_indexes = []
        for file in filenames:
            net = NetworkData.load(base_dir + net_dir + file)
            net_key_indexes.append(net.key)
        return net_key_indexes

    def _net_key_list(self) -> list:
        filenames = file_helper.list_files(base_dir + net_dir)
        if not filenames:
            return []

        netkeys = []
        for file in filenames:
            net = NetworkData.load(base_dir + net_dir + file)
            netkeys.append(net.key)
        return netkeys

    def _generate_key_index(self) -> bytes:
        net_key_indexes = self._net_key_index_list()

        key_index = randint(0, 2**12)
        for x in range(2**12):
            key_index = randint(0, 2**12)
            if key_index not in net_key_indexes:
                return key_index.to_bytes(2, 'big')

        return None

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

    def _parse_template(self, filename) -> (bytes, bytes):
        template = file_helper.read(filename)
        if not template:
            return None, None

        try:
            name = template_helper.get_field(template, 'name')
        except Exception:
            return None, b''

        try:
            key = template_helper.get_field(template, 'key')
            if len(key) != 32:
                return name, len(key)
        except Exception:
            key = None

        return name, key

    def digest(self, flags, flags_values):
        name = None
        key = None

        for x in range(len(flags)):
            f = flags[x]
            fv = flags_values[x]
            if f == '-h' or f == '--help':
                print(self._help)
                return
            elif f == '-t' or f == '--template':
                if fv is None:
                    print(colored.red('Template filename is required'))
                    return
                name, key = self._parse_template(fv)
                if name is None and key is None:
                    print(colored.red(f'File "{fv}" not found'))
                    return
                elif name is None:
                    print(colored.red(f'Field "name" not found in template '
                                      f'file "{fv}"'))
                    return
                elif type(key) is int:
                    print(colored.red(f'The length of key must be 16. The '
                                      f'actual length is {key}'))
                    return
                else:
                    break
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
                print(colored.red(f'The network key "{key.hex()}" already '
                                  f'exist'))
                return

        # generate key index
        key_index = self._generate_key_index()
        if key_index is None:
            print(colored.red('The maxium number of network keys index has '
                              'already reached'))
            return

        net_data = NetworkData(name=name, key=key,
                               key_index=key_index,
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

    def _net_name_list(self) -> list:
        filenames = file_helper.list_files(base_dir + net_dir)
        if not filenames:
            return []

        netnames = []
        for file in filenames:
            netnames.append(file[:-4])
        return netnames

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

        net_names = self._net_name_list()
        if not net_names:
            print()
            return

        print(colored.cyan('Networks created:'))
        for i, name in enumerate(net_names):
            print(colored.cyan(f'{i}. {name}'))


class InfoCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py net info [FLAGS]...

Flags:
  -n, --name\tSpecify the name of network. This flag is mandatory
  -h, --help\tShow the help message'''

    def _net_name_exist(self, name: str) -> bool:
        filenames = file_helper.list_files(base_dir + net_dir)
        if not filenames:
            return False

        # remove file extension
        filenames_fmt = []
        for file in filenames:
            filenames_fmt.append(file[:-4])

        return name in filenames_fmt

    def digest(self, flags, flags_values):
        name = None

        for x in range(len(flags)):
            f = flags[x]
            fv = flags_values[x]
            if f == '-h' or f == '--help':
                print(self._help)
                return
            if f == '-n' or f == '--name':
                name = fv
                break
            else:
                print(colored.red(f'Invalid flag {f}'))
                print(self._help)
                return

        if name is None:
            print(colored.red('No network selected. Please specify network '
                              'name'))

        if not self._net_name_exist(name):
            print(colored.red('This network not exist'))

        net_data = NetworkData.load(base_dir + net_dir + name + '.yml')

        print(colored.cyan('***** Network data *****'))
        print(colored.cyan(net_data))

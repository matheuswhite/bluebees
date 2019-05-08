from common.command import Command
from clint.textui import colored
from client.application.application_data import ApplicationData
from common.file import file_helper
from common.template import template_helper
from random import randint
from client.data_paths import base_dir, net_dir, app_dir


class NewCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py app new <-n|--name> <-w|--network> [FLAGS]...

Flags:
  -n, --name <Application name>\tSpecify the name of application. This flag is mandatory
  -w, --network <Network name> \tSpecify the name of network. This flag is mandatory
  -t, --template <filename>    \tSpecify a template file. This template file can contain the keyworks:
                               \t  * name    (The name of the application)
                               \t  * network (The name of the network)
                               \t  * key     (The key of the application)
                               \tThis template file must contain the "name" and the "network" keywords.
                               \tIf this flag is active, then the flags "-n|--name" and "-w|--network" is not mandatory
  -k, --key  <Network key>     \tSpecify the key of application. This flag is not mandatory
  -h, --help                   \tShow the help message'''

    def _app_name_exist(self, name: str) -> bool:
        filenames = file_helper.list_files(base_dir + app_dir)
        if not filenames:
            return False

        # remove file extension
        filenames_fmt = []
        for file in filenames:
            filenames_fmt.append(file[:-4])

        return name in filenames_fmt

    def _net_name_exist(self, name: str) -> bool:
        filenames = file_helper.list_files(base_dir + net_dir)
        if not filenames:
            return False

        # remove file extension
        filenames_fmt = []
        for file in filenames:
            filenames_fmt.append(file[:-4])

        return name in filenames_fmt

    def _app_key_exist(self, key: bytes) -> bool:
        return key in self._app_key_list()

    def _app_key_index_list(self) -> list:
        filenames = file_helper.list_files(base_dir + app_dir)
        if not filenames:
            return []

        app_key_indexes = []
        for file in filenames:
            app = ApplicationData.load(base_dir + app_dir + file)
            app_key_indexes.append(app.key)
        return app_key_indexes

    def _app_key_list(self) -> list:
        filenames = file_helper.list_files(base_dir + app_dir)
        if not filenames:
            return []

        appkeys = []
        for file in filenames:
            app = ApplicationData.load(base_dir + app_dir + file)
            appkeys.append(app.key)
        return appkeys

    def _generate_key_index(self) -> bytes:
        app_key_indexes = self._app_key_index_list()

        key_index = randint(0, 2**12)
        for x in range(2**12):
            key_index = randint(0, 2**12)
            if key_index not in app_key_indexes:
                return key_index.to_bytes(2, 'big')

        return None

    def _generate_app_key(self) -> bytes:
        app_keys = self._app_key_list()

        key = randint(0, 2**128)
        for x in range(2**128):
            key = randint(0, 2**128)
            if key not in app_keys:
                return key.to_bytes(16, 'big')

        return None

    def _str2bytes(self, key: bytes) -> str:
        try:
            key_str = bytes.fromhex(key)
            return key_str
        except ValueError:
            return None

    def _parse_template(self, filename) -> (str, str, bytes):
        template = file_helper.read(filename)
        if not template:
            return None, None, None

        try:
            name = template_helper.get_field(template, 'name')
        except Exception:
            return None, None, b''

        try:
            network = template_helper.get_field(template, 'network')
        except Exception:
            return name, None, b''

        try:
            key = template_helper.get_field(template, 'key')
            if len(key) != 32:
                return name, network, len(key)
        except Exception:
            key = None

        return name, network, key

    def digest(self, flags, flags_values):
        name = None
        key = None
        network = None

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
                name, network, key = self._parse_template(fv)
                if name is None and network is None and key is None:
                    print(colored.red(f'File "{fv}" not found'))
                    return
                elif name is None:
                    print(colored.red(f'Field "name" not found in template '
                                      f'file "{fv}"'))
                    return
                elif network is None:
                    print(colored.red(f'Field "network" not found in template '
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
            elif f == '-w' or f == '--network':
                network = fv
            else:
                print(colored.red(f'Invalid flag {f}'))
                print(self._help)
                return

        # name processing
        if name is None:
            print(colored.red('Name is required'))
            return

        if self._app_name_exist(name):
            print(colored.red(f'The application name "{name}" already exist'))
            return

        # network processing
        if network is None:
            print(colored.red('Network name is required'))
            return

        if not self._net_name_exist(network):
            print(colored.red(f'The network name "{network}" not exist'))
            return

        # key processing
        if key is None:
            key = self._generate_app_key()
            if key is None:
                print(colored.red('The maxium number of application keys has '
                                  'already reached'))
                return
        else:
            key = self._str2bytes(key)
            if key is None:
                print(colored.red('Invalid key. Please enter with a string '
                                  'of hexadecimal digits'))
                return
            if self._app_key_exist(key):
                print(colored.red(f'The application key "{key.hex()}" already '
                                  f'exist'))
                return

        # generate key index
        key_index = self._generate_key_index()
        if key_index is None:
            print(colored.red('The maxium number of application keys index '
                              'has already reached'))
            return

        app_data = ApplicationData(name=name, network=network, key=key,
                                   key_index=key_index)
        app_data.save()

        print(colored.green('A new application was created.'))
        print(colored.green(app_data))


class ListCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py app list [FLAGS]...

Flags:
  -h, --help\tShow the help message'''

    def _app_name_list(self) -> list:
        filenames = file_helper.list_files(base_dir + app_dir)
        if not filenames:
            return []

        appnames = []
        for file in filenames:
            appnames.append(file[:-4])
        return appnames

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

        app_names = self._app_name_list()
        if not app_names:
            print('No application created')
            return

        print(colored.cyan('Applications created:'))
        for i, name in enumerate(app_names):
            print(colored.cyan(f'{i}. {name}'))


class InfoCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py app info <-n|--name> [FLAGS]...

Flags:
  -n, --name\tSpecify the name of application. This flag is mandatory
  -h, --help\tShow the help message'''

    def _app_name_exist(self, name: str) -> bool:
        filenames = file_helper.list_files(base_dir + app_dir)
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
            print(colored.red('No application selected. Please specify '
                              'application name'))
            return

        if not self._app_name_exist(name):
            print(colored.red('This application not exist'))
            return

        app_data = ApplicationData.load(base_dir + app_dir + name + '.yml')

        print(colored.cyan('***** Application data *****'))
        print(colored.cyan(app_data))

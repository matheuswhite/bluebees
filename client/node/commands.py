from common.command import Command
from clint.textui import colored
from client.node.node_data import NodeData
from client.network.network_data import NetworkData
from common.file import file_helper
from common.template import template_helper
from common.utils import FinishAsync
from random import randint
from client.node.provisioner import Provisioner, LinkOpenError, \
                                    ProvisioningSuccess, ProvisioningError
from client.data_paths import base_dir, node_dir, net_dir
import asyncio


class NewCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py node new <-n|--name> <-w|--network> <-i|--uuid> [FLAGS]...

Flags:
  -n, --name <Node name>      \tSpecify the name of node. This flag is mandatory
  -w, --network <Network name>\tSpecify the name of network. This flag is mandatory
  -i, --uuid <Device UUID>    \tSpecify the UUID of target device. This flag is mandatory.
  -t, --template <filename>   \tSpecify a template file. This template file can contain the keyworks:
                              \t  * name    (The name of the node)
                              \t  * network (The network name)
                              \t  * uuid    (The UUID of target device)
                              \t  * addr    (The address of the node)
                              \tThis template file must contain: "name", "network" and "uuid" keyword.
                              \tIf this flag is active, then the flags "-n|--name", "-w|--network" and "-i|--uuid" is not mandatory
  -a, --address <Node addr>   \tSpecify the address of node. This flag is not mandatory
  -h, --help                  \tShow the help message'''

    def _node_name_exist(self, name: str) -> bool:
        filenames = file_helper.list_files(base_dir + node_dir)
        if not filenames:
            return False

        # remove file extension
        filenames_fmt = []
        for file in filenames:
            filenames_fmt.append(file[:-4])

        return name in filenames_fmt

    def _node_network_exist(self, network: str) -> bool:
        filenames = file_helper.list_files(base_dir + net_dir)
        if not filenames:
            return False

        net_names = []
        for file in filenames:
            net = NetworkData.load(base_dir + net_dir + file)
            net_names.append(net.name)

        return network in net_names

    def _node_addr_exist(self, addr: bytes) -> bool:
        return addr in self._node_addr_list()

    def _node_addr_list(self) -> list:
        filenames = file_helper.list_files(base_dir + node_dir)
        if not filenames:
            return []

        nodeaddrs = []
        for file in filenames:
            node = NodeData.load(base_dir + node_dir + file)
            nodeaddrs.append(node.addr)
        return nodeaddrs

    def _generate_node_addr(self) -> bytes:
        node_addrs = self._node_addr_list()

        addr = randint(0, 2**16)
        for x in range(2**16):
            addr = randint(0, 2**16)
            if addr not in node_addrs:
                return addr.to_bytes(2, 'big')

        return None

    def _str2bytes(self, addr: str) -> bytes:
        try:
            addr_b = bytes.fromhex(addr)
            return addr_b
        except ValueError:
            return None

    def _add_trailing_zeros(self, uuid: bytes) -> bytes:
        if len(uuid) >= 16:
            return uuid[-16:]
        else:
            zeros = bytes(16 - len(uuid))
            return uuid + zeros

    def _parse_template(self, filename) -> dict:
        opts = {'name': None, 'net': None, 'uuid': None, 'addr': None,
                'no_file': False}

        template = file_helper.read(filename)
        if not template:
            opts['no_file'] = True
            return opts

        try:
            opts['name'] = template_helper.get_field(template, 'name')
        except Exception:
            opts['name'] = None

        try:
            opts['net'] = template_helper.get_field(template, 'network')
        except Exception:
            opts['net'] = None

        try:
            opts['uuid'] = template_helper.get_field(template, 'uuid')
        except Exception:
            opts['uuid'] = None

        try:
            opts['addr'] = template_helper.get_field(template, 'address')
            if len(opts['addr']) != 4:
                opts['addr'] = opts['addr']
        except Exception:
            opts['addr'] = None

        return opts

    def _provisioning_device(self, device_uuid: bytes, network: str,
                             addr: bytes):
        print(colored.cyan(f'Provisioning device "{device_uuid}" to network '
                           f'"{network}"'))
        success = False
        net_data = NetworkData.load(base_dir + net_dir + network + '.yml')

        try:
            loop = asyncio.get_event_loop()
            prov = Provisioner(loop, device_uuid, net_data.key,
                               net_data.key_index, net_data.iv_index, addr)
            asyncio.gather(prov.spwan_tasks(loop))
            loop.run_forever()
        except Exception as e:
            print(f'Unknown error\n{e}')
        except LinkOpenError:
            prov.disconnect()
        except ProvisioningError:
            prov.disconnect()
        except ProvisioningSuccess:
            success = True
            prov.disconnect()
        except KeyboardInterrupt:
            print(colored.yellow('Interruption by user'))
            prov.disconnect()
        except RuntimeError:
            print('Runtime error')
        finally:
            tasks_running = asyncio.Task.all_tasks()
            for t in tasks_running:
                t.cancel()
            loop.stop()

        return success

    def digest(self, flags, flags_values):
        opts = {'name': None, 'net': None, 'uuid': None, 'addr': None}

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
                opts = self._parse_template(fv)
                if opts['no_file']:
                    print(colored.red(f'File "{fv}" not found'))
                    return
                elif opts['net'] is None:
                    print(colored.red(f'Field "network" not found in template '
                                      f'file "{fv}"'))
                    return
                elif opts['uuid'] is None:
                    print(colored.red(f'Field "uuid" not found in template '
                                      f'file "{fv}"'))
                    return
                elif opts['name'] is None:
                    print(colored.red(f'Field "name" not found in template '
                                      f'file "{fv}"'))
                    return
                elif type(opts['addr']) is int:
                    print(colored.red(f'The length of address must be . The '
                                      f'actual length is {opts["addr"]}'))
                    return
                else:
                    break
            elif f == '-n' or f == '--name':
                opts['name'] = fv
            elif f == '-a' or f == '--address':
                opts['addr'] = fv
            elif f == '-w' or f == '--network':
                opts['net'] = fv
            elif f == '-i' or f == '--uuid':
                opts['uuid'] = fv
            else:
                print(colored.red(f'Invalid flag {f}'))
                print(self._help)
                return

        # name processing
        if opts['name'] is None:
            print(colored.red('Name is required'))
            return

        if self._node_name_exist(opts['name']):
            print(colored.red(f'The node name "{opts["name"]}" already exist'))
            return

        # network processing
        if opts['net'] is None:
            print(colored.red('Network is required'))
            return

        if not self._node_network_exist(opts['net']):
            print(colored.red(f'The network "{opts["net"]}" not exist'))
            return

        # uuid processing
        if opts['uuid'] is None:
            print(colored.red('Device UUID is required'))
            return

        opts['uuid'] = self._str2bytes(opts['uuid'])
        if opts['uuid'] is None:
            print(colored.red('Invalid device UUID. Please enter with a '
                              'string of hexadecimal digits'))
            return

        opts['uuid'] = self._add_trailing_zeros(opts['uuid'])

        # addr processing
        if opts['addr'] is None:
            opts['addr'] = self._generate_node_addr()
            if opts['addr'] is None:
                print(colored.red('The maxium number of node address has '
                                  'already reached'))
                return
        else:
            opts['addr'] = self._str2bytes(opts['addr'])
            if opts['addr'] is None:
                print(colored.red('Invalid address. Please enter with a '
                                  'string of hexadecimal digits'))
                return
            if self._node_addr_exist(opts['addr']):
                print(colored.red(f'The node address "{opts["addr"].hex()}" '
                                  f'already exist'))
                return

        # provisioning device
        success = self._provisioning_device(opts['uuid'], opts['net'],
                                            opts['addr'])
        if not success:
            print(colored.red(f'Error in provisioning'))
            return

        node_data = NodeData(name=opts['name'], addr=opts['addr'],
                             network=opts['net'], device_uuid=opts['uuid'],
                             ecdh_secret=bytes(32))
        node_data.save()

        print(colored.green('A new node was created.'))
        print(colored.green(node_data))


class ListCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py node list [FLAGS]...

Flags:
  -h, --help\tShow the help message'''

    def _node_name_list(self) -> list:
        filenames = file_helper.list_files(base_dir + node_dir)
        if not filenames:
            return []

        filenames_fmt = []
        for file in filenames:
            filenames_fmt.append(file[:-4])

        return filenames_fmt

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

        node_names = self._node_name_list()
        if not node_names:
            print(colored.yellow('No node created'))
            return

        print(colored.cyan('Nodes created:'))
        for i, name in enumerate(node_names):
            print(colored.cyan(f'{i}. {name}'))


class InfoCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py node info <-n|--name> [FLAGS]...

Flags:
  -n, --name\tSpecify the name of node. This flag is mandatory
  -h, --help\tShow the help message'''

    def _node_name_exist(self, name: str) -> bool:
        filenames = file_helper.list_files(base_dir + node_dir)
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
            print(colored.red('No node selected. Please specify node name'))
            return

        if not self._node_name_exist(name):
            print(colored.red('This node not exist'))
            return

        node_data = NodeData.load(base_dir + node_dir + name + '.yml')

        print(colored.cyan('***** Node data *****'))
        print(colored.cyan(node_data))


class SendCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py node send <-t|--target> <-o|--opcode> <-p|--parameters> [FLAGS]...

Flags:
  -t, --target    \tSpecify the name of node target. This flag is mandatory
  -o, --opcode    \tSpecify the opcode of message. This flag is mandatory
  -p, --parameters\tSpecify the parameters of message. This flag is mandatory
  -h, --help      \tShow the help message'''

    def _node_name_exist(self, name: str) -> bool:
        filenames = file_helper.list_files(base_dir + node_dir)
        if not filenames:
            return False

        # remove file extension
        filenames_fmt = []
        for file in filenames:
            filenames_fmt.append(file[:-4])

        return name in filenames_fmt

    def _str2bytes(self, data: str) -> bytes:
        try:
            data_b = bytes.fromhex(data)
            return data_b
        except ValueError:
            return None

    # ! Fake implementation
    def _send_message(self, target_node: str, opcode: bytes,
                      parameters: bytes):
        print(colored.green(f'Message [{opcode}, {parameters}] was sent to '
                            f'"{target_node}" node'))

    def digest(self, flags, flags_values):
        target = None
        opcode = None
        parameters = None

        for x in range(len(flags)):
            f = flags[x]
            fv = flags_values[x]
            if f == '-h' or f == '--help':
                print(self._help)
                return
            if f == '-t' or f == '--target':
                target = fv
            elif f == '-o' or f == '--opcode':
                opcode = fv
            elif f == '-p' or f == '--parameters':
                parameters = fv
            else:
                print(colored.red(f'Invalid flag {f}'))
                print(self._help)
                return

        # target processing
        if target is None:
            print(colored.red('Target name is required'))
            return

        if not self._node_name_exist(target):
            print(colored.red('This node not exist'))
            return

        # opcode processing
        if opcode is None:
            print(colored.red('Opcode is required'))
            return

        if len(opcode) not in [2, 4, 6]:
            print(colored.red(f'Invalid opcode length. The length of opcode '
                              f'must be 1, 2 or 3 bytes. The current length '
                              f'is {int(len(opcode)/2)}'))
            return

        opcode = self._str2bytes(opcode)
        if opcode is None:
            print(colored.red('Invalid Opcode. Please enter with a '
                              'string of hexadecimal digits'))
            return

        # parameters processing
        if parameters is None:
            print(colored.red('Parameters is required'))
            return

        if len(parameters) >= 380*2:
            print(colored.red(f'Invalid parameters length. The length of '
                              f'parameters must be less than 380. The '
                              f'current length is {int(len(parameters)/2)}'))
            return

        parameters = self._str2bytes(parameters)
        if parameters is None:
            print(colored.red('Invalid Parameters. Please enter with a '
                              'string of hexadecimal digits'))
            return

        self._send_message(target, opcode, parameters)


class ReqCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py node req <-t|--target> <-o|--opcode> <-p|--parameters> [FLAGS]...

Flags:
  -t, --target    \tSpecify the name of node target. This flag is mandatory
  -o, --opcode    \tSpecify the opcode of message. This flag is mandatory
  -p, --parameters\tSpecify the parameters of message. This flag is mandatory
  -h, --help      \tShow the help message'''

    def _node_name_exist(self, name: str) -> bool:
        filenames = file_helper.list_files(base_dir + node_dir)
        if not filenames:
            return False

        # remove file extension
        filenames_fmt = []
        for file in filenames:
            filenames_fmt.append(file[:-4])

        return name in filenames_fmt

    def _str2bytes(self, data: str) -> bytes:
        try:
            data_b = bytes.fromhex(data)
            return data_b
        except ValueError:
            return None

    # ! Fake implementation
    async def _request_message(self, target_node: str, opcode: bytes,
                               parameters: bytes):
        print(colored.green(f'Message [{opcode}, {parameters}] was sent to '
                            f'"{target_node}" node'))
        for x in range(3):
            print(colored.cyan(f'Waiting response...'))
            await asyncio.sleep(1)

        print(colored.green(f'Response received!'))

    def digest(self, flags, flags_values):
        target = None
        opcode = None
        parameters = None

        for x in range(len(flags)):
            f = flags[x]
            fv = flags_values[x]
            if f == '-h' or f == '--help':
                print(self._help)
                return
            if f == '-t' or f == '--target':
                target = fv
            elif f == '-o' or f == '--opcode':
                opcode = fv
            elif f == '-p' or f == '--parameters':
                parameters = fv
            else:
                print(colored.red(f'Invalid flag {f}'))
                print(self._help)
                return

        # target processing
        if target is None:
            print(colored.red('Target name is required'))
            return

        if not self._node_name_exist(target):
            print(colored.red('This node not exist'))
            return

        # opcode processing
        if opcode is None:
            print(colored.red('Opcode is required'))
            return

        if len(opcode) not in [2, 4, 6]:
            print(colored.red(f'Invalid opcode length. The length of opcode '
                              f'must be 1, 2 or 3 bytes. The current length '
                              f'is {int(len(opcode)/2)}'))
            return

        opcode = self._str2bytes(opcode)
        if opcode is None:
            print(colored.red('Invalid Opcode. Please enter with a '
                              'string of hexadecimal digits'))
            return

        # parameters processing
        if parameters is None:
            print(colored.red('Parameters is required'))
            return

        if len(parameters) >= 380*2:
            print(colored.red(f'Invalid parameters length. The length of '
                              f'parameters must be less than 380. The '
                              f'current length is {int(len(parameters)/2)}'))
            return

        parameters = self._str2bytes(parameters)
        if parameters is None:
            print(colored.red('Invalid Parameters. Please enter with a '
                              'string of hexadecimal digits'))
            return

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._request_message(target, opcode,
                                                      parameters))


class ConfigCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py node config <-n|--name> <-c|--config> [FLAGS]...

Flags:
  -n, --name  \tSpecify the name of node. This flag is mandatory
  -c, --config\tSpecify the config file. This config file must contain the keywords:
              \t  * applications (A list of applications to bind to node)
              \t  * models       (A list of models options)
              \t    - index       (The index of model in that node)
              \t    - publish     (The publish address of model)
              \t    - subscribe   (The subscribe address of model)
              \t    - application (The application to bind to model)
              \tThis flag is mandatory
  -h, --help  \tShow the help message'''

    def _node_name_exist(self, name: str) -> bool:
        filenames = file_helper.list_files(base_dir + node_dir)
        if not filenames:
            return False

        # remove file extension
        filenames_fmt = []
        for file in filenames:
            filenames_fmt.append(file[:-4])

        return name in filenames_fmt

    def _parse_config(self, config_file: str) -> dict:
        cfg = {'applications': [], 'models': []}

        template = file_helper.read(config_file)
        if not template:
            return {}

        try:
            cfg['applications'] = template_helper.get_field(template,
                                                            'applications')
        except Exception:
            cfg['applications'] = []

        try:
            cfg['models'] = template_helper.get_field(template, 'models')
        except Exception:
            cfg['models'] = []

        return cfg

    # ! Fake implementation
    async def _config_node(self, name: str, config: dict):
        # TODO: check if application exist

        print(colored.green(f'Configuration sent to "{name}" node'))
        print(colored.cyan(f'Check configuration in "{name}" node...'))

        total_len = len(config['applications']) + len(config['models'])
        for x in range(total_len):
            print(colored.cyan(f'Config {x+1}/{total_len} is OK'))
            await asyncio.sleep(1)

        print(colored.green(f'Configuration done!'))

    def digest(self, flags, flags_values):
        name = None
        config = None

        for x in range(len(flags)):
            f = flags[x]
            fv = flags_values[x]
            if f == '-h' or f == '--help':
                print(self._help)
                return
            if f == '-n' or f == '--name':
                name = fv
            elif f == '-c' or f == '--config':
                config = fv
            else:
                print(colored.red(f'Invalid flag {f}'))
                print(self._help)
                return

        # name processing
        if name is None:
            print(colored.red('Node name is required'))
            return

        if not self._node_name_exist(name):
            print(colored.red('This node not exist'))
            return

        # config processing
        if config is None:
            print(colored.red('Config file is required'))
            return

        config = self._parse_config(config)
        if not config:
            print(colored.yellow('Nothing to configure. Abort command'))
            return

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._config_node(name, config))

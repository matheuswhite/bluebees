from common.command import Command
from clint.textui import colored
from client.node.node_data import NodeData
from client.network.network_data import NetworkData
from common.file import file_helper
from common.template import template_helper
from client.mesh_layers.mesh_context import SoftContext
from client.mesh_layers.element import Element
from random import randint
from client.node.provisioner import Provisioner, LinkOpenError, \
                                    ProvisioningSuccess, ProvisioningError
from client.data_paths import base_dir, node_dir, net_dir
import asyncio


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

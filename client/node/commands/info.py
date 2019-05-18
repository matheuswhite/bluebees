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
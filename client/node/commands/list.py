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

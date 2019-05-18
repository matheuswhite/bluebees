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

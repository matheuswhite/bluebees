from common.module import Module
from common.utils import check_flag
from clint.textui import colored
from client.core.commands import RunCommand


class Core(Module):

    def __init__(self):
        super().__init__('core')
        self._help = '''Usage:
  python bluebees.py core [FLAGS]...
  python bluebees.py core <COMMAND> [ARGS]...

Flags:
  -h, --help\tShow the help message

Commands:
  run\t\tRun the main features of bluebees. This features are:
     \t\t  - Dongle Communication
     \t\t  - Mesh Network Layer
     \t\t  - Internal Broker
     \t\tFor more information about this features see <link>'''
        self._cmds = {
            'run': RunCommand()
        }

    def _digest_non_cmd(self, flags, flags_values):
        if check_flag(('-h', '--help'), flags):
            print(self.help)
        else:
            print(colored.red(f'Invalid flags {flags}'))
            print(self.help)
            return


core = Core()

from common.module import Module
from common.utils import check_flag
from clint.textui import colored
from client.network.commands import NewCommand, ListCommand, InfoCommand


class Network(Module):

    def __init__(self):
        super().__init__('net')
        self._help = '''Usage:
  python bluebees.py net [FLAGS]...
  python bluebees.py net <COMMAND> [ARGS]...

Flags:
  -h, --help\tShow the help message

Commands:
  new \t\tCreate a new network
  list\t\tList the networks created
  info\t\tGet description about a network'''
        self._cmds = {
            'new': NewCommand(),
            'list': ListCommand(),
            'info': InfoCommand()
        }

    def _digest_non_cmd(self, flags, flags_values):
        if check_flag(('-h', '--help'), flags):
            print(self.help)
        else:
            print(colored.red(f'Invalid flags {flags}'))
            print(self.help)
            return


network = Network()

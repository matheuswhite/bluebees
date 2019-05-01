from common.module import Module
from common.utils import check_flag
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
            print(f'Call {self} with flags {flags}')


network = Network()

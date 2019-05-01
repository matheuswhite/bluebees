from common.module import Module
from common.utils import check_flag
from client.node.commands import NewCommand, ListCommand, InfoCommand


class Node(Module):

    def __init__(self):
        super().__init__('node')
        self._help = '''Usage:
  python bluebees.py node [FLAGS]...
  python bluebees.py node <COMMAND> [ARGS]...

Flags:
  -h, --help\tShow the help message

Commands:
  new \t\tCreate a new node
  list\t\tList the nodes created
  info\t\tGet description about a node'''
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


node = Node()

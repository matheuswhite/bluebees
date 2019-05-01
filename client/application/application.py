from common.module import Module
from common.utils import check_flag
from client.application.commands import NewCommand, ListCommand, InfoCommand, \
                                        AttachCommand


class Application(Module):

    def __init__(self):
        super().__init__('app')
        self._help = '''Usage:
  python bluebees.py app [FLAGS]...
  python bluebees.py app <COMMAND> [ARGS]...

Flags:
  -h, --help\tShow the help message

Commands:
  new   \tCreate a new application
  attach\tAttach an application to a node
  list  \tList the applications created
  info  \tGet description about a application'''
        self._cmds = {
            'new': NewCommand(),
            'attach': AttachCommand(),
            'list': ListCommand(),
            'info': InfoCommand()
        }

    def _digest_non_cmd(self, flags, flags_values):
        if check_flag(('-h', '--help'), flags):
            print(self.help)
        else:
            print(f'Call {self} with flags {flags}')


application = Application()

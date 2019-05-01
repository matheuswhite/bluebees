from common.command import Command
from clint.textui import colored


class NewCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py app new [FLAGS]...

Flags:
  -h, --help\tShow the help message'''

    def digest(self, flags, flags_values):

        for x in range(len(flags)):
            f = flags[x]
            if f == '-h' or f == '--help':
                print(self._help)
                return

        print(colored.green('Creating new application...'))


class AttachCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py app attach [FLAGS]...

Flags:
  -h, --help\tShow the help message
  -a, --app \tthe application name that will be attach to a node
  -n, --node\tThe node name that will attached to a application'''

    def digest(self, flags, flags_values):
        app = None
        node = None

        for x in range(len(flags)):
            f = flags[x]
            fv = flags_values[x]
            if f == '-h' or f == '--help':
                print(self._help)
                return
            elif f == '-a' or f == '--app':
                app = fv
            elif f == '-n' or f == '--node':
                node = fv

        if app and node:
            print(colored.green(f'Attaching application {app} to {node} node'))
            return

        print(colored.red('No application or node selected. Interrupting '
                          'attach...'))


class ListCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py app list [FLAGS]...

Flags:
  -h, --help\tShow the help message'''

    def digest(self, flags, flags_values):

        for x in range(len(flags)):
            f = flags[x]
            if f == '-h' or f == '--help':
                print(self._help)
                return

        print(colored.green('Listing applications...'))


class InfoCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py app info [FLAGS]...

Flags:
  -h, --help\tShow the help message
  -n, --name\tThe name of application'''

    def digest(self, flags, flags_values):

        for x in range(len(flags)):
            f = flags[x]
            fv = flags_values[x]
            if f == '-h' or f == '--help':
                print(self._help)
                return
            if f == '-n' or f == '--name':
                print(colored.green(f'Info about {fv} application'))
                return

        print(colored.red('No application selected. Impossible obtain '
                          'info...'))

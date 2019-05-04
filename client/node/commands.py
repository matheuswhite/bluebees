from common.command import Command
from clint.textui import colored


class NewCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py node new [FLAGS]...

Flags:
  -h, --help\tShow the help message'''

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

        print(colored.green('Creating new node...'))


class ListCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py node list [FLAGS]...

Flags:
  -h, --help\tShow the help message'''

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

        print(colored.green('Listing nodes...'))


class InfoCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py node info [FLAGS]...

Flags:
  -h, --help\tShow the help message
  -n, --name\tThe name of node'''

    def digest(self, flags, flags_values):

        for x in range(len(flags)):
            f = flags[x]
            fv = flags_values[x]
            if f == '-h' or f == '--help':
                print(self._help)
                return
            if f == '-n' or f == '--name':
                print(colored.green(f'Info about {fv} node'))
                return
            else:
                print(colored.red(f'Invalid flag {f}'))
                print(self._help)
                return

        print(colored.red('No node selected. Impossible obtain info...'))

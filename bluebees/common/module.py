from clint.textui import colored


class Module:

    def __init__(self, name):
        self._name = name
        self._help = ''
        self._cmds = {}

    @property
    def name(self):
        return self._name

    @property
    def help(self):
        return self._help

    def __repr__(self):
        return f'module {self.name}'

    def __getitem__(self, name):
        return self._cmds[name]

    def digest(self, cmd, flags, flags_values):
        if not cmd:
            self._digest_non_cmd(flags, flags_values)
        else:
            try:
                self[cmd].digest(flags, flags_values)
            except KeyError:
                print(colored.red(f'Command "{cmd}" not found in {self._name}'
                                  f' module'))
                print(self._help)

    def _digest_non_cmd(self, flags, flags_values):
        pass

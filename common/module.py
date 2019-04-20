

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
        pass

    def digest(self, cmd, flags):
        pass

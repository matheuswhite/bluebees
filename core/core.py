from common.module import Module
from common.utils import check_flag
from core.commands import RunCommand


class Core(Module):

    def __init__(self):
        super().__init__('core')
        self._help = 'Commands availables:\nrun\trun the core module'
        self._cmds = {
            'run': RunCommand()
        }

    def _digest_non_cmd(self, flags, flags_values):
        if check_flag(('-h', '--help'), flags):
            print(self.help)
        else:
            print(f'Call {self} with flags {flags}')


core = Core()

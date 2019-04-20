from common.module import Module
from common.utils import check_flag


class Core(Module):

    def __init__(self):
        super().__init__('core')
        self._help = 'Commands availables:\nrun\trun the core module'

    def digest(self, cmd, flags):
        if not cmd:
            if check_flag(('-h', '--help'), flags):
                print(self.help)
            else:
                print(f'Call {cmd} of {self} with flags {flags}')
        else:
            pass


core = Core()

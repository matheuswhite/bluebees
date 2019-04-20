from common.command import Command
from common.utils import find_key
from common.template import template_helper
from common.file import file_helper


class RunCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = 'Execute core service.'

    def _run_opts(self, filename):
        template = file_helper.read(filename)
        core_opts = find_key(template, 'core')
        if not core_opts:
            print('Bad format. Not found core keyword')
            return
        run_opts = find_key(core_opts, 'run')
        if not run_opts:
            print('Bad format. Not found run keyword')
            return

        print('***** Run Options *****')
        for opt in run_opts.keys():
            opt_value = template_helper.get_field(run_opts, opt)
            print(f'{opt}: {opt_value}')

    def digest(self, flags, flags_values):
        for x in range(len(flags)):
            f = flags[x]
            fv = flags_values[x]
            if f == '-h' or f == '--help':
                print(self._help)
                return
            if f == '-o' or f == '--options':
                self._run_opts(fv)
                return

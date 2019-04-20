from common.command import Command
from common.utils import find_key
from common.template import template_helper
from common.file import file_helper


class RunCommand(Command):

    def __init__(self):
        super().__init__()

    def digest(self, flags, flags_values):
        for x in range(len(flags)):
            f = flags[x]
            fv = flags_values[x]
            if '-o' == f or '--options' == f:
                template = file_helper.read(fv)
                core_opts = find_key(template, 'core')
                if not core_opts:
                    print('Bad format. Not found core keyword')
                    continue
                run_opts = find_key(core_opts, 'run')
                if not run_opts:
                    print('Bad format. Not found run keyword')
                    continue

                print('***** Run Options *****')
                for opt in run_opts.keys():
                    opt_value = template_helper.get_field(run_opts, opt)
                    print(f'{opt}: {opt_value}')

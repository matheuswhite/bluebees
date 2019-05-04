from common.command import Command
from common.utils import find_key
from common.template import template_helper
from common.file import file_helper
from client.core.dongle import Dongle
from clint.textui import colored
import asyncio


class RunCommand(Command):

    def __init__(self):
        super().__init__()
        self._help = '''Usage:
  python bluebees.py core run [FLAGS]...

Flags:
  -h, --help              \tShow the help message
  -o, --options <filename>\tPass a YAML file with the options. Miss this flags will be load default options.
                          \tFor more information about the option file see <link>'''

    def _parse_options(self, filename):
        template = file_helper.read(filename)
        core_opts = find_key(template, 'core')
        if not core_opts:
            print(colored.yellow('Bad format in {filename}, not found "core" '
                                 'keyword.\nUsing default options'))
            return None
        run_opts = find_key(core_opts, 'run')
        if not run_opts:
            print(colored.yellow('Bad format in {filename}, not found "run" '
                                 'keyword.\nUsing default options'))
            return None

        opts = {}
        print('***** User Run Options *****')
        for opt in run_opts.keys():
            opt_value = template_helper.get_field(run_opts, opt)
            opts[opt] = opt_value
            print(f'{opt}: {opt_value}')

        return opts

    # TODO Implement load default options of RunCommand class
    def _load_default_options(self):
        return {
            'port': 9521,
            'baudrate': 115200,
            'serial_port': 'COM11'
        }

    # TODO Implement merge options of RunCommand class
    def _merge_options(self, options):
        return options

    def digest(self, flags, flags_values):
        opts = None

        for x in range(len(flags)):
            f = flags[x]
            fv = flags_values[x]
            if f == '-h' or f == '--help':
                print(self._help)
                return
            if f == '-o' or f == '--options':
                opts = self._parse_options(fv)
            else:
                print(colored.red(f'Invalid flag {f}'))
                print(self._help)
                return

        if opts is None:
            opts = self._load_default_options()
        else:
            opts = self._merge_options(opts)

        print(colored.green('Running core module...'))
        # try:
        #     loop = asyncio.get_event_loop()
        #     dongle = Dongle(loop=loop, serial_port=opts['serial_port'],
        #                     baudrate=opts['baudrate'], port=opts['port'])
        #     task_group = asyncio.gather(dongle.tasks())
        #     loop.run_until_complete(task_group)
        # except KeyboardInterrupt:
        #     print('End async')
        # finally:
        #     task_group.cancel()
        #     loop.close()

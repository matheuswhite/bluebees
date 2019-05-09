from common.command import Command
from common.utils import find_key
from common.template import template_helper
from common.file import file_helper
from client.core.dongle import Dongle
from common.broker import Broker
from client.data_paths import base_dir, config_dir
from clint.textui import colored
from serial import SerialException
import asyncio
import sys
import warnings


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
            print(colored.yellow(f'Bad format in "{filename}", not found "core" '
                                 f'keyword.'))
            return None
        run_opts = find_key(core_opts, 'run')
        if not run_opts:
            print(colored.yellow(f'Bad format in "{filename}", not found "run" '
                                 f'keyword.'))
            return None

        opts = {}
        print(colored.cyan('Using user options:'))
        for opt in run_opts.keys():
            opt_value = template_helper.get_field(run_opts, opt)
            opts[opt] = opt_value
            print(colored.cyan(f'* {opt}: {opt_value}'))

        return opts

    def _load_default_options(self, debug=False) -> dict:
        default_opts = file_helper.read(base_dir + config_dir +
                                        'default_options.yml')
        core_run_opts = find_key(find_key(default_opts, 'core'), 'run')

        if debug:
            print(colored.yellow('Using default options:'))
            for k in core_run_opts.keys():
                print(colored.yellow(f'* {k}: {core_run_opts[k]}'))

        return core_run_opts

    def _merge_options(self, options: dict) -> dict:
        core_run_opts = self._load_default_options()
        opts = options
        if 'baudrate' not in options.keys():
            print(colored.yellow(f'Not find "baudrate" value in option file. '
                                 f'Using defalt value: '
                                 f'{core_run_opts["baudrate"]}'))
            opts['baudrate'] = core_run_opts['baudrate']
        if 'serial_port' not in options.keys():
            print(colored.yellow(f'Not find "serial_port" value in option '
                                 f'file. Using defalt value: '
                                 f'{core_run_opts["serial_port"]}'))
            opts['serial_port'] = core_run_opts['serial_port']

        return opts

    def _run_algorithm(self, opts: dict):
        print('Running core features...')
        try:
            warnings.simplefilter('ignore')

            loop = asyncio.get_event_loop()
            broker = Broker(loop=loop)
            dongle = Dongle(loop=loop, serial_port=opts['serial_port'],
                            baudrate=opts['baudrate'])
            asyncio.gather(dongle.spwan_tasks(loop), broker.tasks())
            loop.run_forever()
        except KeyboardInterrupt:
            pass
            dongle.disconnect()
            broker.disconnect()
        except RuntimeError:
            pass
        except SerialException:
            print(colored.red(f'Serial port {opts["serial_port"]} not '
                              f'available'))
        finally:
            for t in asyncio.Task.all_tasks():
                t.cancel()
            loop.stop()
            print('Stop core features')

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
            opts = self._load_default_options(debug=True)
        else:
            opts = self._merge_options(opts)

        self._run_algorithm(opts)

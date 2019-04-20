from clint.arguments import Args
from common.module import Module
from core.core import core
from common.utils import check_flag
from common.template import template_helper


class MainModule(Module):

    def __init__(self, module_list):
        super().__init__('$')
        self._module_list = module_list
        self._help = f'''Please, use this command format:
<module> <cmd> <flags>

Modules available:
{self.module_list_str()}'''
        self._about = ' ____  _     _    _ ______ ____  ______ ______  _____\n'\
                      '|  _ \| |   | |  | |  ____|  _ \|  ____|  ____|/ ____|\n'\
                      '| |_) | |   | |  | | |__  | |_) | |__  | |__  | (___\n'\
                      '|  _ <| |   | |  | |  __| |  _ <|  __| |  __|  \___ \\\n'\
                      '| |_) | |___| |__| | |____| |_) | |____| |____ ____) |\n'\
                      '|____/|______\____/|______|____/|______|______|_____/\n'\
                      '\t\t\t\tMade by: Matheus White'
        self._license = '''MIT License

Copyright (c) 2018 Matheus White

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.'''

    def module_list_str(self):
        m_list = ''
        for module in self._module_list:
            m_list += f'{module}\n'

        return m_list[:-1]

    def digest(self, cmd, flags):
        if check_flag(('-h', '--help'), flags):
            print(self.help)
        elif check_flag(('-a', '--about'), flags):
            print(self._about)
        elif check_flag(('-l', '--license'), flags):
            print(self._license)
        else:
            print(f'Call nothing with flags {flags}')


module_list = {
    core.name: core
}

main_module = MainModule(module_list)
module_list['$'] = main_module

if __name__ == "__main__":
    args = Args()

    module = args.grouped['_'][0]
    cmd = args.grouped['_'][1]
    flags = args.flags._args

    if not cmd and not module:
        module_list['$'].digest(cmd, flags)
    else:
        try:
            module_list[module].digest(cmd, flags)
            template_helper.read('device_template.yaml')
        except KeyError:
            print(f'Module not found')
            print(module_list['$'].help)

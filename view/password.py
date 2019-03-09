from clint.textui import indent, colored, puts
from view.element import Element
import platform
if platform.system() == 'Windows':
    import msvcrt
    getch = msvcrt
else:
    import getch


class Password(Element):

    def __init__(self, description: str):
        super().__init__()

        self.description = description

    @staticmethod
    def _getpass(hide_symbol='*'):
        buf = ''
        counter = 0
        while True:
            ch = getch.getch()
            if ch == '\n':
                print('')
                break
            elif ch == '\x7f':
                if counter > 0:
                    buf = buf[:-1]
                    print('\b \b', end='', flush=True)
                    counter -= 1
            else:
                buf += ch
                print(hide_symbol[0], end='', flush=True)
                counter += 1
        return buf

    def run(self, page, options):
        with indent(len(page.quote) + 1, quote=page.quote):
            puts(colored.blue(self.description + ': '), newline=False)
            print('', end='', flush=True)
            password = self._getpass()
            return password

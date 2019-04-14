from view.page import back_cmd, exit_cmd
from view.element import Element
from clint.textui import puts, colored, indent


class Options(Element):

    def __init__(self, description: str, options=None, dynamic_options=None):
        super().__init__()

        self.description = description
        self.options = options
        self.dynamic_options = dynamic_options

    def _error_handler(self, val: str):
        try:
            val_int = int(val)
            if 1 <= val_int <= len(self.options):
                return True, val_int
            else:
                with indent(6, quote='[ERR]'):
                    puts(colored.red(f'Por favor, entre com um dos índices acima, ou use o command {back_cmd} para '
                                     f'voltar'))
                    return False, -1
        except ValueError:
            with indent(6, quote='[ERR]'):
                puts(colored.red('Por favor, entre com um número inteiro'))
                return False, -1

    def run(self, page, options):
        is_valid = False
        val_int = None
        if self.options is None:
            self.options = self.dynamic_options()
        while not is_valid:
            with indent(len(page.quote) + 1, quote=page.quote):
                puts(colored.blue(self.description))
            with indent(len(page.quote) + 1, quote=''):
                for x in range(len(self.options)):
                    puts(colored.blue(f'{x+1}. {self.options[x]}'))
            with indent(len(page.quote) + 1, quote=page.quote):
                puts('', newline=False)
                val = input('')
                if val == back_cmd:
                    return back_cmd
            is_valid, val_int = self._error_handler(val)
        return self.options[val_int-1]


class ConditionalOptions(Element):

    def __init__(self, description: str, fail_description: str, options=None, dynamic_options=None):
        super().__init__()

        self.description = description
        self.fail_description = fail_description
        self.options = options
        self.dynamic_options = dynamic_options

    def _error_handler(self, val: str):
        try:
            val_int = int(val)
            if 1 <= val_int <= len(self.options):
                return True, val_int
            else:
                with indent(6, quote='[ERR]'):
                    puts(colored.red(f'Por favor, entre com um dos índices acima, ou use o command {back_cmd} para '
                                     f'voltar'))
                    return False, -1
        except ValueError:
            with indent(6, quote='[ERR]'):
                puts(colored.red('Por favor, entre com um número inteiro'))
                return False, -1

    def run(self, page, options):
        is_valid = False
        val_int = None
        if self.options is None:
            self.options = self.dynamic_options()
        with indent(6, quote='[ERR]'):
            if len(self.options) == 0:
                puts(colored.red(self.fail_description))
                return exit_cmd
        while not is_valid:
            with indent(len(page.quote) + 1, quote=page.quote):
                puts(colored.blue(self.description))
            with indent(len(page.quote) + 1, quote=''):
                for x in range(len(self.options)):
                    puts(colored.blue(f'{x+1}. {self.options[x]}'))
            with indent(len(page.quote) + 1, quote=page.quote):
                puts('', newline=False)
                val = input('')
                if val == back_cmd:
                    return back_cmd
            is_valid, val_int = self._error_handler(val)
        return self.options[val_int-1]

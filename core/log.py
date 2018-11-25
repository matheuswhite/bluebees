from enum import Enum
from time import gmtime, strftime
from termcolor import colored


class LogLevel(Enum):
    Dbg = 4,
    Log = 3,
    Wrn = 2,
    Err = 1,
    Succ = 0,


class Log:

    def __init__(self, module_name: str):
        self.level = LogLevel.Dbg.value
        self.module_name = module_name
        self.is_disable = False

    def disable(self):
        self.is_disable = True

    def log(self, message):
        if self.level >= LogLevel.Log.value and not self.is_disable:
            time = strftime('%H:%M:%S', gmtime())
            print(colored(f'[{time}][{self.module_name}]{message}', 'white'))

    def wrn(self, message):
        if self.level >= LogLevel.Wrn.value and not self.is_disable:
            time = strftime('%H:%M:%S', gmtime())
            print(colored(f'[{time}][{self.module_name}]{message}', 'yellow'))

    def err(self, message):
        if self.level >= LogLevel.Err.value and not self.is_disable:
            time = strftime('%H:%M:%S', gmtime())
            print(colored(f'[{time}][{self.module_name}]{message}', 'red'))

    def succ(self, message):
        if self.level >= LogLevel.Succ.value and not self.is_disable:
            time = strftime('%H:%M:%S', gmtime())
            print(colored(f'[{time}][{self.module_name}]{message}', 'green'))

    def dbg(self, message):
        if self.level >= LogLevel.Dbg.value and not self.is_disable:
            time = strftime('%H:%M:%S', gmtime())
            print(colored(f'[{time}][{self.module_name}]{message}', 'blue'))

from enum import Enum
from time import time
from termcolor import colored


class LogLevel(Enum):
    Log = 0,
    Wrn = 1
    Err = 2


class Log:

    def __init__(self, module_name: str):
        self.level = LogLevel.Log
        self.module_name = module_name

    def log(self, message):
        if self.level <= LogLevel.Log:
            print(colored(f'[{time()}][{self.module_name}]{message}', 'white'))

    def wrn(self, message):
        if self.level <= LogLevel.Wrn:
            print(colored(f'[{time()}][{self.module_name}]{message}', 'yellow'))

    def err(self, message):
        if self.level <= LogLevel.Err:
            print(colored(f'[{time()}][{self.module_name}]{message}', 'red'))

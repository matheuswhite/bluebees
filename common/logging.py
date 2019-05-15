from clint.textui import colored
import datetime


DEBUG = 0
INFO = 1
WARNING = 2
ERROR = 3
CRITICAL = 4


class LoggingSystem:

    def __init__(self):
        self.loggers = {}

    def get_logger(self, name: str):
        if name not in self.loggers.keys():
            self.loggers[name] = Logger(name=name)
        return self.loggers[name]


class Logger:

    def __init__(self, name):
        self.level = DEBUG
        self.name = name
        self.time_fmt = '%H:%M:%S %d/%m/%Y'

    def set_level(self, level: int):
        if DEBUG <= level <= CRITICAL:
            self.level = level

    def debug(self, message: str):
        if self.level <= DEBUG:
            print(colored.cyan(f'[{datetime.datetime.now().strftime(self.time_fmt)}][{self.name}] '
                               f'{message}'))

    def info(self, message: str):
        if self.level <= INFO:
            print(colored.white(f'[{datetime.datetime.now().strftime(self.time_fmt)}][{self.name}] '
                                f'{message}'))

    def warning(self, message: str):
        if self.level <= WARNING:
            print(colored.yellow(f'[{datetime.datetime.now().strftime(self.time_fmt)}][{self.name}] '
                                 f'{message}'))

    def error(self, message: str):
        if self.level <= ERROR:
            print(colored.red(f'[{datetime.datetime.now().strftime(self.time_fmt)}][{self.name}] '
                              f'{message}'))

    def critical(self, message: str):
        if self.level <= CRITICAL:
            print(colored.magenta(f'[{datetime.datetime.now().strftime(self.time_fmt)}][{self.name}] '
                                  f'{message}'))

    def success(self, message: str):
        print(colored.green(f'[{datetime.datetime.now().strftime(self.time_fmt)}][{self.name}] '
                            f'{message}'))


log_sys = LoggingSystem()

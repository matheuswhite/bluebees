import click
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
            click.echo(click.style(f'[{datetime.datetime.now().strftime(self.time_fmt)}][{self.name}] '
                                   f'{message}', fg='cyan'))

    def info(self, message: str):
        if self.level <= INFO:
            click.echo(click.style(f'[{datetime.datetime.now().strftime(self.time_fmt)}][{self.name}] '
                                   f'{message}', fg='white'))

    def warning(self, message: str):
        if self.level <= WARNING:
            click.echo(click.style(f'[{datetime.datetime.now().strftime(self.time_fmt)}][{self.name}] '
                                   f'{message}', fg='yellow'))

    def error(self, message: str):
        if self.level <= ERROR:
            click.echo(click.style(f'[{datetime.datetime.now().strftime(self.time_fmt)}][{self.name}] '
                                   f'{message}', fg='red'))

    def critical(self, message: str):
        if self.level <= CRITICAL:
            click.echo(click.style(f'[{datetime.datetime.now().strftime(self.time_fmt)}][{self.name}] '
                                   f'{message}', fg='magenta'))

    def success(self, message: str):
        click.echo(click.style(f'[{datetime.datetime.now().strftime(self.time_fmt)}][{self.name}] '
                               f'{message}', fg='green'))


log_sys = LoggingSystem()

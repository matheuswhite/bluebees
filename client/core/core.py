import click
from client.core.commands.run import run


@click.group()
def core():
    '''Bluebees core feature'''
    pass


core.add_command(run)

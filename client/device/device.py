import click
from client.device.commands.list import list


@click.group()
def device():
    '''Device feature'''
    pass


device.add_command(list)

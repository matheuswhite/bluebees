import click
from bluebees.client.device.commands.list import list


@click.group()
def device():
    '''Device feature'''
    pass


device.add_command(list)

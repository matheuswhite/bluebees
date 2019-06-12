import click
from bluebees.client.network.commands.new import new
from bluebees.client.network.commands.info import info
from bluebees.client.network.commands.list import list


@click.group()
def net():
    '''Mesh network feature'''
    pass


net.add_command(new)
net.add_command(info)
net.add_command(list)

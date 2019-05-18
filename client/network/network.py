import click
from client.network.commands.new import new
from client.network.commands.info import info
from client.network.commands.list import list


@click.group()
def net():
    '''Mesh network feature'''
    pass


net.add_command(new)
net.add_command(info)
net.add_command(list)

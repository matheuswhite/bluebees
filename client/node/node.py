import click
from client.node.commands.new import new
from client.node.commands.info import info
from client.node.commands.list import list
from client.node.commands.send import send
from client.node.commands.req import req
from client.node.commands.config import config
from client.node.commands.add_appkey import add_appkey


@click.group()
def node():
    '''Mesh node feature'''
    pass


node.add_command(new)
node.add_command(info)
node.add_command(list)
node.add_command(send)
node.add_command(req)
node.add_command(config)
node.add_command(add_appkey)

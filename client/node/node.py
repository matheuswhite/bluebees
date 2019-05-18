# from common.module import Module
# from common.utils import check_flag
# from clint.textui import colored
# from client.node.commands import NewCommand, ListCommand, InfoCommand, \
#                                  SendCommand, ReqCommand, ConfigCommand


# class Node(Module):

#     def __init__(self):
#         super().__init__('node')
#         self._help = '''Usage:
#   python bluebees.py node [FLAGS]...
#   python bluebees.py node <COMMAND> [ARGS]...

# Flags:
#   -h, --help\tShow the help message

# Commands:
#   new   \t\tCreate a new node
#   list  \t\tList the nodes created
#   info  \t\tGet description about a node
#   send  \t\tSend a message to node
#   req   \t\tRequest a message to node (Send a message and wait the response).
#   config\t\tSet the node configuration'''
#         self._cmds = {
#             'new': NewCommand(),
#             'list': ListCommand(),
#             'info': InfoCommand(),
#             'send': SendCommand(),
#             'req': ReqCommand(),
#             'config': ConfigCommand()
#         }

#     def _digest_non_cmd(self, flags, flags_values):
#         if check_flag(('-h', '--help'), flags):
#             print(self.help)
#         else:
#             print(colored.red(f'Invalid flags {flags}'))
#             print(self.help)
#             return


# node = Node()
import click
from client.node.commands.new import new
from client.node.commands.info import info
from client.node.commands.list import list
from client.node.commands.send import send
from client.node.commands.req import req
from client.node.commands.config import config


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

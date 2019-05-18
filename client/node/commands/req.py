from client.node.node_data import node_name_list
from common.utils import check_hex_string
import click
import asyncio


def validate_target(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if not node_name_list() or value not in node_name_list():
        raise click.BadParameter(f'The "{value}" node not exist')
    return value


def validate_opcode(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if not check_hex_string(value):
        raise click.BadParameter('Bad formatting on opcode hex string')
    if len(value) not in [2, 4, 6]:
        raise click.BadParameter('The length of opcode must be 1, 2 or 3 '
                                 'bytes')
    return value


def validate_parameters(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if not check_hex_string(value):
        raise click.BadParameter('Bad formatting on parameter hex string')
    if len(value) > (380 * 2):
        raise click.BadParameter('The length of parameter must be less than '
                                 '380 bytes')
    if len(value) % 2 == 1:
        value = value + '0'
    return value


# ! Fake implementation
async def request_message(self, target_node: str, opcode: bytes,
                          parameters: bytes):
    click.echo(click.style(f'Message [{opcode}, {parameters}] was sent to '
                           f'"{target_node}" node', fg='green'))
    for x in range(3):
        click.echo(click.style('Waiting response...', fg='cyan'))
        await asyncio.sleep(1)

    click.echo(click.style('Response received', fg='green'))


@click.command()
@click.option('--target', '-t', type=str, default='', required=True,
              help='Specify the name of node target', callback=validate_target)
@click.option('--opcode', '-o', type=str, default='', required=True,
              help='Specify the opcode of message', callback=validate_opcode)
@click.option('--parameters', '-p', type=str, default='', required=True,
              help='Specify the parameters of message',
              callback=validate_parameters)
def req(target, opcode, parameters):
    '''Request a message to node (Send a message and wait the response)'''

    loop = asyncio.get_event_loop()
    loop.run_until_complete(request_message(target, opcode, parameters))

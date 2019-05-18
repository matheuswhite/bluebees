from client.node.node_data import NodeData, node_name_list
from client.data_paths import base_dir, node_dir
from client.mesh_layers.mesh_context import SoftContext
from client.mesh_layers.element import Element
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
        raise click.BadParameter('Bad formatting on parameters hex string')
    if len(value) > (380 * 2):
        raise click.BadParameter('The length of parameter must be less than '
                                 '380 bytes')
    if len(value) % 2 == 1:
        value = value + '0'
    return value


@click.command()
@click.option('--target', '-t', type=str, default='', required=True,
              help='Specify the name of node target', callback=validate_target)
@click.option('--opcode', '-o', type=str, default='', required=True,
              help='Specify the opcode of message', callback=validate_opcode)
@click.option('--parameters', '-p', type=str, default='', required=True,
              help='Specify the parameters of message',
              callback=validate_parameters)
def send(target, opcode, parameters):
    '''Send a message to node'''

    click.echo(click.style(f'Sending message [{opcode}, {parameters}] to '
                           f'"{target}" node', fg='green'))
    node_data = NodeData.load(base_dir + node_dir + target + '.yml')

    try:
        loop = asyncio.get_event_loop()
        client_element = Element()
        if not node_data.apps:
            app_name = ''
            is_devkey = True
        else:
            app_name = node_data.apps[0]
            is_devkey = False
        context = SoftContext(src_addr=b'\x00\x01',
                              dst_addr=node_data.addr,
                              node_name=node_data.name,
                              network_name=node_data.network,
                              application_name=app_name,
                              is_devkey=is_devkey,
                              ack_timeout=30,
                              segment_timeout=10)

        asyncio.gather(client_element.spwan_tasks(loop))
        send_task = asyncio.gather(client_element.send_message(
            opcode=opcode, parameters=parameters, ctx=context))
        loop.run_until_complete(send_task)
    except Exception as e:
        click.echo(f'Unknown error\n{e}')
    except KeyboardInterrupt:
        click.echo(click.style('Interruption by user', fg='yellow'))
    except RuntimeError:
        click.echo('Runtime error')
    finally:
        client_element.disconnect()
        tasks_running = asyncio.Task.all_tasks()
        for t in tasks_running:
            t.cancel()
        loop.stop()

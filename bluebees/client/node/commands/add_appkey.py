from bluebees.client.node.node_data import NodeData, node_name_list
from bluebees.client.application.application_data import ApplicationData, app_name_list
from bluebees.client.network.network_data import NetworkData
from bluebees.client.data_paths import base_dir, node_dir, app_dir, net_dir
from bluebees.client.mesh_layers.mesh_context import SoftContext
from bluebees.client.mesh_layers.element import Element
from bluebees.common.utils import run_seq
import click
import asyncio
import traceback


def validate_target(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if not node_name_list() or value not in node_name_list():
        raise click.BadParameter(f'The "{value}" node not exist')
    return value


def validate_app(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if not app_name_list() or value not in app_name_list():
        raise click.BadParameter(f'The "{value}" application not exist')
    return value


@click.command()
@click.option('--target', '-t', type=str, default='', required=True,
              help='Specify the name of node target', callback=validate_target)
@click.option('--app', '-a', type=str, default='', required=True,
              help='Specify the name of application', callback=validate_app)
def add_appkey(target, app):
    '''Add a appkey to node'''

    click.echo(click.style(f'Add the appkey of "{app}" application to '
                           f'"{target}" node', fg='green'))
    node_data = NodeData.load(base_dir + node_dir + target + '.yml')
    app_data = ApplicationData.load(base_dir + app_dir + app + '.yml')
    net_data = NetworkData.load(base_dir + net_dir + node_data.network + '.yml')

    net_key = int.from_bytes(net_data.key_index, 'big')
    app_key = int.from_bytes(app_data.key_index, 'big')
    key_index = (net_key | (app_key << 12)).to_bytes(3, 'big')[::-1]

    opcode = b'\x00'
    r_opcode = b'\x80\x03'
    parameters = key_index + app_data.key

    try:
        loop = asyncio.get_event_loop()
        client_element = Element()
        context = SoftContext(src_addr=b'\x00\x01',
                              dst_addr=node_data.addr,
                              node_name=node_data.name,
                              network_name=node_data.network,
                              application_name='',
                              is_devkey=True,
                              ack_timeout=10,
                              segment_timeout=3)
        run_seq_t = run_seq([
            client_element.spwan_tasks(loop),
            client_element.send_message(opcode=opcode, parameters=parameters,
                                        ctx=context),
            client_element.recv_message(opcode=r_opcode, segment_timeout=3,
                                        timeout=10, ctx=context)
        ])
        results = loop.run_until_complete(run_seq_t)

        content = results[2][0]
        if content:
            if content[0] == 0:
                if content[1:] == key_index:
                    click.echo(click.style('App key add with successful',
                                           fg='green'))
                    if app_data.name not in node_data.apps:
                        node_data.apps.append(app_data.name)
                        node_data.save()

                    if node_data.name not in app_data.nodes:
                        app_data.nodes.append(node_data.name)
                        app_data.save()
                else:
                    click.echo(click.style(f'Wrong key index: {content[1:].hex()}',
                                           fg='red'))
            else:
                click.echo(click.style(f'Fail. Error code: {content[0:1].hex()}',
                                       fg='red'))
    except KeyboardInterrupt:
        click.echo(click.style('Interruption by user', fg='yellow'))
    except RuntimeError:
        click.echo('Runtime error')
    except Exception:
        click.echo(traceback.format_exc())
    finally:
        client_element.disconnect()
        tasks_running = asyncio.Task.all_tasks()
        for t in tasks_running:
            t.cancel()
        loop.stop()

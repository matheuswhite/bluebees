from client.node.node_data import NodeData, node_name_list
from client.application.application_data import ApplicationData, app_name_list
from client.network.network_data import NetworkData
from client.data_paths import base_dir, node_dir, app_dir, net_dir
from client.mesh_layers.mesh_context import SoftContext
from client.mesh_layers.element import Element
import click
import asyncio


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


async def run_seq(seq_tasks: list):
    results = []
    for t in seq_tasks:
        t_h = asyncio.gather(t)
        r = await t_h
        results.append(r)
        await asyncio.sleep(.5)
    return results


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
    print(f'Net_key: {hex(net_key)}, App_key: {hex(app_key)}')
    key_index = (net_key | (app_key << 12)).to_bytes(3, 'big')
    print(f'Key index: {key_index.hex()}')

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
                              application_name=node_data.devkey,
                              is_devkey=True,
                              ack_timeout=30,
                              segment_timeout=10)
        run_seq_t = run_seq([
            client_element.spwan_tasks(loop),
            client_element.send_message(opcode=opcode, parameters=parameters,
                                        ctx=context),
            client_element.recv_message(opcode=r_opcode, segment_timeout=10,
                                        timeout=30)
        ])
        results = loop.run_until_complete(run_seq_t)
        print(f'Receive message: {results[2]}')
    except KeyboardInterrupt:
        click.echo(click.style('Interruption by user', fg='yellow'))
    except RuntimeError:
        click.echo('Runtime error')
    except Exception as e:
        click.echo(f'Unknown error\n[{e}]')
    finally:
        client_element.disconnect()
        tasks_running = asyncio.Task.all_tasks()
        for t in tasks_running:
            t.cancel()
        loop.stop()

from Crypto.Random import get_random_bytes
from bluebees.client.node.node_data import NodeData, node_name_list, node_addr_list
from bluebees.client.network.network_data import NetworkData, net_name_list
from bluebees.client.data_paths import base_dir, net_dir
from bluebees.client.node.provisioner import Provisioner, LinkOpenError, \
                                    ProvisioningSuccess, ProvisioningError
from bluebees.common.file import file_helper
from bluebees.common.template import template_helper
from bluebees.common.utils import check_hex_string
from bluebees.client.mesh_layers.address import address_type, UNICAST_ADDRESS
import click
import asyncio


def validate_name(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if node_name_list() and value in node_name_list():
        raise click.BadParameter(f'The "{value}" node already exist')
    return value


def validate_network(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if not net_name_list() or value not in net_name_list():
        raise click.BadParameter(f'The "{value}" network not exist')
    return value


def validate_uuid(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if not check_hex_string(value):
        raise click.BadParameter('Bad formatting on uuid hex string')
    if len(value) % 2 == 1:
        value = value + '0'
    return value


def validate_addr(ctx, param, value):
    if not value:
        raise click.BadParameter('The maximum number of nodes was '
                                 'reached')
    if not check_hex_string(value):
        raise click.BadParameter('Bad formatting on address hex string')
    if len(value) != 4:
        raise click.BadParameter('The length of node address is 2 bytes')
    if address_type(bytes.fromhex(value)) != UNICAST_ADDRESS:
        raise click.BadParameter('The address must be a unicast address')
    return value


def random_addr():
    addr_list = node_addr_list()

    for x in range(2**16):
        addr = get_random_bytes(2)
        if addr not in addr_list and address_type(addr) == UNICAST_ADDRESS \
           and addr != b'\x00\x01':
            return addr.hex()

    return None


def provisioning_device(device_uuid: bytes, network: str,
                        addr: bytes, node_name: str, debug: bool):
    click.echo(click.style(f'Provisioning device "{device_uuid}" to network '
                           f'"{network}"', fg='cyan'))
    success = False
    devkey = None
    net_data = NetworkData.load(base_dir + net_dir + network + '.yml')

    try:
        loop = asyncio.get_event_loop()
        prov = Provisioner(loop, device_uuid, net_data.key,
                           net_data.key_index, net_data.iv_index, addr,
                           debug=debug)
        asyncio.gather(prov.spwan_tasks(loop))
        loop.run_forever()
    except Exception as e:
        click.echo(f'Unknown error\n{e}')
    except LinkOpenError:
        pass
    except ProvisioningError:
        pass
    except ProvisioningSuccess:
        devkey = prov.devkey
        success = True
        net_data = NetworkData.load(base_dir + net_dir + network + '.yml')
        net_data.nodes.append(node_name)
        net_data.save()
    except KeyboardInterrupt:
        click.echo(click.style('Interruption by user', fg='yellow'))
        if prov and prov.tasks_h:
            prov.tasks_h.cancel()
            close_task = asyncio.gather(prov.close_link(b'\x02'))
            loop.run_until_complete(close_task)
    except RuntimeError:
        click.echo('Runtime error')
    finally:
        prov.disconnect()
        tasks_running = asyncio.Task.all_tasks()
        for t in tasks_running:
            t.cancel()
        loop.stop()

    return success, devkey


def parse_template(ctx, param, value):
    if not value:
        return value

    template = file_helper.read(value)
    if not template:
        raise click.BadParameter(f'File "{value}" not found')

    try:
        name, name_is_seq = template_helper.get_field(template, 'name')
        validate_name(ctx, param, name)
    except KeyError:
        raise click.BadParameter(f'Field "name" not found in template file '
                                 f'"{value}"')
    except click.BadParameter as bp:
        if name_is_seq:
            template_helper.update_sequence(template, 'name')
        raise bp

    try:
        network, net_is_seq = template_helper.get_field(template, 'network')
        validate_network(ctx, param, network)
    except KeyError:
        raise click.BadParameter(f'Field "network" not found in template file '
                                 f'"{value}"')
    except click.BadParameter as bp:
        if net_is_seq:
            template_helper.update_sequence(template, 'network')
        raise bp

    try:
        uuid, _ = template_helper.get_field(template, 'uuid')
    except KeyError:
        raise click.BadParameter(f'Field "uuid" not found in template file '
                                 f'"{value}"')

    try:
        address, _ = template_helper.get_field(template, 'address')
        validate_addr(ctx, param, address)
    except KeyError:
        address = random_addr()

    address = bytes.fromhex(address)

    if len(uuid) < 32:
        uuid = bytes.fromhex(uuid) + bytes((32 - len(uuid)) // 2)
    elif len(uuid) > 32:
        uuid = bytes.fromhex(uuid)[0:16]
    else:
        uuid = bytes.fromhex(uuid)

    # provisioning device
    success, devkey = provisioning_device(uuid, network, address, name, False)
    if not success:
        click.echo(click.style('Error in provisioning', fg='red'))
    else:
        node_data = NodeData(name=name, addr=address, network=network,
                             device_uuid=uuid, devkey=devkey)
        node_data.save()

        if name_is_seq:
            template_helper.update_sequence(template, 'name')
        if net_is_seq:
            template_helper.update_sequence(template, 'network')

        click.echo(click.style('A new node was created.', fg='green'))
        click.echo(click.style(str(node_data), fg='green'))

    ctx.exit()


@click.command()
@click.option('--name', '-n', type=str, default='', required=True,
              help='Specify the name of node', callback=validate_name)
@click.option('--network', '-w', type=str, default='', required=True,
              help='Specify the name of network', callback=validate_network)
@click.option('--uuid', '-i', type=str, default='', required=True,
              help='Specify the UUID of target device', callback=validate_uuid)
@click.option('--address', '-a', type=str, default=random_addr(),
              help='Specify the address of node', callback=validate_addr)
@click.option('--template', '-t', type=str, default='',
              help='Specify a YAML template file. A file example is shown in'
                   ' node_template.yml. This template file must contain the '
                   '"name", "network" and "uuid" keyword.',
                   callback=parse_template, is_eager=True)
def new(name, network, address, uuid, template):
    '''Create a new node'''

    if len(uuid) < 32:
        uuid = bytes.fromhex(uuid) + bytes((32 - len(uuid)) // 2)
    elif len(uuid) > 32:
        uuid = bytes.fromhex(uuid)[0:16]
    else:
        uuid = bytes.fromhex(uuid)

    address = bytes.fromhex(address)

    # provisioning device
    success, devkey = provisioning_device(uuid, network, address, name, False)
    if not success:
        click.echo(click.style('Error in provisioning', fg='red'))
    else:
        node_data = NodeData(name=name, addr=address, network=network,
                             device_uuid=uuid, devkey=devkey)
        node_data.save()

        click.echo(click.style('A new node was created.', fg='green'))
        click.echo(click.style(str(node_data), fg='green'))

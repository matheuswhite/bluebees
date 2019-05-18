from Crypto.Random import get_random_bytes
from client.network.network_data import NetworkData, net_name_list, \
                                        net_key_list, net_key_index_list
import click


def validate_name(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if net_name_list() and value in net_name_list():
        raise click.BadParameter(f'The "{value}" network already exist')
    return value


def validate_key(ctx, param, value):
    if not value:
        raise click.BadParameter('The maximum number of network was reached')
    if len(value) % 2 == 1:
        value = '0' + value
    return value


def validate_key_index(value):
    if not value:
        raise click.BadParameter('The maximum number of network was reached')
    return value


def random_key():
    key_list = net_key_list()

    for x in range(2**128):
        key = get_random_bytes(16)
        if key not in key_list:
            return key.hex()

    return None


def random_key_index():
    key_index_list = net_key_index_list()

    for x in range(2**12):
        key_index = get_random_bytes(2)
        if key_index not in key_index_list:
            return key_index.hex()

    return None


@click.command()
@click.option('--name', '-n', type=str, default='',
              help='Specify the name of network', callback=validate_name)
@click.option('--key', '-k', type=str, default=random_key(),
              help='Specify the key of network', callback=validate_key)
@click.option('--template', '-t', type=str, default='',
              help='Specify a YAML template file. A file example is shown in'
                   ' net_template.yml. This template file must contain the '
                   '"name" keyword.')
def new(name, key, template):
    '''Create a new network'''
    key_index = random_key_index()
    validate_key_index(key_index)

    if len(key) < 32:
        key = bytes((32 - len(key)) // 2) + bytes.fromhex(key)
    else:
        key = bytes.fromhex(key)

    net_data = NetworkData(name=name, key=key,
                           key_index=bytes.fromhex(key_index),
                           iv_index=bytes(4))
    net_data.save()

    click.echo(click.style('A new network was created', fg='green'))
    click.echo(click.style(str(net_data), fg='green'))

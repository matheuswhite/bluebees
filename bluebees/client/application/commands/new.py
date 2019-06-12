from Crypto.Random import get_random_bytes
from bluebees.client.application.application_data import ApplicationData, \
                                                app_name_list, app_key_list, \
                                                app_key_index_list
from bluebees.client.network.network_data import NetworkData, net_name_list
from bluebees.client.data_paths import base_dir, net_dir
from bluebees.common.file import file_helper
from bluebees.common.template import template_helper
from bluebees.common.utils import check_hex_string
from random import randint
import click


def validate_name(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if app_name_list() and value in app_name_list():
        raise click.BadParameter(f'The "{value}" application already exist')
    return value


def validate_network(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if not net_name_list() or value not in net_name_list():
        raise click.BadParameter(f'The "{value}" network not exist')
    return value


def validate_key(ctx, param, value):
    if not value:
        raise click.BadParameter('The maximum number of application was '
                                 'reached')
    if not check_hex_string(value):
        raise click.BadParameter('Bad formatting on key hex string')
    if len(value) % 2 == 1:
        value = value + '0'
    return value


def validate_key_index(value):
    if not value:
        raise click.BadParameter('The maximum number of application was '
                                 'reached')
    return value


def random_key():
    key_list = app_key_list()

    for x in range(2**128):
        key = get_random_bytes(16)
        if key not in key_list:
            return key.hex()

    return None


def random_key_index():
    key_index_list = app_key_index_list()

    for x in range(2**12):
        key_index = randint(0, 2**12).to_bytes(2, 'big')
        if key_index not in key_index_list:
            return key_index.hex()

    return None


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
        key, _ = template_helper.get_field(template, 'key')
        validate_key(ctx, param, key)
    except KeyError:
        key = random_key()

    key_index = random_key_index()
    validate_key_index(key_index)

    if len(key) < 32:
        key = bytes.fromhex(key) + bytes((32 - len(key)) // 2)
    elif len(key) > 32:
        key = bytes.fromhex(key)[0:16]
    else:
        key = bytes.fromhex(key)

    app_data = ApplicationData(name=name, key=key,
                               key_index=bytes.fromhex(key_index),
                               network=network)
    app_data.save()

    net_data = NetworkData.load(base_dir + net_dir + network + '.yml')
    if app_data.name not in net_data.apps:
        net_data.apps.append(app_data.name)
    net_data.save()

    if name_is_seq:
        template_helper.update_sequence(template, 'name')
    if net_is_seq:
        template_helper.update_sequence(template, 'network')

    click.echo(click.style('A new application was created', fg='green'))
    click.echo(click.style(str(app_data), fg='green'))

    ctx.exit()


@click.command()
@click.option('--name', '-n', type=str, default='', required=True,
              help='Specify the name of application', callback=validate_name)
@click.option('--network', '-w', type=str, default='', required=True,
              help='Specify the name of network', callback=validate_network)
@click.option('--key', '-k', type=str, default=random_key(),
              help='Specify the key of application', callback=validate_key)
@click.option('--template', '-t', type=str, default='',
              help='Specify a YAML template file. A file example is shown in'
                   ' app_template.yml. This template file must contain the '
                   '"name" and the "network" keyword.',
                   callback=parse_template, is_eager=True)
def new(name, network, key, template):
    '''Create a new application'''
    key_index = random_key_index()
    validate_key_index(key_index)

    if len(key) < 32:
        key = bytes.fromhex(key) + bytes((32 - len(key)) // 2)
    elif len(key) > 32:
        key = bytes.fromhex(key)[0:16]
    else:
        key = bytes.fromhex(key)

    app_data = ApplicationData(name=name, key=key,
                               key_index=bytes.fromhex(key_index),
                               network=network)
    app_data.save()

    net_data = NetworkData.load(base_dir + net_dir + network + '.yml')
    if app_data.name not in net_data.apps:
        net_data.apps.append(app_data.name)
    net_data.save()

    click.echo(click.style('A new application was created', fg='green'))
    click.echo(click.style(str(app_data), fg='green'))

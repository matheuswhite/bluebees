import click
from bluebees.client.network.network_data import NetworkData, net_name_list
from bluebees.client.data_paths import base_dir, net_dir


def validate_name(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if not net_name_list() or value not in net_name_list():
        raise click.BadParameter(f'The "{value}" network not exist')
    return value


@click.command()
@click.option('--name', '-n', type=str, default='', required=True,
              help='Specify the name of network', callback=validate_name)
def info(name):
    '''Get description about a network'''

    net_data = NetworkData.load(base_dir + net_dir + name + '.yml')

    click.echo(click.style('***** Network data *****', fg='cyan'))
    click.echo(click.style(str(net_data), fg='cyan'))

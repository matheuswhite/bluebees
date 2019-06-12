import click
from bluebees.client.node.node_data import NodeData, node_name_list
from bluebees.client.data_paths import base_dir, node_dir


def validate_name(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if not node_name_list() or value not in node_name_list():
        raise click.BadParameter(f'The "{value}" node not exist')
    return value


@click.command()
@click.option('--name', '-n', type=str, default='', required=True,
              help='Specify the name of application', callback=validate_name)
def info(name):
    '''Get description about a node'''

    node_data = NodeData.load(base_dir + node_dir + name + '.yml')

    click.echo(click.style('***** Node data *****', fg='cyan'))
    click.echo(click.style(str(node_data), fg='cyan'))

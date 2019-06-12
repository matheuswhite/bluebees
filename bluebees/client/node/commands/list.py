import click
from bluebees.client.node.node_data import node_name_list


@click.command()
def list():
    '''List the nodes created'''

    node_names = node_name_list()
    if not node_names:
        click.echo(click.style('No node created', fg='red'))
    else:
        click.echo(click.style('Nodes created:', fg='cyan'))
        for i, name in enumerate(node_names):
            click.echo(click.style(f'{i}. {name}', fg='cyan'))

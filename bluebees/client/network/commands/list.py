import click
from bluebees.client.network.network_data import net_name_list


@click.command()
def list():
    '''List the networks created'''

    net_names = net_name_list()
    if not net_names:
        click.echo(click.style('No network created', fg='red'))
    else:
        click.echo(click.style('Networks created:', fg='cyan'))
        for i, name in enumerate(net_names):
            click.echo(click.style(f'{i}. {name}', fg='cyan'))

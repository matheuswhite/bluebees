import click
from bluebees.client.application.application_data import app_name_list


@click.command()
def list():
    '''List the applications created'''

    app_names = app_name_list()
    if not app_names:
        click.echo(click.style('No application created', fg='red'))
    else:
        click.echo(click.style('Applications created:', fg='cyan'))
        for i, name in enumerate(app_names):
            click.echo(click.style(f'{i}. {name}', fg='cyan'))

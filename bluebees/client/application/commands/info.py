import click
from bluebees.client.application.application_data import ApplicationData, app_name_list
from bluebees.client.data_paths import base_dir, app_dir


def validate_name(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if not app_name_list() or value not in app_name_list():
        raise click.BadParameter(f'The "{value}" application not exist')
    return value


@click.command()
@click.option('--name', '-n', type=str, default='', required=True,
              help='Specify the name of application', callback=validate_name)
def info(name):
    '''Get description about a application'''

    app_data = ApplicationData.load(base_dir + app_dir + name + '.yml')

    click.echo(click.style('***** Application data *****', fg='cyan'))
    click.echo(click.style(str(app_data), fg='cyan'))

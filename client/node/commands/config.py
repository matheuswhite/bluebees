from client.node.node_data import node_name_list
from client.application.application_data import app_name_list
from common.file import file_helper
from common.template import template_helper
from common.utils import check_hex_string, order
from tqdm import tqdm
import click
import asyncio


def validate_name(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if not node_name_list() or value not in node_name_list():
        raise click.BadParameter(f'The "{value}" node not exist')
    return value


def validate_app(value):
    if not app_name_list() or value not in app_name_list():
        raise click.BadParameter(f'The "{value}" application not exist')


def validate_model(value):
    try:
        index = value['index']
        index_order = str(index) + order(index)

        if type(index) != int:
            raise click.BadParameter('The index value must be a integer')
    except KeyError:
        raise click.BadParameter('index keyword not found')

    try:
        if type(value['publish']) != str:
            raise click.BadParameter(f'On {index_order} model, the publish '
                                     f'value must be a hex string')
        elif not check_hex_string(value['publish']):
            raise click.BadParameter(f'On {index_order} model, bad formatting'
                                     f' of hex string, on publish value')
        elif len(value['publish']) != 4:
            raise click.BadParameter(f'On {index_order} model, the publish '
                                     f'value length must be 2 bytes')
    except KeyError:
        pass

    try:
        if type(value['subscribe']) != str:
            raise click.BadParameter(f'On {index_order} model, the subscribe '
                                     f'value must be a hex string')
        elif not check_hex_string(value['subscribe']):
            raise click.BadParameter(f'On {index_order} model, bad formatting'
                                     f' of hex string, on subscribe value'
                                     f' model')
        elif len(value['subscribe']) != 4:
            raise click.BadParameter(f'On {index_order} model, the subscribe'
                                     f' value length must be 2 bytes')
    except KeyError:
        pass

    try:
        if not app_name_list() or \
           value['application'] not in app_name_list():
            raise click.BadParameter(f'On {index_order} model, the '
                                     f'"{value["application"]}" application '
                                     f'not exist')
    except KeyError:
        raise click.BadParameter('application keyword not found')


def parse_config(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    else:
        cfg = {'applications': [], 'models': []}

        template = file_helper.read(value)
        if not template:
            raise click.BadParameter(f'File "{value}" not found')

        try:
            cfg['applications'] = template_helper.get_field(template,
                                                            'applications')
            for app in cfg['applications']:
                validate_app(app)
        except KeyError:
            cfg['applications'] = []

        try:
            cfg['models'] = template_helper.get_field(template, 'models')
            for model in cfg['models']:
                validate_model(model)
        except KeyError:
            cfg['models'] = []

        return cfg


# ! Fake implementation
async def config_node(name: str, config: dict):
    click.echo(click.style(f'Configuration sent to "{name}" node', fg='green'))
    click.echo(click.style(f'Check configuration in "{name}" node...',
                           fg='cyan'))

    total_len = len(config['applications']) + len(config['models'])
    for x in tqdm(range(total_len)):
        await asyncio.sleep(1)

    click.echo(click.style(f'Configuration done!', fg='green'))


@click.command()
@click.option('--name', '-n', type=str, default='', required=True,
              help='Specify the name of node', callback=validate_name)
@click.option('--config', '-c', type=str, default='', required=True,
              help='Specify a YAML config file. A file example is shown in'
                   ' node_config.yml', callback=parse_config)
def config(name, config):
    '''Set the node configuration'''

    loop = asyncio.get_event_loop()
    loop.run_until_complete(config_node(name, config))

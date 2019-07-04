from bluebees.client.node.node_data import node_name_list
from bluebees.client.application.application_data import ApplicationData, app_name_list
from bluebees.client.node.node_data import NodeData
from bluebees.client.network.network_data import NetworkData
from bluebees.common.file import file_helper
from bluebees.common.utils import check_hex_string, order, run_seq
from bluebees.client.data_paths import base_dir, node_dir, app_dir, net_dir
from bluebees.client.mesh_layers.element import Element
from bluebees.client.mesh_layers.mesh_context import SoftContext
from bluebees.client.mesh_layers.access_layer import check_opcode, check_parameters, \
                                            OpcodeLengthError, \
                                            OpcodeBadFormat, OpcodeReserved, \
                                            ParametersLengthError
from tqdm import tqdm
import click
import asyncio
import traceback
import ruamel


def validate_name(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if not node_name_list() or value not in node_name_list():
        raise click.BadParameter(f'The "{value}" node not exist')
    return value


def validate_app(value):
    if not app_name_list() or value not in app_name_list():
        raise click.BadParameter(f'The "{value}" application not exist')


def validate_model(value, index):
    try:
        id_ = value['id']
        index_order = str(index) + order(index)

        if type(id_) != str:
            raise click.BadParameter('The id value must be a hex string')
        elif not check_hex_string(id_):
            raise click.BadParameter(f'On {index_order} model, id is bad '
                                     f'formatting of hex string')
        elif len(id_) not in [4, 8]:
            raise click.BadParameter(f'On {index_order} model, the id '
                                     f'length must be 2 or 4 bytes')
    except KeyError:
        raise click.BadParameter('id keyword not found')

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
        if type(value['subscribe']) != ruamel.yaml.comments.CommentedSeq:
            raise click.BadParameter(f'On {index_order} model, the subscribe '
                                     f'value must be a list of hex string')
        for i, addr in enumerate(value['subscribe']):
            if type(addr) != str:
                raise click.BadParameter(f'On {index_order} model, the '
                                         f'{i+1}{order(i+1)} subscribe value '
                                         f'must be a hex string')
            elif not check_hex_string(addr):
                raise click.BadParameter(f'On {index_order} model, bad '
                                         f'formatting of hex string, on '
                                         f'{i+1}{order(i+1)} subscribe value'
                                         f' model')
            elif len(addr) != 4:
                raise click.BadParameter(f'On {index_order} model, the '
                                         f'{i+1}{order(i+1)} subscribe value '
                                         f'length must be 2 bytes')
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


def validate_single_cmd(file, index, value):
    try:
        opcode = value['opcode']
        try:
            if type(opcode) != str:
                raise click.BadParameter(f'On {file} file, the opcode of the'
                                         f'{index}{order(index)} command must '
                                         f'be a hex string')
            elif not check_hex_string(opcode):
                raise click.BadParameter(f'On {file} file, bad formatting of '
                                         f'opcode on the {index}{order(index)}'
                                         f' command')
            check_opcode(bytes.fromhex(opcode))
        except OpcodeLengthError:
            raise click.BadParameter(f'On {file} file, the length of opcode in'
                                     f' the {index}{order(index)} command must'
                                     f' be less than 3')
        except OpcodeBadFormat:
            raise click.BadParameter(f'On {file} file, the opcode in'
                                     f' the {index}{order(index)} command is '
                                     f'wrong')
        except OpcodeReserved:
            raise click.BadParameter(f'On {file} file, the opcode in'
                                     f' the {index}{order(index)} command is '
                                     f'wrong')
    except KeyError:
        raise click.BadParameter(f'On {file} file, the {index}{order(index)}'
                                 f' command not contains "opcode" keyword')

    try:
        parameters = value['parameters']
        try:
            if type(parameters) != str:
                raise click.BadParameter(f'On {file} file, the parameters of '
                                         f'the {index}{order(index)} command '
                                         f'must be a hex string')
            elif not check_hex_string(parameters):
                raise click.BadParameter(f'On {file} file, bad formatting of '
                                         f'parameters on the '
                                         f'{index}{order(index)} command')
            check_parameters(bytes.fromhex(opcode), bytes.fromhex(parameters))
        except ParametersLengthError:
            raise click.BadParameter(f'On {file} file, the length of '
                                     f'parameters in the {index}{order(index)}'
                                     f' command is wrong')
    except KeyError:
        raise click.BadParameter(f'On {file} file, the {index}{order(index)}'
                                 f' command not contains "parameters" keyword')

    try:
        application = value['application']
        if type(application) != str:
            raise click.BadParameter(f'On {file} file, the application of '
                                     f'the {index}{order(index)} command '
                                     f'must be a string')
        elif not app_name_list() or application not in app_name_list():
            raise click.BadParameter(f'On {file} file, the application of '
                                     f'the {index}{order(index)} command '
                                     f'not exist')
    except KeyError:
        pass

    try:
        tries = value['tries']
        if type(tries) != int:
            raise click.BadParameter(f'On {file} file, the tries of '
                                     f'the {index}{order(index)} command '
                                     f'must be a integer')
        elif tries <= 0:
            raise click.BadParameter(f'On {file} file, the tries of '
                                     f'the {index}{order(index)} command '
                                     f'must be non-zero and positive')
    except KeyError:
        pass


def validate_post_cmds(value):
    file = file_helper.read(value)
    if not file:
        raise click.BadParameter(f'File "{value}" not found')

    try:
        commands = file['commands']
        if type(commands) != ruamel.yaml.comments.CommentedSeq:
            raise click.BadParameter(f'On {value} file, The "commands" must be'
                                     f' a list')
        for i, cmd in enumerate(commands):
            validate_single_cmd(value, i + 1, cmd)
    except KeyError:
        raise click.BadParameter(f'Not found "commands" keyword on {value}'
                                 f' file')


def parse_config(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    else:
        cfg = file_helper.read(value)
        if not cfg:
            raise click.BadParameter(f'File "{value}" not found')

        try:
            if type(cfg['applications']) != ruamel.yaml.comments.CommentedSeq:
                raise click.BadParameter(f'The "applications" must be a list')

            for app in cfg['applications']:
                validate_app(app)
        except KeyError:
            cfg['applications'] = []

        try:
            for i, model in enumerate(cfg['models']):
                validate_model(model, i + 1)
        except KeyError:
            cfg['models'] = []

        try:
            if type(cfg['post_cmds']) != ruamel.yaml.comments.CommentedSeq:
                raise click.BadParameter(f'The "post_cmds" must be a list')

            for cmd_file in cfg['post_cmds']:
                validate_post_cmds(cmd_file)
        except KeyError:
            cfg['post_cmds'] = []

        return cfg, value


async def appkey_add(client_element: Element, target: str,
                     application: str) -> bool:
    node_data = NodeData.load(base_dir + node_dir + target + '.yml')
    app_data = ApplicationData.load(base_dir + app_dir + application + '.yml')
    net_data = NetworkData.load(base_dir + net_dir + app_data.network + '.yml')

    net_key = int.from_bytes(net_data.key_index, 'big')
    app_key = int.from_bytes(app_data.key_index, 'big')
    key_index = (net_key | (app_key << 12)).to_bytes(3, 'big')[::-1]

    opcode = b'\x00'
    r_opcode = b'\x80\x03'
    parameters = key_index + app_data.key

    context = SoftContext(src_addr=b'\x00\x01', dst_addr=node_data.addr,
                          node_name=node_data.name,
                          network_name=node_data.network,
                          application_name='',
                          is_devkey=True, ack_timeout=3, segment_timeout=3)

    success = await client_element.send_message(opcode=opcode,
                                                parameters=parameters,
                                                ctx=context)
    if not success:
        return False

    r_content = await client_element.recv_message(opcode=r_opcode,
                                                  segment_timeout=1,
                                                  timeout=3, ctx=context)

    if r_content:
        if r_content[0] == 0 and r_content[1:] == key_index:
            if app_data.name not in node_data.apps:
                node_data.apps.append(app_data.name)
                node_data.save()

            if node_data.name not in app_data.nodes:
                app_data.nodes.append(node_data.name)
                app_data.save()

            return True

    return False


async def model_app_bind(client_element: Element, target: str, model_id: bytes,
                         application: str) -> bool:
    node_data = NodeData.load(base_dir + node_dir + target + '.yml')
    app_data = ApplicationData.load(base_dir + app_dir + application + '.yml')

    key_index = app_data.key_index

    opcode = b'\x80\x3d'
    r_opcode = b'\x80\x3e'
    parameters = node_data.addr[::-1] + key_index[::-1] + model_id[::-1]

    context = SoftContext(src_addr=b'\x00\x01', dst_addr=node_data.addr,
                          node_name=node_data.name,
                          network_name=node_data.network,
                          application_name='',
                          is_devkey=True, ack_timeout=3, segment_timeout=3)

    success = await client_element.send_message(opcode=opcode,
                                                parameters=parameters,
                                                ctx=context)
    if not success:
        return False

    r_content = await client_element.recv_message(opcode=r_opcode,
                                                  segment_timeout=1,
                                                  timeout=3, ctx=context)

    if r_content:
        if r_content[0] == 0 and r_content[1:] == parameters:
            return True

    return False


async def model_publication_set(client_element: Element, target: str,
                                model_id: bytes, addr: bytes,
                                application: str) -> bool:
    node_data = NodeData.load(base_dir + node_dir + target + '.yml')
    app_data = ApplicationData.load(base_dir + app_dir + application + '.yml')

    key_index = app_data.key_index
    default_ttl = b'\x07'
    period = b'\x00'
    default_xmit_int = b'\x40'

    opcode = b'\x03'
    r_opcode = b'\x80\x19'
    parameters = node_data.addr[::-1] + addr[::-1] + key_index[::-1] + \
        default_ttl[::-1] + period[::-1] + default_xmit_int[::-1] + \
        model_id[::-1]

    context = SoftContext(src_addr=b'\x00\x01', dst_addr=node_data.addr,
                          node_name=node_data.name,
                          network_name=node_data.network,
                          application_name='',
                          is_devkey=True, ack_timeout=3, segment_timeout=3)

    success = await client_element.send_message(opcode=opcode,
                                                parameters=parameters,
                                                ctx=context)
    if not success:
        return False

    r_content = await client_element.recv_message(opcode=r_opcode,
                                                  segment_timeout=1,
                                                  timeout=3, ctx=context)

    if r_content:
        if r_content[0] == 0 and r_content[1:] == parameters:
            return True

    return False


async def model_subscription_add(client_element: Element, target: str,
                                 model_id: bytes, addr: bytes) -> bool:
    node_data = NodeData.load(base_dir + node_dir + target + '.yml')

    opcode = b'\x80\x1b'
    r_opcode = b'\x80\x1f'
    parameters = node_data.addr[::-1] + addr[::-1] + model_id[::-1]

    context = SoftContext(src_addr=b'\x00\x01', dst_addr=node_data.addr,
                          node_name=node_data.name,
                          network_name=node_data.network,
                          application_name='',
                          is_devkey=True, ack_timeout=3, segment_timeout=3)

    success = await client_element.send_message(opcode=opcode,
                                                parameters=parameters,
                                                ctx=context)
    if not success:
        return False

    r_content = await client_element.recv_message(opcode=r_opcode,
                                                  segment_timeout=1,
                                                  timeout=3, ctx=context)

    if r_content:
        if r_content[0] == 0 and r_content[1:] == parameters:
            return True

    return False


async def send_cmd(client_element: Element, target: str, opcode: bytes,
                   parameters: bytes, application: str):
    node_data = NodeData.load(base_dir + node_dir + target + '.yml')

    app_name = application if application else node_data.apps[0]

    context = SoftContext(src_addr=b'\x00\x01', dst_addr=node_data.addr,
                          node_name=node_data.name,
                          network_name=node_data.network,
                          application_name=app_name,
                          is_devkey=False, ack_timeout=3, segment_timeout=3)

    success = await client_element.send_message(opcode=opcode,
                                                parameters=parameters,
                                                ctx=context)
    return success


async def config_task(target: str, client_element: Element, config: dict):
    tries = 3
    total_steps = len(config['applications'])
    for m in config['models']:
        total_steps += 1
        if 'publication' in m.keys():
            total_steps += 1
        if 'subscription' in m.keys():
            total_steps += len(m['subscription'])
    for cmd_file in config['post_cmds']:
        file = file_helper.read(cmd_file)
        total_steps += len(file['commands'])

    with tqdm(range(total_steps)) as pbar:
        success = True

        for app in config['applications']:
            for t in range(tries):
                success = await appkey_add(client_element, target, app)
                if success:
                    break
            if not success:
                click.echo(click.style(f'\nError on appkey add. Application: '
                                       f'{app}', fg='red'))
                return None
            pbar.update(1)

        for model in config['models']:
            for t in range(tries):
                success = await model_app_bind(client_element, target,
                                               bytes.fromhex(model['id']),
                                               model['application'])
                if success:
                    break
            if not success:
                click.echo(click.style(f'\nError on model app bind. '
                                       f'Model id: 0x{model["id"]}', fg='red'))
                return None
            pbar.update(1)

            if 'publication' in model:
                for t in range(tries):
                    success = await model_publication_set(
                        client_element, target, bytes.fromhex(model['id']),
                        bytes.fromhex(model['publication']),
                        model['application'])
                    if success:
                        break
                if not success:
                    click.echo(click.style(f'\nError on model publication set.'
                                           f' Model id: 0x{model["id"]}',
                                           fg='red'))
                    return None
                pbar.update(1)

            if 'subscription' in model:
                for s in model['subscription']:
                    for t in range(tries):
                        success = await model_subscription_add(
                            client_element, target, bytes.fromhex(model['id']),
                            bytes.fromhex(s))
                        if success:
                            break
                    if not success:
                        click.echo(click.style(f'\nError on model subscription'
                                               f' add. Model id: 0x'
                                               f'{model["id"]}', fg='red'))
                        return None
                    pbar.update(1)

        for post_cmd in config['post_cmds']:
            file = file_helper.read(post_cmd)
            for cmd in file['commands']:
                tries = cmd['tries'] if 'tries' in cmd.keys() else 1
                application = cmd['application'] if \
                    'application' in cmd.keys() else ''
                for t in range(tries):
                    success = await send_cmd(client_element, target,
                                             bytes.fromhex(cmd['opcode']),
                                             bytes.fromhex(cmd['parameters']),
                                             application)
                    await asyncio.sleep(.1)
                if not success:
                    click.echo(click.style(f'\nError on send cmd. cmd file: '
                                           f'{post_cmd}', fg='red'))
                    return None
                pbar.update(1)


@click.command()
@click.option('--name', '-n', type=str, default='', required=True,
              help='Specify the name of node', callback=validate_name)
@click.option('--config', '-c', type=str, default='', required=True,
              help='Specify a YAML config file. A file example is shown in'
                   ' node_config.yml', callback=parse_config)
def config(name, config):
    '''Set the node configuration'''

    click.echo(click.style(f'Config "{name}" node using {config[1]} config '
                           f'file', fg='green'))

    try:
        loop = asyncio.get_event_loop()
        client_element = Element()

        run_seq_t = run_seq([
            client_element.spwan_tasks(loop),
            config_task(name, client_element, config[0])
        ])
        loop.run_until_complete(run_seq_t)
    except KeyboardInterrupt:
        click.echo(click.style('Interruption by user', fg='yellow'))
    except RuntimeError:
        click.echo('Runtime error')
    except Exception:
        click.echo(traceback.format_exc())
    finally:
        client_element.disconnect()
        tasks_running = asyncio.Task.all_tasks()
        for t in tasks_running:
            t.cancel()
        loop.stop()

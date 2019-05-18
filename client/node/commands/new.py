# from common.command import Command
# from clint.textui import colored
# from client.node.node_data import NodeData
# from client.network.network_data import NetworkData
# from common.file import file_helper
# from common.template import template_helper
# from client.mesh_layers.mesh_context import SoftContext
# from client.mesh_layers.element import Element
# from random import randint
# from client.node.provisioner import Provisioner, LinkOpenError, \
#                                     ProvisioningSuccess, ProvisioningError
# from client.data_paths import base_dir, node_dir, net_dir
# import asyncio


# class NewCommand(Command):

#     def __init__(self):
#         super().__init__()
#         self._help = '''Usage:
#   python bluebees.py node new <-n|--name> <-w|--network> <-i|--uuid> [FLAGS]...

# Flags:
#   -n, --name <Node name>      \tSpecify the name of node. This flag is mandatory
#   -w, --network <Network name>\tSpecify the name of network. This flag is mandatory
#   -i, --uuid <Device UUID>    \tSpecify the UUID of target device. This flag is mandatory.
#   -t, --template <filename>   \tSpecify a template file. This template file can contain the keyworks:
#                               \t  * name    (The name of the node)
#                               \t  * network (The network name)
#                               \t  * uuid    (The UUID of target device)
#                               \t  * addr    (The address of the node)
#                               \tThis template file must contain: "name", "network" and "uuid" keyword.
#                               \tIf this flag is active, then the flags "-n|--name", "-w|--network" and "-i|--uuid" is not mandatory
#   -a, --address <Node addr>   \tSpecify the address of node. This flag is not mandatory
#   -h, --help                  \tShow the help message'''

#     def _node_name_exist(self, name: str) -> bool:
#         filenames = file_helper.list_files(base_dir + node_dir)
#         if not filenames:
#             return False

#         # remove file extension
#         filenames_fmt = []
#         for file in filenames:
#             filenames_fmt.append(file[:-4])

#         return name in filenames_fmt

#     def _node_network_exist(self, network: str) -> bool:
#         filenames = file_helper.list_files(base_dir + net_dir)
#         if not filenames:
#             return False

#         net_names = []
#         for file in filenames:
#             net = NetworkData.load(base_dir + net_dir + file)
#             net_names.append(net.name)

#         return network in net_names

#     def _node_addr_exist(self, addr: bytes) -> bool:
#         return addr in self._node_addr_list()

#     def _node_addr_list(self) -> list:
#         filenames = file_helper.list_files(base_dir + node_dir)
#         if not filenames:
#             return []

#         nodeaddrs = []
#         for file in filenames:
#             node = NodeData.load(base_dir + node_dir + file)
#             nodeaddrs.append(node.addr)
#         return nodeaddrs

#     def _generate_node_addr(self) -> bytes:
#         node_addrs = self._node_addr_list()

#         addr = randint(0, 2**16)
#         for x in range(2**16):
#             addr = randint(0, 2**16)
#             if addr not in node_addrs:
#                 return addr.to_bytes(2, 'big')

#         return None

#     def _str2bytes(self, addr: str) -> bytes:
#         try:
#             addr_b = bytes.fromhex(addr)
#             return addr_b
#         except ValueError:
#             return None

#     def _add_trailing_zeros(self, uuid: bytes) -> bytes:
#         if len(uuid) >= 16:
#             return uuid[-16:]
#         else:
#             zeros = bytes(16 - len(uuid))
#             return uuid + zeros

#     def _parse_template(self, filename) -> dict:
#         opts = {'name': None, 'net': None, 'uuid': None, 'addr': None,
#                 'no_file': False, 'debug': False}

#         template = file_helper.read(filename)
#         if not template:
#             opts['no_file'] = True
#             return opts

#         try:
#             opts['name'] = template_helper.get_field(template, 'name')
#         except Exception:
#             opts['name'] = None

#         try:
#             opts['net'] = template_helper.get_field(template, 'network')
#         except Exception:
#             opts['net'] = None

#         try:
#             opts['uuid'] = template_helper.get_field(template, 'uuid')
#         except Exception:
#             opts['uuid'] = None

#         try:
#             opts['debug'] = template_helper.get_field(template, 'debug')
#         except Exception:
#             opts['debug'] = None

#         try:
#             opts['addr'] = template_helper.get_field(template, 'address')
#             if len(opts['addr']) != 4:
#                 opts['addr'] = opts['addr']
#         except Exception:
#             opts['addr'] = None

#         return opts

#     def _provisioning_device(self, device_uuid: bytes, network: str,
#                              addr: bytes, debug: bool):
#         print(colored.cyan(f'Provisioning device "{device_uuid}" to network '
#                            f'"{network}"'))
#         success = False
#         devkey = None
#         net_data = NetworkData.load(base_dir + net_dir + network + '.yml')

#         try:
#             loop = asyncio.get_event_loop()
#             prov = Provisioner(loop, device_uuid, net_data.key,
#                                net_data.key_index, net_data.iv_index, addr,
#                                debug=debug)
#             asyncio.gather(prov.spwan_tasks(loop))
#             loop.run_forever()
#         except Exception as e:
#             print(f'Unknown error\n{e}')
#         except LinkOpenError:
#             pass
#         except ProvisioningError:
#             pass
#         except ProvisioningSuccess:
#             devkey = prov.devkey
#             success = True
#         except KeyboardInterrupt:
#             print(colored.yellow('Interruption by user'))
#             if prov and prov.tasks_h:
#                 prov.tasks_h.cancel()
#                 close_task = asyncio.gather(prov.close_link(b'\x02'))
#                 loop.run_until_complete(close_task)
#         except RuntimeError:
#             print('Runtime error')
#         finally:
#             prov.disconnect()
#             tasks_running = asyncio.Task.all_tasks()
#             for t in tasks_running:
#                 t.cancel()
#             loop.stop()

#         return success, devkey

#     def digest(self, flags, flags_values):
#         opts = {'name': None, 'net': None, 'uuid': None, 'addr': None}

#         for x in range(len(flags)):
#             f = flags[x]
#             fv = flags_values[x]
#             if f == '-h' or f == '--help':
#                 print(self._help)
#                 return
#             elif f == '-t' or f == '--template':
#                 if fv is None:
#                     print(colored.red('Template filename is required'))
#                     return
#                 opts = self._parse_template(fv)
#                 if opts['no_file']:
#                     print(colored.red(f'File "{fv}" not found'))
#                     return
#                 elif opts['net'] is None:
#                     print(colored.red(f'Field "network" not found in template '
#                                       f'file "{fv}"'))
#                     return
#                 elif opts['uuid'] is None:
#                     print(colored.red(f'Field "uuid" not found in template '
#                                       f'file "{fv}"'))
#                     return
#                 elif opts['name'] is None:
#                     print(colored.red(f'Field "name" not found in template '
#                                       f'file "{fv}"'))
#                     return
#                 elif type(opts['addr']) is int:
#                     print(colored.red(f'The length of address must be . The '
#                                       f'actual length is {opts["addr"]}'))
#                     return
#                 else:
#                     break
#             elif f == '-n' or f == '--name':
#                 opts['name'] = fv
#             elif f == '-a' or f == '--address':
#                 opts['addr'] = fv
#             elif f == '-w' or f == '--network':
#                 opts['net'] = fv
#             elif f == '-i' or f == '--uuid':
#                 opts['uuid'] = fv
#             else:
#                 print(colored.red(f'Invalid flag {f}'))
#                 print(self._help)
#                 return

#         # name processing
#         if opts['name'] is None:
#             print(colored.red('Name is required'))
#             return

#         if self._node_name_exist(opts['name']):
#             print(colored.red(f'The node name "{opts["name"]}" already exist'))
#             return

#         # network processing
#         if opts['net'] is None:
#             print(colored.red('Network is required'))
#             return

#         if not self._node_network_exist(opts['net']):
#             print(colored.red(f'The network "{opts["net"]}" not exist'))
#             return

#         # uuid processing
#         if opts['uuid'] is None:
#             print(colored.red('Device UUID is required'))
#             return

#         opts['uuid'] = self._str2bytes(opts['uuid'])
#         if opts['uuid'] is None:
#             print(colored.red('Invalid device UUID. Please enter with a '
#                               'string of hexadecimal digits'))
#             return

#         opts['uuid'] = self._add_trailing_zeros(opts['uuid'])

#         # addr processing
#         if opts['addr'] is None:
#             opts['addr'] = self._generate_node_addr()
#             if opts['addr'] is None:
#                 print(colored.red('The maxium number of node address has '
#                                   'already reached'))
#                 return
#         else:
#             opts['addr'] = self._str2bytes(opts['addr'])
#             if opts['addr'] is None:
#                 print(colored.red('Invalid address. Please enter with a '
#                                   'string of hexadecimal digits'))
#                 return
#             if self._node_addr_exist(opts['addr']):
#                 print(colored.red(f'The node address "{opts["addr"].hex()}" '
#                                   f'already exist'))
#                 return

#         # provisioning device
#         success, devkey = self._provisioning_device(opts['uuid'], opts['net'],
#                                                     opts['addr'],
#                                                     opts['debug'])
#         if not success:
#             print(colored.red(f'Error in provisioning'))
#             return

#         node_data = NodeData(name=opts['name'], addr=opts['addr'],
#                              network=opts['net'], device_uuid=opts['uuid'],
#                              devkey=devkey)
#         node_data.save()

#         print(colored.green('A new node was created.'))
#         print(colored.green(node_data))
from Crypto.Random import get_random_bytes
from client.node.node_data import NodeData, node_name_list, node_addr_list
from client.network.network_data import NetworkData, net_name_list
from client.data_paths import base_dir, net_dir
from client.node.provisioner import Provisioner, LinkOpenError, \
                                    ProvisioningSuccess, ProvisioningError
from common.file import file_helper
from common.template import template_helper
import click
import asyncio


def validate_name(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if node_name_list() and value in node_name_list():
        raise click.BadParameter(f'The "{value}" node already exist')
    return value


def validate_network(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if not net_name_list() or value not in net_name_list():
        raise click.BadParameter(f'The "{value}" network not exist')
    return value


def validate_uuid(ctx, param, value):
    if not value:
        raise click.BadParameter('This option is required')
    if len(value) % 2 == 1:
        value = '0' + value
    return value


def validate_addr(ctx, param, value):
    if not value:
        raise click.BadParameter('The maximum number of nodes was '
                                 'reached')
    if len(value) != 4:
        raise click.BadParameter('The length of node address is 2 bytes')
    return value


def random_addr():
    addr_list = node_addr_list()

    for x in range(2**16):
        addr = get_random_bytes(2)
        if addr not in addr_list:
            return addr.hex()

    return None


def provisioning_device(device_uuid: bytes, network: str,
                        addr: bytes, debug: bool):
    click.echo(click.style(f'Provisioning device "{device_uuid}" to network '
                           f'"{network}"', fg='cyan'))
    success = False
    devkey = None
    net_data = NetworkData.load(base_dir + net_dir + network + '.yml')

    try:
        loop = asyncio.get_event_loop()
        prov = Provisioner(loop, device_uuid, net_data.key,
                           net_data.key_index, net_data.iv_index, addr,
                           debug=debug)
        asyncio.gather(prov.spwan_tasks(loop))
        loop.run_forever()
    except Exception as e:
        click.echo(f'Unknown error\n{e}')
    except LinkOpenError:
        pass
    except ProvisioningError:
        pass
    except ProvisioningSuccess:
        devkey = prov.devkey
        success = True
    except KeyboardInterrupt:
        click.echo(click.style('Interruption by user', fg='yellow'))
        if prov and prov.tasks_h:
            prov.tasks_h.cancel()
            close_task = asyncio.gather(prov.close_link(b'\x02'))
            loop.run_until_complete(close_task)
    except RuntimeError:
        click.echo('Runtime error')
    finally:
        prov.disconnect()
        tasks_running = asyncio.Task.all_tasks()
        for t in tasks_running:
            t.cancel()
        loop.stop()

    return success, devkey


def parse_template(ctx, param, value):
    if not value:
        return value

    template = file_helper.read(value)
    if not template:
        raise click.BadParameter(f'File "{value}" not found')

    try:
        name = template_helper.get_field(template, 'name')
        validate_name(ctx, param, name)
    except KeyError:
        raise click.BadParameter(f'Field "name" not found in template file '
                                 f'"{value}"')

    try:
        network = template_helper.get_field(template, 'network')
        validate_network(ctx, param, network)
    except KeyError:
        raise click.BadParameter(f'Field "network" not found in template file '
                                 f'"{value}"')

    try:
        uuid = template_helper.get_field(template, 'uuid')
    except KeyError:
        raise click.BadParameter(f'Field "uuid" not found in template file '
                                 f'"{value}"')

    try:
        address = template_helper.get_field(template, 'address')
        validate_addr(ctx, param, address)
    except KeyError:
        address = random_addr()

    if len(uuid) < 32:
        uuid = bytes.fromhex(uuid) + bytes((32 - len(uuid)) // 2)
    elif len(uuid) > 32:
        uuid = bytes.fromhex(uuid)[0:16]
    else:
        uuid = bytes.fromhex(uuid)

    # provisioning device
    success, devkey = provisioning_device(uuid, network, address, False)
    if not success:
        click.echo(click.style('Error in provisioning', fg='red'))
    else:
        node_data = NodeData(name=name, addr=address, network=network,
                             device_uuid=uuid, devkey=devkey)
        node_data.save()

        click.echo(click.style('A new node was created.', fg='green'))
        click.echo(click.style(str(node_data), fg='green'))

    ctx.exit()


@click.command()
@click.option('--name', '-n', type=str, default='', required=True,
              help='Specify the name of node', callback=validate_name)
@click.option('--network', '-w', type=str, default='', required=True,
              help='Specify the name of network', callback=validate_network)
@click.option('--uuid', '-i', type=str, default='', required=True,
              help='Specify the UUID of target device', callback=validate_uuid)
@click.option('--address', '-a', type=str, default=random_addr(),
              help='Specify the address of node', callback=validate_addr)
@click.option('--template', '-t', type=str, default='',
              help='Specify a YAML template file. A file example is shown in'
                   ' node_template.yml. This template file must contain the '
                   '"name", "network" and "uuid" keyword.',
                   callback=parse_template, is_eager=True)
def new(name, network, address, uuid, template):
    '''Create a new node'''

    if len(uuid) < 32:
        uuid = bytes.fromhex(uuid) + bytes((32 - len(uuid)) // 2)
    elif len(uuid) > 32:
        uuid = bytes.fromhex(uuid)[0:16]
    else:
        uuid = bytes.fromhex(uuid)

    # provisioning device
    success, devkey = provisioning_device(uuid, network, address, False)
    if not success:
        click.echo(click.style('Error in provisioning', fg='red'))
    else:
        node_data = NodeData(name=name, addr=address, network=network,
                             device_uuid=uuid, devkey=devkey)
        node_data.save()

        click.echo(click.style('A new node was created.', fg='green'))
        click.echo(click.style(str(node_data), fg='green'))

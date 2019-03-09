from view.page import Page
from view.question import *
from view.options import *
from model.mesh_manager import mesh_manager
from core.provisioning import Provisioning
from core.gprov import GenericProvisioner
from core.dongle import DongleDriver
from serial import Serial
from serial.serialutil import SerialException
from core.scheduling import scheduler
import platform
from model.device import Device
from client.crypto import CRYPTO


def _node_name_check(name: str):
    nodes = list(mesh_manager.nodes.keys())
    return name not in nodes


def _get_devices():
    return [f'Device {dev.uuid.hex()}' for dev in list(mesh_manager.devices.values())]


def _list_networks():
    return list(mesh_manager.networks.keys())


class CreateNodeCommand(Element):

    def __init__(self):
        super().__init__()

    def _config_provisioner(self):
        serial = Serial()
        serial.baudrate = 115200
        serial.port = self._get_serial_port()
        dongle_driver = DongleDriver(serial)
        gprov = GenericProvisioner(dongle_driver)
        provisioning = Provisioning(gprov, dongle_driver)
        return provisioning

    def _get_serial_port(self):
        self.dongle_port = 'COM3' if platform.system() == 'Windows' else '/dev/ttyACM0'
        return self.dongle_port

    def _provisioning(self, dev_name: str, net_name: str, unicast_address: bytes):
        try:
            prov = self._config_provisioner()
        except SerialException:
            permission = '' if platform.system() == 'Windows' else "Use 'sudo chmod 777 {self.dongle_port}' para " \
                                                                   "dar permissão para o dongle"
            puts(colored.red(f"O dongle não está na porta {self.dongle_port} ou está sem permissão." + permission))
            return exit_cmd

        device_uuid = mesh_manager.devices[dev_name].uuid
        net_key = mesh_manager.networks[net_name].key
        key_index = mesh_manager.networks[net_name].index
        iv_index = mesh_manager.networks[net_name].iv_index

        connection_id = 0xaabbccdd
        prov_task = scheduler.spawn_task(prov.provisioning_device_t, connection_id=connection_id,
                                         device_uuid=device_uuid, net_key=net_key, key_index=key_index,
                                         iv_index=iv_index, unicast_address=unicast_address)

        scheduler.run()

        # while True:
        if prov_task.has_error():
            return 'ERROR'
        else:
            return 'OK'

    def run(self, page, options):
        node_name = page.element_results[1]
        net_name = page.element_results[2]
        dev_name = page.element_results[3]

        node = mesh_manager.new_node(node_name, net_name)

        with indent(len(page.quote) + 1, quote=''):
            ret = self._provisioning(dev_name, net_name, node.unicast_address)
            if ret == exit_cmd:
                return exit_cmd
            elif ret == 'ERROR':
                puts(colored.red(f'Error to configure {dev_name}'))
                return exit_cmd

        node.save()
        mesh_manager.remove_device(dev_name)

        with indent(len(page.quote) + 1, quote=page.quote):
            puts(colored.blue('Uma novo nó foi criado'))
        with indent(len(page.quote) + 1, quote=''):
            puts(colored.blue('Nome: ') + f'{node.name}')
            puts(colored.blue('Endereço Unicast: ') + f'{node.unicast_address}')
            puts(colored.blue('Rede associada ao nó: ') + f'{node.net_name}')


create_node_page = Page()
create_node_page += Question(question='Qual o nome do nó que será criado', end_quote=Q_MARK,
                             valid_answer_check=_node_name_check)
create_node_page += ConditionalOptions(description='Escolha qual das redes abaixo o nó fará parte:',
                                       fail_description="Nenhuma rede encontrada. Por favor, crie uma rede antes de "
                                                        "criar um nó, com o comando 'create network'",
                                       dynamic_options=_list_networks)
create_node_page += ConditionalOptions(description='Escolha o dispositivo alvo', fail_description="Nenhum dispositivo "
                                                                                                  "encontrado. "
                                                                                                  "Por favor, "
                                                                                                  "use o comando "
                                                                                                  "'scan devices' "
                                                                                                  "para encontrar "
                                                                                                  "novos dipositivos",
                                       dynamic_options=_get_devices)
create_node_page += CreateNodeCommand()

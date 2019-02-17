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
        self.dongle_port = '/dev/ttyACM0'
        return self.dongle_port

    def _provisioning(self, dev_name: str, net_name: str, unicast_address: bytes):
        prov = self._config_provisioner()

        device_uuid = mesh_manager.devices[dev_name].uuid
        net_key = mesh_manager.networks[net_name].key
        key_index = CRYPTO.k3(net_key)
        iv_index = mesh_manager.networks[net_name].iv_index

        scheduler.run()

        connection_id = 0xaabbccdd
        scheduler.spawn_task(prov.provisioning_device_t, connection_id=connection_id, device_uuid=device_uuid,
                             net_key=net_key, key_index=key_index, iv_index=iv_index, unicast_address=unicast_address)

        while prov.is_alive:
            pass

    def run(self, page):
        node_name = page.element_results[1]
        net_name = page.element_results[2]
        dev_name = page.element_results[3]

        node = mesh_manager.new_node(node_name, net_name)

        self._provisioning(dev_name, net_name, node.unicast_address)

        with indent(len(page.quote) + 1, quote=page.quote):
            puts(colored.blue('Uma novo nó foi criado'))
        with indent(len(page.quote) + 1, quote=''):
            puts(colored.blue('Nome: ') + f'{node.name}')
            puts(colored.blue('Endereço Unicast: ') + f'{node.unicast_address}')
            puts(colored.blue('Rede associada ao nó: ') + f'{node.net_name}')


create_node_page = Page(arguments=['create', 'node'])
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

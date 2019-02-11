from view.page import Page
from view.question import *
from view.options import *
from model.mesh_manager import mesh_manager


def _node_name_check(name: str):
    return True


def _get_devices():
    return [f'Device {dev.uuid.hex()}' for dev in list(mesh_manager.devices.values())]


def _list_networks():
    return list(mesh_manager.networks.keys())


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

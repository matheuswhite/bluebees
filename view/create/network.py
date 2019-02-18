from view.page import Page
from view.question import *
from view.element import Element
from clint.textui import puts, colored, indent
from model.mesh_manager import mesh_manager


def _network_name_check(name: str):
    nets = list(mesh_manager.networks.keys())
    return name not in nets


class CreateNetworkCommand(Element):

    def __init__(self):
        super().__init__()

    def run(self, page):
        network_name = page.element_results[1]
        network = mesh_manager.new_network(network_name)

        with indent(len(page.quote) + 1, quote=page.quote):
            puts(colored.blue('Uma nova rede foi criada'))
        with indent(len(page.quote) + 1, quote=''):
            puts(colored.blue('Nome: ') + f'{network_name}')
            puts(colored.blue('Network key: ') + f'{network.key}')
            puts(colored.blue('Network index: ') + f'{network.index}')
            puts(colored.blue('IV index: ') + f'{network.iv_index}')


create_network_page = Page(arguments=['create', 'network'])
create_network_page += Question(question='Qual o nome do rede que será criada', end_quote=Q_MARK,
                                valid_answer_check=_network_name_check)
create_network_page += CreateNetworkCommand()

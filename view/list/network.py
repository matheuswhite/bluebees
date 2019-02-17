from view.page import Page
from view.element import Element
from clint.textui import puts, colored, indent
from model.mesh_manager import mesh_manager


class ListNetworkCommand(Element):

    def __init__(self):
        super().__init__()

    def run(self, page):
        nets = mesh_manager.networks.keys()
        if len(nets) == 0:
            with indent(len(page.quote) + 1, quote=page.quote):
                puts(colored.yellow("Nenhuma rede criada. Use o comando 'create network' para criar uma nova rede"))
        else:
            with indent(len(page.quote) + 1, quote=page.quote):
                puts(colored.blue('Redes criadas:'))
            with indent(len(page.quote) + 1, quote=''):
                for x in range(len(nets)):
                    puts(colored.blue(f'{x+1}. {nets[x]}'))


list_network_page = Page(arguments=['list', 'network'])
list_network_page += ListNetworkCommand()

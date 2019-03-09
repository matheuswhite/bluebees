from view.page import Page
from view.element import Element
from clint.textui import puts, colored, indent
from model.mesh_manager import mesh_manager


class ListNodeCommand(Element):

    def __init__(self):
        super().__init__()

    def run(self, page, options):
        nodes = list(mesh_manager.nodes.keys())
        if len(nodes) == 0:
            with indent(len(page.quote) + 1, quote=page.quote):
                puts(colored.yellow("Nenhum nó criado. Use o comando 'create node' para criar um novo nó"))
        else:
            with indent(len(page.quote) + 1, quote=page.quote):
                puts(colored.blue('Nós criados:'))
            with indent(len(page.quote) + 1, quote=''):
                for x in range(len(nodes)):
                    puts(colored.blue(f'{x+1}. {nodes[x]}'))


list_node_page = Page()
list_node_page += ListNodeCommand()

from view.page import Page
from view.element import Element
from clint.textui import puts, colored, indent
from model.mesh_manager import mesh_manager


class ListDevicesCommand(Element):

    def __init__(self):
        super().__init__()

    def run(self, page, options):
        devs = list(mesh_manager.devices.keys())
        if len(devs) == 0:
            with indent(len(page.quote) + 1, quote=page.quote):
                puts(colored.yellow("Nenhum disposivito escaneado. Use o comando 'scan device' para procurar novos "
                                    "dispositivos"))
        else:
            with indent(len(page.quote) + 1, quote=page.quote):
                puts(colored.blue('Dipositivos encontrados:'))
            with indent(len(page.quote) + 1, quote=''):
                for x in range(len(devs)):
                    puts(colored.blue(f'{x+1}. {devs[x]}'))


list_device_page = Page()
list_device_page += ListDevicesCommand()

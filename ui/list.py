from ui.ui import Command, Menu
import model.database


class ListNet(Command):

    def __init__(self, name):
        super().__init__(name)

    def run(self):
        nets = model.database.nets.get_all()
        if len(nets) == 0:
            print('No nets available')
        else:
            print('Nets available:')
            for n in nets:
                print(f'\t{n}')


class ListApps(Command):

    def __init__(self, name):
        super().__init__(name)

    def run(self):
        apps = model.database.apps.get_all()
        if len(apps) == 0:
            print('No apps available')
        else:
            print('Apps available:')
            for a in apps:
                print(f'\t{a}')


class ListNodes(Command):

    def __init__(self, name):
        super().__init__(name)

    def run(self):
        nodes = model.database.nodes.get_all()
        if len(nodes) == 0:
            print('No nodes available')
        else:
            print('Nodes available:')
            for n in nodes:
                print(f'\t{n}')


class ListDevices(Command):

    def __init__(self, name):
        super().__init__(name)

    def run(self):
        devs = model.database.devices.get_all()
        if len(devs) == 0:
            print('No devices available')
        else:
            print('Devices available:')
            for d in devs:
                print(f'\t{d}')


list_menu = Menu('List', 'What you want list?')
list_menu.add_choice(ListNet('Nets'))
list_menu.add_choice(ListApps('Apps'))
list_menu.add_choice(ListNodes('Nodes'))
list_menu.add_choice(ListDevices('Devices'))

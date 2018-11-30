from ui.ui import Command, Menu, BackCommand
from model.database import nets, apps, nodes, devices, Storage


class Detail(Command):

    def __init__(self, name, storage: Storage, parent):
        super().__init__(name)

        self.storage = storage
        self.parent = parent

    def run(self):
        item_selected_name = self.parent.answer
        item_selected = self.storage.get(item_selected_name)

        print(repr(item_selected))


class DetailMenu(Menu):

    def __init__(self, name, message, storage):
        super().__init__(name, message)

        self.storage = storage
        self.has_back_cmd = False

    def _atomic_run(self):
        self.choices = []
        self._children = {}
        coll = self.storage.get_all()
        for i in coll:
            self.add_choice(Detail(i.name, self.storage, self))
        self.add_choice(BackCommand('Back'))

        return super()._atomic_run()

    def run(self):
        super().run()


detail_menu = Menu('Detail', 'What you want detail?')
detail_menu.add_choice(DetailMenu('Net', 'What net you want detail?', storage=nets))
detail_menu.add_choice(DetailMenu('App', 'What app you want detail?', storage=apps))
detail_menu.add_choice(DetailMenu('Node', 'What node you want detail?', storage=nodes))
detail_menu.add_choice(DetailMenu('Device', 'What device you want detail?', storage=devices))

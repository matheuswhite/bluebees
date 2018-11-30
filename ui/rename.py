from ui.ui import Questions, SingleQuestion, Menu, BackCommand
from model.database import nets, apps, nodes, devices, Storage


# TODO: check if the name already exist in storage
class Rename(Questions):

    def __init__(self, name, storage: Storage, parent):
        super().__init__(name)

        self.storage = storage
        self.parent = parent
        self.question = SingleQuestion('Rename Single Question', f'Type \'{self.name}\' new name:', index=1,
                                       max_questions=1)

    def run(self):
        self.question.run()
        new_name = self.question.answer
        item_name = self.parent.answer

        self.storage.update_name(item_name, new_name)


class RenameMenu(Menu):

    def __init__(self, name, message, storage):
        super().__init__(name, message)

        self.storage = storage
        self.has_back_cmd = False

    def _atomic_run(self):
        self.choices = []
        self._children = {}
        coll = self.storage.get_all()
        for i in coll:
            self.add_choice(Rename(i.name, self.storage, self))
        self.add_choice(BackCommand('Back'))

        return super()._atomic_run()

    def run(self):
        super().run()


rename_menu = Menu('Rename', 'What you want rename?')
rename_menu.add_choice(RenameMenu('Net', 'What net you want rename?', storage=nets))
rename_menu.add_choice(RenameMenu('App', 'What app you want rename?', storage=apps))
rename_menu.add_choice(RenameMenu('Node', 'What node you want rename?', storage=nodes))
rename_menu.add_choice(RenameMenu('Device', 'What device you want rename?', storage=devices))

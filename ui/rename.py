from ui.ui import Questions, SingleQuestion, Menu, BackCommand
import model.database


# TODO: check if the name already exist in storage
class Rename(Questions):

    def __init__(self, name, storage: model.database.Storage, parent):
        super().__init__(name)

        self.storage = storage
        self.parent = parent
        self.question = SingleQuestion('Rename Single Question', f'Type \'{self.name}\' new name:')

    def run(self):
        self.question.run()
        new_name = self.question.answer
        item_name = self.parent.answer

        self.storage.update_name(item_name, new_name)


class RenameMenu(Menu):

    def __init__(self, name, message, index, storage):
        super().__init__(name, message, index=index)

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


rename_menu = Menu('Rename', 'What you want rename?', index=1)
rename_menu.add_choice(RenameMenu('Net', 'What net you want rename?', index=2, storage=model.database.nets))
rename_menu.add_choice(RenameMenu('App', 'What app you want rename?', index=2, storage=model.database.apps))
rename_menu.add_choice(RenameMenu('Node', 'What node you want rename?', index=2, storage=model.database.nodes))
rename_menu.add_choice(RenameMenu('Device', 'What device you want rename?', index=2, storage=model.database.devices))

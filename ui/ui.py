from PyInquirer import prompt
from ui.ui_config import default_style


class UiElement:

    def __init__(self, name):
        self.name = name

    def run(self):
        pass


class Command(UiElement):

    def __init__(self, name):
        super().__init__(name)

    def run(self):
        pass


class BackCommand(UiElement):

    def __init__(self, name):
        super().__init__(name)

    def run(self):
        return True


class SingleQuestion(UiElement):

    def __init__(self, name, message, default_option=None, style=None):
        super().__init__(name)

        self.message = message
        self.default_option = default_option
        self.style = style if style else default_style
        self.answer = None

    def run(self):
        message = f'{self.message} ({self.default_option})' if self.default_option else self.message
        question = {
            'type': 'input',
            'name': self.name,
            'message': message,
        }
        self.answer = prompt(question, style=self.style)
        self.answer = list(self.answer.values())[0]
        if self.answer == '' and self.default_option:
            self.answer = self.default_option
        if self.answer == '\\back' or self.answer == '\\b':
            return True


class Questions(UiElement):

    def __init__(self, name, questions=None):
        super().__init__(name)

        self.questions = questions if questions else []

    def add_question(self, question: UiElement):
        self.questions.append(question)

    def run(self):
        for q in self.questions:
            ret = q.run()
            if ret is not None:
                break


class Menu(UiElement):

    def __init__(self, name: str, message: str, index: int=None, style=None, has_back_cmd=True):
        super().__init__(name)

        self.message = message
        self.style = style if style else default_style
        self.choices = []
        self.answer = None
        self._children = {}
        self.index = str(index) if index is not None else '?'
        self.has_back_cmd = has_back_cmd
        if self.has_back_cmd:
            self.add_choice(BackCommand('Back'))

    def add_choice(self, choice: UiElement):
        self._children[choice.name] = choice
        if self.has_back_cmd:
            self.choices.insert(len(self.choices)-1, choice.name)
        else:
            self.choices.append(choice.name)

    def _atomic_run(self):
        question = {
            'type': 'list',
            'qmark': self.index,
            'name': self.name,
            'message': self.message,
            'choices': self.choices
        }
        self.answer = prompt(question, style=self.style)
        self.answer = list(self.answer.values())[0]
        ui_element = self._children[self.answer]
        print('\x1bc')
        return ui_element

    def run(self):
        is_back = None
        while is_back is None:
            ui_element = self._atomic_run()
            is_back = ui_element.run()

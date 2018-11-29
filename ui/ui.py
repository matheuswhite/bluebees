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


class Questions(UiElement):

    def __init__(self, name, questions=None):
        super().__init__(name)

        self.questions = questions if questions else []

    def add_question(self, question: UiElement):
        self.questions.append(question)

    def run(self):
        for q in self.questions:
            q.run()


class Menu(UiElement):

    def __init__(self, name: str, message: str, style=None):
        super().__init__(name)

        self.message = message
        self.style = style if style else default_style
        self.choices = []
        self._answer = None
        self._children = {}

    def add_choice(self, choice: UiElement):
        self._children[choice.name] = choice
        self.choices.append(choice.name)

    def run(self):
        question = {
            'type': 'list',
            'name': self.name,
            'message': self.message,
            'choices': self.choices
        }
        self._answer = prompt(question, style=self.style)
        self._answer = list(self._answer.values())[0]
        ui_element = self._children[self._answer]
        ui_element.run()

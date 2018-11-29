from ui.ui import Command, SingleQuestion, Menu, Questions


class CreateNet(Command):

    def __init__(self, name, parent: Questions):
        super().__init__(name)

        self.parent = parent
        self.answer = None

    def run(self):
        answers = [q.answer for q in self.parent.questions]
        for i in range(len(answers)-1):
            print(f'Answer {i}: {answers[i]}')


class CreateApp(Command):

    def __init__(self, name, parent: Questions):
        super().__init__(name)

        self.parent = parent
        self.answer = None

    def run(self):
        answers = [q.answer for q in self.parent.questions]
        for i in range(len(answers)-1):
            print(f'Answer {i}: {answers[i]}')


class CreateNode(Command):

    def __init__(self, name, parent: Questions):
        super().__init__(name)

        self.parent = parent
        self.answer = None
        self.node_counter = 0
        self.parent.questions[0].default_option = f'node{self.node_counter}'

    def run(self):
        answers = [q.answer for q in self.parent.questions]
        for i in range(len(answers)-1):
            print(f'Answer {i}: {answers[i]}')
        self.node_counter += 1
        self.parent.questions[0].default_option = f'node{self.node_counter}'


_create_net_menu = Questions('Net')
_create_net_menu.add_question(SingleQuestion('Name', 'Enter a net name:'))
_create_net_menu.add_question(SingleQuestion('Address', 'Enter the net address:'))
_create_net_menu.add_question(CreateNet('Create Net', _create_net_menu))

_create_app_menu = Questions('App')
_create_app_menu.add_question(SingleQuestion('Name', 'Enter a app name:'))
_create_app_menu.add_question(SingleQuestion('Address', 'Enter the app address:'))
_create_app_menu.add_question(CreateApp('Create App', _create_app_menu))

_create_node_menu = Questions('Node')
_create_node_menu.add_question(SingleQuestion('Name', 'Enter a node name:'))
_create_node_menu.add_question(SingleQuestion('Address', 'Enter the node address:'))
_create_node_menu.add_question(CreateNode('Create Node', _create_node_menu))

create_menu = Menu('Create', 'What you want create?')
create_menu.add_choice(_create_net_menu)
create_menu.add_choice(_create_app_menu)
create_menu.add_choice(_create_node_menu)

from ui.ui import Command, SingleQuestion, Menu, Questions
from model.node import Node
from model.app import App
from model.net import Net
from model.database import nets, apps, nodes, devices, Storage
import re


class CreateNet(Command):

    def __init__(self, name, parent: Questions):
        super().__init__(name)

        self.parent = parent
        self.answer = None
        self.net_cnt = 0
        self.parent.questions[0].default_option = f'net{self.net_cnt}'

    def run(self):
        answers = [q.answer for q in self.parent.questions]
        net = Net(answers[0], answers[1])
        nets.add(net)
        print('New net created!')
        print(net)
        self.net_cnt += 1
        self.parent.questions[0].default_option = f'net{self.net_cnt}'


class CreateApp(Command):

    def __init__(self, name, parent: Questions):
        super().__init__(name)

        self.parent = parent
        self.answer = None
        self.app_cnt = 0
        self.parent.questions[0].default_option = f'app{self.app_cnt}'

    def run(self):
        answers = [q.answer for q in self.parent.questions]
        app = App(answers[0], answers[1])
        apps.add(app)
        print('New app created!')
        print(app)
        self.app_cnt += 1
        self.parent.questions[0].default_option = f'app{self.app_cnt}'


class CreateNode(Command):

    def __init__(self, name, parent: Questions):
        super().__init__(name)

        self.parent = parent
        self.answer = None
        self.node_cnt = 0
        self.parent.questions[0].default_option = f'node{self.node_cnt}'

    def run(self):
        answers = [q.answer for q in self.parent.questions]
        node = Node(answers[0], answers[1])
        nodes.add(node)
        print('New node created!')
        print(node)
        self.node_cnt += 1
        self.parent.questions[0].default_option = f'node{self.node_cnt}'


def is_word(val):
    return re.match(r'^\w+$', val) is not None


_create_net_menu = Questions('Net')
_create_net_menu.add_question(SingleQuestion('Name', 'Enter a net name:', index=1, max_questions=2,
                                             validate=is_word, validate_message='Forbidden name format. Use only '
                                                                                'underscore and alphanumerics'))
_create_net_menu.add_question(SingleQuestion('Address', 'Enter the net address:', index=2, max_questions=2))
_create_net_menu.add_question(CreateNet('Create Net', _create_net_menu))

_create_app_menu = Questions('App')
_create_app_menu.add_question(SingleQuestion('Name', 'Enter a app name:', index=1, max_questions=2,
                                             validate=is_word, validate_message='Forbidden name format. Use only '
                                                                                'underscore and alphanumerics'))
_create_app_menu.add_question(SingleQuestion('Address', 'Enter the app address:', index=2, max_questions=2))
_create_app_menu.add_question(CreateApp('Create App', _create_app_menu))

_create_node_menu = Questions('Node')
_create_node_menu.add_question(SingleQuestion('Name', 'Enter a node name:', index=1, max_questions=2,
                                             validate=is_word, validate_message='Forbidden name format. Use only '
                                                                                'underscore and alphanumerics'))
_create_node_menu.add_question(SingleQuestion('Address', 'Enter the node address:', index=2, max_questions=2))
_create_node_menu.add_question(CreateNode('Create Node', _create_node_menu))

create_menu = Menu('Create', 'What you want create?')
create_menu.add_choice(_create_net_menu)
create_menu.add_choice(_create_app_menu)
create_menu.add_choice(_create_node_menu)

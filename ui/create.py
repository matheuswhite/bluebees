from ui.ui import Command, SingleQuestion, Menu, Questions
from model.node import Node
from model.app import App
from model.net import Net
import model.database


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
        model.database.nets.add(net)
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
        model.database.apps.add(app)
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
        model.database.nodes.add(node)
        print('New node created!')
        print(node)
        self.node_cnt += 1
        self.parent.questions[0].default_option = f'node{self.node_cnt}'


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

create_menu = Menu('Create', 'What you want create?', index=1)
create_menu.add_choice(_create_net_menu)
create_menu.add_choice(_create_app_menu)
create_menu.add_choice(_create_node_menu)

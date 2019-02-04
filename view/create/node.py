from view.page import Page
from view.question import *
from view.options import *
from view.password import *


def _tf_check(answer: str):
    answer = answer.lower()
    return answer in ['yes', 'y', 'no', 'n']


def _node_name_check(name: str):
    return True


def _get_devices():
    return ['device 1234', 'device 1024', 'device 5991']


create_node_page = Page(arguments=['create', 'node'])
create_node_page += Password(description='Entre com uma senha')
create_node_page += Question(question='Qual o nome do nó que será criado', end_quote=Q_MARK,
                             valid_answer_check=_node_name_check)
create_node_page += Options(description='Escolha o dispositivo que deseja provisionar', dynamic_options=_get_devices)

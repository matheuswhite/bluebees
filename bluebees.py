# -*- coding: utf-8 -*-
"""
hierarchical prompt usage example
"""
from PyInquirer import style_from_dict, Token, prompt

devs = [
    '0001',
    '0002',
    '0003',
    '0004'
]

style = style_from_dict({
    Token.Separator: '#6C6C6C',
    Token.QuestionMark: '#0080FF bold',
    #Token.Selected: '',  # default
    Token.Selected: '#FF9D00 bold',
    Token.Pointer: '#FF9D00 bold',
    Token.Instruction: '#0080FF',  # default
    Token.Answer: '#FF9D00',
    Token.Question: '#0080FF bold',
})

commands_prompt = {
    'type': 'list',
    'name': 'command',
    'message': 'Choose command:',
    'choices': ['Create', 'Name', 'Bind Devices', 'List', 'Detail']
}

create_prompt = {
    'type': 'list',
    'name': 'Create',
    'message': 'What you want create?',
    'choices': ['Net', 'App', 'Node']
}

name_prompt = {
    'type': 'list',
    'name': 'Name',
    'message': 'What you want name?',
    'choices': ['Net', 'App', 'Node', 'Devices']
}

bind_devices_prompt = {
    'type': 'list',
    'name': 'Bind Devices',
    'message': 'What is the first device you want bind?',
    'choices': devs
}

list_prompt = {
    'type': 'list',
    'name': 'List',
    'message': 'What you want list?',
    'choices': ['Net', 'App', 'Node', 'Devices', 'All']
}

detail_prompt = {
    'type': 'list',
    'name': 'Detail',
    'message': 'What you want name?',
    'choices': ['Net', 'App', 'Node', 'Devices']
}

sub_cmds = {
    create_prompt['name']: create_prompt,
    list_prompt['name']: list_prompt,
    name_prompt['name']: name_prompt,
    detail_prompt['name']: detail_prompt,
    bind_devices_prompt['name']: bind_devices_prompt
}

if __name__ == '__main__':
    while True:
        try:
            cmd = prompt(commands_prompt, style=style)
            sub_cmd = sub_cmds[cmd['command']]
            print(prompt(sub_cmd, style=style))
        except KeyError:
            break

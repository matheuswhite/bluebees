# -*- coding: utf-8 -*-
"""
hierarchical prompt usage example
"""
from PyInquirer import style_from_dict, Token, prompt

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
    'choices': ['Create', 'List', 'Name', 'Detail']
}

create_prompt = {
    'type': 'list',
    'name': 'Create',
    'message': 'What you want create?',
    'choices': ['Node', 'App', 'Net']
}

list_prompt = {
    'type': 'list',
    'name': 'List',
    'message': 'What you want list?',
    'choices': ['Devices', 'Nodes', 'Apps', 'Nets', 'All']
}

name_prompt = {
    'type': 'list',
    'name': 'Name',
    'message': 'What you want name?',
    'choices': ['Device', 'Node', 'App', 'Net']
}

detail_prompt = {
    'type': 'list',
    'name': 'Detail',
    'message': 'What you want name?',
    'choices': ['Device', 'Node', 'App', 'Net']
}

sub_cmds = {
    create_prompt['name']: create_prompt,
    list_prompt['name']: list_prompt,
    name_prompt['name']: name_prompt,
    detail_prompt['name']: detail_prompt,
}

if __name__ == '__main__':
    while True:
        try:
            cmd = prompt(commands_prompt, style=style)
            sub_cmd = sub_cmds[cmd['command']]
            print(prompt(sub_cmd, style=style))
        except KeyError:
            break

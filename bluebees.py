# -*- coding: utf-8 -*-
from clint.arguments import Args
from view.page import Page
from typing import List
from clint.textui import indent, puts, colored
from view.create.node import create_node_page
from view.create.network import create_network_page
from view.scan.device import scan_device_page
from view.list.network import list_network_page
from view.list.device import list_device_page
from view.list.node import list_node_page


def rebuild_cmd(args: List):
    cmd = "'"
    for a in args:
        cmd += f'{a} '
    return cmd[:-1] + "'"


def main():
    args = Args()

    main_page = {
        'create': {
            'network': create_network_page,
            'node': create_node_page
        },
        'list': {
            'device': list_device_page,
            'network': list_network_page,
            'node': list_node_page
        },
        'scan': {
            'device': scan_device_page
        }
    }

    grouped_args = args.grouped
    flags = args.flags

    if '-h' in flags or '--help' in flags:
        print(f'Help {flags}')
        return

    try:
        page = main_page
        for a in grouped_args['_'][0:]:
            page = page[a]
    except KeyError:
        puts(colored.red(f'[ERR] The command {rebuild_cmd(args.all)} not exits'))
        return

    if type(page) is not Page:
        puts(colored.red(f'[ERR] The command {rebuild_cmd(args.all)} not exits'))
        return

    options = {}

    if '-t' in flags:
        options['template_file'] = grouped_args['-t'][0]
    elif '--template' in flags:
        options['template_file'] = grouped_args['-t'][0]
        page.run(template_file=options['template_file'])

    page.run(options=options)


if __name__ == '__main__':
    main()


#     license_ = '''
# MIT License
#
# Copyright (c) 2018 Matheus White
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# '''
#     logo = ' ____  _     _    _ ______ ____  ______ ______  _____\n'\
#            '|  _ \| |   | |  | |  ____|  _ \|  ____|  ____|/ ____|\n'\
#            '| |_) | |   | |  | | |__  | |_) | |__  | |__  | (___\n'\
#            '|  _ <| |   | |  | |  __| |  _ <|  __| |  __|  \___ \\\n'\
#            '| |_) | |___| |__| | |____| |_) | |____| |____ ____) |\n'\
#            '|____/|______\____/|______|____/|______|______|_____/'
#     print(logo)
#     print('\t\t\t\tMade by: Matheus White\n')

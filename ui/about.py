from ui.ui import Command,  Menu


class License(Command):

    def __init__(self, name):
        super().__init__(name)

    def run(self):
        license_ = '''
MIT License

Copyright (c) 2018 Matheus White

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
        '''
        print(license_)


class Credits(Command):

    def __init__(self, name):
        super().__init__(name)

    def run(self):
        logo = ' ____  _     _    _ ______ ____  ______ ______  _____\n' \
               '|  _ \| |   | |  | |  ____|  _ \|  ____|  ____|/ ____|\n' \
               '| |_) | |   | |  | | |__  | |_) | |__  | |__  | (___\n' \
               '|  _ <| |   | |  | |  __| |  _ <|  __| |  __|  \___ \\\n' \
               '| |_) | |___| |__| | |____| |_) | |____| |____ ____) |\n' \
               '|____/|______\____/|______|____/|______|______|_____/'
        print(logo)
        print('\t\t\t\tMade by: Matheus White\n')


about_menu = Menu('About', 'What you want know?', index=1)
about_menu.add_choice(License('License'))
about_menu.add_choice(Credits('Credits'))

from core.log import Log
from pyfiglet import Figlet

f = Figlet(font='big')

log = Log('Commands')

devs = [
    '0001',
    '0002',
    '0003',
    '0004',
    '0005',
]

apps_ = [
    '0213',
    '9283'
]


class Commands:

    def list(self, all=None, devices=None, apps=None, ):
        if devices or all:
            print('Devices UUID:')
            for i in range(len(devs)):
                print(f'\t{i}: {devs[i]}')
        if apps or all:
            print('Apps:')
            for i in range(len(apps_)):
                print(f'\t{i}: {apps_[i]}')

    def about(self):
        print('Made by: Matheus White')
        print(f.renderText('BLUEBEES'))

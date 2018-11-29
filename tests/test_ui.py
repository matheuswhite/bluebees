import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ui.create import create_menu

if __name__ == '__main__':
    while True:
        create_menu.run()

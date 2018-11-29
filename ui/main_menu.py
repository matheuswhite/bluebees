from ui.ui import Menu, BackCommand
from ui.create import create_menu
from ui.about import about_menu
from ui.list import list_menu

main_menu = Menu('main', 'Choose a command:', index=0, has_back_cmd=False)
main_menu.add_choice(create_menu)
main_menu.add_choice(list_menu)
main_menu.add_choice(about_menu)
main_menu.add_choice(BackCommand('Exit'))

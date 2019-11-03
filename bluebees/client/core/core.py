import click
from bluebees.client.core.commands.dongle import dongle
from bluebees.client.core.commands.hci import hci


@click.group()
def core():
    '''Bluebees core feature'''
    pass


core.add_command(dongle)
core.add_command(hci)

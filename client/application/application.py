import click
from client.application.commands.new import new
from client.application.commands.info import info
from client.application.commands.list import list


@click.group()
def app():
    '''Mesh application feature'''
    pass


app.add_command(new)
app.add_command(info)
app.add_command(list)

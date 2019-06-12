import click
from bluebees.client.core.core import core
from bluebees.client.network.network import net
from bluebees.client.application.application import app
from bluebees.client.node.node import node
from bluebees.client.device.device import device


@click.group()
def cli():
    pass


@cli.command()
def about():
    '''Show the about information'''
    click.echo(message=click.style('''
 ____  _     _    _ ______ ____  ______ ______  _____
|  _ \| |   | |  | |  ____|  _ \|  ____|  ____|/ ____|
| |_) | |   | |  | | |__  | |_) | |__  | |__  | (___
|  _ <| |   | |  | |  __| |  _ <|  __| |  __|  \___ \\
| |_) | |___| |__| | |____| |_) | |____| |____ ____) |
|____/|______\____/|______|____/|______|______|_____/
\t\t\t\tMade by: Matheus White''', fg='cyan'))


@cli.command()
def license():
    '''Show the licence of this software'''
    with open('LICENSE') as f:
        content = f.read()
        click.echo(content)


cli.add_command(core)
cli.add_command(net)
cli.add_command(app)
cli.add_command(node)
cli.add_command(device)

if __name__ == "__main__":
    cli()

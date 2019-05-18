import click
from client.core.core import core
from client.network.network import net
from client.application.application import app
from client.node.node import node


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
def licence():
    '''Show the licence of this software'''
    click.echo('''
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
SOFTWARE.''')


cli.add_command(core)
cli.add_command(net)
cli.add_command(app)
cli.add_command(node)

if __name__ == "__main__":
    cli()

import click
import warnings
import asyncio
from bluebees.client.core.dongle import Dongle
from bluebees.common.broker import Broker
from serial import SerialException


@click.command()
@click.option('--baudrate', '-b', type=int, default=115200,
              help='The baudrate of dongle', show_default=True)
@click.option('--port', '-p', type=str, default='COM9',
              help='The serial port of dongle', show_default=True)
def run(baudrate, port):
    '''Run the main features of bluebees. This features are:
         - Dongle Communication
         - Internal Broker'''

    click.echo(click.style(f'Serial port: {port}', fg='yellow'))
    click.echo(click.style(f'Baudrate: {baudrate}', fg='yellow'))
    click.echo('Running core features...')
    try:
        warnings.simplefilter('ignore')

        loop = asyncio.get_event_loop()
        broker = Broker(loop=loop)
        dongle = Dongle(loop=loop, serial_port=port, baudrate=baudrate)
        asyncio.gather(dongle.spwan_tasks(loop), broker.tasks())
        loop.run_forever()
    except KeyboardInterrupt:
        dongle.serial.close()
        dongle.disconnect()
        broker.disconnect()
    except RuntimeError:
        pass
    except SerialException:
        click.echo(click.style(f'Serial port {port} not avaolable', fg='red'))
    finally:
        for t in asyncio.Task.all_tasks():
            t.cancel()
        loop.stop()
        click.echo('Stop core features')

import click
import warnings
import asyncio
from bluebees.client.core.hci import HCI
from bluebees.common.broker import Broker
from serial import SerialException
from serial.tools.list_ports import comports
from asyncserial import Serial


@click.command()
def hci():
    '''Run the main features of bluebees. This features are:
         - Dongle Communication
         - Internal Broker'''

    loop = asyncio.get_event_loop()

    click.echo('Running core features using HCI...')
    try:
        warnings.simplefilter('ignore')
        broker = Broker(loop=loop)
        hci = HCI(loop=loop)
        asyncio.gather(hci.spwan_tasks(loop), broker.tasks())
        loop.run_forever()
    except KeyboardInterrupt:
        hci.finish()
        hci.disconnect()
        broker.disconnect()
    except RuntimeError:
        pass
    finally:
        for t in asyncio.Task.all_tasks():
            t.cancel()
        loop.stop()
        click.echo('Stop core features')

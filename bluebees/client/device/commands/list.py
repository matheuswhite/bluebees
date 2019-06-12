import click
import asyncio
from bluebees.client.device.list_devices import ListDevices


@click.command()
def list():
    '''List unprovisioned devices'''

    try:
        loop = asyncio.get_event_loop()
        list_devices = ListDevices()

        asyncio.gather(list_devices.spwan_tasks(loop))
        loop.run_forever()
    except KeyboardInterrupt:
        click.echo(click.style('Interruption by user', fg='yellow'))
    except RuntimeError:
        click.echo('Runtime error')
    except Exception as e:
        click.echo(f'Unknown error\n[{e}]')
    finally:
        list_devices.disconnect()
        tasks_running = asyncio.Task.all_tasks()
        for t in tasks_running:
            t.cancel()
        loop.stop()

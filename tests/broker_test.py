import sys
sys.path.append('C:\\Users\\tenor\\OneDrive\\Documentos\\bluebees\\')

import asyncio
from common.broker import Broker


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()

        broker = Broker(loop=loop)
        print('Running broker tasks...')
        task_group = asyncio.gather(broker.tasks())
        loop.run_until_complete(task_group)
    except KeyboardInterrupt:
        print('End of program')
        broker.disconnect()
    finally:
        for t in asyncio.Task.all_tasks():
            t.cancel()
        loop.stop()

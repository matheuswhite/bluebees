import sys
sys.path.append('C:\\Users\\tenor\\OneDrive\\Documentos\\bluebees\\')

import asyncio
from common.client import Client
from asyncio import CancelledError


class TestClient(Client):

    def __init__(self, topic_sub: bytes, topic_pub: bytes):
        super().__init__(sub_topic_list=[topic_sub],
                         pub_topic_list=[topic_pub])
        self.topic_pub = topic_pub

        self.all_tasks += [self.consumer(), self.produce()]

    async def produce(self):
        counter = 0
        while self.is_connected:
            await self.messages_to_send.put((self.topic_pub,
                                             f'Content {counter}'.encode('utf-8')))

            await asyncio.sleep(1)

            print(f'Sending data to {self.topic_pub}')
            counter += 1

    async def consumer(self):
        while self.is_connected:
            (topic, content) = await self.messages_received.get()

            print(f'Messsage {content} received from {topic} topic')


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        arg1 = sys.argv[1] if len(sys.argv) >= 2 else 'A'
        arg2 = sys.argv[2] if len(sys.argv) >= 3 else 'B'
        client1 = TestClient(topic_pub=f'channel{arg1}'.encode('utf-8'),
                             topic_sub=f'channel{arg2}'.encode('utf-8'))

        print('Running client tasks...')
        asyncio.gather(client1.spwan_tasks(loop))
        loop.run_forever()
    except KeyboardInterrupt:
        print('End of program')
        client1.disconnect()
    except RuntimeError as err:
        print('End of program')
    finally:
        tasks_running = asyncio.Task.all_tasks()
        for t in tasks_running:
            t.cancel()
        loop.stop()

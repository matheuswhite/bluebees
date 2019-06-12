import asyncio
import zmq.asyncio
from zmq.asyncio import Context
from bluebees.common.logging import log_sys, INFO
from bluebees.common.asyncio_fixup import wakeup


class Client:

    def __init__(self, sub_topic_list: list, pub_topic_list: list):
        self.pub_topic_list = pub_topic_list + [b'disconnect']
        self.messages_to_send = asyncio.Queue()
        self.messages_received = asyncio.Queue()

        self.client_log = log_sys.get_logger('client')
        self.client_log.set_level(INFO)

        self.pub_url = 'tcp://127.0.0.1:'
        self.broker_listen_url = 'tcp://127.0.0.1:9500'
        self.broker_pub_url = 'tcp://127.0.0.1:9501'

        self.ctx = Context.instance()

        self.pub_sock = self.ctx.socket(zmq.PUB)
        self.sub_sock = self.ctx.socket(zmq.SUB)

        self.sub_sock.connect(self.broker_pub_url)

        sub_topic_list += [b'disconnect']
        for st in sub_topic_list:
            self.sub_sock.setsockopt(zmq.SUBSCRIBE, st)

        self.loop = None
        self.tasks_h = None
        self.is_connected = False
        self.client_tasks = [self._subscribe_task(), self._publish_task()]
        self.all_tasks = []

    async def connect_to_broker(self):
        pub_topics = b' '.join(self.pub_topic_list)

        req_sock = self.ctx.socket(zmq.REQ)
        req_sock.connect(self.broker_listen_url)

        await req_sock.send(pub_topics)

        # ! blocking command
        pub_port = await req_sock.recv_multipart()
        pub_port = pub_port[0].decode('utf-8')

        self.pub_url += pub_port
        self.pub_sock.bind(self.pub_url)

        self.is_connected = True

    async def _subscribe_task(self):
        while self.is_connected:
            [topic, content] = await self.sub_sock.recv_multipart()

            self.client_log.debug(f'Receive message from "{topic}" topic with '
                                  f'{content} content')
            if topic == b'disconnect' and content == b'broker':
                self.is_connected = False
                self.client_log.critical('Disconnected from broker')
                self.loop.stop()

            await self.messages_received.put((topic, content))

    async def _publish_task(self):
        while self.is_connected:
            (topic, content) = await self.messages_to_send.get()

            self.client_log.debug(f'Sending message to "{topic}" topic with '
                                  f'{content} content')
            await self.pub_sock.send_multipart([topic, content])
            self.client_log.debug('Message sent')

    def disconnect(self):
        self.is_connected = False
        self.pub_sock.send_multipart([b'disconnect', b''])

    async def spwan_tasks(self, loop):
        self.loop = loop

        loop.create_task(wakeup())

        await self.connect_to_broker()
        self.client_log.success('Connected to broker')

        asyncio.gather(*self.client_tasks)
        self.tasks_h = asyncio.gather(*self.all_tasks)

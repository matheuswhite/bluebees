import asyncio
import zmq.asyncio
from zmq.asyncio import Context
from bluebees.common.logging import log_sys, INFO
from bluebees.common.asyncio_fixup import wakeup


class Broker:

    def __init__(self, loop):
        self.loop = loop
        self.publish_queue = asyncio.Queue()

        self.broker_log = log_sys.get_logger('broker')
        self.broker_log.set_level(INFO)

        self.listen_url = 'tcp://127.0.0.1:9500'
        self.pub_url = 'tcp://127.0.0.1:9501'
        self.ctx = Context.instance()

        self.pub_sock = self.ctx.socket(zmq.PUB)
        self.listen_sock = self.ctx.socket(zmq.REP)
        self.subs = {}

        self.pub_sock.bind(self.pub_url)
        self.listen_sock.bind(self.listen_url)

    def _gen_client_port(self):
        port = 9502
        while port in self.subs.keys():
            port += 1
            if port >= 9603:
                raise Exception('Max number of clients')

        return port

    async def _spawn_client(self, topic_list: list):
        client_port = self._gen_client_port()
        await self.listen_sock.send(str(client_port).encode('utf-8'))
        self.subs[client_port] = self.ctx.socket(zmq.SUB)
        self.subs[client_port].connect(f'tcp://127.0.0.1:{client_port}')
        for topic in topic_list:
            self.subs[client_port].setsockopt(zmq.SUBSCRIBE, topic)

        # ! spawn corroutine to receive data from topic_list on client port
        self.loop.create_task(self._subscribe_task(self.subs[client_port],
                                                   client_port))
        self.broker_log.info(f'New client connected using port {client_port}')

    async def _subscribe_task(self, sub_socket, port):
        while True:
            [topic, content] = await sub_socket.recv_multipart()

            if topic == b'disconnect' and content != b'broker':
                del self.subs[port]
                self.broker_log.warning(f'Client on port {port} diconnected')
                break

            await self.publish_queue.put((topic, content))

    async def _publish_task(self):
        while True:
            (topic, content) = await self.publish_queue.get()

            await self.pub_sock.send_multipart([topic, content])

    async def _listen_task(self):
        while True:
            content = await self.listen_sock.recv_multipart()
            topic_list = content[0].split(b' ')

            await asyncio.sleep(1)

            await self._spawn_client(topic_list)

    def disconnect(self):
        self.pub_sock.send_multipart([b'disconnect', b'broker'])

    def tasks(self):
        return asyncio.gather(self._listen_task(), self._publish_task(),
                              wakeup())

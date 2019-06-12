from bluebees.common.client import Client
from bluebees.common.logging import log_sys, INFO, DEBUG


class ListDevices(Client):

    def __init__(self):
        super().__init__(sub_topic_list=[b'beacon'], pub_topic_list=[])

        self.log = log_sys.get_logger('list_devices')
        self.log.set_level(INFO)
        self.index = 1
        self.cache = []

        self.all_tasks += [self.list_devices_task()]

    async def list_devices_task(self):
        self.log.success(f'Listing unprovisioned devices...')
        self.log.warning(f'Press Ctrl+C to cancel operation')

        while True:
            msg_type, content = await self.messages_received.get()

            if msg_type != b'beacon':
                self.log.debug(f'Message type wrong: {msg_type}')
                continue

            if content[0] != 0:
                self.log.debug(f'Not a unprovisioned device beacon')
                continue

            if content[1:] in self.cache:
                self.log.debug(f'UUID already in cache')
                continue

            self.cache.append(content[1:])
            self.log.info(f'{self.index}. {content[1:].hex()}')

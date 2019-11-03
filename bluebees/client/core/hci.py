import asyncio
from dataclasses import dataclass
from bluebees.common.client import Client
from bluebees.common.logging import log_sys, INFO, DEBUG
from asyncio import wait_for
from bluebees.bleson import MeshBeacon, Observer, get_provider


@dataclass
class AdvMessage:
    msg_type: bytes
    content: bytes

BT_DATA_MESH_PROV = b'\x29'
BT_DATA_MESH_MESSAGE = b'\x2a'
BT_DATA_MESH_BEACON = b'\x2b'

class HCI(Client):

    def __init__(self, loop):
        super().__init__(sub_topic_list=[b'message_s', b'prov_s'],
                         pub_topic_list=[b'message', b'prov', b'beacon'])

        self.log = log_sys.get_logger('hci')
        self.log.set_level(DEBUG)

        self.loop = loop

        self.caches = {
            b'message': [],
            b'beacon': [],
            b'prov': []
        }

        self.adapter = get_provider().get_adapter()
        self.observer = Observer(self.adapter)
        self.beacon = MeshBeacon(self.adapter)

        self.observer.on_advertising_data = self._advertisement_cb
        self.observer.start()

        self.all_tasks += [self._write_task(),
                           self._clear_caches_task()]

    def finish(self):
        self.observer.stop()
        self.beacon.stop()

    def _translate_adv_message(self, advertisement) -> (AdvMessage, bool):
        raw_data = advertisement.raw_data
        if raw_data[11:12] not in [BT_DATA_MESH_PROV, BT_DATA_MESH_MESSAGE, BT_DATA_MESH_BEACON]:
            return None, False

        msg_type = b''
        content = raw_data[12:]

        if raw_data[11:12] == BT_DATA_MESH_PROV:
            msg_type = b'prov'
        elif raw_data[11:12] == BT_DATA_MESH_MESSAGE:
            msg_type = b'message'
        elif raw_data[11:12] == BT_DATA_MESH_BEACON:
            msg_type = b'beacon'

        return AdvMessage(msg_type=msg_type, content=content), True

    async def _put_data(self, adv_msg):
        await self.messages_to_send.put((adv_msg.msg_type, adv_msg.content))

    def _advertisement_cb(self, advertisement):
        (adv_msg, is_valid) = self._translate_adv_message(advertisement)

        if not is_valid:
            return

        self.log.debug(f'Got a message with type {adv_msg.msg_type} and content {adv_msg.content.hex()}')

        self.loop.create_task(self._put_data(adv_msg))

    async def _clear_caches_task(self):
        while True:
            await asyncio.sleep(5 * 60)
            self.log.info('Cleaning caches...')
            self.caches = {
                b'message': [],
                b'beacon': [],
                b'prov': []
            }
            self.log.info('Caches clean')

    async def _send_adv(self, adv_msg: AdvMessage):
        beacon_type = b''
        if adv_msg.msg_type == b'prov_s':
            beacon_type = BT_DATA_MESH_PROV
        elif adv_msg.msg_type == b'message_s':
            beacon_type = BT_DATA_MESH_MESSAGE

        data = adv_msg.content
        self.beacon.set_packet(beacon_type, data)
        self.beacon.start()
        await asyncio.sleep(.2)
        self.beacon.stop()

    async def _write_task(self):
        while True:
            (msg_type, content) = await self.messages_received.get()
            self.log.debug(f'Send a message with type {msg_type} and content {content.hex()}')
            adv_msg = AdvMessage(msg_type, content)

            await self._send_adv(adv_msg)

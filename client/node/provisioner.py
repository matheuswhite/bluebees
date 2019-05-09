from common.client import Client
from dataclasses import dataclass
from clint.textui import colored
from common.utils import order, FinishAsync
from client.core.dongle import DongleMessage
from asyncio import wait_for, sleep
from ecdsa import NIST256p, SigningKey
from ecdsa.ellipticcurve import Point
from common.crypto import crypto
from Crypto.Random import get_random_bytes
import asyncio


@dataclass
class ProvisioningContext:
    device_link: bytes
    client_tr_number: int
    node_tr_number: int

    public_key: Point
    private_key: int
    node_public_key: Point
    ecdh_secret: bytes
    random_provisioner: bytes
    random_device: bytes
    confirmation_key: bytes
    confirmation_salt: bytes
    auth: bytes

    invite_pdu: bytes
    capabilities_pdu: bytes
    start_pdu: bytes
    node_confirmation: bytes


@dataclass
class DeviceInfo:
    uuid: bytes
    attention: int

    netkey: bytes
    key_index: bytes
    flags: bytes
    iv_index: bytes
    address: bytes


class Provisioner(Client):

    def __init__(self, loop, device_uuid: bytes, netkey: bytes,
                 key_index: bytes, iv_index: bytes, address: bytes,
                 flags=b'\x00', attention_duration=5):
        super().__init__(sub_topic_list=[b'prov'], pub_topic_list=[b'prov_s'])

        self.loop = loop
        self.device_info = DeviceInfo(uuid=device_uuid,
                                      attention=attention_duration,
                                      netkey=netkey,
                                      key_index=key_index,
                                      flags=flags,
                                      iv_index=iv_index,
                                      address=address)
        self.prov_ctx = ProvisioningContext(device_link=b'\xaa\xbb\xcc\xdd',
                                            client_tr_number=0x00,
                                            node_tr_number=0x80,
                                            public_key=None,
                                            private_key=None,
                                            ecdh_secret=None,
                                            random_provisioner=None,
                                            confirmation_key=None,
                                            auth=None,
                                            invite_pdu=None,
                                            capabilities_pdu=None,
                                            start_pdu=None,
                                            node_confirmation=None,
                                            confirmation_salt=None,
                                            random_device=None,
                                            node_public_key=None)

        self.all_tasks += [self._provisioning_device()]

    # link method
    async def _open_link(self):
        msg_type = b'prov_s'
        content = self.prov_ctx.device_link
        content += self.prov_ctx.client_tr_number.to_bytes(1, 'big')
        content += b'\x03'  # open opcode
        content += self.device_info.uuid

        await self.messages_to_send.put(DongleMessage(msg_type, content))

    async def _wait_link_ack(self):
        while True:
            (_, dongle_msg) = await self.messages_received.get()
            print('dbg1')
            msg_type = dongle_msg.msg_type
            content = dongle_msg.content

            print('dbg2')
            expected_tr_number = self.prov_ctx.client_tr_number.to_bytes(1,
                                                                         'big')

            print('dbg3')
            if msg_type == b'prov' and \
               content[0:4] == self.prov_ctx.device_link and \
               content[4:5] == expected_tr_number and content[5:6] == b'\x07':
                break
            print('dbg4')
        print('dbg5')

    async def close_link(self, reason: bytes):
        msg_type = b'prov_s'
        content = self.prov_ctx.device_link
        content += self.prov_ctx.client_tr_number.to_bytes(1, 'big')
        content += b'\x0b'

        for x in range(3):
            await self.messages_to_send.put(DongleMessage(msg_type, content))
            await sleep(1)

    # send pdu methods
    async def __wait_ack(self):
        while True:
            (_, dongle_msg) = await self.messages_received.get()
            msg_type = dongle_msg.msg_type
            content = dongle_msg.content

            expected_tr_number = self.prov_ctx.client_tr_number.to_bytes(1,
                                                                         'big')

            if msg_type == b'prov' and \
               content[0:4] == self.prov_ctx.device_link and \
               content[4:5] == expected_tr_number and content[5:6] == b'\x01':
                return

    async def _send_pdu(self, tries: int, phase_name: str, total_timeout: int,
                        mount_pdu_func) -> bool:
        timeout = int(tries / total_timeout)
        for try_ in range(tries):
            print(colored.cyan(f'Send {phase_name} PDU'))
            content = mount_pdu_func()

            await self.messages_to_send.put(DongleMessage(b'prov_s', content))

            try:
                print(colored.cyan('Waiting ack...'))
                await wait_for(self.__wait_ack(), timeout)

                print(colored.green(f'Send {phase_name} PDU successful'))
                self.prov_ctx.client_tr_number += 1
                return True
            except TimeoutError:
                print(colored.yellow(f'{try_ + 1}{order(try_ + 1)} '
                                     f'{phase_name} PDU fail'))

        return False

    # wait pdu methods
    async def __send_ack(self):
        content = self.prov_ctx.device_link
        content += self.prov_ctx.node_tr_number.to_bytes(1, 'big')
        content += b'\x01'

        await self.messages_to_send.put(DongleMessage(b'prov_s', content))

    async def __wait_pdu_atomic(self, check_pdu_func):
        while True:
            (_, dongle_msg) = await self.messages_received.get()
            msg_type = dongle_msg.msg_type
            content = dongle_msg.content

            expected_tr_number = self.prov_ctx.node_tr_number.to_bytes(1,
                                                                       'big')

            if msg_type == b'prov' and \
               content[0:4] == self.prov_ctx.device_link and \
               content[4:5] == expected_tr_number and \
               check_pdu_func(content[5:]):
                return

    async def _wait_pdu(self, ack_tries: int, phase_name: str, timeout: int,
                        check_pdu_func) -> bool:
        try:
            print(colored.cyan(f'Waiting {phase_name} PDU...'))
            await wait_for(self.__wait_pdu_atomic(check_pdu_func), timeout)

            for try_ in range(ack_tries):
                print(f'Send {try_ + 1}{order(try_ + 1)} ack pdu')
                await self.__send_ack()
                await sleep(1)

            self.prov_ctx.node_tr_number += 1
            return True
        except TimeoutError:
            return False

    # invite phase
    def _mount_invite_pdu(self) -> bytes:
        content = self.prov_ctx.device_link
        content += self.prov_ctx.client_tr_number.to_bytes(1, 'big')
        content += b'\x00'
        content += self.device_info.attention.to_bytes(1, 'big')

        self.prov_ctx.invite_pdu = content[6:]

        return content

    def _check_capabilities_pdu(self, content) -> bool:
        print(colored.magenta('Capabilities:'))
        print(colored.magenta(f'Number of Elements: {content[1]}'))
        print(colored.magenta(f'Algorithms: {int.from_bytes(content[2:4], "big")}'))
        print(colored.magenta(f'Public Key Type: {content[4]}'))
        print(colored.magenta(f'Static OOB Type: {content[5]}'))
        print(colored.magenta(f'Output OOB Size: {content[6]}'))
        print(colored.magenta(f'Output OOB Action: {int.from_bytes(content[7:9], "big")}'))
        print(colored.magenta(f'Input OOB Size: {content[9]}'))
        print(colored.magenta(f'Input OOB Action: {int.from_bytes(content[10:12], "big")}'))

        self.prov_ctx.capabilities_pdu = content[1:]

        return content[0:1] == b'\x01' and len(content[1:]) == 11

    # exchanging public key phase
    def _mount_start_pdu(self) -> bytes:
        content = self.prov_ctx.device_link
        content += self.prov_ctx.client_tr_number.to_bytes(1, 'big')
        content += b'\x02'
        content += b'\x00\x00\x00\x00\x00'

        self.prov_ctx.start_pdu = content[6:]

        return content

    def _mount_public_key_pdu(self) -> bytes:
        sk = SigningKey.generate(curve=NIST256p)
        vk = sk.get_verifying_key()
        self.prov_ctx.private_key = sk.privkey.secret_multiplier
        self.prov_ctx.public_key = vk.pubkey.point
        public_key_x = self.prov_ctx.public_key.x().to_bytes(32, 'big')
        public_key_y = self.prov_ctx.public_key.y().to_bytes(32, 'big')

        content = self.prov_ctx.device_link
        content += self.prov_ctx.client_tr_number.to_bytes(1, 'big')
        content += b'\x03'
        content += public_key_x
        content += public_key_y

        return content

    def _check_public_key_pdu(self, content) -> bool:
        self.prov_ctx.node_public_key = Point(curve=NIST256p.curve,
                                              x=int.from_bytes(content[1:33], 'big'),
                                              y=int.from_bytes(content[33:65], 'big'))

        self.prov_ctx.ecdh_secret = (self.prov_ctx.private_key * self.prov_ctx.node_public_key).x()

        return content[0:1] == b'\x03' and len(content[1:]) == 64

    # authentication phase
    def _mount_confirmation_pdu(self) -> bytes:
        self.prov_ctx.auth_value = bytes(16)

        self.prov_ctx.random_provisioner = get_random_bytes(16)

        confirmation_inputs = self.prov_ctx.invite_pdu
        confirmation_inputs += self.prov_ctx.capabilities_pdu
        confirmation_inputs += self.prov_ctx.start_pdu
        confirmation_inputs += self.prov_ctx.public_key.x().to_bytes(32, 'big')
        confirmation_inputs += self.prov_ctx.public_key.y().to_bytes(32, 'big')
        confirmation_inputs += self.prov_ctx.node_public_key.x().to_bytes(32, 'big')
        confirmation_inputs += self.prov_ctx.node_public_key.y().to_bytes(32, 'big')

        self.prov_ctx.confirmation_salt = crypto.s1(text=confirmation_inputs)
        self.prov_ctx.confirmation_key = crypto.k1(n=self.prov_ctx.ecdh_secret,
                                                   salt=self.prov_ctx.confirmation_salt,
                                                   p=b'prck')

        content = self.prov_ctx.device_link
        content += self.prov_ctx.client_tr_number.to_bytes(1, 'big')
        content += b'\x05'
        content += crypto.aes_cmac(key=confirmation_key,
                                   text=random_provisioner + auth_value)

        return content

    def _check_confirmation_pdu(self, content) -> bool:
        self.prov_ctx.node_confirmation = content[1:17]

        return content[0:1] == b'\x05' and len(content[1:]) == 16

    def _mount_random_pdu(self) -> bytes:
        content = self.prov_ctx.device_link
        content += self.prov_ctx.client_tr_number.to_bytes(1, 'big')
        content += b'\x06'
        content += self.prov_ctx.random_provisioner

        return content

    def _check_random_pdu(self, content) -> bool:
        self.prov_ctx.random_device = content[1:]

        calc_confirmation = crypto.aes_cmac(key=self.prov_ctx.confirmation_key,
                                            text=self.prov_ctx.random_device +
                                            self.prov_ctx.auth)

        return content[0:1] == b'\x06' and len(content[1:]) == 16 and \
            self.prov_ctx.node_confirmation == calc_confirmation

    # distribuition of provisioning data phase
    def _mount_data_pdu(self) -> bytes:
        prov_input = self.prov_ctx.confirmation_salt + \
                     self.prov_ctx.random_provisioner + \
                     self.prov_ctx.random_device
        prov_data = self.device_info.netkey + self.device_info.key_index + \
            self.device_info.flags + self.device_info.iv_index + \
            self.device_info.address

        prov_salt = crypto.s1(text=prov_input)
        session_key = crypto.k1(n=self.prov_ctx.ecdh_secret, salt=prov_salt,
                                p=b'prsk')
        session_nonce = crypto.k1(n=self.prov_ctx.ecdh_secret, salt=prov_salt,
                                  p=b'prsn')[3:]

        encrypted_data, data_mic = crypto.aes_ccm_complete(key=session_key,
                                                           nonce=session_nonce,
                                                           text=prov_data,
                                                           adata=b'')

        content = self.prov_ctx.device_link
        content += self.prov_ctx.client_tr_number.to_bytes(1, 'big')
        content += b'\x07'
        content += encrypted_data
        content += data_mic

        return content

    def _check_complete_pdu(self, content) -> bool:
        return content[0:1] == b'\x08'

    async def _provisioning_device(self):
        success = False

        # link open phase
        for try_ in range(3):
            print(colored.cyan(f'Open device link '
                               f'{self.prov_ctx.device_link}'))
            await self._open_link()

            try:
                print(colored.cyan(f'Waiting link ack...'))
                await wait_for(self._wait_link_ack(), timeout=3)

                print(colored.green('Link open successfull'))
                success = True
                break
            except asyncio.TimeoutError:
                print(colored.yellow(f'{try_ + 1}{order(try_ + 1)} open link '
                                     f'try fail'))
                continue

        if not success:
            print(colored.red('Link open fail'))
            raise FinishAsync

        # invitation phase
        success = await self._send_pdu(tries=10, phase_name='invite',
                                       total_timeout=30,
                                       mount_pdu_func=self._mount_invite_pdu)
        if not success:
            print(colored.red('Send invite PDU fail'))
            await self.close_link()
            return

        success = await self._wait_pdu(ack_tries=3, phase_name='capabilities',
                                       timeout=30,
                                       check_pdu_func=self._check_capabilities_pdu)
        if not success:
            print(colored.red('Wait capabilities PDU fail'))
            await self.close_link()
            return

        # exchanging public keys phase
        success = await self._send_pdu(tries=10, phase_name='start',
                                       total_timeout=30,
                                       mount_pdu_func=self._mount_start_pdu)
        if not success:
            print(colored.red('Send start PDU fail'))
            await self.close_link()
            return

        success = await self._send_pdu(tries=10, phase_name='exchange keys',
                                       total_timeout=30,
                                       mount_pdu_func=self._mount_public_key_pdu)
        if not success:
            print(colored.red('Send public key PDU fail'))
            await self.close_link()
            return

        success = await self._wait_pdu(ack_tries=3, phase_name='exchange keys',
                                       timeout=30,
                                       check_pdu_func=self._check_public_key_pdu)
        if not success:
            print(colored.red('Wait public key PDU fail'))
            await self.close_link()
            return

        # authentication phase
        success = await self._send_pdu(tries=10, phase_name='confirmation',
                                       total_timeout=30,
                                       mount_pdu_func=self._mount_confirmation_pdu)
        if not success:
            print(colored.red('Send confirmation PDU fail'))
            await self.close_link()
            return

        success = await self._wait_pdu(ack_tries=3, phase_name='confirmation',
                                       timeout=30,
                                       check_pdu_func=self._check_confirmation_pdu)
        if not success:
            print(colored.red('Wait confirmation PDU fail'))
            await self.close_link()
            return

        success = await self._send_pdu(tries=10, phase_name='random',
                                       total_timeout=30,
                                       mount_pdu_func=self._mount_random_pdu)
        if not success:
            print(colored.red('Send random PDU fail'))
            await self.close_link()
            return

        success = await self._wait_pdu(ack_tries=3, phase_name='random',
                                       timeout=30,
                                       check_pdu_func=self._check_random_pdu)
        if not success:
            print(colored.red('Wait random PDU fail'))
            await self.close_link()
            return

        # distribuition of provisioning data phase
        success = await self._send_pdu(tries=10, phase_name='data',
                                       total_timeout=30,
                                       mount_pdu_func=self._mount_data_pdu)
        if not success:
            print(colored.red('Send data PDU fail'))
            await self.close_link()
            return

        success = await self._wait_pdu(ack_tries=3, phase_name='complete',
                                       timeout=30,
                                       check_pdu_func=self._check_complete_pdu)
        if not success:
            print(colored.red('Wait complete PDU fail'))
            await self.close_link()
            return

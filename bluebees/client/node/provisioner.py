from bluebees.common.client import Client
from dataclasses import dataclass
from bluebees.common.utils import order, crc8
from asyncio import wait_for
from ecdsa import NIST256p, SigningKey
from ecdsa.ellipticcurve import Point
from bluebees.common.crypto import crypto
from Crypto.Random import get_random_bytes
from typing import List
from bluebees.common.logging import log_sys, INFO, DEBUG
from tqdm import tqdm
import asyncio


class LinkOpenError(KeyboardInterrupt):
    pass


class ProvisioningSuccess(KeyboardInterrupt):
    pass


class ProvisioningError(KeyboardInterrupt):
    pass


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
    auth_value: bytes

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


@dataclass
class GenericProvContext:
    segn: int
    total_length: int
    fcs: int
    current_index: int
    content: bytes

    def reset(self):
        self.segn = 0
        self.total_length = 0
        self.fcs = 0
        self.current_index = 0
        self.content = b''


class Provisioner(Client):

    def __init__(self, loop, device_uuid: bytes, netkey: bytes,
                 key_index: bytes, iv_index: bytes, address: bytes,
                 flags=b'\x00', attention_duration=5, debug=False):
        super().__init__(sub_topic_list=[b'prov'], pub_topic_list=[b'prov_s'])

        self.log = log_sys.get_logger('provisioner')
        if debug:
            self.log.set_level(DEBUG)
        else:
            self.log.set_level(INFO)

        self.adv_mtu = 24
        self.start_pdu = 0
        self.cont_pdu = 2

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
                                            auth_value=None,
                                            invite_pdu=None,
                                            capabilities_pdu=None,
                                            start_pdu=None,
                                            node_confirmation=None,
                                            confirmation_salt=None,
                                            random_device=None,
                                            node_public_key=None)
        self.g_recv_ctx = GenericProvContext(segn=0, total_length=0, fcs=0,
                                             current_index=0, content=b'')

        sk = SigningKey.generate(curve=NIST256p)
        vk = sk.get_verifying_key()
        self.prov_ctx.private_key = sk.privkey.secret_multiplier
        self.prov_ctx.public_key = vk.pubkey.point

        self.prov_ctx.random_provisioner = get_random_bytes(16)

        self.devkey = None

        self.all_tasks += [self._provisioning_device()]

    # link method
    def __close_reason(self, reason: bytes) -> str:
        if reason == b'\x00':
            return 'success'
        elif reason == b'\x01':
            return 'timeout'
        elif reason == b'\x02':
            return 'fail'
        else:
            return 'unknown'

    async def _open_link(self):
        msg_type = b'prov_s'
        content = self.prov_ctx.device_link
        content += self.prov_ctx.client_tr_number.to_bytes(1, 'big')
        content += b'\x03'  # open opcode
        content += self.device_info.uuid

        await self.messages_to_send.put((msg_type, content))

    async def _wait_link_ack(self):
        while True:
            (msg_type, content) = await self.messages_received.get()

            expected_tr_number = self.prov_ctx.client_tr_number.to_bytes(1,
                                                                         'big')

            if msg_type == b'prov' and \
               content[0:4] == self.prov_ctx.device_link and \
               content[4:5] == expected_tr_number and content[5:6] == b'\x07':
                break

    async def close_link(self, reason: bytes):
        msg_type = b'prov_s'
        content = self.prov_ctx.device_link
        content += self.prov_ctx.client_tr_number.to_bytes(1, 'big')
        content += b'\x0b'
        content += reason

        for x in range(3):
            await self.messages_to_send.put((msg_type, content))
            await asyncio.sleep(.3)

    # send pdu methods
    def __mount_generic_prov_pdu(self, content: bytes) -> List[bytes]:
        adv_header = self.prov_ctx.device_link
        adv_header += self.prov_ctx.client_tr_number.to_bytes(1, 'big')
        g_pdus = []

        # start pdu
        last_index = int((len(content) - 1) / self.adv_mtu)
        segn = (last_index << 2).to_bytes(1, 'big')
        total_length = len(content).to_bytes(2, 'big')
        fcs = crc8(content).to_bytes(1, 'big')
        data = content[0:self.adv_mtu - 4]
        g_pdus.append(adv_header + segn + total_length + fcs + data)

        # contiuation pdu
        content = content[self.adv_mtu - 4:]
        for x in range(last_index):
            index = (((x + 1) << 2) | 0x02).to_bytes(1, 'big')
            data = content[0:self.adv_mtu - 1]
            g_pdus.append(adv_header + index + data)
            content = content[self.adv_mtu - 1:]

        return g_pdus

    async def __wait_ack(self):
        while True:
            (msg_type, content) = await self.messages_received.get()

            expected_tr_number = self.prov_ctx.client_tr_number.to_bytes(1,
                                                                         'big')

            if msg_type == b'prov' and \
               content[0:4] == self.prov_ctx.device_link and \
               content[5:6] == b'\x0b' and content[6:7] != b'\x00':
                self.log.error(f'The device close link. Reason: '
                               f'{self.__close_reason(content[6:7])}')
                raise ProvisioningError

            if msg_type == b'prov' and \
               content[0:4] == self.prov_ctx.device_link and \
               content[4:5] == expected_tr_number and content[5:6] == b'\x01':
                return

    async def _send_pdu(self, tries: int, phase_name: str, total_timeout: int,
                        mount_pdu_func) -> bool:
        timeout = int(total_timeout / tries)
        for try_ in range(tries):
            self.log.debug(f'Send {phase_name} PDU')
            content = mount_pdu_func()

            generic_prov_pdus = self.__mount_generic_prov_pdu(content)

            for pdu in generic_prov_pdus:
                await self.messages_to_send.put((b'prov_s', pdu))

            try:
                self.log.debug('Waiting ack...')
                await wait_for(self.__wait_ack(), timeout=timeout)

                self.log.debug(f'Send {phase_name} PDU successful')
                self.prov_ctx.client_tr_number += 1
                return True
            except asyncio.TimeoutError:
                self.log.debug(f'{try_ + 1}{order(try_ + 1)} '
                               f'{phase_name} PDU fail')

        return False

    # wait pdu methods
    def __remount_recv_pdu(self, content) -> bytes:
        node_tr_number = self.prov_ctx.node_tr_number.to_bytes(1, 'big')
        expected_adv_header = self.prov_ctx.device_link + node_tr_number

        if content[0:5] != expected_adv_header:
            return None

        content = content[5:]

        pdu_type = content[0] & 0x03
        if pdu_type == self.start_pdu:
            self.g_recv_ctx.reset()
            self.g_recv_ctx.segn = (content[0] & 0xfc) >> 2
            self.g_recv_ctx.total_length = int.from_bytes(content[1:3], 'big')
            self.g_recv_ctx.fcs = content[3]
            self.g_recv_ctx.current_index = 1
            self.g_recv_ctx.content = content[4:self.adv_mtu]

            if self.g_recv_ctx.segn == 0:
                calc_fcs = crc8(self.g_recv_ctx.content)
                total_len = len(self.g_recv_ctx.content)
                if total_len != self.g_recv_ctx.total_length:
                    self.g_recv_ctx.reset()
                    self.log.debug('Wrong total len')
                elif calc_fcs != self.g_recv_ctx.fcs:
                    self.g_recv_ctx.reset()
                    self.log.debug('Wrong FCS')
                else:
                    pdu = self.g_recv_ctx.content
                    self.g_recv_ctx.reset()
                    return pdu
        elif pdu_type == self.cont_pdu:
            index = (content[0] & 0xfc) >> 2
            if index == self.g_recv_ctx.current_index:
                if index != self.g_recv_ctx.segn:
                    self.g_recv_ctx.current_index += 1
                    self.g_recv_ctx.content += content[1:self.adv_mtu]
                else:
                    self.g_recv_ctx.content += content[1: self.adv_mtu]
                    calc_fcs = crc8(self.g_recv_ctx.content)
                    total_len = len(self.g_recv_ctx.content)
                    if total_len != self.g_recv_ctx.total_length:
                        self.g_recv_ctx.reset()
                        self.log.debug('Wrong total len')
                    elif calc_fcs != self.g_recv_ctx.fcs:
                        self.g_recv_ctx.reset()
                        self.log.debug('Wrong FCS')
                    else:
                        pdu = self.g_recv_ctx.content
                        self.g_recv_ctx.reset()
                        return pdu

        return None

    async def __send_ack(self):
        content = self.prov_ctx.device_link
        content += self.prov_ctx.node_tr_number.to_bytes(1, 'big')
        content += b'\x01'

        await self.messages_to_send.put((b'prov_s', content))

    async def __wait_pdu_atomic(self, check_pdu_func):
        while True:
            (msg_type, content) = await self.messages_received.get()

            if msg_type != b'prov':
                continue

            if content[0:4] == self.prov_ctx.device_link and \
               content[5:6] == b'\x0b' and content[6:7] != b'\x00':
                self.log.error(f'The device close link. Reason: '
                               f'{self.__close_reason(content[6:7])}')
                raise ProvisioningError

            pdu = self.__remount_recv_pdu(content)

            if pdu and check_pdu_func(pdu):
                return

    async def _wait_pdu(self, ack_tries: int, phase_name: str, timeout: int,
                        check_pdu_func) -> bool:
        try:
            self.log.debug(f'Waiting {phase_name} PDU...')
            await wait_for(self.__wait_pdu_atomic(check_pdu_func), timeout)

            for try_ in range(ack_tries):
                self.log.debug(f'Send {try_ + 1}{order(try_ + 1)} ack pdu')
                await self.__send_ack()
                await asyncio.sleep(.3)

            self.prov_ctx.node_tr_number += 1
            return True
        except TimeoutError:
            return False

    # invite phase
    def _mount_invite_pdu(self) -> bytes:
        content = b'\x00'
        content += self.device_info.attention.to_bytes(1, 'big')

        self.prov_ctx.invite_pdu = self.device_info.attention.to_bytes(1, 'big')

        return content

    def _check_capabilities_pdu(self, content) -> bool:
        self.log.debug('Capabilities:')
        self.log.debug(f'Number of Elements: {content[1]}')
        self.log.debug(f'Algorithms: {int.from_bytes(content[2:4], "big")}')
        self.log.debug(f'Public Key Type: {content[4]}')
        self.log.debug(f'Static OOB Type: {content[5]}')
        self.log.debug(f'Output OOB Size: {content[6]}')
        self.log.debug(f'Output OOB Action: {int.from_bytes(content[7:9], "big")}')
        self.log.debug(f'Input OOB Size: {content[9]}')
        self.log.debug(f'Input OOB Action: {int.from_bytes(content[10:12], "big")}')

        self.prov_ctx.capabilities_pdu = content[1:]

        return content[0:1] == b'\x01' and len(content[1:]) == 11

    # exchanging public key phase
    def _mount_start_pdu(self) -> bytes:
        content = b'\x02'
        content += b'\x00\x00\x00\x00\x00'

        self.prov_ctx.start_pdu = b'\x00\x00\x00\x00\x00'

        return content

    def _mount_public_key_pdu(self) -> bytes:
        public_key_x = self.prov_ctx.public_key.x().to_bytes(32, 'big')
        public_key_y = self.prov_ctx.public_key.y().to_bytes(32, 'big')

        content = b'\x03'
        content += public_key_x
        content += public_key_y

        self.log.debug(f'Pub key x {public_key_x.hex()}')
        self.log.debug(f'Pub key y {public_key_y.hex()}')

        return content

    def _check_public_key_pdu(self, content) -> bool:
        self.prov_ctx.node_public_key = Point(curve=NIST256p.curve,
                                              x=int.from_bytes(content[1:33], 'big'),
                                              y=int.from_bytes(content[33:65], 'big'))

        self.prov_ctx.ecdh_secret = (self.prov_ctx.private_key * self.prov_ctx.node_public_key).x().to_bytes(32, 'big')

        return content[0:1] == b'\x03' and len(content[1:]) == 64

    # authentication phase
    def _mount_confirmation_pdu(self) -> bytes:
        self.prov_ctx.auth_value = bytes(16)

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

        content = b'\x05'
        content += crypto.aes_cmac(key=self.prov_ctx.confirmation_key,
                                   text=self.prov_ctx.random_provisioner +
                                   self.prov_ctx.auth_value)

        self.log.debug(f'ConfInputs[0]   {confirmation_inputs[0:64].hex()}')
        self.log.debug(f'ConfInputs[64]  {confirmation_inputs[64:128].hex()}')
        self.log.debug(f'ConfInputs[128] {confirmation_inputs[128:145].hex()}')
        self.log.debug(f'confirmation key: {self.prov_ctx.confirmation_key.hex()}')
        self.log.debug(f'random device: {self.prov_ctx.random_provisioner.hex()}')
        self.log.debug(f'authvalue: {self.prov_ctx.auth_value.hex()}')

        return content

    def _check_confirmation_pdu(self, content) -> bool:
        self.prov_ctx.node_confirmation = content[1:17]

        return content[0:1] == b'\x05' and len(content[1:]) == 16

    def _mount_random_pdu(self) -> bytes:
        content = b'\x06'
        content += self.prov_ctx.random_provisioner

        return content

    def _check_random_pdu(self, content) -> bool:
        self.prov_ctx.random_device = content[1:]

        calc_confirmation = crypto.aes_cmac(key=self.prov_ctx.confirmation_key,
                                            text=self.prov_ctx.random_device +
                                            self.prov_ctx.auth_value)

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

        self.devkey = crypto.k1(n=self.prov_ctx.ecdh_secret, salt=prov_salt,
                                p=b'prdk')[0:16]

        content = b'\x07'
        content += encrypted_data
        content += data_mic

        return content

    def _check_complete_pdu(self, content) -> bool:
        return content[0:1] == b'\x08'

    async def _provisioning_device(self):
        success = False

        # need for broker get the first message
        await asyncio.sleep(.1)

        # link open phase
        self.log.info(f'Opening link with device {self.device_info.uuid}')
        for try_ in range(10):
            self.log.debug(f'Open device link {self.prov_ctx.device_link}')
            await self._open_link()

            try:
                self.log.debug(f'Waiting link ack...')
                await wait_for(self._wait_link_ack(), timeout=3)

                self.log.success('Link open successfull')
                success = True
                break
            except asyncio.TimeoutError:
                self.log.debug(f'{try_ + 1}{order(try_ + 1)} open link try '
                               f'fail')
                continue

        if not success:
            self.log.error('Link open fail')
            raise LinkOpenError

        with tqdm(range(11)) as pbar:
            # invitation phase
            success = await self._send_pdu(tries=10, phase_name='invite',
                                           total_timeout=30,
                                           mount_pdu_func=self._mount_invite_pdu)
            if not success:
                self.log.error('FAIL')
                await self.close_link(b'\x01')  # timeout
                raise ProvisioningError

            pbar.update(1)
            success = await self._wait_pdu(ack_tries=3, phase_name='capabilities',
                                           timeout=30,
                                           check_pdu_func=self._check_capabilities_pdu)
            if not success:
                self.log.error('FAIL')
                await self.close_link(b'\x01')  # timeout
                raise ProvisioningError

            # exchanging public keys phase
            pbar.update(1)
            success = await self._send_pdu(tries=10, phase_name='start',
                                           total_timeout=30,
                                           mount_pdu_func=self._mount_start_pdu)
            if not success:
                self.log.error('FAIL')
                await self.close_link(b'\x01')  # timeout
                raise ProvisioningError

            pbar.update(1)
            success = await self._send_pdu(tries=10, phase_name='exchange keys',
                                           total_timeout=30,
                                           mount_pdu_func=self._mount_public_key_pdu)
            if not success:
                self.log.error('FAIL')
                await self.close_link(b'\x01')  # timeout
                raise ProvisioningError

            pbar.update(1)
            success = await self._wait_pdu(ack_tries=3, phase_name='exchange keys',
                                           timeout=30,
                                           check_pdu_func=self._check_public_key_pdu)
            if not success:
                self.log.error('FAIL')
                await self.close_link(b'\x01')  # timeout
                raise ProvisioningError

            # authentication phase
            pbar.update(1)
            success = await self._send_pdu(tries=10, phase_name='confirmation',
                                           total_timeout=30,
                                           mount_pdu_func=self._mount_confirmation_pdu)
            if not success:
                self.log.error('FAIL')
                await self.close_link(b'\x01')  # timeout
                raise ProvisioningError

            pbar.update(1)
            success = await self._wait_pdu(ack_tries=3, phase_name='confirmation',
                                           timeout=30,
                                           check_pdu_func=self._check_confirmation_pdu)
            if not success:
                self.log.error('FAIL')
                await self.close_link(b'\x01')  # timeout
                raise ProvisioningError

            pbar.update(1)
            success = await self._send_pdu(tries=10, phase_name='random',
                                           total_timeout=30,
                                           mount_pdu_func=self._mount_random_pdu)
            if not success:
                self.log.error('FAIL')
                await self.close_link(b'\x01')  # timeout
                raise ProvisioningError

            pbar.update(1)
            success = await self._wait_pdu(ack_tries=3, phase_name='random',
                                           timeout=30,
                                           check_pdu_func=self._check_random_pdu)
            if not success:
                self.log.error('FAIL')
                await self.close_link(b'\x01')  # timeout
                raise ProvisioningError

            # distribuition of provisioning data phase
            pbar.update(1)
            success = await self._send_pdu(tries=10, phase_name='data',
                                           total_timeout=30,
                                           mount_pdu_func=self._mount_data_pdu)
            if not success:
                self.log.error('FAIL')
                await self.close_link(b'\x01')  # timeout
                raise ProvisioningError

            pbar.update(1)
            success = await self._wait_pdu(ack_tries=3, phase_name='complete',
                                           timeout=30,
                                           check_pdu_func=self._check_complete_pdu)
            if not success:
                self.log.error('FAIL')
                await self.close_link(b'\x01')  # timeout
                raise ProvisioningError

            await self.close_link(b'\x00')

            pbar.update(1)
            raise ProvisioningSuccess

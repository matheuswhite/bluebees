from client.mesh_layers.mesh_context import HardContext, SoftContext
from client.network.network_data import NetworkData
from client.data_paths import base_dir, app_dir, net_dir
from common.logging import log_sys, INFO
import asyncio


class NetworkLayer:

    def __init__(self, send_queue, recv_queue):
        self.hard_ctx = HardContext()
        self.hard_ctx.reset()
        self.send_queue = send_queue
        self.recv_queue = recv_queue

        self.log = log_sys.get_logger('network_layer')
        self.log.set_level(INFO)

        # (transport_pdu: bytes, soft_ctx: SoftContext)
        self.transport_pdus = asyncio.Queue()

    # send methods
    def _gen_security_material(self,
                               net_data: NetworkData) -> (int, bytes, bytes):
        pass

    def _encrypt(self, soft_ctx: SoftContext, transport_pdu: bytes,
                 encryption_key: bytes,
                 net_nonce: bytes) -> (bytes, bytes, bytes):
        pass

    def _obsfucate(self, ctl: int, ttl: int, seq: int, src: bytes,
                   enc_dst: bytes, enc_transport_pdu: bytes, net_mic: bytes,
                   privacy_key: bytes) -> bytes:
        pass

    async def send_pdu(self, transport_pdu: bytes, soft_ctx: SoftContext):
        net_data = NetworkData.load(base_dir + net_dir + soft_ctx.network_name
                                    + '.yml')

        nid, encryption_key, privacy_key = \
            self._gen_security_material(net_data)
        
        net_pdu = b''
        net_pdu += (int.from_bytes(net_data.iv_index, 'big') & 0x01) << 7) | nid)
        ivi = (int.from_bytes(net_data.iv_index, 'big') & 0x01) << 7 | nid
        ctl = 0x80 if self.hard_ctx.is_ctrl_msg else 0x00
        ttl = self.hard_ctx.ttl & 0x7f
        seq = self.hard_ctx.seq
        src = soft_ctx.src_addr

        net_nonce = b'\x00' + (ctl | ttl).to_bytes(1, 'big') + seq + src + \
            b'\x00\x00' + net_data.iv_index

        enc_dst, enc_transport_pdu, net_mic = self._encrypt(soft_ctx,
                                                            transport_pdu,
                                                            encryption_key,
                                                            net_nonce)

        obsfucated = self._obsfucate(ctl, ttl, seq, src, enc_dst,
                                     enc_transport_pdu, net_mic, privacy_key)

        network_pdu = (ivi | nid).to_bytes(1, 'big') + obsfucated + enc_dst + \
            enc_transport_pdu + net_mic

        await self.send_queue.put((b'message_s', network_pdu))

    # receive methods
    def _clean_message(self, net_pdu: bytes) -> bytes:
        pass

    def _fill_hard_ctx(self, transport_pdu: bytes):
        pass

    def _decrypt(self, encrypted_pdu: bytes) -> bytes:
        pass

    def _fill_soft_ctx(self, transport_pdu: bytes) -> SoftContext:
        pass

    async def recv_pdu(self):
        while True:
            msg_type, net_pdu = await self.recv_queue.get()

            # got a message from another channel
            if msg_type != b'message':
                self.log.critical(f'Got a message from "{msg_type}" channel')
                continue

            # remove obsfucation
            transport_pdu = self._clean_message(net_pdu[1:7])

            # update seq, is_crtl_msg
            self._fill_hard_ctx(transport_pdu)

            if self.hard_ctx.is_crtl_msg == 0:
                net_mic = net_pdu[-4:]
                encrypted_pdu = net_pdu[7:-4]
                transport_pdu += self._decrypt(encrypted_pdu)
                calc_net_mic = transport_pdu[-4:]
            else:
                net_mic = net_pdu[-8:]
                encrypted_pdu = net_pdu[7:-8]
                transport_pdu += self._decrypt(encrypted_pdu)
                calc_net_mic = transport_pdu[-8:]

            if net_mic != calc_net_mic:
                self.log.debug(f'NetMIC wrong. Receive "{net_mic}" and '
                               f'calculated "{calc_net_mic}"')
                continue

            soft_ctx = self._fill_soft_ctx(transport_pdu)

            await self.transport_pdus.put((transport_pdu, soft_ctx))

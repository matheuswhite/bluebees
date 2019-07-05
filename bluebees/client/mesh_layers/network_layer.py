from bluebees.client.mesh_layers.mesh_context import HardContext, SoftContext
from bluebees.client.network.network_data import NetworkData
from bluebees.client.node.node_data import NodeData
from bluebees.client.data_paths import base_dir, net_dir, node_dir
from bluebees.common.logging import log_sys, INFO, DEBUG
from bluebees.common.crypto import crypto
from bluebees.common.file import file_helper
import asyncio


# ! The SEQ number is different for each node
# ! Each new provisioned node send message with SEQ start with zero
class NetworkLayer:

    def __init__(self, send_queue, recv_queue):
        self.hard_ctx = HardContext(seq=0, ttl=2, is_ctrl_msg=True,
                                    seq_zero=0, seg_o=0, seg_n=0, szmic=0)
        self.send_queue = send_queue
        self.recv_queue = recv_queue

        self.log = log_sys.get_logger('network_layer')
        self.log.set_level(INFO)

        # (transport_pdu: bytes, soft_ctx: SoftContext)
        self.transport_pdus = asyncio.Queue()

    def __increment_seq(self, soft_ctx: SoftContext):
        node_name = soft_ctx.node_name
        node_data = NodeData.load(base_dir + node_dir + node_name + '.yml')
        node_data.seq += 1
        node_data.save()

    # send methods
    def _gen_security_material(self,
                               net_data: NetworkData) -> (int, bytes, bytes):
        materials = crypto.k2(n=net_data.key, p=b'\x00')
        nid = materials[0] & 0x7f
        encryption_key = materials[1:17]
        privacy_key = materials[17:33]
        return nid, encryption_key, privacy_key

    def _encrypt(self, soft_ctx: SoftContext, transport_pdu: bytes,
                 encryption_key: bytes,
                 net_nonce: bytes) -> (bytes, bytes, bytes):
        mic_size = 8 if self.hard_ctx.is_ctrl_msg else 4
        aes_ccm_result, mic = crypto.aes_ccm_complete(key=encryption_key,
                                                      nonce=net_nonce,
                                                      text=soft_ctx.dst_addr +
                                                      transport_pdu,
                                                      adata=b'',
                                                      mic_size=mic_size)
        enc_dst = aes_ccm_result[0:2]
        encrypted_data = aes_ccm_result[2:]
        net_mic = mic
        return enc_dst, encrypted_data, net_mic

    def __xor(self, a: bytes, b: bytes):
        c = b''
        for x in range(len(a)):
            c += int(a[x] ^ b[x]).to_bytes(1, 'big')
        return c

    def _obsfucate(self, ctl: int, ttl: int, seq: int, src: bytes,
                   enc_dst: bytes, enc_transport_pdu: bytes, net_mic: bytes,
                   privacy_key: bytes, net_data: NetworkData) -> bytes:
        privacy_random = (enc_dst + enc_transport_pdu + net_mic)[0:7]
        pecb = crypto.e(key=privacy_key, plaintext=b'\x00\x00\x00\x00\x00' +
                                                   net_data.iv_index +
                                                   privacy_random)
        obsfucated_data = self.__xor((ctl | ttl).to_bytes(1, 'big') +
                                     seq.to_bytes(3, 'big') + src, pecb[0:6])
        return obsfucated_data

    async def send_pdu(self, transport_pdu: bytes, soft_ctx: SoftContext):
        net_data = NetworkData.load(base_dir + net_dir + soft_ctx.network_name
                                    + '.yml')
        node_data = NodeData.load(base_dir + node_dir + soft_ctx.node_name
                                  + '.yml')
        self.hard_ctx.seq = node_data.seq

        nid, encryption_key, privacy_key = \
            self._gen_security_material(net_data)

        ivi = ((int.from_bytes(net_data.iv_index, 'big') & 0x01) << 7)
        ctl = 0x80 if self.hard_ctx.is_ctrl_msg else 0x00
        ttl = 0x02
        seq = self.hard_ctx.seq
        src = soft_ctx.src_addr

        net_nonce = b'\x00' + (ctl | ttl).to_bytes(1, 'big') + \
            seq.to_bytes(3, 'big') + src + b'\x00\x00' + net_data.iv_index

        enc_dst, enc_transport_pdu, net_mic = self._encrypt(soft_ctx,
                                                            transport_pdu,
                                                            encryption_key,
                                                            net_nonce)

        obsfucated = self._obsfucate(ctl, ttl, seq, src, enc_dst,
                                     enc_transport_pdu, net_mic, privacy_key,
                                     net_data)

        network_pdu = (ivi | nid).to_bytes(1, 'big') + obsfucated + enc_dst + \
            enc_transport_pdu + net_mic

        await self.send_queue.put((b'message_s', network_pdu))

        self.__increment_seq(soft_ctx)

    # receive methods
    def __search_network_by_nid(self, nid: int) -> NetworkData:
        filenames = file_helper.list_files(base_dir + net_dir)

        for f in filenames:
            net_data = NetworkData.load(base_dir + net_dir + f)
            net_nid, _, _ = self._gen_security_material(net_data)
            if net_nid == nid:
                return net_data

        return None

    def __search_node_by_addr(self, addr: bytes) -> NodeData:
        filenames = file_helper.list_files(base_dir + node_dir)

        for f in filenames:
            node_data = NodeData.load(base_dir + node_dir + f)
            if addr == node_data.addr:
                return node_data

        return None

    def _clean_message(self, net_pdu: bytes, net_data: NetworkData) -> bytes:
        _, _, privacy_key = self._gen_security_material(net_data)
        privacy_random = net_pdu[7:14]
        obsfucated_data = net_pdu[1:7]
        pecb = crypto.e(key=privacy_key, plaintext=b'\x00\x00\x00\x00\x00' +
                        net_data.iv_index + privacy_random)
        clean_result = self.__xor(obsfucated_data, pecb[0:6])
        return clean_result

    # TODO [Enhancement] Check the seq number
    def _fill_hard_ctx(self, clean_pdu: bytes):
        self.hard_ctx.is_ctrl_msg = ((clean_pdu[0] & 0x80) >> 7) == 1
        self.hard_ctx.ttl = clean_pdu[0] & 0x7f
        self.hard_ctx.seq = int.from_bytes(clean_pdu[1:4], 'big')

    def _decrypt(self, encrypted_pdu: bytes, src: bytes,
                 net_data: NetworkData, net_mic: bytes) -> (bytes, bool):
        _, encryption_key, _ = self._gen_security_material(net_data)

        ctl = 0x80 if self.hard_ctx.is_ctrl_msg else 0x00
        ttl = self.hard_ctx.ttl
        seq = self.hard_ctx.seq
        network_nonce = b'\x00' + (ctl | ttl).to_bytes(1, 'big') + \
            seq.to_bytes(3, 'big') + src + b'\x00\x00' + net_data.iv_index

        decrypted_pdu, mic_is_ok = crypto.aes_ccm_decrypt(
            key=encryption_key, nonce=network_nonce, text=encrypted_pdu,
            mic=net_mic)

        self.log.debug(f'ttl: {ttl}, ctl: {ctl}, seq: {hex(seq)}, pdu: '
                       f'{decrypted_pdu.hex()}')
        self.log.debug(f'Nonce: {network_nonce.hex()}, key: '
                       f'{encryption_key.hex()}')

        return decrypted_pdu, mic_is_ok

    async def recv_pdu(self):
        while True:
            self.log.debug(f'Waiting message...')
            msg_type, net_pdu = await self.recv_queue.get()

            # got a message from another channel
            if msg_type != b'message':
                continue

            # get network by nid
            nid = net_pdu[0] & 0x7f
            net_data = self.__search_network_by_nid(nid)
            if not net_data:
                continue

            # remove obsfucation
            clean_pdu = self._clean_message(net_pdu, net_data)

            # update seq, is_ctrl_msg
            self._fill_hard_ctx(clean_pdu)

            # decrypting
            src_addr = clean_pdu[-2:]
            mic_size = 8 if self.hard_ctx.is_ctrl_msg else 4
            net_mic = net_pdu[-mic_size:]
            encrypted_pdu = net_pdu[7:-mic_size]
            decrypted_pdu, mic_is_ok = self._decrypt(encrypted_pdu, src_addr,
                                                     net_data, net_mic)
            if not mic_is_ok:
                self.log.debug(f'Src addr: {src_addr.hex()}')
                self.log.debug(f'NetMIC wrong. Receive "{net_mic.hex()}"')
                continue

            # update seq number in node_data YAML file
            node_data = self.__search_node_by_addr(src_addr)
            if not node_data:
                self.log.debug(f'Node with addr {src_addr} is unknown')
                continue

            node_data.seq = self.hard_ctx.seq
            node_data.save()

            soft_ctx = SoftContext(src_addr=b'', dst_addr=b'', node_name='',
                                   network_name='', application_name='',
                                   is_devkey=False, ack_timeout=0,
                                   segment_timeout=0)
            soft_ctx.src_addr = src_addr
            soft_ctx.dst_addr = decrypted_pdu[0:2]
            soft_ctx.node_name = node_data.name
            soft_ctx.network_name = net_data.name

            transport_pdu = decrypted_pdu[2:]
            await self.transport_pdus.put((transport_pdu, soft_ctx,
                                           self.hard_ctx.seq))

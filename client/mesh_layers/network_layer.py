from client.mesh_layers.mesh_context import HardContext, SoftContext
from client.network.network_data import NetworkData
from client.data_paths import base_dir, net_dir
from common.logging import log_sys, INFO
from common.crypto import crypto
from common.file import file_helper
import asyncio


class NetworkLayer:

    def __init__(self, send_queue, recv_queue):
        self.hard_ctx = HardContext(seq=0, ttl=3, is_ctrl_msg=True,
                                    seq_zero=0, seg_o=0, seg_n=0, szmic=0)
        self.hard_ctx.reset()
        self.send_queue = send_queue
        self.recv_queue = recv_queue

        self.log = log_sys.get_logger('network_layer')
        self.log.set_level(INFO)

        # (transport_pdu: bytes, soft_ctx: SoftContext)
        self.transport_pdus = asyncio.Queue()

    def increment_seq(self, soft_ctx: SoftContext):
        net_name = soft_ctx.network_name
        net_data = NetworkData.load(base_dir + net_dir + net_name + '.yml')
        net_data.seq += 1
        net_data.save()

    # send methods
    def _gen_security_material(self,
                               net_data: NetworkData) -> (int, bytes, bytes):
        materials = crypto.k2(n=net_data.key, p=b'\x00')
        nid = materials[0] & 0x7f
        encryption_key = materials[1:17]
        privacy_key = materials[17:33]
        # print(f'nid: {nid}, enc_key: {encryption_key.hex()}, priv_key: {privacy_key.hex()}')
        return nid, encryption_key, privacy_key

    def _encrypt(self, soft_ctx: SoftContext, transport_pdu: bytes,
                 encryption_key: bytes,
                 net_nonce: bytes) -> (bytes, bytes, bytes):
        mic_size = 8 if self.hard_ctx.is_ctrl_msg else 4
        aes_ccm_result, mic = crypto.aes_ccm_complete(key=encryption_key, nonce=net_nonce,
                                        text=soft_ctx.dst_addr + transport_pdu,
                                        adata=b'', mic_size=mic_size)
        enc_dst = aes_ccm_result[0:2]
        encrypted_data = aes_ccm_result[2:]
        net_mic = mic
        print(f'len pdu: {len(transport_pdu)}, data: {encrypted_data.hex()}, mic: {mic.hex()}')
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
        self.hard_ctx.seq = net_data.seq

        nid, encryption_key, privacy_key = \
            self._gen_security_material(net_data)

        ivi = ((int.from_bytes(net_data.iv_index, 'big') & 0x01) << 7)
        ctl = 0x80 if self.hard_ctx.is_ctrl_msg else 0x00
        ttl = self.hard_ctx.ttl & 0x7f
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

    # receive methods
    def __search_network_by_nid(self, nid: int) -> NetworkData:
        filenames = file_helper.list_files(base_dir + net_dir)

        for f in filenames:
            net_data = NetworkData.load(base_dir + net_dir + f)
            net_nid, _, _ = self._gen_security_material(net_data)
            if net_nid == nid:
                return net_data

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
        self.hard_ctx.is_ctrl_msg = (clean_pdu[0] & 0x80 >> 7) == 1
        self.hard_ctx.seq = int.from_bytes(clean_pdu[1:4], 'big')

    # TODO implement enc_key and net_nonce
    def _decrypt(self, encrypted_pdu: bytes) -> (bytes, bytes):
        encryption_key = b''
        network_nonce = b''
        mic_size = 8 if self.hard_ctx.is_ctrl_msg else 4
        decrypted_pdu, calc_net_mic = crypto.aes_ccm_complete(key=encryption_key,
                                        nonce=network_nonce,
                                        text=encrypted_pdu, adata=b'', mic_size=mic_size)

        return decrypted_pdu, calc_net_mic

    async def recv_pdu(self):
        while True:
            msg_type, net_pdu = await self.recv_queue.get()

            # got a message from another channel
            if msg_type != b'message':
                # self.log.critical(f'Got a message from "{msg_type}" channel.'
                #                   f' msg: {net_pdu.hex()}')
                continue

            print('n0')
            # get network by nid
            nid = net_pdu[0] & 0x7f
            print('n1')
            net_data = self.__search_network_by_nid(nid)
            print('n2')
            if not net_data:
                continue

            # remove obsfucation
            print('n3')
            clean_pdu = self._clean_message(net_pdu, net_data)

            # update seq, is_ctrl_msg
            print('n4')
            self._fill_hard_ctx(clean_pdu)

            # update seq number in net_data YAML file
            print('n5')
            net_data.seq = self.hard_ctx.seq
            print(f'n6, net_data: {net_data}')
            net_data.save()

            print('n7')
            net_mic = net_pdu[-8:] if self.hard_ctx.is_ctrl_msg else \
                net_pdu[-4:]
            print('n8')
            encrypted_pdu = net_pdu[7:]
            print('n9')
            decrypted_pdu, calc_net_mic = self._decrypt(encrypted_pdu)
            print('n10')
            if net_mic != calc_net_mic:
                self.log.debug(f'NetMIC wrong. Receive "{net_mic}" and '
                               f'calculated "{calc_net_mic}"')
                continue
            print('n11')
            soft_ctx = SoftContext(src_addr=b'', dst_addr=b'', node_name='',
                                   network_name='', application_name='',
                                   is_devkey=False, ack_timeout=0,
                                   segment_timeout=0)
            print('n12')
            soft_ctx.src_addr = clean_pdu[-2:]
            print('n13')
            soft_ctx.dst_addr = decrypted_pdu[0:2]
            print('n14')
            soft_ctx.network_name = net_data.name

            print('n15')
            transport_pdu = decrypted_pdu[2:]
            print('n16')
            await self.transport_pdus.put((transport_pdu, soft_ctx))
            print('n17')

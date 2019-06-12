from bluebees.client.mesh_layers.network_layer import NetworkLayer
from bluebees.client.mesh_layers.mesh_context import SoftContext
from bluebees.client.network.network_data import NetworkData
from bluebees.client.application.application_data import ApplicationData
from bluebees.client.node.node_data import NodeData
from bluebees.client.data_paths import base_dir, net_dir, app_dir, node_dir
from bluebees.common.logging import log_sys, INFO, DEBUG
from bluebees.client.mesh_layers.address import address_type, UNICAST_ADDRESS, \
                                       GROUP_ADDRESS
from bluebees.client.node.group_data import find_group_by_addr
from bluebees.common.crypto import crypto
from bluebees.common.file import file_helper
from typing import List
import asyncio

LT_MTU = 12


# ! Segment Acknowledgment message is a control message and the CTL value is 1,
# !   and its sizemic is 64-bits
# ! Control messages has sizemic equals to 64-bits, since access message has
# !   sizemic equals to 32-bits.
class AckTimeout(Exception):
    pass


class TransportLayer:

    def __init__(self, send_queue, recv_queue):
        self.net_layer = NetworkLayer(send_queue=send_queue,
                                      recv_queue=recv_queue)

        self.log = log_sys.get_logger('transport_layer')
        self.log.set_level(INFO)

    # * Send Methods
    def _encrypt_access_pdu(self, pdu: bytes, soft_ctx: SoftContext) -> bytes:
        net_data = NetworkData.load(base_dir + net_dir +
                                    soft_ctx.network_name + '.yml')
        node_data = NodeData.load(base_dir + node_dir + soft_ctx.node_name +
                                  '.yml')
        self.net_layer.hard_ctx.seq = node_data.seq

        if not soft_ctx.is_devkey:
            app_data = ApplicationData.load(base_dir + app_dir +
                                            soft_ctx.application_name +
                                            '.yml')
            app_key = app_data.key
            app_nonce = b'\x01\x00' + \
                self.net_layer.hard_ctx.seq.to_bytes(3, 'big') + \
                soft_ctx.src_addr + soft_ctx.dst_addr + net_data.iv_index
        else:
            node_data = NodeData.load(base_dir + node_dir +
                                      soft_ctx.node_name + '.yml')
            app_key = node_data.devkey
            app_nonce = b'\x02\x00' + \
                self.net_layer.hard_ctx.seq.to_bytes(3, 'big') + \
                soft_ctx.src_addr + soft_ctx.dst_addr + net_data.iv_index

        result, mic = crypto.aes_ccm_complete(key=app_key, nonce=app_nonce,
                                              text=pdu, adata=b'', mic_size=4)

        return result + mic

    def _unsegmented_transport_pdu(self, pdu: bytes,
                                   soft_ctx: SoftContext) -> bytes:
        if not soft_ctx.is_devkey:
            app_data = ApplicationData.load(base_dir + app_dir +
                                            soft_ctx.application_name +
                                            '.yml')
            aid = crypto.k4(n=app_data.key)
            unseg_tr_pdu = 0x40
        else:
            node_data = NodeData.load(base_dir + node_dir +
                                      soft_ctx.node_name + '.yml')
            aid = crypto.k4(n=node_data.devkey)
            unseg_tr_pdu = 0x00

        unseg_tr_pdu = (unseg_tr_pdu | (int.from_bytes(aid, 'big') &
                        0x3f)).to_bytes(1, 'big')
        unseg_tr_pdu += pdu

        return unseg_tr_pdu

    def __header_segmented_transport_pdu(self, soft_ctx: SoftContext,
                                         seg_o: int) -> bytes:
        net_data = NetworkData.load(base_dir + net_dir +
                                    soft_ctx.network_name + '.yml')
        node_data = NodeData.load(base_dir + node_dir + soft_ctx.node_name +
                                  '.yml')
        seq_auth = (int.from_bytes(net_data.iv_index, 'big') << 24) | \
            node_data.seq
        self.net_layer.hard_ctx.seq_zero = seq_auth & 0x1fff

        first_byte = 0x80
        if not soft_ctx.is_devkey:
            app_data = ApplicationData.load(base_dir + app_dir +
                                            soft_ctx.application_name +
                                            '.yml')
            aid = crypto.k4(n=app_data.key)
            first_byte = first_byte | 0x40
        else:
            node_data = NodeData.load(base_dir + node_dir +
                                      soft_ctx.node_name + '.yml')
            aid = crypto.k4(n=node_data.devkey)
        first_byte = (first_byte | (aid[0] & 0x3f)).to_bytes(1, 'big')

        cont = (self.net_layer.hard_ctx.seg_n & 0x1f)
        cont = cont | ((seg_o & 0x1f) << 5)
        cont = cont | ((self.net_layer.hard_ctx.seq_zero & 0x1fff) << 10)
        cont = cont.to_bytes(3, 'big')

        return first_byte + cont

    def _segmented_transport_pdu(self, pdu: bytes,
                                 soft_ctx: SoftContext) -> List[bytes]:
        self.net_layer.hard_ctx.seg_n = (len(pdu) - 1) // LT_MTU
        segments = []

        for seg_o in range(self.net_layer.hard_ctx.seg_n + 1):
            header = self.__header_segmented_transport_pdu(soft_ctx, seg_o)
            segments.append(header + pdu[0:LT_MTU])
            pdu = pdu[LT_MTU:]

        return segments

    # * Notes
    # *  - In this implementation, all received message, with dst addr setted
    # *  to a group address, will be discard
    # *  - In this implementation, the nodes contains only one element
    def __check_addresses(self, recv_ctx: SoftContext,
                          ctx: SoftContext) -> bool:
        if address_type(recv_ctx.dst_addr) == UNICAST_ADDRESS:
            send_dst_type = address_type(ctx.dst_addr)
            if send_dst_type == UNICAST_ADDRESS:
                return (recv_ctx.dst_addr == ctx.src_addr) and \
                    (recv_ctx.src_addr == ctx.dst_addr)
            elif send_dst_type == GROUP_ADDRESS:
                group = find_group_by_addr(ctx.dst_addr)
                if not group:
                    return False

                return (recv_ctx.dst_addr == ctx.src_addr) and \
                    (recv_ctx.src_addr in group.sub_addrs)
        else:
            return False

    async def _wait_ack(self, soft_ctx: SoftContext, segments: List[bytes]):
        ack_bits = 0
        expected_ack_bits = (2 ** (self.net_layer.hard_ctx.seg_n + 1)) - 1
        while True:
            self.log.debug(f'Waiting ack...')
            ack_pdu, r_ctx, seq_num = await self.net_layer.transport_pdus.get()
            self.log.debug(f'Got ack')

            # not same src and dst address (discard)
            if not self.__check_addresses(r_ctx, soft_ctx):
                self.log.debug(f'Src {r_ctx.src_addr.hex()}, '
                               f'Dst: {r_ctx.dst_addr.hex()}')
                continue

            # not control message (discard)
            if not self.net_layer.hard_ctx.is_ctrl_msg:
                self.log.debug('Not control message')
                continue

            # not ack pdu (discard)
            if ack_pdu[0] != 0x00:
                self.log.debug('Not ack pdu')
                continue

            # seq zero wrong (discard)
            pdu_seq_zero = (int.from_bytes(ack_pdu[1:3], 'big') & 0x7ffc) >> 2
            if pdu_seq_zero != self.net_layer.hard_ctx.seq_zero:
                self.log.debug(f'Seq_zero: {pdu_seq_zero}')
                continue

            ack_bits = ack_bits | int.from_bytes(ack_pdu[3:7], 'big')
            self.log.debug(f'Ack bits: {hex(ack_bits)}')
            if ack_bits == expected_ack_bits:
                return
            else:
                # resend missing segments
                bits = ack_bits
                for i, seg in enumerate(segments):
                    if bits & 0x01 == 0:
                        self.log.debug(f'Send segment: {i}|{seg.hex()}')
                        await self.net_layer.send_pdu(seg, soft_ctx)
                    bits = bits >> 1
                self.log.debug(f'Ack bits [a]: {hex(ack_bits)}')

    async def send_pdu(self, access_pdu: bytes, soft_ctx: SoftContext):
        success = False

        crypt_access_pdu = self._encrypt_access_pdu(access_pdu, soft_ctx)

        if len(crypt_access_pdu) <= LT_MTU:
            transport_pdu = self._unsegmented_transport_pdu(crypt_access_pdu,
                                                            soft_ctx)
            self.net_layer.hard_ctx.is_ctrl_msg = False

            await self.net_layer.send_pdu(transport_pdu, soft_ctx)

            success = True
        else:
            segments = self._segmented_transport_pdu(crypt_access_pdu,
                                                     soft_ctx)
            self.net_layer.hard_ctx.is_ctrl_msg = False

            for i, seg in enumerate(segments):
                await self.net_layer.send_pdu(seg, soft_ctx)
                self.log.debug(f'Send segment: {i}|{seg.hex()}')

            try:
                await asyncio.wait_for(self._wait_ack(soft_ctx, segments),
                                       soft_ctx.ack_timeout)
                success = True
            except asyncio.TimeoutError:
                self.log.debug('Wait ack timeout')

        return success

    # * Receive Methods
    async def __send_ack(self, seg_o_table: dict, soft_ctx: SoftContext):
        if not seg_o_table:
            return

        pdu = 0x00
        pdu = pdu | ((self.net_layer.hard_ctx.seq_zero & 0x1fff) << 2)
        pdu = pdu.to_bytes(3, 'big')
        block_ack = 0x0000_0001
        for k, _ in seg_o_table.items():
            block_ack = block_ack | (1 << k)
            self.log.debug(f'block ack: {block_ack}, k: {k}')
        pdu += block_ack.to_bytes(4, 'big')

        self.log.debug(f'Ack seq zero: '
                       f'{hex(self.net_layer.hard_ctx.seq_zero)}')
        self.net_layer.hard_ctx.is_ctrl_msg = True
        await self.net_layer.send_pdu(pdu, soft_ctx)

    def __search_application_by_aid(self, aid: int) -> str:
        filenames = file_helper.list_files(base_dir + app_dir)

        for f in filenames:
            app_data = ApplicationData.load(base_dir + app_dir + f)
            app_aid = crypto.k4(n=app_data.key)
            if app_aid == aid:
                return app_data.name

        return None

    def __search_node_by_addr(self, addr: bytes) -> str:
        filenames = file_helper.list_files(base_dir + node_dir)

        for f in filenames:
            node_data = NodeData.load(base_dir + node_dir + f)
            if addr == node_data.addr:
                return node_data.name

        return ''

    def _fill_hard_ctx(self, start_pdu: bytes):
        self.net_layer.hard_ctx.szmic = (start_pdu[1] & 0x80) >> 7
        self.net_layer.hard_ctx.seq_zero = \
            (int.from_bytes(start_pdu[1:3], 'big') & 0x7ffc) >> 2
        self.net_layer.hard_ctx.seg_o = \
            (int.from_bytes(start_pdu[2:4], 'big') & 0x03e0) >> 5
        self.net_layer.hard_ctx.seg_n = start_pdu[3] & 0x1f

        self.log.debug(f'Seq zero: {hex(self.net_layer.hard_ctx.seq_zero)}')

    def _fill_soft_ctx(self, start_pdu: bytes,
                       ctx: SoftContext) -> SoftContext:
        afk = start_pdu[0] & 0x40 >> 6
        aid = start_pdu[0] & 0x3f
        if afk == 1:
            app_name = self.__search_application_by_aid(aid)
            if not app_name:
                return None
            ctx.application_name = app_name
            ctx.is_devkey = False
        else:
            ctx.application_name = ''
            ctx.is_devkey = True

        return ctx

    def _join_segments(self, sorted_segments: List[bytes]) -> bytes:
        tr_pdu = b''
        for seg in sorted_segments:
            tr_pdu += seg[4:]

        return tr_pdu

    def _decrypt_transport_pdu(self, pdu: bytes, ctx: SoftContext,
                               first_seq: int) -> bytes:
        if self.net_layer.hard_ctx.szmic == 0:
            encrypted_pdu = pdu[0:-4]
            transport_mic = pdu[-4:]
        else:
            encrypted_pdu = pdu[0:-8]
            transport_mic = pdu[-8:]

        self.log.debug(f'Encrypted pdu: {encrypted_pdu.hex()}, mic = '
                       f'{transport_mic.hex()}')

        net_data = NetworkData.load(base_dir + net_dir + ctx.network_name +
                                    '.yml')

        if ctx.is_devkey:
            self.log.debug(f'Using devkey, node name [{ctx.node_name}]')
            if not ctx.node_name:
                self.log.debug('No node found')
                return None

            node_data = NodeData.load(base_dir + node_dir + ctx.node_name +
                                      '.yml')
            key = node_data.devkey
            nonce = b'\x02'
        else:
            app_data = ApplicationData.load(base_dir + app_dir +
                                            ctx.application_name + '.yml')
            key = app_data.key
            nonce = b'\x01'

        nonce += (self.net_layer.hard_ctx.szmic << 7).to_bytes(1, 'big')
        nonce += (first_seq).to_bytes(3, 'big')
        nonce += ctx.src_addr
        nonce += ctx.dst_addr
        nonce += net_data.iv_index

        access_pdu, mic_is_ok = crypto.aes_ccm_decrypt(key=key, nonce=nonce,
                                                       text=encrypted_pdu,
                                                       mic=transport_mic)

        self.log.debug(f'Access PDU: {access_pdu.hex()}, first seq: '
                       f'{hex(first_seq)}')

        if not mic_is_ok:
            self.log.debug(f'Mic is wrong, pdu: {access_pdu.hex()}, seq: '
                           f'{hex(first_seq)}')
            return None
        else:
            return access_pdu

    async def _collect_segments(self, soft_ctx: SoftContext) -> List[bytes]:
        seg_o_table = {}
        ack_counter = 0
        while len(seg_o_table) < self.net_layer.hard_ctx.seg_n:
            self.log.debug('Waiting segment')
            pdu, r_ctx, seq_num = await self.net_layer.transport_pdus.get()
            self.log.debug(f'Got segment, pdu: {pdu.hex()}')

            seq_zero = (int.from_bytes(pdu[1:3], 'big') & 0x7ffc) >> 2
            if seq_zero != self.net_layer.hard_ctx.seq_zero:
                self.log.debug('Seq zero diff')
                continue

            # not same src and dst address (discard)
            if not self.__check_addresses(r_ctx, soft_ctx):
                self.log.debug('Invalid address')
                continue

            # each 10 messages received, sent a ack
            if ack_counter >= 10:
                await self.__send_ack(seg_o_table, soft_ctx)
                ack_counter = 0
            else:
                ack_counter += 1

            # control message (discard)
            if self.net_layer.hard_ctx.is_ctrl_msg:
                self.log.debug('Control message')
                continue

            # unsegmented pdu (discard)
            if ((pdu[0] & 0x80) >> 7) == 0:
                self.log.debug('unsegmented pdu')
                continue

            seg_o = (int.from_bytes(pdu[2:4], 'big') & 0x03e0) >> 5
            # segment already received (discard)
            if seg_o in seg_o_table.keys():
                self.log.debug('unsegmented pdu')
                continue

            self.log.debug('correct segment')
            seg_o_table[seg_o] = pdu

        # send ack message
        await self.__send_ack(seg_o_table, soft_ctx)

        segments = []
        for _, v in seg_o_table.items():
            segments.append(v)

        return segments

    async def recv_pdu(self, segment_timeout: int,
                       soft_ctx: SoftContext) -> (bytes, SoftContext):
        start_pdu, r_ctx, seq_num = await self.net_layer.transport_pdus.get()

        while self.net_layer.hard_ctx.is_ctrl_msg:
            start_pdu, r_ctx, seq_num = \
                await self.net_layer.transport_pdus.get()

        self.log.debug('Testing if is segmented...')
        if ((start_pdu[0] & 0x80) >> 7) == 0:
            # unsegmented pdu
            self.log.debug(f'Is unsegmented. PDU: {start_pdu.hex()}')

            # filling soft context
            r_ctx = self._fill_soft_ctx(start_pdu=start_pdu, ctx=r_ctx)
            if not r_ctx:
                return None, None

            # checking addresses
            if not self.__check_addresses(r_ctx, soft_ctx):
                self.log.debug('Not same address')
                return None, None

            # decrypting pdu
            self.log.debug('Start decrypting...')
            access_pdu = self._decrypt_transport_pdu(
                start_pdu[1:], r_ctx, seq_num)
            self.log.debug('End decrypt')
            if not access_pdu:
                return None, None
        else:
            # segmented pdu

            # store the seq number of first segment
            first_seq = seq_num
            self.log.debug(f'First seq: {hex(first_seq)}')

            # filling hard context
            self.log.debug(f'Is segmented. PDU: {start_pdu.hex()}')
            self._fill_hard_ctx(start_pdu)

            # filling soft context
            self.log.debug(f'fill soft ctx')
            r_ctx = self._fill_soft_ctx(start_pdu=start_pdu, ctx=r_ctx)
            if not r_ctx:
                self.log.debug(f'not soft ctx')
                return None, None

            # checking addresses
            if not self.__check_addresses(r_ctx, soft_ctx):
                self.log.debug('Not same address')
                return None, None

            # collecting segments
            try:
                self.log.debug(f'collect segments')
                sorted_segments = \
                    await asyncio.wait_for(self._collect_segments(soft_ctx),
                                           segment_timeout)
            except Exception as e:
                raise e
            except asyncio.TimeoutError:
                self.log.debug('Giving up of segmented message')

            # join segments
            self.log.debug(f'join segments')
            transport_pdu = self._join_segments([start_pdu] + sorted_segments)

            # decrypting pdu
            self.log.debug(f'decryption pdu')
            access_pdu = self._decrypt_transport_pdu(transport_pdu, r_ctx,
                                                     first_seq)
            if not access_pdu:
                return None, None

        self.log.debug(f'ret pdu')
        return access_pdu, r_ctx

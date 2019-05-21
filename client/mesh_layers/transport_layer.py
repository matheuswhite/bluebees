from client.mesh_layers.network_layer import NetworkLayer
from client.mesh_layers.mesh_context import SoftContext
from client.network.network_data import NetworkData
from client.application.application_data import ApplicationData
from client.node.node_data import NodeData
from client.data_paths import base_dir, net_dir, app_dir, node_dir
from common.logging import log_sys, INFO, DEBUG
from common.crypto import crypto
from common.file import file_helper
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
        self.log.set_level(DEBUG)

    # send methods
    def _encrypt_access_pdu(self, pdu: bytes, soft_ctx: SoftContext) -> bytes:
        net_data = NetworkData.load(base_dir + net_dir +
                                    soft_ctx.network_name + '.yml')
        self.net_layer.hard_ctx.seq = net_data.seq

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

        print(f'App_key: {app_key.hex()}, app_nonce: {app_nonce.hex()}, mic: {mic.hex()}, result (len {len(result)}: {result.hex()})')

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

        unseg_tr_pdu = (unseg_tr_pdu | (int.from_bytes(aid, 'big') & 0x3f)).to_bytes(1, 'big')
        unseg_tr_pdu += pdu

        print(f'aid: {aid.hex()}, unseg_tr: {unseg_tr_pdu.hex()}')

        return unseg_tr_pdu

    def __header_segmented_transport_pdu(self, soft_ctx: SoftContext,
                                         seg_o: int) -> bytes:
        net_data = NetworkData.load(base_dir + net_dir +
                                    soft_ctx.network_name + '.yml')
        seq_auth = (int.from_bytes(net_data.iv_index, 'big') << 24) | \
            net_data.seq
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

    def __check_addresses(self, recv_ctx: SoftContext, ctx: SoftContext):
        return (recv_ctx.src_addr == ctx.dst_addr) and \
            (recv_ctx.dst_addr == ctx.src_addr)

    async def _wait_ack(self, soft_ctx: SoftContext, segments: List[bytes]):
        ack_bits = 0
        expected_ack_bits = (2 ** (self.net_layer.hard_ctx.seg_n + 1)) - 1
        while True:
            self.log.debug(f'Waiting ack...')
            ack_pdu, r_ctx = await self.net_layer.transport_pdus.get()
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
                        self.log.debug(f'Send segment: {i}')
                        await self.net_layer.send_pdu(seg, soft_ctx)
                    bits = bits >> 1
                self.log.debug(f'Ack bits [a]: {hex(ack_bits)}')

    async def send_pdu(self, access_pdu: bytes, soft_ctx: SoftContext):
        self.net_layer.hard_ctx.reset()

        crypt_access_pdu = self._encrypt_access_pdu(access_pdu, soft_ctx)

        if len(crypt_access_pdu) <= LT_MTU:
            transport_pdu = self._unsegmented_transport_pdu(crypt_access_pdu,
                                                            soft_ctx)
            self.net_layer.hard_ctx.is_ctrl_msg = False

            await self.net_layer.send_pdu(transport_pdu, soft_ctx)
        else:
            segments = self._segmented_transport_pdu(crypt_access_pdu,
                                                     soft_ctx)
            self.net_layer.hard_ctx.is_ctrl_msg = False

            for seg in segments:
                await self.net_layer.send_pdu(seg, soft_ctx)

            try:
                await asyncio.wait_for(self._wait_ack(soft_ctx, segments),
                                       soft_ctx.ack_timeout)
            except asyncio.TimeoutError:
                self.log.error('Wait ack timeout')

    # receive methods
    async def __send_ack(self, seg_o_table: dict, soft_ctx: SoftContext):
        if not seg_o_table:
            return

        pdu = 0x00
        pdu = pdu | ((self.net_layer.hard_ctx.seq_zero & 0x1fff) << 2)
        pdu = pdu.to_bytes(3, 'big')
        block_ack = 0x0000_0000
        for k, _ in seg_o_table.items():
            block_ack = block_ack | (1 << k)
        pdu += block_ack.to_bytes(4, 'big')

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

        return None

    def _fill_hard_ctx(self, start_pdu: bytes):
        self.net_layer.hard_ctx.szmic = (start_pdu[1] & 0x80) >> 7
        self.net_layer.hard_ctx.seq_zero = \
            (int.from_bytes(start_pdu[1:3], 'big') & 0x7ffc) >> 7
        self.net_layer.hard_ctx.seg_o = \
            (int.from_bytes(start_pdu[2:4], 'big') & 0x03e0) >> 5
        self.net_layer.hard_ctx.seg_n = start_pdu[3] & 0x1f

    def _fill_soft_ctx(self, start_pdu: bytes,
                       ctx: SoftContext) -> SoftContext:
        afk = start_pdu[0] & 0x40 >> 6
        aid = start_pdu[0] & 0x3f
        if afk == 1:
            app_name = self.__search_application_by_aid(aid)
            ctx.application_name = app_name
            ctx.is_devkey = False
        else:
            ctx.application_name = ''
            ctx.is_devkey = True

        node_name = self.__search_node_by_addr(ctx.src_addr)
        if not node_name:
            self.log.error(f'Node not found with addr {ctx.src_addr.hex()}')
            return None

        ctx.node_name = node_name

        return ctx

    def _join_segments(self, sorted_segments: List[bytes]) -> bytes:
        tr_pdu = b''
        for seg in sorted_segments:
            tr_pdu += seg[4:]

        return tr_pdu

    def _decrypt_transport_pdu(self, pdu: bytes, ctx: SoftContext) -> bytes:
        encrypted_pdu = pdu[0:-4]
        transport_mic = pdu[-4:]

        net_data = NetworkData.load(base_dir + net_dir + ctx.network_name +
                                    '.yml')

        if ctx.is_devkey:
            self.log.debug(f'node name: {ctx.node_name}')
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
        nonce += self.net_layer.hard_ctx.seq.to_bytes(3, 'big')
        nonce += ctx.src_addr
        nonce += ctx.dst_addr
        nonce += net_data.iv_index

        access_pdu, mic_is_ok = crypto.aes_ccm_decrypt(key=key, nonce=nonce,
                                                       text=encrypted_pdu,
                                                       mic=transport_mic)

        self.log.debug(f'Access PDU: {access_pdu.hex()}')

        if not mic_is_ok:
            self.log.warning(f'Mic is wrong')
            return None
        else:
            return access_pdu

    async def _collect_segments(self, soft_ctx: SoftContext) -> List[bytes]:
        seg_o_table = {}
        ack_counter = 0
        while len(seg_o_table) < self.net_layer.hard_ctx.seg_n:
            pdu, r_ctx = await self.net_layer.transport_pdus.get()

            # not same src and dst address (discard)
            if not self.__check_addresses(r_ctx, soft_ctx):
                continue

            # each 10 messages received, sent a ack
            if ack_counter >= 10:
                await self.__send_ack(seg_o_table, soft_ctx)
                ack_counter = 0
            else:
                ack_counter += 1

            # control message (discard)
            if self.net_layer.hard_ctx.is_ctrl_msg:
                continue

            # unsegmented pdu (discard)
            if ((pdu[0] & 0x80) >> 7) == 0:
                continue

            seg_o = (int.from_bytes(pdu[2:4], 'big') & 0x03e0) >> 5
            # segment already received (discard)
            if seg_o in seg_o_table.keys():
                continue

            seg_o_table[seg_o] = pdu

        # send ack message
        await self.__send_ack(seg_o_table, soft_ctx)

        segments = []
        for _, v in seg_o_table.items():
            segments.append(v)

        return segments

    async def recv_pdu(self, segment_timeout: int) -> (bytes, SoftContext):
        # self.net_layer.hard_ctx.reset()

        start_pdu, soft_ctx = await self.net_layer.transport_pdus.get()

        while self.net_layer.hard_ctx.is_ctrl_msg:
            start_pdu, soft_ctx = await self.net_layer.transport_pdus.get()

        # unsegmented pdu
        self.log.debug('Testing if is segmented...')
        if ((start_pdu[0] & 0x80) >> 7) == 0:
            self.log.debug(f'Is unsegmented. PDU: {start_pdu.hex()}')
            soft_ctx = self._fill_soft_ctx(start_pdu=start_pdu, ctx=soft_ctx)
            if not soft_ctx:
                return None, None

            start_pdu = start_pdu[1:]
            self.log.debug('Start decrypting...')
            access_pdu = self._decrypt_transport_pdu(start_pdu, soft_ctx)
            self.log.debug('End decrypt')

            return access_pdu, soft_ctx

        # segmented pdu
        self._fill_hard_ctx(start_pdu)
        soft_ctx = self._fill_soft_ctx(start_pdu=start_pdu, ctx=soft_ctx)
        if not soft_ctx:
            return None, None

        try:
            sorted_segments = \
                await asyncio.wait_for(self._collect_segments(soft_ctx),
                                       segment_timeout)
        except Exception as e:
            self.log.critical(f'Unknown Exception:\n{e}')
            return None, None
        except asyncio.TimeoutError:
            self.log.debug('Giving up of segmented message')

        transport_pdu = self._join_segments([start_pdu] + sorted_segments)

        access_pdu = self._decrypt_transport_pdu(transport_pdu, soft_ctx)

        return access_pdu, soft_ctx

from client.mesh_layers.network_layer import NetworkLayer
from client.mesh_layers.mesh_context import HardContext, SoftContext
from client.network.network_data import NetworkData
from client.application.application_data import ApplicationData
from client.node.node_data import NodeData
from client.data_paths import base_dir, net_dir, app_dir, node_dir
from common.logging import log_sys, INFO
from common.crypto import crypto
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

    def __init__(self):
        self.net_layer = NetworkLayer()

        self.log = log_sys.get_logger('transport_layer')
        self.log.set_level(INFO)

    # send methods
    def _encrypt_access_pdu(self, pdu: bytes, soft_ctx: SoftContext) -> bytes:
        net_data = NetworkData.load(base_dir + net_dir +
                                    soft_ctx.network_name + '.yml')
        if not soft_ctx.is_devkey:
            app_data = ApplicationData.load(base_dir + app_dir +
                                            soft_ctx.application_name +
                                            '.yml')
            app_key = app_data.key
            app_nonce = b'\x01\x00' + \
                self.net_layer.hard_ctx.seq.to_bytes(3, 'big') + \
                soft_ctx.src_addr.to_bytes(2, 'big') + \
                soft_ctx.dst_addr.to_bytes(2, 'big') + net_data.iv_index
        else:
            node_data = NodeData.load(base_dir + node_dir +
                                      soft_ctx.node_name + '.yml')
            app_key = node_data.devkey
            app_nonce = b'\x02\x00' + \
                self.net_layer.hard_ctx.seq.to_bytes(3, 'big') + \
                soft_ctx.src_addr.to_bytes(2, 'big') + \
                soft_ctx.dst_addr.to_bytes(2, 'big') + net_data.iv_index

        return crypto.aes_ccm(key=app_key, nonce=app_nonce, text=pdu,
                              adata=b'')

    def _unsegmented_transport_pdu(self, pdu: bytes,
                                   soft_ctx: SoftContext) -> bytes:
        if not soft_ctx.is_devkey:
            app_data = ApplicationData.load(base_dir + app_dir +
                                            soft_ctx.application_name +
                                            '.yml')
            aid = crypto.k4(n=app_data.key)
            unseg_tr_pdu = 0x00
        else:
            node_data = NodeData.load(base_dir + node_dir +
                                      soft_ctx.node_name + '.yml')
            aid = crypto.k4(n=node_data.devkey)
            unseg_tr_pdu = 0x40

        unseg_tr_pdu = (unseg_tr_pdu | (aid & 0x3f)).to_bytes(1, 'big')
        unseg_tr_pdu += pdu

        return unseg_tr_pdu

    def __header_segmented_transport_pdu(self, soft_ctx: SoftContext,
                                         seg_n: int, seg_o: int) -> bytes:
        net_data = NetworkData.load(base_dir + net_dir +
                                    soft_ctx.network_name + '.yml')
        seq_auth = (int.from_bytes(net_data.iv_index, 'big') << 24) | \
            net_data.seq
        seq_zero = seq_auth & 0x1fff

        first_byte = 0x80
        if not soft_ctx.is_devkey:
            app_data = ApplicationData.load(base_dir + app_dir +
                                            soft_ctx.application_name +
                                            '.yml')
            aid = crypto.k4(n=app_data.key)
        else:
            node_data = NodeData.load(base_dir + node_dir +
                                      soft_ctx.node_name + '.yml')
            aid = crypto.k4(n=node_data.devkey)
            first_byte = first_byte | 0x40
        first_byte = (first_byte | (aid & 0x3f)).to_bytes(1, 'big')

        cont = (seg_n & 0x1f)
        cont = cont | ((seg_o & 0x1f) << 5)
        cont = (cont | ((seq_zero & 0x1fff) << 10)).to_bytes(3, 'big')

        return first_byte + cont

    def _segmented_transport_pdu(self, pdu: bytes,
                                 soft_ctx: SoftContext) -> List[bytes]:
        seg_n = int((len(pdu) - 1) / LT_MTU)
        segments = []

        for seg_o in range(seg_n + 1):
            header = self.__header_segmented_transport_pdu(soft_ctx, seg_n,
                                                           seg_o)
            segments.append(header + pdu[0:LT_MTU])
            pdu = pdu[LT_MTU:]

        return segments

    async def _wait_ack(self, soft_ctx: SoftContext):
        pass

    async def send_pdu(self, access_pdu: bytes, soft_ctx: SoftContext):
        self.net_layer.hard_ctx.reset()

        crypt_access_pdu = self._encrypt_access_pdu(access_pdu, soft_ctx)

        if len(crypt_access_pdu) <= LT_MTU:
            transport_pdu = self._unsegmented_transport_pdu(crypt_access_pdu,
                                                            soft_ctx)
            self.net_layer.hard_ctx.is_crtl_msg = False

            await self.net_layer.send_pdu(transport_pdu, soft_ctx)
        else:
            segments = self._segmented_transport_pdu(crypt_access_pdu,
                                                     soft_ctx)
            self.net_layer.hard_ctx.is_crtl_msg = False

            for seg in segments:
                await self.net_layer.send_pdu(seg, soft_ctx)

            await self._wait_ack(soft_ctx)

    # receive methods
    def _fill_hard_ctx(self, start_pdu: bytes):
        pass

    def _fill_soft_ctx(self, start_pdu: bytes,
                       is_segmented: bool) -> SoftContext:
        pass

    def _join_segments(self, sorted_segments: List[bytes]) -> bytes:
        pass

    def _decrypt_transport_pdu(self, pdu: bytes, ctx: SoftContext) -> bytes:
        pass

    async def _collect_segments(self):
        pass

    async def recv_pdu(self, segment_timeout: int) -> bytes:
        self.net_layer.hard_ctx.reset()

        start_pdu = await self.net_layer.transport_pdus.get()

        # unsegmented pdu
        if ((start_pdu[0] & 0x80) >> 7) == 0:
            soft_ctx = self._fill_soft_ctx(start_pdu=start_pdu,
                                           is_segmented=False)

            start_pdu = start_pdu[1:]
            access_pdu = self._decrypt_transport_pdu(start_pdu, soft_ctx)

            return access_pdu

        # segmented pdu
        self._fill_hard_ctx(start_pdu)
        soft_ctx = self._fill_soft_ctx(start_pdu=start_pdu,
                                       is_segmented=True)

        try:
            sorted_segments = await asyncio.wait_for(self._collect_segments(),
                                                     segment_timeout)
        except Exception as e:
            self.log.critical(f'Unknown Exception:\n{e}')
            return
        except asyncio.TimeoutError:
            self.log.debug('Giving up of segmented message')

        transport_pdu = self._join_segments([start_pdu] + sorted_segments)

        access_pdu = self._decrypt_transport_pdu(transport_pdu, soft_ctx)

        return access_pdu

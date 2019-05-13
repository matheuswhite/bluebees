from client.mesh_layers.network_layer import NetworkLayer
from client.mesh_layers.mesh_context import HardContext, SoftContext
from common.logging import log_sys, INFO
from typing import List
import asyncio

LT_MTU = 12


class AckTimeout(Exception):
    pass


class TransportLayer:

    def __init__(self):
        self.net_layer = NetworkLayer()

        self.log = log_sys.get_logger('transport_layer')
        self.log.set_level(INFO)

    # send methods
    def _encrypt_access_pdu(self, pdu: bytes, soft_ctx: SoftContext) -> bytes:
        pass

    def _unsegmented_transport_pdu(self, pdu: bytes,
                                   soft_ctx: SoftContext) -> bytes:
        pass

    def _segmented_transport_pdu(self, pdu: bytes,
                                 soft_ctx: SoftContext) -> List[bytes]:
        pass

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

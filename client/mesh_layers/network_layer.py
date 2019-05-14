from client.mesh_layers.mesh_context import HardContext, SoftContext
import asyncio


class NetworkLayer:

    def __init__(self):
        self.hard_ctx = HardContext()
        self.hard_ctx.reset()

        # (transport_pdu: bytes, soft_ctx: SoftContext)
        self.transport_pdus = asyncio.Queue()

    async def send_pdu(self, transport_pdu: bytes, soft_ctx: SoftContext):
        pass

    async def recv_pdu(self):
        while True:
            pass

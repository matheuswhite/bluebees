#!/usr/bin/python3
from core.socket import Socket, Address, PDU


class ProvisioningBearerSocket(Socket):

    def __init__(self, device_uuid: bytes, dongle_port: str):
        super().__init__(Address.UUID(device_uuid))

        self._dongle_port = dongle_port

    def open(self):
        super().open()

    def write(self, payload: PDU):
        super().write(payload)

    async def read(self):
        super().read()

    def close(self):
        super().close()

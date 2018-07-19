#!/usr/bin/python3
from core.socket import Socket, Address, PDU
from core.dongle_socket import *
from core.adv_socket import ProvisioningBearerADVSocket


class GenericProvisioningPDU(PDU):

    def __init__(self, control: bytes, payload: bytes):
        super().__init__(control + payload)


class GenericProvisioningSocket(Socket):

    def __init__(self, device_uuid: bytes, dongle_port: str, prov_bearer: int):
        super().__init__(Address.UUID(device_uuid))

        self.__dongle_port = dongle_port
        self.__prov_bearer = prov_bearer

    def open(self):
        super().open()

    def write(self, payload: PDU):
        super().write(payload)

        if self.__prov_bearer == PB_ADV:
            with ProvisioningBearerADVSocket(self.address.value, self.__dongle_port) as socket:
                pass
                # TODO: write gprov pdu
        else:
            raise NotImplemented

    async def read(self):
        super().read()

    def close(self):
        super().close()

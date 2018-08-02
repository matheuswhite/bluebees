#!/usr/bin/python3
from core.socket import Socket, Address, PDU
from core.dongle_socket import *
from core.adv_socket import ProvisioningBearerADVSocket, ADV_MTU_SIZE
from math import ceil


class GenericProvisioningPDU(PDU):

    def __init__(self, control: bytes, payload: bytes):
        super().__init__(control + payload)


class GenericProvisioningSocket(Socket):

    def __init__(self, device_uuid: bytes, dongle_port: str, prov_bearer: int):
        super().__init__(Address.UUID(device_uuid))

        self.__dongle_port = dongle_port
        self.__prov_bearer = prov_bearer
        self.__socket = None

    def __segment_payload(self, payload):
        if self.__prov_bearer == PB_ADV:
            GPROV_MTU_SIZE = ADV_MTU_SIZE
        else:
            raise NotImplemented

        payload_length = len(payload)

        if payload_length > GPROV_MTU_SIZE:
            last_seg_number = int(ceil(payload_length / GPROV_MTU_SIZE))

            for x in range(0, last_seg_number):
                yield payload[:GPROV_MTU_SIZE]
                payload = payload[GPROV_MTU_SIZE:]
        else:
            yield payload

    def open(self):
        super().open()

        if self.__prov_bearer == PB_ADV:
            self.__socket = ProvisioningBearerADVSocket(self.address.value, self.__dongle_port)
            self.__socket.open()
        else:
            raise NotImplemented

    def write(self, payload: PDU):
        super().write(payload)

        if self.__prov_bearer == PB_ADV:
            # Transaction Start
            last_seg_number = int(ceil(len(payload.value) / ADV_MTU_SIZE)) - 1

            # Delay random 20~50ms

            # Transaction Continuation

            # Delay random 20~50ms


        else:
            raise NotImplemented

    def read(self):
        super().read()

    def close(self):
        super().close()

        if self.__prov_bearer == PB_ADV:
            self.__socket.close()
        else:
            raise NotImplemented

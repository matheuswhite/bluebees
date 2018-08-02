#!/usr/bin/python3
from core.socket import Address
from core.dongle_socket import DongleSocket

DEFAULT_ATTENTION_DURATION = 3


class Network:
    pass


class OOB:

    def __init__(self, size, action):
        self.size = size
        self.action = action


class DeviceCapabilities:

    def __init__(self, parameters: bytes):
        self.n_elements = parameters[0:1]
        self.algorithm = parameters[1:3]
        self.public_key_type = parameters[3:4]
        self.static_oob_type = parameters[4:5]
        self.output_oob = OOB(parameters[5:6], parameters[6:8])
        self.input_oob = OOB(parameters[8:9], parameters[9:11])


class Device:

    def __init__(self, uuid: bytes):
        self.uuid = uuid
        self.__capabilities = None
        self.__attention_duration = DEFAULT_ATTENTION_DURATION

    @property
    def capabilities(self):
        return self.__capabilities

    @capabilities.setter
    def capabilities(self, value):
        self.__capabilities = value

    @property
    def attention_duration(self):
        return self.__attention_duration

    @attention_duration.setter
    def attention_duration(self, value):
        self.__attention_duration = value


class Provisioner:

    def __init__(self, dongle_address: str):
        self.__dongle_addr = dongle_address

    @staticmethod
    def is_scan_packet(packet: bytes):
        return packet[0:1] == 0x00 and len(packet) == 23

    def get_unprovisioned_device(self):
        with DongleSocket(self.__dongle_addr, 115200) as socket:
            while True:
                packet = socket.read()
                if self.is_scan_packet(packet):
                    return Device(uuid=packet[1:17])

    async def provision_device(self, device: Device):
        # invite ->
        # capabilities <-
        # start ->

        return device

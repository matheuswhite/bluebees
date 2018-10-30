from data_structs.buffer import Buffer
from dataclasses import dataclass


class Capabilities:

    def __init__(self, buffer: Buffer):
        self.number_elements = buffer.pull_u8()
        self.algorithms = buffer.pull_be16()
        self.public_key_type = buffer.pull_u8()
        self.static_oob_type = buffer.pull_u8()
        self.output_oob_size = buffer.pull_u8()
        self.output_oob_action = buffer.pull_be16()
        self.input_oob_size = buffer.pull_u8()
        self.input_oob_action = buffer.pull_be16()


@dataclass
class ProvisioningData:
    netkey: bytes
    netkey_index: int
    key_refresh_flag: int
    iv_update_flag: int
    current_iv_index: int
    unicast_address: bytes


class Device:

    def __init__(self, uuid: bytes):
        self.__uuid = uuid
        self.__capabilities = None
        self.__provisioning_data = None

    @property
    def uuid(self):
        return self.__uuid

    @property
    def capabilities(self):
        return self.__capabilities

    @capabilities.setter
    def capabilities(self, capabilities: Capabilities):
        self.__capabilities = capabilities

    @property
    def provisioning_data(self):
        return self.__provisioning_data

    @provisioning_data.setter
    def provisioning_data(self, prov_data: ProvisioningData):
        self.__provisioning_data = prov_data

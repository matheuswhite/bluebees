from core.buffer import Buffer


class Capabilities:

    def __init__(self, buffer: Buffer):
        self.__number_elements = buffer.pull_u8()
        self.__algorithms = buffer.pull_be16()
        self.__public_key_type = buffer.pull_u8()
        self.__static_oob_type = buffer.pull_u8()
        self.__output_oob_size = buffer.pull_u8()
        self.__output_oob_action = buffer.pull_be16()
        self.__input_oob_size = buffer.pull_u8()
        self.__input_oob_action = buffer.pull_be16()

    @property
    def number_elements(self):
        return self.__number_elements

    @property
    def algorithms(self):
        return self.__algorithms

    @property
    def public_key_type(self):
        return self.__public_key_type

    @property
    def static_oob_type(self):
        return self.__static_oob_type

    @property
    def output_oob_size(self):
        return self.__output_oob_size

    @property
    def output_oob_action(self):
        return self.__output_oob_action

    @property
    def input_oob_size(self):
        return self.__input_oob_size

    @property
    def input_oob_action(self):
        return self.__input_oob_action


class ProvisioningData:

    def __init__(self, netkey, netkey_index, key_refresh_flag, iv_update_flag, current_iv_index, unicast_address):
        self.__netkey = netkey
        self.__netkey_index = netkey_index
        self.__key_refresh_flag = key_refresh_flag
        self.__iv_update_flag = iv_update_flag
        self.__current_iv_index = current_iv_index
        self.__unicast_address = unicast_address

    @property
    def netkey(self):
        return self.__netkey

    @property
    def netkey_index(self):
        return self.__netkey_index

    @property
    def key_refresh_flag(self):
        return self.__key_refresh_flag

    @property
    def iv_update_flag(self):
        return self.__iv_update_flag

    @property
    def current_iv_index(self):
        return self.__current_iv_index

    @property
    def unicast_address(self):
        return self.__unicast_address


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

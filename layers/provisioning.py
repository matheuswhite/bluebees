from core.utils import timer
from threading import Event
from core.link import Link
from data_structs.buffer import Buffer
from layers.gprov import CLOSE_SUCCESS, CLOSE_FAIL, CLOSE_TIMEOUT
from core.device import Capabilities


PROVISIONING_INVITE = 0x00
PROVISIONING_CAPABILITIES = 0x01
PROVISIONING_START = 0x02
PROVISIONING_PUBLIC_KEY = 0x03
PROVISIONING_INPUT_COMPLETE = 0x04
PROVISIONING_CONFIRMATION = 0x05
PROVISIONING_RANDOM = 0x06
PROVISIONING_DATA = 0x07
PROVISIONING_COMPLETE = 0x08
PROVISIONING_FAILED = 0x09


class ProvisioningFail(Exception):
    pass


class ProvisioningTimeout(Exception):
    pass


class ProvisioningLayer:

    def __init__(self, gprov_layer, dongle_driver):
        self.__gprov_layer = gprov_layer
        self.__dongle_driver = dongle_driver
        self.__link = None
        self.__device_capabilities = None
        self.__priv_key = None
        self.__pub_key = None
        self.__device_pub_key = None
        self.default_attention_duration = 5
        self.public_key_type = 0x00
        self.authentication_method = 0x00
        self.authentication_action = 0x00
        self.authentication_size = 0x00

    def scan(self, timeout=None):
        device = None

        if timeout is not None:
            scan_timeout_event = Event()
            timer(timeout, scan_timeout_event)
            while not scan_timeout_event.is_set():
                content = self.__dongle_driver.recv('beacon', 1, 0.5)
                if content is not None:
                    device = self.__process_beacon_content(content)
                    break
        else:
            content = self.__dongle_driver.recv('beacon')
            device = self.__process_beacon_content(content)

        return device

    def provisioning_device(self, device_uuid: bytes):
        self.__link = Link(device_uuid)
        self.__gprov_layer.open(self.__link)

        try:
            self.__invitation_prov_phase()
            self.__exchanging_pub_keys_prov_phase()
            self.__authentication_prov_phase()
            self.__send_data_prov_phase()

            self.__link.close_reason = CLOSE_SUCCESS
        except ProvisioningFail:
            self.__link.close_reason = CLOSE_FAIL
        except ProvisioningTimeout:
            self.__link.close_reason = CLOSE_TIMEOUT
        finally:
            self.__gprov_layer.close(self.__link)

    # TODO: change this to get only device uuid
    def __process_beacon_content(self, content):
        return content

    def __invitation_prov_phase(self):
        # send prov invite
        send_buff = Buffer()
        send_buff.push_u8(PROVISIONING_INVITE)
        send_buff.push_u8(self.default_attention_duration)
        self.__gprov_layer.send(self.__link, send_buff.buffer_be())

        # recv prov capabilities
        recv_buff = Buffer()
        content = self.__gprov_layer.recv(self.__link)
        recv_buff.push_be(content)
        opcode = recv_buff.pull_u8()
        if opcode != PROVISIONING_CAPABILITIES:
            raise ProvisioningFail()
        self.__device_capabilities = Capabilities(recv_buff)

    def __exchanging_pub_keys_prov_phase(self):
        # send prov start (No OOB)
        start_buff = Buffer()
        start_buff.push_u8(PROVISIONING_START)
        start_buff.push_u8(0x00)
        start_buff.push_u8(self.public_key_type)
        start_buff.push_u8(self.authentication_method)
        start_buff.push_u8(self.authentication_action)
        start_buff.push_u8(self.authentication_size)
        self.__gprov_layer.send(self.__link, start_buff.buffer_be())

        # gen priv_key and pub_key
        self.__gen_keys()

        # send my pub key
        pub_key_buff = Buffer()
        pub_key_buff.push_u8(PROVISIONING_PUBLIC_KEY)
        pub_key_buff.push_be(self.__pub_key['x'])
        pub_key_buff.push_be(self.__pub_key['y'])
        self.__gprov_layer.send(self.__link, pub_key_buff.buffer_be())

        # recv device pub key
        recv_buff = Buffer()
        content = self.__gprov_layer.recv(self.__link)
        recv_buff.push_be(content)
        opcode = recv_buff.pull_u8()
        if opcode != PROVISIONING_PUBLIC_KEY:
            raise ProvisioningFail()
        self.__device_pub_key = {
            'x': recv_buff.pull_be(32),
            'y': recv_buff.pull_be(32)
        }

        # calc ecdh_secret = P-256(priv_key, dev_pub_key)
        self.__calc_ecdh_secret()

    def __authentication_prov_phase(self):
        raise NotImplementedError

    def __send_data_prov_phase(self):
        raise NotImplementedError

    def __gen_keys(self):
        self.__priv_key = 0
        self.__pub_key = {
            'x': b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                 b'\x00\x00\x00\x00\x00\x00\x00\x00',
            'y': b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                 b'\x00\x00\x00\x00\x00\x00\x00\x00'
        }

        raise NotImplementedError

    def __calc_ecdh_secret(self):
        raise NotImplementedError

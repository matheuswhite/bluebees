from core.utils import timer
from threading import Event
from core.link import Link
from data_structs.buffer import Buffer
from layers.gprov import CLOSE_SUCCESS, CLOSE_FAIL, CLOSE_TIMEOUT
from core.device import Capabilities
from ecdsa import SigningKey, NIST256p

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


# TODO: Add the verification o provisioning fail at each step
class ProvisioningLayer:

    def __init__(self, gprov_layer, dongle_driver):
        self.__gprov_layer = gprov_layer
        self.__dongle_driver = dongle_driver
        self.__link = None
        self.__device_capabilities = None
        self.__priv_key = None
        self.__pub_key = None
        self.__device_pub_key = None
        self.__ecdh_secret = None
        self.__sk = None
        self.__vk = None
        self.__provisioning_invite = None
        self.__provisioning_capabilities = None
        self.__provisioning_start = None
        self.__auth_value = None
        self.__random_provisioner = None
        self.__random_device = None
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
    @staticmethod
    def __process_beacon_content(content: bytes):
        return content.split(b' ')[1]

    def __invitation_prov_phase(self):
        # send prov invite
        send_buff = Buffer()
        send_buff.push_u8(PROVISIONING_INVITE)
        send_buff.push_u8(self.default_attention_duration)
        self.__gprov_layer.send(self.__link, send_buff.buffer_be())

        self.__provisioning_invite = self.default_attention_duration

        # recv prov capabilities
        recv_buff = Buffer()
        content = self.__gprov_layer.recv(self.__link)
        recv_buff.push_be(content)
        opcode = recv_buff.pull_u8()
        self.__provisioning_capabilities = recv_buff.buffer_be()
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
        self.__provisioning_start = start_buff.buffer_be()[1:]
        self.__auth_value = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
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
        buff = Buffer()

        # calc crypto values need
        confirmation_inputs = self.__provisioning_invite + self.__provisioning_capabilities + \
                              self.__provisioning_start + self.__pub_key['x'] + self.__pub_key['y'] + \
                              self.__device_pub_key['x'] + self.__device_pub_key['y']
        confirmation_salt = self.__s1(confirmation_inputs)
        confirmation_key = self.__k1(self.__ecdh_secret, confirmation_salt, 'prck')

        self.__gen_random_provisioner()

        # send confirmation provisioner
        confirmation_provisioner = self.__aes_cmac(confirmation_key, self.__random_provisioner, self.__auth_value)
        buff.push_be(confirmation_provisioner)
        self.__gprov_layer.send(self.__link, buff.buffer_be())

        # recv confiramtion device
        recv_confirmation_device = self.__recv(opcode_verification=PROVISIONING_CONFIRMATION)

        # send random provisioner
        buff.clear()
        buff.push_be(self.__random_provisioner)
        self.__gprov_layer.send(self.__link, buff.buffer_be())

        # recv random device
        self.__random_device = self.__recv(PROVISIONING_RANDOM)

        # check info
        calc_confiramtion_device = self.__aes_cmac(confirmation_key, self.__random_device, self.__auth_value)

        if recv_confirmation_device != calc_confiramtion_device:
            raise ProvisioningFail()

    def __send_data_prov_phase(self):
        raise NotImplementedError

    def __recv(self, opcode_verification=None):
        buff = Buffer()
        buff.push_be(self.__gprov_layer.recv(self.__link))
        opcode = buff.pull_u8()
        content = buff.buffer_be()
        if opcode == PROVISIONING_FAILED:
            raise ProvisioningFail()
        if opcode_verification is not None:
            if opcode != opcode_verification:
                raise ProvisioningFail()
            return content
        else:
            return opcode, content

    def __gen_keys(self):

        self.__sk = SigningKey.generate(curve=NIST256p)
        self.__vk = self.__sk.get_verifying_key()

        self.__priv_key = self.__sk.to_string()
        self.__pub_key = {
            'x': self.__vk.to_string()[0:32],
            'y': self.__vk.to_string()[32:64]
        }

    # TODO: ECDHsecret is 32 bytes or 64 bytes
    def __calc_ecdh_secret(self):
        secret = self.__sk.privkey.secret_multiplier * self.__vk.pubkey.point

        self.__ecdh_secret = {
            'x': secret.x().to_bytes(32, 'big'),
            'y': secret.y().to_bytes(32, 'big')
        }

    def __s1(self, input_):
        raise NotImplementedError

    def __k1(self, shared_secret, salt, msg):
        raise NotImplementedError

    def __gen_random_provisioner(self):
        self.__random_provisioner = 0

        raise NotImplementedError

    def __aes_cmac(self, key, random, auth):
        raise NotImplementedError

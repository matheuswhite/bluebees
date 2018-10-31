from core.device import Device, Capabilities, ProvisioningData
from core.link import Link
from layers.gprov import GProvLayer
from layers.dongle import DongleDriver
from data_structs.buffer import Buffer
from threading import Event
from core.utils import threaded
from fastecdsa import keys, curve


class Provisioning:

    def __init__(self, gprov_layer: GProvLayer, dongle_driver: DongleDriver):
        self.__gprov_layer = gprov_layer
        self.__dongle_driver = dongle_driver
        self.__devices = []
        self.__link = None
        self.default_attention_duration = 5
        self.is_scan_disable = Event()

    def enable_scan(self):
        self.is_scan_disable.clear()
        self.__scan_task()

    def disable_scan(self):
        self.is_scan_disable.set()

    @threaded
    def __scan_task(self):
        while not self.is_scan_disable.is_set():
            device_uuid = self.__dongle_driver.recv('beacon')
            device = Device(device_uuid)
            self.__devices.append(device)

    @property
    def devices(self):
        return self.__devices

    '''
    This provisioning don't use OOB feature
    '''
    def provisioning_device(self, device: Device):
        self.__gen_new_link(device.uuid)

        device.capabilities = self.__invite_device()

        self.__start_provisioning(device.capabilities)

        priv_key, pub_key_x, pub_key_y = self.__gen_pub_keys()

        dev_pub_key_x, dev_pub_key_y = self.__exchange_public_keys(pub_key_x, pub_key_y)

        self.__start_prov_confirmation()

        self.__start_prov_random_confirmation()

        prov_data = self.__new_prov_data()

        self.__send_prov_data(prov_data)

        self.__close_link()

    def __gen_new_link(self, dev_uuid):
        self.__link = Link(dev_uuid)
        self.__link = self.__gprov_layer.open(self.__link)

    def __invite_device(self):
        invite_msg = Buffer()
        # add invite opcode
        invite_msg.push_u8(0x00)
        # add attention duration
        invite_msg.push_u8(self.default_attention_duration)
        # send invite msg
        self.__gprov_layer.send(self.__link, invite_msg.buffer_be())

        content = self.__gprov_layer.recv()

        capabilities_msg = Buffer()
        capabilities_msg.push_be(content)

        type_ = capabilities_msg.pull_u8()

        if type_ != 0x01:
            raise Exception(f'Expected capabilities msg, but got {type_}')

        capabilities = Capabilities(capabilities_msg)

        return capabilities

    def __start_provisioning(self, capabilities: Capabilities):
        start_msg = Buffer()
        # add start opcode
        start_msg.push_u8(0x02)
        # add algorithm
        start_msg.push_u8(0x00)
        # add public key (No OOB)
        start_msg.push_u8(0x00)
        # add authentication method (No OOB)
        start_msg.push_u8(0x00)
        # add authentication action
        start_msg.push_u8(0x00)
        # add authentication size
        start_msg.push_u8(0x00)
        # send start msg
        self.__gprov_layer.send(self.__link, start_msg.buffer_be())

    # TODO: Implement __gen_pub_keys
    def __gen_pub_keys(self):
        priv_key, pub_key = keys.gen_keypair(curve.P256)
        return priv_key, (pub_key & 0xFFFFFFFF_00000000) >> 32, pub_key & 0x00000000_FFFFFFFF

    def __exchange_public_keys(self, pub_key_x, pub_key_y):
        exchange_keys_msg = Buffer()
        # add exchange keys opcode
        exchange_keys_msg.push_u8(0x03)
        # add public key x
        exchange_keys_msg.push_be32(pub_key_x)
        # add public key y
        exchange_keys_msg.push_be32(pub_key_y)
        # send exchange_keys msg
        self.__gprov_layer.send(self.__link, exchange_keys_msg.buffer_be())

        content = self.__gprov_layer.recv()

        exchange_keys_msg = Buffer()
        exchange_keys_msg.push_be(content)

        type_ = exchange_keys_msg.pull_u8()

        if type_ != 0x05:
            raise Exception(f'Expected exchange_keys msg, but got {type_}')

        dev_pub_key_x = exchange_keys_msg.pull_be32()
        dev_pub_key_y = exchange_keys_msg.pull_be32()

        return dev_pub_key_x, dev_pub_key_y

    def __start_prov_confirmation(self):
        confirmation_msg = Buffer()
        # add confirmation opcode
        confirmation_msg.push_u8(0x05)
        # add zeros
        confirmation_msg.push_be32(0)
        confirmation_msg.push_be32(0)
        confirmation_msg.push_be32(0)
        confirmation_msg.push_be32(0)
        # send confirmation msg
        self.__gprov_layer.send(self.__link, confirmation_msg.buffer_be())

        content = self.__gprov_layer.recv()

        confirmation_msg = Buffer()
        confirmation_msg.push_be(content)

        type_ = confirmation_msg.pull_u8()

        if type_ != 0x05:
            raise Exception(f'Expected confirmation msg, but got {type_}')

        return confirmation_msg.pull_all_be()

    def __start_prov_random_confirmation(self):
        random_msg = Buffer()
        # add random opcode
        random_msg.push_u8(0x06)
        # add zeros
        random_msg.push_be32(0)
        random_msg.push_be32(0)
        random_msg.push_be32(0)
        random_msg.push_be32(0)
        # send random msg
        self.__gprov_layer.send(self.__link, random_msg.buffer_be())

        content = self.__gprov_layer.recv()

        random_msg = Buffer()
        random_msg.push_be(content)

        type_ = random_msg.pull_u8()

        if type_ != 0x06:
            raise Exception(f'Expected random msg, but got {type_}')

        return random_msg.pull_all_be()

    def __send_prov_data(self, prov_data: ProvisioningData):
        pass

    def __close_link(self):
        self.__link.close_reason = b'\x00'
        self.__gprov_layer.close(self.__link)

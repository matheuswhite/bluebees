from core.device import Device, Capabilities
from core.link import Link
from core.message import ProvMessage
from core.gprov import GProvLayer
from core.buffer import Buffer


class Provisioning:

    def __init__(self):
        self.__gprov = GProvLayer()
        self.default_attention_duration = 3

    def enable_scan(self):
        pass

    def disable_scan(self):
        pass

    # Generator
    def devices(self):
        pass

    '''
    This provisioning don't use OOB feature
    '''
    def provisioning_device(self, device: Device):
        link = self.__new_link(device.uuid)

        device.capabilities = self.__invite_device(link)

        self.__start_provisioning(link)

        pub_key, dev_pub_key = self.__gen_pub_keys(link)

        self.__start_prov_confirmation(link)

        self.__start_prov_random_confirmation(link)

        self.__send_prov_data(link)

    def __new_link(self, dev_uuid):
        new_link = Link(dev_uuid)

        new_link = self.__gprov.open(new_link)

        return new_link

    def __invite_device(self, link: Link):
        invite_msg = ProvMessage()

        invite_msg.encode_msg(0x00, bytes(self.default_attention_duration))

        self.__gprov.send(link, invite_msg)

        type_, parameters = self.__gprov.recv(link)

        if type_ != 0x01:
            raise Exception('Expected capabilities msg, but got {}'.format(type_))

        param_buffer = Buffer()
        param_buffer.push_be(parameters)

        capabilities = Capabilities(param_buffer)

        return capabilities

import json

class ProvData:

    def __init__(self, prov_public_key_x: bytes, prov_public_key_y: bytes, dev_public_key_x: bytes, dev_public_key_y: bytes,
                    prov_priv_key: bytes, random_provisioner: bytes, random_device: bytes, auth_value: bytes, 
                    invite_pdu: bytes, capabilities_pdu: bytes, start_pdu: bytes, network_key: bytes, key_index: bytes,
                    flags: bytes, iv_index: bytes, unicast_address: bytes):
        self.prov_public_key_x = prov_public_key_x
        self.prov_public_key_y = prov_public_key_y
        self.dev_public_key_x = dev_public_key_x
        self.dev_public_key_y = dev_public_key_y
        self.prov_priv_key = prov_priv_key
        self.random_provisioner = random_provisioner
        self.random_device = random_device
        self.auth_value = auth_value
        self.invite_pdu = invite_pdu
        self.capabilities_pdu = capabilities_pdu
        self.start_pdu = start_pdu
        self.network_key = network_key
        self.key_index = key_index
        self.flags = flags
        self.iv_index = iv_index
        self.unicast_address = unicast_address

    @classmethod
    def bytes2str(cls, value: bytes):
        return value.hex()

    @classmethod
    def str2bytes(cls, value: str):
        return bytes.fromhex(value)

    def save(self, filename: str):
        with open(filename, 'w') as file:
            data = {
                'prov_public_key_x': self.bytes2str(self.prov_public_key_x),
                'prov_public_key_y': self.bytes2str(self.prov_public_key_y),
                'dev_public_key_x': self.bytes2str(self.dev_public_key_x),
                'dev_public_key_y': self.bytes2str(self.dev_public_key_y),
                'prov_priv_key': self.bytes2str(self.prov_priv_key),
                'random_provisioner': self.bytes2str(self.random_provisioner),
                'random_device': self.bytes2str(self.random_device),
                'auth_value': self.bytes2str(self.auth_value),
                'invite_pdu': self.bytes2str(self.invite_pdu),
                'capabilities_pdu': self.bytes2str(self.capabilities_pdu),
                'start_pdu': self.bytes2str(self.start_pdu),
                'network_key': self.bytes2str(self.network_key),
                'key_index': self.bytes2str(self.key_index),
                'flags': self.bytes2str(self.flags),
                'iv_index': self.bytes2str(self.iv_index),
                'unicast_address': self.bytes2str(self.unicast_address)
            }
            json.dump(data, file)

    @classmethod
    def load(cls, filename: str):
        with open(filename, 'r') as file:
            data = json.load(file)
            return cls(cls.str2bytes(data['prov_public_key_x']), cls.str2bytes(data['prov_public_key_y']), cls.str2bytes(data['dev_public_key_x']),
                        cls.str2bytes(data['dev_public_key_y']), cls.str2bytes(data['prov_priv_key']), cls.str2bytes(data['random_provisioner']), cls.str2bytes(data['random_device']),
                        cls.str2bytes(data['auth_value']), cls.str2bytes(data['invite_pdu']), cls.str2bytes(data['capabilities_pdu']), cls.str2bytes(data['start_pdu']),
                        cls.str2bytes(data['network_key']), cls.str2bytes(data['key_index']),  cls.str2bytes(data['flags']), cls.str2bytes(data['iv_index']), cls.str2bytes(data['unicast_address']))

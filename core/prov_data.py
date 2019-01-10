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

    def save(self, filename: str):
        with open(filename, 'w') as file:
            data = {
                'prov_public_key_x': self.prov_public_key_x,
                'prov_public_key_y': self.prov_public_key_y,
                'dev_public_key_x': self.dev_public_key_x,
                'dev_public_key_y': self.dev_public_key_y,
                'prov_priv_key': self.prov_priv_key,
                'random_provisioner': self.random_provisioner,
                'random_device': self.random_device,
                'auth_value': self.auth_value,
                'invite_pdu': self.invite_pdu,
                'capabilities_pdu': self.capabilities_pdu,
                'start_pdu': self.start_pdu,
                'network_key': self.network_key,
                'key_index': self.key_index,
                'flags': self.flags,
                'iv_index': self.iv_index,
                'unicast_address': self.unicast_address
            }
            json.dump(data, file)

    @classmethod
    def load(cls, filename: str):
        with open(filename, 'r') as file:
            data = json.load(file)
            return cls(data['prov_public_key_x'], data['prov_public_key_y'], data['dev_public_key_x'],
                        data['dev_public_key_y'], data['prov_priv_key'], data['random_provisioner'], data['random_device'],
                        data['auth_value'], data['invite_pdu'], data['capabilities_pdu'], data['start_pdu'],
                        data['network_key'], data['key_index'],  data['flags'], data['iv_index'], data['unicast_address'])

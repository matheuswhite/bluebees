from ecdsa import NIST256p
from ecdsa.ecdsa import Public_key, Private_key
from ecdsa.ellipticcurve import Point
from bluebees.common.crypto import crypto


def product(priv, pub):
    priv = int.from_bytes(priv, 'big')
    pub_point = Point(curve=NIST256p.curve, x=int.from_bytes(pub['x'], 'big'),
                      y=int.from_bytes(pub['y'], 'big'))
    pub_key = Public_key(generator=NIST256p.generator, point=pub_point)
    priv_key = Private_key(public_key=pub_key, secret_multiplier=priv)

    return (priv_key.secret_multiplier * pub_key.point).x()


def aes_ccm(key, nonce, data, adata):
    ct, mic = crypto.aes_ccm_complete(key, nonce, data, adata)
    return ct, mic


def aes_cmac(key: bytes, msg: bytes):
    return crypto.aes_cmac(key, msg)


def s1(input_: bytes):
    return crypto.s1(input_)


def k1(shared_secret: bytes, salt: bytes, msg: bytes):
    return crypto.k1(shared_secret, salt, msg)


def calc_confirmation_key(confirmation_inputs: bytes, ecdh_secret: bytes):
    confirmation_salt = crypto.s1(confirmation_inputs)
    confirmation_key = crypto.k1(ecdh_secret, confirmation_salt, b'prck')

    return confirmation_key


def calc_confirmation(confirmation_key: bytes, random_provisioner: bytes,
                      auth_value: bytes):
    confirmation_provisioner = crypto.aes_cmac(confirmation_key,
                                               random_provisioner + auth_value)

    return confirmation_provisioner


def test_crypto():
    # exchange public keys
    prov_priv_key = b'\x06\xa5\x16\x69\x3c\x9a\xa3\x1a\x60\x84\x54\x5d\x0c\x5d\xb6\x41\xb4\x85\x72\xb9\x72\x03\xdd\xff\xb7\xac\x73\xf7\xd0\x45\x76\x63'
    prov_pub_key = {}
    prov_pub_key['x'] = b'\x2c\x31\xa4\x7b\x57\x79\x80\x9e\xf4\x4c\xb5\xea\xaf\x5c\x3e\x43\xd5\xf8\xfa\xad\x4a\x87\x94\xcb\x98\x7e\x9b\x03\x74\x5c\x78\xdd'
    prov_pub_key['y'] = b'\x91\x95\x12\x18\x38\x98\xdf\xbe\xcd\x52\xe2\x40\x8e\x43\x87\x1f\xd0\x21\x10\x91\x17\xbd\x3e\xd4\xea\xf8\x43\x77\x43\x71\x5d\x4f'
    prov_random = b'\x8b\x19\xac\x31\xd5\x8b\x12\x4c\x94\x62\x09\xb5\xdb\x10\x21\xb9'

    dev_priv_key = b'\x52\x9a\xa0\x67\x0d\x72\xcd\x64\x97\x50\x2e\xd4\x73\x50\x2b\x03\x7e\x88\x03\xb5\xc6\x08\x29\xa5\xa3\xca\xa2\x19\x50\x55\x30\xba'
    dev_pub_key = {}
    dev_pub_key['x'] = b'\xf4\x65\xe4\x3f\xf2\x3d\x3f\x1b\x9d\xc7\xdf\xc0\x4d\xa8\x75\x81\x84\xdb\xc9\x66\x20\x47\x96\xec\xcf\x0d\x6c\xf5\xe1\x65\x00\xcc'
    dev_pub_key['y'] = b'\x02\x01\xd0\x48\xbc\xbb\xd8\x99\xee\xef\xc4\x24\x16\x4e\x33\xc2\x01\xc2\xb0\x10\xca\x6b\x4d\x43\xa8\xa1\x55\xca\xd8\xec\xb2\x79'
    dev_random = b'\x55\xa2\xa2\xbc\xa0\x4c\xd3\x2f\xf6\xf3\x46\xbd\x0a\x0c\x1a\x3a'

    assert len(prov_priv_key) == 32
    assert len(prov_pub_key['x']) == 32
    assert len(prov_pub_key['y']) == 32
    assert len(prov_random) == 16

    assert len(dev_priv_key) == 32
    assert len(dev_pub_key['x']) == 32
    assert len(dev_pub_key['y']) == 32
    assert len(dev_random) == 16

    expected_prov_ecdh = 0xab85843a2f6d883f62e5684b38e307335fe6e1945ecd19604105c6f23221eb69
    expected_dev_ecdh = 0xab85843a2f6d883f62e5684b38e307335fe6e1945ecd19604105c6f23221eb69

    prov_ecdh = product(prov_priv_key, dev_pub_key)
    dev_ecdh = product(dev_priv_key, prov_pub_key)

    assert prov_ecdh == expected_prov_ecdh
    assert dev_ecdh == expected_dev_ecdh

    # authentication
    invite_pdu = b'\x00'
    capabilities_pdu = b'\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00'
    start_pdu = b'\x00\x00\x00\x00\x00'
    confirmation_inputs = invite_pdu + capabilities_pdu + start_pdu + \
                          prov_pub_key['x'] + prov_pub_key['y'] + \
                          dev_pub_key['x'] + dev_pub_key['y']

    confirmation_salt = b'\x5f\xaa\xbe\x18\x73\x37\xc7\x1c\xc6\xc9\x73\x36\x9d\xca\xa7\x9a'
    ecdh_secret = b'\xab\x85\x84\x3a\x2f\x6d\x88\x3f\x62\xe5\x68\x4b\x38\xe3\x07\x33\x5f\xe6\xe1\x94\x5e\xcd\x19\x60\x41\x05\xc6\xf2\x32\x21\xeb\x69'

    expected_confirmation_key = b'\xe3\x1f\xe0\x46\xc6\x8e\xc3\x39\xc4\x25\xfc\x66\x29\xf0\x33\x6f'
    confirmation_key = calc_confirmation_key(confirmation_inputs, ecdh_secret)

    assert expected_confirmation_key == confirmation_key

    auth_value = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    expected_confirmation = b'\xb3\x8a\x11\x4d\xfd\xca\x1f\xe1\x53\xbd\x2c\x1e\x0d\xc4\x6a\xc2'
    confirmation = calc_confirmation(confirmation_key, prov_random, auth_value)

    assert expected_confirmation == confirmation

    # distribuition provisioning data
    confirmation_salt = b'\x5f\xaa\xbe\x18\x73\x37\xc7\x1c\xc6\xc9\x73\x36\x9d\xca\xa7\x9a'
    prov_random = b'\x8b\x19\xac\x31\xd5\x8b\x12\x4c\x94\x62\x09\xb5\xdb\x10\x21\xb9'
    dev_random = b'\x55\xa2\xa2\xbc\xa0\x4c\xd3\x2f\xf6\xf3\x46\xbd\x0a\x0c\x1a\x3a'
    provisioning_inputs = confirmation_salt + prov_random + dev_random

    network_key = b'\xef\xb2\x25\x5e\x64\x22\xd3\x30\x08\x8e\x09\xbb\x01\x5e\xd7\x07'
    key_index = b'\x05\x67'
    flags = b'\x00'
    iv_index = b'\x01\x02\x03\x04'
    unicast_address = b'\x0b\x0c'

    provisioning_salt = s1(provisioning_inputs)
    provisioning_data = network_key + key_index + flags + iv_index + \
        unicast_address

    session_key = k1(ecdh_secret, provisioning_salt, b'prsk')
    session_nonce = k1(ecdh_secret, provisioning_salt, b'prsn')
    session_nonce = session_nonce[3:]

    encrypted_provisioning_data, provisioning_data_mic = aes_ccm(session_key,
                                                                 session_nonce,
                                                                 provisioning_data,
                                                                 b'')

    expected_provisioning_salt = b'\xa2\x1c\x7d\x45\xf2\x01\xcf\x94\x89\xa2\xfb\x57\x14\x50\x15\xb4'
    expected_session_key = b'\xc8\x02\x53\xaf\x86\xb3\x3d\xfa\x45\x0b\xbd\xb2\xa1\x91\xfe\xa3'
    expected_session_nonce = b'\xda\x7d\xdb\xe7\x8b\x5f\x62\xb8\x1d\x68\x47\x48\x7e'
    expected_encrypted_provisioning_data = b'\xd0\xbd\x7f\x4a\x89\xa2\xff\x62\x22\xaf\x59\xa9\x0a\x60\xad\x58\xac\xfe\x31\x23\x35\x6f\x5c\xec\x29'
    expected_provisioning_data_mic = b'\x73\xe0\xec\x50\x78\x3b\x10\xc7'

    assert len(provisioning_salt) == len(expected_provisioning_salt)
    assert len(session_key) == len(expected_session_key)
    assert len(session_nonce) == len(expected_session_nonce)
    assert len(encrypted_provisioning_data) == len(expected_encrypted_provisioning_data)
    assert len(provisioning_data_mic) == len(expected_provisioning_data_mic)

    assert provisioning_salt == expected_provisioning_salt
    assert session_key == expected_session_key
    assert session_nonce == expected_session_nonce
    assert encrypted_provisioning_data == expected_encrypted_provisioning_data
    assert provisioning_data_mic == expected_provisioning_data_mic

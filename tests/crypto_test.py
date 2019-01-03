from ecdsa import NIST256p
from ecdsa.ecdsa import Public_key, Private_key
from ecdsa.ellipticcurve import Point
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Hash import CMAC
from core.log import Log

def product(priv, pub):
    priv = int.from_bytes(priv, 'big')
    pub_point = Point(curve=NIST256p.curve, x=int.from_bytes(pub['x'], 'big'), y=int.from_bytes(pub['y'], 'big'))
    pub_key = Public_key(generator=NIST256p.generator, point=pub_point)
    priv_key = Private_key(public_key=pub_key, secret_multiplier=priv)

    return (priv_key.secret_multiplier * pub_key.point).x()

def test_crypto():
    log = Log("Crypto")

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

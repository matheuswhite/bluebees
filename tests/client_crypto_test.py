from binascii import a2b_hex
from client.crypto import CRYPTO


def test_s1():
    expected = a2b_hex('b73cefbd641ef2ea598c2b6efb62f79c')
    assert CRYPTO.s1(b'test') == expected


def test_k1():
    expected = a2b_hex('f6ed15a8934afbe7d83e8dcb57fcf5d7')
    n = a2b_hex('3216d1509884b533248541792b877f98')
    salt = a2b_hex('2ba14ffa0df84a2831938d57d276cab4')
    p = a2b_hex('5a09d60797eeb4478aada59db3352a0d')
    assert CRYPTO.k1(n, salt, p) == expected


def test_k2():
    expected_result = a2b_hex('7f9f589181a0f50de73c8070c7a6d27f464c715bd4a64b938f99b453351653124f')
    expected_nid = a2b_hex('7f')
    expected_encryption_key = a2b_hex('9f589181a0f50de73c8070c7a6d27f46')
    expected_privacy_key = a2b_hex('4c715bd4a64b938f99b453351653124f')
    n = a2b_hex('f7a2a44f8e8a8029064f173ddc1e2b00')
    p = a2b_hex('00')

    result = CRYPTO.k2(n, p)
    nid = result[0:1]
    encryption_key = result[1:17]
    privacy_key = result[17:]

    assert result == expected_result
    assert nid == expected_nid
    assert encryption_key == expected_encryption_key
    assert privacy_key == expected_privacy_key


def test_k3():
    expected_network_id = a2b_hex('ff046958233db014')
    n = a2b_hex('f7a2a44f8e8a8029064f173ddc1e2b00')

    network_id = CRYPTO.k3(n)

    assert network_id == expected_network_id


def test_k4():
    expected_aid = a2b_hex('38')
    n = a2b_hex('3216d1509884b533248541792b877f98')

    aid = CRYPTO.k4(n)

    assert aid == expected_aid


def test_e_encrypt():
    expected = a2b_hex('6ca487507564')
    privacy_key = a2b_hex('8b84eedec100067d670971dd2aa700cf')
    plaintext = a2b_hex('000000000012345678b5e5bfdacbaf6c')

    assert len(privacy_key) == 16
    assert len(plaintext) == 16
    assert CRYPTO.e(privacy_key, plaintext) == expected


def xor(a, b):
    c = b''
    for x in range(len(a)):
        c += int(a[x] ^ b[x]).to_bytes(1, 'big')
    return c


def test_xor():
    expected = a2b_hex('eca487516765')
    a = a2b_hex('6ca487507564')
    b = a2b_hex('800000011201')

    assert xor(a, b) == expected


def test_e_decrypt():
    privacy_random = a2b_hex('b5e5bfdacbaf6cb7fb6bff871f035444ce83a670df')[0:7]
    privacy_key = a2b_hex('8b84eedec100067d670971dd2aa700cf')
    iv_index = a2b_hex('12345678')
    plain_text = b'\x00\x00\x00\x00\x00' + iv_index + privacy_random
    pecb = CRYPTO.e(privacy_key, plain_text)
    obfuscated_data = a2b_hex('eca487516765')

    expected_pecb = a2b_hex('6ca487507564')
    expected = a2b_hex('800000011201')

    assert pecb == expected_pecb
    assert xor(obfuscated_data, pecb) == expected


def test_aes_ccm_encrypt():
    dst = a2b_hex('fffd')
    transport_pdu = a2b_hex('034b50057e400000010000')
    network_nonce = a2b_hex('00800000011201000012345678')
    encryption_key = a2b_hex('0953fa93e7caac9638f58820220a398e')

    expected_result = a2b_hex('b5e5bfdacbaf6cb7fb6bff871f')
    result = CRYPTO.aes_ccm(encryption_key, network_nonce, dst + transport_pdu, b'')
    assert result == expected_result


def test_aes_ccm_decrypt():
    encrypted_pdu = a2b_hex('b5e5bfdacbaf6cb7fb6bff871f')
    network_nonce = a2b_hex('00800000011201000012345678')
    encryption_key = a2b_hex('0953fa93e7caac9638f58820220a398e')

    expected_result = a2b_hex('fffd034b50057e400000010000')
    result = CRYPTO.aes_ccm(encryption_key, network_nonce, encrypted_pdu, b'')
    assert result == expected_result


if __name__ == '__main__':
    test_s1()
    test_k1()
    test_k2()
    test_k3()
    test_k4()
    test_e_encrypt()
    test_xor()
    test_e_decrypt()
    test_aes_ccm_encrypt()
    test_aes_ccm_decrypt()

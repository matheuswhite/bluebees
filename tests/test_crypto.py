from bluebees.common.crypto import crypto


def test_s1():
    expected = bytes.fromhex('b73cefbd641ef2ea598c2b6efb62f79c')
    assert crypto.s1(b'test') == expected


def test_k1():
    expected = bytes.fromhex('f6ed15a8934afbe7d83e8dcb57fcf5d7')
    n = bytes.fromhex('3216d1509884b533248541792b877f98')
    salt = bytes.fromhex('2ba14ffa0df84a2831938d57d276cab4')
    p = bytes.fromhex('5a09d60797eeb4478aada59db3352a0d')
    assert crypto.k1(n, salt, p) == expected


def test_k2():
    expected_result = bytes.fromhex('7f9f589181a0f50de73c8070c7a6d27f464c715'
                                    'bd4a64b938f99b453351653124f')
    expected_nid = bytes.fromhex('7f')
    expected_encryption_key = bytes.fromhex('9f589181a0f50de73c8070c7a6d27f46')
    expected_privacy_key = bytes.fromhex('4c715bd4a64b938f99b453351653124f')
    n = bytes.fromhex('f7a2a44f8e8a8029064f173ddc1e2b00')
    p = bytes.fromhex('00')

    result = crypto.k2(n, p)
    nid = result[0:1]
    encryption_key = result[1:17]
    privacy_key = result[17:]

    assert result == expected_result
    assert nid == expected_nid
    assert encryption_key == expected_encryption_key
    assert privacy_key == expected_privacy_key


def test_k3():
    expected_network_id = bytes.fromhex('ff046958233db014')
    n = bytes.fromhex('f7a2a44f8e8a8029064f173ddc1e2b00')

    network_id = crypto.k3(n)

    assert network_id == expected_network_id


def test_k4():
    expected_aid = bytes.fromhex('38')
    n = bytes.fromhex('3216d1509884b533248541792b877f98')

    aid = crypto.k4(n)

    assert aid == expected_aid


def test_e_encrypt():
    expected = bytes.fromhex('6ca487507564')
    privacy_key = bytes.fromhex('8b84eedec100067d670971dd2aa700cf')
    plaintext = bytes.fromhex('000000000012345678b5e5bfdacbaf6c')

    assert len(privacy_key) == 16
    assert len(plaintext) == 16
    assert crypto.e(privacy_key, plaintext) == expected


def xor(a, b):
    c = b''
    for x in range(len(a)):
        c += int(a[x] ^ b[x]).to_bytes(1, 'big')
    return c


def test_xor():
    expected = bytes.fromhex('eca487516765')
    a = bytes.fromhex('6ca487507564')
    b = bytes.fromhex('800000011201')

    assert xor(a, b) == expected


def test_e_decrypt():
    privacy_random = bytes.fromhex('b5e5bfdacbaf6cb7fb6bff871f035444ce83a670'
                                   'df')[0:7]
    privacy_key = bytes.fromhex('8b84eedec100067d670971dd2aa700cf')
    iv_index = bytes.fromhex('12345678')
    plain_text = b'\x00\x00\x00\x00\x00' + iv_index + privacy_random
    pecb = crypto.e(privacy_key, plain_text)
    obfuscated_data = bytes.fromhex('eca487516765')

    expected_pecb = bytes.fromhex('6ca487507564')
    expected = bytes.fromhex('800000011201')

    assert pecb == expected_pecb
    assert xor(obfuscated_data, pecb) == expected


def test_aes_ccm_encrypt():
    dst = bytes.fromhex('fffd')
    transport_pdu = bytes.fromhex('034b50057e400000010000')
    network_nonce = bytes.fromhex('00800000011201000012345678')
    encryption_key = bytes.fromhex('0953fa93e7caac9638f58820220a398e')

    expected_result = bytes.fromhex('b5e5bfdacbaf6cb7fb6bff871f')
    result = crypto.aes_ccm(encryption_key, network_nonce, dst +
                            transport_pdu, b'')
    assert result == expected_result


def test_aes_ccm_decrypt():
    encrypted_pdu = bytes.fromhex('b5e5bfdacbaf6cb7fb6bff871f')
    network_nonce = bytes.fromhex('00800000011201000012345678')
    encryption_key = bytes.fromhex('0953fa93e7caac9638f58820220a398e')

    expected_result = bytes.fromhex('fffd034b50057e400000010000')
    result = crypto.aes_ccm(encryption_key, network_nonce, encrypted_pdu, b'')
    assert result == expected_result


def test_aes_ccm_mic_check():
    '''Message #7'''
    encrypted_pdu = bytes.fromhex('0d0d730f94d7f3509d')
    network_nonce = bytes.fromhex('008b0148352345000012345678')
    encryption_key = bytes.fromhex('0953fa93e7caac9638f58820220a398e')
    mic = bytes.fromhex('f987bb417eb7c05f')

    expected_result = bytes.fromhex('000300a6ac00000002')
    result, check = crypto.aes_ccm_decrypt(encryption_key, network_nonce,
                                           encrypted_pdu, mic)
    assert result == expected_result
    assert check is True

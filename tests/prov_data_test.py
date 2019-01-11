from core.prov_data import ProvData

def test_save_load():
    data = ProvData(b'prov_public_key_x', b'prov_public_key_y', b'dev_public_key_x', b'dev_public_key_y', b'prov_priv_key',
                    b'random_provisioner', b'random_device', b'auth_value', b'invite_pdu', b'capabilities_pdu', b'start_pdu',
                    b'network_key', b'key_index', b'flags', b'iv_index', b'\x00\x01\x02\x03')
    data.save('test_prov_data.json')

    load_data = ProvData.load('test_prov_data.json')

    assert load_data.prov_public_key_x == b'prov_public_key_x'
    assert load_data.prov_public_key_y == b'prov_public_key_y'
    assert load_data.dev_public_key_x == b'dev_public_key_x'
    assert load_data.dev_public_key_y == b'dev_public_key_y'
    assert load_data.prov_priv_key == b'prov_priv_key'
    assert load_data.random_provisioner == b'random_provisioner'
    assert load_data.auth_value == b'auth_value'
    assert load_data.invite_pdu == b'invite_pdu'
    assert load_data.capabilities_pdu == b'capabilities_pdu'
    assert load_data.start_pdu == b'start_pdu'
    assert load_data.network_key == b'network_key'
    assert load_data.key_index == b'key_index'
    assert load_data.flags == b'flags'
    assert load_data.iv_index == b'iv_index'
    assert load_data.unicast_address == b'\x00\x01\x02\x03'

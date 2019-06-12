from bluebees.common.file import file_helper
from bluebees.client.application.application_data import ApplicationData
from bluebees.client.data_paths import base_dir, app_dir
from Crypto.Random import get_random_bytes
import pathlib


def test_application_data():
    name = 'test_app'
    key = get_random_bytes(16)
    key_index = get_random_bytes(2)
    network = f'test_net'
    num_nodes = 10

    nodes = []
    for x in range(num_nodes):
        nodes.append(f'test_node{x}')

    data = ApplicationData(name=name, key=key, key_index=key_index,
                           network=network, nodes=nodes)

    assert file_helper.file_exist(base_dir + app_dir + name + '.yml') is \
        False

    data.save()

    assert file_helper.file_exist(base_dir + app_dir + name + '.yml') is \
        True

    r_data = ApplicationData.load(base_dir + app_dir + name + '.yml')

    assert data == r_data


def test_cleanup():
    pathlib.Path(base_dir + app_dir + 'test_app.yml').unlink()

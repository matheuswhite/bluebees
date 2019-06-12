from bluebees.common.file import file_helper
from bluebees.client.node.node_data import NodeData
from bluebees.client.data_paths import base_dir, node_dir
from Crypto.Random import get_random_bytes
import pathlib


def test_application_data():
    name = 'test_node'
    addr = get_random_bytes(2)
    devkey = get_random_bytes(16)
    device_uuid = get_random_bytes(16)
    network = f'test_net'
    num_apps = 10

    apps = []
    for x in range(num_apps):
        apps.append(f'test_app{x}')

    data = NodeData(name=name, addr=addr, network=network,
                    device_uuid=device_uuid, devkey=devkey, apps=apps)

    assert file_helper.file_exist(base_dir + node_dir + name + '.yml') is \
        False

    data.save()

    assert file_helper.file_exist(base_dir + node_dir + name + '.yml') is \
        True

    r_data = NodeData.load(base_dir + node_dir + name + '.yml')

    assert data == r_data


def test_cleanup():
    pathlib.Path(base_dir + node_dir + 'test_node.yml').unlink()

from bluebees.common.file import file_helper
import pathlib


def test_file_exist():
    assert file_helper.file_exist('non_exist_file.yml') is False


def test_load():
    assert file_helper.file_exist('load_file.yml') is False

    content = file_helper.load('load_file.yml', default_content={
        'val_int': 95,
        'val_str': 'october',
        'val_bytes': b'\x24',
        'val_bool': True
    })

    assert file_helper.file_exist('load_file.yml') is True
    assert content['val_int'] == 95
    assert content['val_str'] == 'october'
    assert content['val_bytes'] == b'\x24'
    assert content['val_bool'] is True

    content = file_helper.load('load_file.yml', default_content={})

    assert content['val_int'] == 95
    assert content['val_str'] == 'october'
    assert content['val_bytes'] == b'\x24'
    assert content['val_bool'] is True


def test_write_read():
    content = {
        'val_int': 95,
        'val_str': 'october',
        'val_bytes': b'\x24',
        'val_bool': True
    }

    assert file_helper.file_exist('write_read_file.yml') is False

    file_helper.write('write_read_file.yml', content)

    assert file_helper.file_exist('write_read_file.yml') is True

    r_content = file_helper.read('write_read_file.yml')

    assert r_content['val_int'] == 95
    assert r_content['val_str'] == 'october'
    assert r_content['val_bytes'] == b'\x24'
    assert r_content['val_bool'] is True


def test_dir_exist():
    empty_content = {}
    dir_path = 'test_dir/'

    assert file_helper.dir_exist(dir_path) is False

    file_helper.write(dir_path + 'empty_file.yml', empty_content)

    assert file_helper.dir_exist(dir_path) is True


def test_list_files():
    base_content = {
        'val_int': 1,
        'val_str': 'str',
        'val_bytes': b'\x00',
        'val_bool': True
    }
    base_dir = 'list_dir/'
    num_files = 100

    all_contents = {}
    for x in range(num_files):
        base_content['val_int'] += 1
        base_content['val_str'] += str(x)
        base_content['val_bytes'] += x.to_bytes(1, 'big')
        base_content['val_bool'] = not base_content['val_bool']

        all_contents[f'file_{x}.yml'] = dict(base_content)

    for x in range(num_files):
        file_name = f'file_{x}.yml'
        file_helper.write(base_dir + file_name, all_contents[file_name])

    filenames = file_helper.list_files(base_dir)

    for x in range(num_files):
        assert file_helper.read(base_dir + filenames[x]) == \
            all_contents[filenames[x]]


def test_cleanup():
    def delete_folder(pth):
        for sub in pth.iterdir():
            if sub.is_dir():
                delete_folder(sub)
            else:
                sub.unlink()
        pth.rmdir()

    delete_folder(pathlib.Path('list_dir/'))
    delete_folder(pathlib.Path('test_dir/'))
    pathlib.Path('load_file.yml').unlink()
    pathlib.Path('write_read_file.yml').unlink()

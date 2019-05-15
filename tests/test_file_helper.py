from common.file import file_helper


def test_file_exist():
    assert file_helper.file_exist('non_exist_file.yml') == False

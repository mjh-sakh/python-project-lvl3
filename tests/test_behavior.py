import logging
import os
import tempfile
from pathlib import Path
from typing import TextIO

import pytest

from page_loader import download
from page_loader.downloader import SYSTEM_EXIT_CODES

PROJECT_FOLDER = os.getcwd()
TEST_FOLDER = "tests"
FIXTURES_FOLDER = "fixtures"


def locate(file_name):
    file_path = os.path.join(PROJECT_FOLDER, TEST_FOLDER, FIXTURES_FOLDER, file_name)
    return file_path


def check_if_same(file1: TextIO, file2: TextIO):
    lines1 = file1.readlines()
    lines2 = file2.readlines()
    if len(lines1) != len(lines2):
        return False
    for line1, line2 in zip(lines1, lines2):
        if line1 != line2:
            return False
    return True


@pytest.fixture
def temp_folder():
    with tempfile.TemporaryDirectory() as temp_folder:
        os.chdir(temp_folder)
        yield temp_folder
        os.chdir(PROJECT_FOLDER)


@pytest.mark.parametrize("page_url, expected_file", [
    ("https://sheldonbrown.com/harris/bikes.html", "sheldonbrown-com-harris-bikes.html"),
])
def test_download(temp_folder, page_url, expected_file):
    file_path = download(page_url, temp_folder)
    assert os.path.isfile(file_path)
    folder_path, file_name = os.path.split(file_path)
    assert Path(folder_path).resolve() == Path(temp_folder).resolve()
    assert file_name == expected_file
    # with open(file_path) as file1:
    #     with open(locate(expected_file)) as file2:
    #         assert check_if_same(file1, file2)


# @pytest.mark.parametrize("page_url, sub_folder", [
#     ("https://sheldonbrown.com/harris/bikes.html", "test"),
# ])
# def test_download_creates_folder(temp_folder, sub_folder, page_url):
#     save_folder = os.path.join(temp_folder, sub_folder)
#     file_path = download(page_url, save_folder)
#     assert os.path.isdir(save_folder)


@pytest.mark.parametrize("page_url", [
    ("https://sheldonbrown.com/harris/bikes.html"),
])
def test_download_defaults_to_cwd(temp_folder, page_url):
    file_path = download(page_url)
    folder_path = os.path.dirname(file_path)
    assert Path(folder_path).resolve() == Path(temp_folder).resolve()


@pytest.mark.parametrize("page_url, core_name, expected_names", [
    ("https://sheldonbrown.com/harris/bikes.html", "sheldonbrown-com-harris-bikes",
     "sheldonbrown-com-harris-bikes-files.txt"),  # absolute links
    ("http://hpmor.com", "hpmor-com", "hpmor-com-files.txt"),  # relative links
])
def test_download_saves_imgs(temp_folder, page_url, core_name, expected_names, caplog):
    # caplog.set_level(logging.DEBUG)
    subfolder = 'subfolder'
    os.mkdir(subfolder)
    file_path = download(page_url, subfolder)
    files_folder_name = f'{core_name}_files'
    full_path = os.path.join(subfolder, files_folder_name)
    assert os.path.isdir(full_path)
    saved_names_list = os.listdir(full_path)
    with open(locate(expected_names)) as f:
        expected_names_list = [line.rstrip() for line in f]
    assert sorted(saved_names_list) == sorted(expected_names_list)


@pytest.mark.parametrize("url, folder, expected_ex_type, expected_ex_args", [
    ('abracadabra', None, SystemExit, (SYSTEM_EXIT_CODES['connection_bad_url'],)),
    ('ya.ru/abracadabra', None, SystemExit, (SYSTEM_EXIT_CODES['connection_bad_response'],)),
    ('httppp://ya.ru/abracadabra', None, SystemExit, (SYSTEM_EXIT_CODES['connection_other'],)),
    ('http://hexlet.io', 'test', SystemExit, (SYSTEM_EXIT_CODES['file_not_found'],)),
])
def test_download_exit_codes(temp_folder, url, folder, expected_ex_type, expected_ex_args, caplog):
    caplog.set_level(logging.DEBUG)
    with pytest.raises(expected_ex_type) as ex_info:
        download(url, folder)
    assert ex_info.value.args == expected_ex_args


@pytest.mark.parametrize("url, folder, expected_log_message", [
    ('abracadabra', None, 'Invalid url'),
    ('httppp://ya.ru/abracadabra', None, 'Some other error arose'),
    ('ya.ru', None, 'Looks that schema is missed'),
    ('http://ya.ru/abracadabra', None, 'Was not able to load page. Aborted.'),
    ('http://hexlet.io', 'test', "Folder doesn't exist:"),
])
def test_download_writes_log(temp_folder, url, folder, expected_log_message, caplog):
    caplog.set_level(logging.DEBUG)
    try:
        download(url, folder)
    except BaseException:
        pass
    finally:
        assert expected_log_message in caplog.text

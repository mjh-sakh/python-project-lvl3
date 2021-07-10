import logging
import os
import tempfile
from pathlib import Path

import pytest
from bs4 import BeautifulSoup as bs
from requests import exceptions
from requests_mock import ANY as mock_ANY

from page_loader import download
from page_loader.downloader import SYSTEM_EXIT_CODES

PROJECT_FOLDER = os.getcwd()
TEST_FOLDER = "tests"
FIXTURES_FOLDER = "fixtures"


def locate(file_name):
    file_path = os.path.join(PROJECT_FOLDER, TEST_FOLDER, FIXTURES_FOLDER, file_name)
    return file_path


def read_text(file: str):
    text: str
    with open(file, encoding='utf-8') as f:
        text = f.read()
    return text


@pytest.fixture
def temp_folder():
    with tempfile.TemporaryDirectory() as temp_folder:
        os.chdir(temp_folder)
        yield temp_folder
        os.chdir(PROJECT_FOLDER)


@pytest.mark.parametrize("page_url, expected_file", [
    ("https://sheldonbrown.com/harris/bikes.html", "sheldonbrown-com-harris-bikes.html"),
])
def test_download(temp_folder, page_url, expected_file, requests_mock):
    requests_mock.get(page_url, text=read_text(locate(expected_file)))
    file_path = download(page_url, temp_folder)
    assert os.path.isfile(file_path)
    folder_path, file_name = os.path.split(file_path)
    assert Path(folder_path).resolve() == Path(temp_folder).resolve()
    assert file_name == expected_file
    assert bs(read_text(file_path)).prettify() == bs(read_text(locate(expected_file))).prettify()


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
def test_download_defaults_to_cwd(temp_folder, page_url, requests_mock):
    requests_mock.get(page_url, text="test")
    file_path = download(page_url)
    folder_path = os.path.dirname(file_path)
    assert Path(folder_path).resolve() == Path(temp_folder).resolve()


@pytest.mark.parametrize("page_url, core_name, expected_names", [
    # ("https://sheldonbrown.com/harris/bikes.html", "sheldonbrown-com-harris-bikes", "sheldonbrown-com-harris-bikes-files.txt"),  # absolute links
    # ("http://hpmor.com", "hpmor-com", "hpmor-com-files.txt"),  # relative links
    ('http://hexlet.io/courses', 'hexlet-io-courses', 'hexlet-io-courses-files.txt')
])
def test_download_saves_imgs(temp_folder, page_url, core_name, expected_names, caplog, requests_mock):
    requests_mock.get(url=mock_ANY, text="test")  # for src
    requests_mock.get(page_url, text=read_text(locate(f'original_{core_name}.html')))  # for page
    os.mkdir('level1')
    os.mkdir('level1//level2')
    subfolder = os.path.join('level1', 'level2')
    file_path = download(page_url, subfolder)
    files_folder_name = f'{core_name}_files'
    full_path = os.path.join(subfolder, files_folder_name)
    assert os.path.isdir(full_path)
    saved_names_list = os.listdir(full_path)
    with open(locate(expected_names)) as f:
        expected_names_list = [line.rstrip() for line in f]
    assert sorted(saved_names_list) == sorted(expected_names_list)
    assert bs(read_text(file_path)).prettify() == bs(read_text(locate(f'saved_{core_name}.html'))).prettify()


@pytest.mark.parametrize("url, folder, expected_ex_type, expected_sys_exit_code, mock_kwargs", [
    ('abracadabra', None, ConnectionError, SYSTEM_EXIT_CODES['connection_bad_url'], {'url': 'http://abracadabra/', 'exc': exceptions.ConnectionError}),
    ('ya.ru/abracadabra', None, ConnectionError, SYSTEM_EXIT_CODES['connection_bad_response'], {'url': 'http://ya.ru/abracadabra', 'status_code': 404}),
    ('httppp://ya.ru/abracadabra', None, ConnectionError, SYSTEM_EXIT_CODES['connection_other'], {'url': 'httppp://ya.ru/abracadabra', 'exc': exceptions.InvalidSchema}),
    ('http://hexlet.io', 'test', FileNotFoundError, SYSTEM_EXIT_CODES['file_not_found'], {'url': 'http://hexlet.io', 'text': 'test'}),
])
def test_download_exit_codes(temp_folder, url, folder, expected_ex_type, expected_sys_exit_code, mock_kwargs, caplog, requests_mock):
    caplog.set_level(logging.DEBUG)
    requests_mock.get(**mock_kwargs)
    with pytest.raises(expected_ex_type) as ex_info:
        download(url, folder)
    assert ex_info.value.args[-1] == expected_sys_exit_code


@pytest.mark.parametrize("url, folder, expected_log_message, mock_kwargs", [
    ('ya.ru', None, 'Looks that schema is missed', {'url': 'http://ya.ru', 'text': 'test'}),
    ('http://hexlet.io', 'test', "Folder doesn't exist:", {'url': 'http://hexlet.io', 'text': 'test'}),
    ('http://ya.ru/abracadabra', None, 'Was not able to load page. Aborted.', {'url': 'http://ya.ru/abracadabra', 'status_code': 404}),
    ('httppp://ya.ru/abracadabra', None, 'Some other error arose', {'url': 'httppp://ya.ru/abracadabra', 'exc': exceptions.InvalidSchema}),
    ('abracadabra', None, 'Invalid url', {'url': 'http://abracadabra/', 'exc': exceptions.ConnectionError}),
    ('ya.ru', None, 'Some other error arose', {'url': 'http://ya.ru', 'exc': exceptions.Timeout}),
])
def test_download_writes_log(temp_folder, url, folder, expected_log_message, mock_kwargs, caplog, requests_mock):
    requests_mock.get(**mock_kwargs)
    caplog.set_level(logging.DEBUG)
    try:
        download(url, folder)
    except OSError:
        pass
    finally:
        assert expected_log_message in caplog.text

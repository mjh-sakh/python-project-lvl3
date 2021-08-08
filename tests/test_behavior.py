import logging
import os
import random
import tempfile
import subprocess
from pathlib import Path

import pytest
import requests
from bs4 import BeautifulSoup as bs
from requests import exceptions
from requests_mock import ANY as mock_ANY

from page_loader import download, SYSTEM_EXIT_CODES
from page_loader.downloader import make_name

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


def mock_content(run_id: int):
    """
    Create dynamic content for mocked downloaded file.

    Content is simply a string with downloaded file name, but with random number
    that is not known to application code being added.
    First ensures that content is unique for each file.
    Second ensures that download function cannot generate content in the same way.

    Args:
         run_id: random number for each test run
    """
    def make_content(request: requests.Request, _):
        return f'{make_name(request.url)}-{run_id}'
    return make_content


@pytest.fixture
def temp_folder():
    with tempfile.TemporaryDirectory() as temp_folder:
        os.chdir(temp_folder)
        yield temp_folder
        os.chdir(PROJECT_FOLDER)


@pytest.fixture(scope='session')
def build_project():
    subprocess.run(['make', 'build'])
    subprocess.run(['make', 'package-install'])


@pytest.mark.parametrize("page_url, expected_file", [
    ("https://sheldonbrown.com/harris/bikes.html", "sheldonbrown-com-harris-bikes.html"),
])
def test_download(requests_mock, temp_folder, page_url, expected_file):
    requests_mock.get(page_url, text=read_text(locate(expected_file)))
    file_path = download(page_url, temp_folder)
    assert os.path.isfile(file_path)
    folder_path, file_name = os.path.split(file_path)
    assert Path(folder_path).resolve() == Path(temp_folder).resolve()
    assert file_name == expected_file
    assert bs(read_text(file_path), features="html.parser").prettify() == bs(read_text(locate(expected_file)), features="html.parser").prettify()


@pytest.mark.parametrize("page_url", [
    "https://sheldonbrown.com/harris/bikes.html",
])
def test_download_defaults_to_cwd(requests_mock, temp_folder, page_url):
    requests_mock.get(page_url, text="test")
    file_path = download(page_url)
    folder_path = os.path.dirname(file_path)
    assert Path(folder_path).resolve() == Path(temp_folder).resolve()


@pytest.mark.parametrize("page_url, core_name, expected_names", [
    ('http://hexlet.io/courses', 'hexlet-io-courses', 'hexlet-io-courses-files.txt'),
    ('http://test.ru/foo/bar.html', 'test-ru-foo-bar', 'test-ru-foo-bar-files.txt'),
])
def test_download_saves_imgs(caplog, requests_mock,
                             temp_folder,
                             page_url, core_name, expected_names):
    caplog.set_level(logging.DEBUG)
    test_run_id = random.randint(0, 10_000)
    requests_mock.get(url=mock_ANY, text=mock_content(test_run_id))  # for src content
    requests_mock.get(page_url, text=read_text(locate(f'original_{core_name}.html')))  # for page
    os.mkdir('level1')  # creating subfolders inside temp_folder to ensure proper behavior when far away from cwd
    os.mkdir('level1//level2')
    subfolder = os.path.join('level1', 'level2')
    file_path = download(page_url, subfolder)
    files_folder_name = f'{core_name}_files'
    full_path = os.path.join(subfolder, files_folder_name)
    assert os.path.isdir(full_path)
    assert bs(read_text(file_path), features="html.parser").prettify() == bs(read_text(locate(f'saved_{core_name}.html')), features="html.parser").prettify()
    saved_names_list = os.listdir(full_path)
    with open(locate(expected_names)) as f:
        expected_names_list = [line.rstrip() for line in f]
    assert sorted(saved_names_list) == sorted(expected_names_list)
    for name in expected_names_list:
        # assert os.path.isfile(os.path.join(full_path, name))
        assert read_text(os.path.join(full_path, name)) == f'{name}-{test_run_id}'


@pytest.mark.parametrize("url, folder, expected_ex_type, expected_sys_exit_code, mock_kwargs", [
    ('abracadabra', None, ConnectionError, SYSTEM_EXIT_CODES['connection_err'], {'url': 'http://abracadabra/', 'exc': exceptions.ConnectionError}),
    ('ya.ru/abracadabra', None, ConnectionError, SYSTEM_EXIT_CODES['connection_err'], {'url': 'http://ya.ru/abracadabra', 'status_code': 404}),
    ('httppp://ya.ru/abracadabra', None, ConnectionError, SYSTEM_EXIT_CODES['connection_err'], {'url': 'httppp://ya.ru/abracadabra', 'exc': exceptions.InvalidSchema}),
    ('http://hexlet.io', 'test', FileNotFoundError, SYSTEM_EXIT_CODES['file_sys_err'], {'url': 'http://hexlet.io', 'text': 'test'}),
])
def test_download_raises_and_exits(caplog, requests_mock,
                                   build_project, temp_folder,
                                   url, folder, expected_ex_type, expected_sys_exit_code, mock_kwargs):
    caplog.set_level(logging.DEBUG)
    requests_mock.get(**mock_kwargs)
    with pytest.raises(expected_ex_type):
        download(url, folder)
    if folder is None:
        os.mkdir('tmp')
    complete_run = subprocess.run(['page-loader', '-o', folder or 'tmp', url])
    assert complete_run.returncode == expected_sys_exit_code


@pytest.mark.parametrize("url, folder, expected_log_message, mock_kwargs", [
    ('ya.ru', None, 'Looks that schema is missed', {'url': 'http://ya.ru', 'text': 'test'}),
    ('http://hexlet.io', 'test', "Folder doesn't exist:", {'url': 'http://hexlet.io', 'text': 'test'}),
    ('http://ya.ru/abracadabra', None, 'Was not able to load page. Aborted.', {'url': 'http://ya.ru/abracadabra', 'status_code': 404}),
    ('httppp://ya.ru/abracadabra', None, 'Some other error arose', {'url': 'httppp://ya.ru/abracadabra', 'exc': exceptions.InvalidSchema}),
    ('abracadabra', None, 'Invalid url', {'url': 'http://abracadabra/', 'exc': exceptions.ConnectionError}),
    ('ya.ru', None, 'Some other error arose', {'url': 'http://ya.ru', 'exc': exceptions.Timeout}),
])
def test_download_writes_log(caplog, requests_mock,
                             temp_folder,
                             url, folder, expected_log_message, mock_kwargs):
    requests_mock.get(**mock_kwargs)
    caplog.set_level(logging.DEBUG)
    try:
        download(url, folder)
    except OSError:
        pass
    finally:
        assert expected_log_message in caplog.text

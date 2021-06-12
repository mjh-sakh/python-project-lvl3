import os

import pytest

from tests.test_behavior import temp_folder
from page_loader.downloader import is_absolute, save_file


@pytest.mark.parametrize("tested_link, result", [
    ('/relative/link.com', False),
    ('http://www.ya.ru/', True),
    ('https://hexlet.io', True),
])
def test_is_absolute(tested_link, result):
    assert is_absolute(tested_link) == result


@pytest.mark.parametrize("page_url, file_url", [
    ("http://hpmor.com", "/snap-cover-small.jpg"),
    ("doesnt matter", "http://www.hpmor.com/snap-cover-small.jpg")
])
def test_save_file(temp_folder, page_url, file_url):
    save_file(file_url, page_url, 'img')
    assert len(os.listdir('img')) == 1

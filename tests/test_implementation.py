import os

import pytest

from tests.test_behavior import temp_folder
from page_loader.downloader import is_absolute, save_file, make_name


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

@pytest.mark.parametrize("raw, extension, result", [
    ('http://site.com', False, 'site-com'),
    ('http://site.com', True, 'site-com'),
    ('http://site.com', '.text', 'site-com.text'),
    ('http://web.site.ru/here', False, 'web-site-ru-here'),
    ('http://web.site.ru/here', True, 'web-site-ru-here'),
    ('http://web.site.ru/here', '.text', 'web-site-ru-here.text'),
    ('http://web.site.ru/here.ext', False, 'web-site-ru-here'),
    ('http://web.site.ru/here.ext', True, 'web-site-ru-here.ext'),
    ('http://web.site.ru/here.ext', '.text', 'web-site-ru-here.text'),
    ('site', False, 'site'),
    ('site', True, 'site'),
    ('site', '.text', 'site.text'),
    ('site/one.ext', False, 'site-one'),
    ('site/one.ext', True, 'site-one.ext'),
    ('site/one.ext', '.text', 'site-one.text'),
    ('abc123_-!zzz', False, 'abc123---zzz'),
])
def test_make_name(raw, extension, result):
    assert make_name(raw, extension) == result

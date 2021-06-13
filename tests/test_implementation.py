import pytest

from page_loader.downloader import is_absolute, make_name, is_local


@pytest.mark.parametrize("tested_link, result", [
    ('/relative/link.com', False),
    ('http://www.ya.ru/', True),
    ('https://hexlet.io', True),
])
def test_is_absolute(tested_link, result):
    assert is_absolute(tested_link) == result


@pytest.mark.parametrize("raw, extension, result", [
    ('http://site.com', False, 'site-com'),
    ('http://site.com', True, 'site-com.html'),
    ('http://site.com', '.text', 'site-com.text'),
    ('http://web.site.ru/here', False, 'web-site-ru-here'),
    ('http://web.site.ru/here', True, 'web-site-ru-here.html'),
    ('http://web.site.ru/here', '.text', 'web-site-ru-here.text'),
    ('http://web.site.ru/here.ext', False, 'web-site-ru-here'),
    ('http://web.site.ru/here.ext', True, 'web-site-ru-here.ext'),
    ('http://web.site.ru/here.ext', '.text', 'web-site-ru-here.text'),
    ('site', False, 'site'),
    ('site', True, 'site.html'),
    ('site', '.text', 'site.text'),
    ('site/one.ext', False, 'site-one'),
    ('site/one.ext', True, 'site-one.ext'),
    ('site/one.ext', '.text', 'site-one.text'),
    ('abc123_-!zzz', False, 'abc123---zzz'),
])
def test_make_name(raw, extension, result):
    assert make_name(raw, extension) == result


def test_is_local():
    assert is_local('http://www.site.ru/file.ext', 'http://site.ru') is True

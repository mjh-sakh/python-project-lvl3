# flake8: noqa
__version__ = "0.1.0"

from types import MappingProxyType

SYSTEM_EXIT_CODES = MappingProxyType({
    'connection_bad_url': 10,
    'connection_bad_response': 11,
    'connection_other': 19,
    'file_not_found': 20,
    'file_permission': 21,
})

from page_loader.downloader import download

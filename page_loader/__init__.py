# flake8: noqa
__version__ = "0.1.0"

from types import MappingProxyType

SYSTEM_EXIT_CODES = MappingProxyType({
    'connection_err': 10,
    'file_sys_err': 11,
    'other': 2,
})

from page_loader.downloader import download

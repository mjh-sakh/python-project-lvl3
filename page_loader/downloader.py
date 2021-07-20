"""Main module to save page."""

import logging
import os
import re
from types import MappingProxyType
from typing import Union, Optional

import requests
from bs4 import BeautifulSoup  # type: ignore
from progress.bar import Bar  # type: ignore
from urllib.parse import urlparse

from page_loader.url_utilities import is_local, convert_to_absolute, check_url_and_get_code

DOWNLOAD_OBJECTS = MappingProxyType({
    'img': ('src', True),
    'link': ('href', False),
    'script': ('src', False),
})


def count_files_to_download(soup: BeautifulSoup, url: str) -> int:  # noqa: WPS210
    """
    Count number of files to be downloaded.

    Args:
        soup: BeautifulSoup of the page
        url: home url to check is_local

    Returns:
        Count of files to be downloaded.
    """
    count = 0
    for download_object, (key, always_download) in DOWNLOAD_OBJECTS.items():
        for object_ in soup.find_all(download_object):
            item_link = object_.get(key)
            if item_link and (always_download or is_local(item_link, url)):
                count += 1
    return count


def download(url: str, folder: Optional[str] = None) -> str:  # noqa: C901, WPS210, WPS213, WPS231
    """
    Download page, including images and local content of link and script.

    Page will be saved in the current working directory,
    unless folder is specified.

    Args:
        url: page address, str
        folder: folder, str

    Returns:
        Address of saved page.
    """
    logging.debug(f'Download requested for url: {url}')
    if folder is None:
        folder = os.getcwd()
    check_environment(folder)
    page_code = check_url_and_get_code(url)
    soup = BeautifulSoup(page_code, features='html.parser')
    downloads_folder = make_name(url, '_files')
    progress_bar = Bar('Downloading', max=count_files_to_download(soup, url))
    for download_object, (key, always_download) in DOWNLOAD_OBJECTS.items():
        for object_ in soup.find_all(download_object):
            item_link = object_.get(key)
            if item_link and (always_download or is_local(item_link, url)):
                item_link = convert_to_absolute(item_link, url)
                item_file_name = make_name(item_link)
                try:
                    item_content = download_content(item_link)
                except ConnectionError as ex:  # noqa: WPS440
                    logging.warning(f'Exception raised when saving {item_link}\n\t{ex.args[0]}')
                except Exception:
                    logging.debug('Unknown error:', exc_info=True)
                    logging.warning(f'Exception raised when saving {item_link}')
                else:
                    logging.debug(f'Downloaded object: {object_}\n{url}')
                    save_file(
                        item_content,
                        os.path.join(folder, downloads_folder),
                        item_file_name,
                    )
                    object_[key] = '/'.join((downloads_folder, item_file_name))
                finally:
                    progress_bar.next()  # noqa: B305
    progress_bar.finish()
    return save_file(
        content=soup.prettify(formatter='html5').encode(),
        folder=folder,
        file_name=make_name(url, '.html'),
    )


def check_environment(folder: str) -> None:
    """
    Check that folder and wright access are present.

    Args:
        folder: folder name, str

    Raises:
        FileNotFoundError: specified folder doesn't exist.
        PermissionError: do not have write access.
    """
    if not os.path.exists(folder):
        err_message = f"Folder doesn't exist: {folder}"
        logging.error(err_message)
        raise FileNotFoundError(err_message)
    if not os.access('.', os.W_OK):
        err_message = "Don't have write access."
        logging.error(err_message)
        raise PermissionError(err_message)


def download_content(file_url: str) -> bytes:
    """
    Download content using requests.get.

    Args:
        file_url: file url, str.

    Returns:
        Response content (bytes).

    Raises:
        ConnectionError: if status code is not 200.
    """
    response = requests.get(file_url)
    if response.ok:
        return response.content
    raise ConnectionError(
        f'Error on request. Returned status code: {response.status_code}',
    )


def save_file(content: bytes, folder: str, file_name: str) -> str:  # noqa: WPS110
    """
    Write content to file with *file_name* under *folder*.

    Args:
         content: content to write, bytes
         folder: folder where file should be located, str
         file_name: file name, str

    Returns:
        Path to newly created file.
    """
    if not os.path.exists(folder):
        os.mkdir(folder)
    file_path = os.path.join(folder, file_name)
    with open(file_path, 'wb') as f:  # noqa: WPS111
        f.write(content)
    return file_path


def make_name(  # noqa: WPS210
    url: str,
    set_extension: Union[bool, str] = True,
    default_extension: str = '.html',
) -> str:
    """
    Make file name out of url.

    Name is made by first removing schema
    and then replacing non-letters and non-numbers with '-'.

    Add extension options:
        True: default, keeps original extension
              or adds default if there was no extension
        False: returns name without extension
        str: adds specified extension, replaces existing

    Example: https://example.com/file.jpg
    Coverts to: example-com-file.jpg

    Args:
        url: url, str
        set_extension: see options above, bool or str
        default_extension: str

    Returns:
        Name string.
    """
    url_parts = urlparse(url)
    core_url = url_parts.netloc + url_parts.path
    trimmed_url = core_url.strip('/')
    match = re.search(r'/.+(\.\w+)$', trimmed_url)
    if match:
        ending = match.group(1)
        trimmed_url = trimmed_url[:-len(ending)]
    else:
        ending = default_extension
    transformed_url = re.sub(r'[\W_]', '-', trimmed_url)
    if not set_extension:
        return transformed_url
    if set_extension is True:
        return f'{transformed_url}{ending}'
    return f'{transformed_url}{set_extension}'

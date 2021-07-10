"""Main module to save page."""

import logging
import os
import re
from types import MappingProxyType
from typing import Union, Optional

import requests
from bs4 import BeautifulSoup  # type: ignore
from progress.bar import Bar  # type: ignore

from page_loader.url_utilities import is_local, convert_to_absolute

SYSTEM_EXIT_CODES = MappingProxyType({
    'connection_bad_url': 10,
    'connection_bad_response': 11,
    'connection_other': 19,
    'file_not_found': 20,
    'file_permission': 21,
})

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


# TODO: remove below ignores for final refactor (as well see config.cfg)
def download(url: str, folder: Optional[str] = None) -> str:  # noqa: C901, WPS238, WPS210, WPS213, WPS231
    """
    Download page, including images and local content of link and script.

    Page will be saved in the current working directory,
    unless folder is specified.

    Args:
        url: page address, str
        folder: folder, str

    Returns:
        Address of saved page.

    Raises:
          ConnectionError: cannot get reguested page.
          FileNotFoundError: specified folder doesn't exist.
          PermissionError: do not have write access.
    """
    logging.debug(f'Download requested for url: {url}')
    if folder is None:
        folder = os.getcwd()
    if not os.path.exists(folder):
        err_message = f"Folder doesn't exist: {folder}"
        logging.error(err_message)
        raise FileNotFoundError(err_message, SYSTEM_EXIT_CODES['file_not_found'])
    if not os.access('.', os.W_OK):
        err_message = "Don't have write access."
        logging.error(err_message)
        raise PermissionError(err_message, SYSTEM_EXIT_CODES['file_permission'])
    if not re.search('//', url):
        logging.warning(f'Looks that schema is missed in "{url}", added "http://" and continue.')
        url = f'http://{url}'
    try:
        page = requests.get(url)
    except requests.exceptions.ConnectionError as ex:
        logging.debug(ex)
        err_message = f'Invalid url: {url}. Aborted.'
        logging.error(err_message)
        raise ConnectionError(err_message, SYSTEM_EXIT_CODES['connection_bad_url']) from ex
    except Exception as ex:
        err_message = 'Some other error arose. Aborted.'
        logging.error(err_message, exc_info=True)
        raise ConnectionError('Some other error arose. Aborted.', SYSTEM_EXIT_CODES['connection_other']) from ex
    if not page.ok:
        err_message = f'Was not able to load page. Aborted.\n\tReturned status code is {page.status_code}.'
        logging.error(err_message)
        raise ConnectionError(err_message, SYSTEM_EXIT_CODES['connection_bad_response'])  # noqa: E501
    page_code = page.text
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
                    logging.warning(
                        f'Exception raised when saving {item_link}', exc_info=True,
                    )
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
    file_name = make_name(url, '.html')
    file_path = save_file(soup.prettify(formatter='html5').encode(), os.getcwd(), file_name)
    if working_in_sub_folder_flag:  # TODO: avoid chdir in logic at all
        os.chdir(original_cwd)
    return file_path


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
    scheme = re.match('.+//', url)
    trimmed_url = url[len(scheme[0]):] if scheme else url
    trimmed_url = trimmed_url.strip('/')

    # Regex explanation: two conditions with OR
    # first: (?<=//).+/\S+(\.\w+)$
    #   if there is // in the line,
    #   consider (\.\w+) template only if there is '/' between it and //
    # or second: ^(?:(?!//).)*?(\.\w+)$
    #   if there is no // in the line
    #   take (\.\w+) template at the end of the line
    match = re.search(r'(?<=//).+/\S+(\.\w+)$|^(?:(?!//).)*?(\.\w+)$', url)
    if match:
        group1, group2 = match.groups()
        ending = group1 or group2
        trimmed_url = trimmed_url[:-len(ending)]
    else:
        ending = default_extension
    transformed_url = re.sub(r'[\W_]', '-', trimmed_url)
    if not set_extension:
        return transformed_url
    if set_extension is True:
        return f'{transformed_url}{ending}'
    return f'{transformed_url}{set_extension}'

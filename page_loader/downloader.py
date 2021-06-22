import logging
import os
import re
import sys
from types import MappingProxyType
from typing import Union, Optional
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup  # type: ignore

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


def download(url: str, folder: Optional[str] = None) -> str:
    logging.debug(f'Download requested for url: {url}')
    if folder is None:
        folder = os.getcwd()
    if not os.path.exists(folder):
        err_message = f"Folder doesn't exist: {folder}"
        logging.error(err_message)
        raise FileNotFoundError(err_message, SYSTEM_EXIT_CODES['file_not_found'])
    working_in_sub_folder_flag = False
    if folder is not None:
        os.chdir(folder)
        working_in_sub_folder_flag = True
    if not os.access('.', os.W_OK):
        err_message = "Don't have write access."
        logging.error(err_message)
        raise PermissionError(err_message, SYSTEM_EXIT_CODES['file_permission'])
    if not re.search('//', url):
        logging.warning(f'Looks that schema is missed in "{url}", added "http://" and continue.')  # noqa: E501
        url = f'http://{url}'
    try:
        page = requests.get(url)
    except requests.exceptions.ConnectionError as ex:
        logging.debug(ex)
        err_message = f'Invalid url: {url}. Aborted.'
        logging.error(err_message)
        raise ConnectionError(err_message, SYSTEM_EXIT_CODES['connection_bad_url']) from ex  # noqa: E501
    except Exception as ex:
        err_message = 'Some other error arose. Aborted.'
        logging.error(err_message, exc_info=True)
        raise ConnectionError('Some other error arose. Aborted.', SYSTEM_EXIT_CODES['connection_other']) from ex  # noqa: E501
    if not page.ok:
        err_message = f'Was not able to load page. Aborted.\nReturned status code is {page.status_code}.'  # noqa: E501
        logging.error(err_message)
        raise ConnectionError(err_message, SYSTEM_EXIT_CODES['connection_bad_response'])  # noqa: E501
    page_code = page.text
    soup = BeautifulSoup(page_code, features='html.parser')
    downloads_folder = make_name(url, '_files')
    for download_object, (key, always_download) in DOWNLOAD_OBJECTS.items():
        for object_ in soup.find_all(download_object):
            item_link = object_.get(key)
            if item_link and (always_download or is_local(item_link, url)):
                item_file_name = make_name(item_link)
                try:
                    item_content = download_content(item_link, url)
                except Exception:
                    logging.warning(
                        f'Exception raised when saving {item_link}', exc_info=True,  # noqa: E501
                    )
                else:
                    logging.debug(f'Downloaded object: {object_}\n{url}')
                    object_[key] = save_file(item_content, downloads_folder, item_file_name)  # noqa: E501
    file_name = make_name(url, '.html')
    file_path = save_file(soup.encode(), os.getcwd(), file_name)
    if working_in_sub_folder_flag:
        os.chdir('..')
    return file_path


def is_local(link: str, local_link: str) -> bool:
    parse = urlparse(link)
    if not parse.netloc:
        return True
    parse_local = urlparse(local_link)
    return parse.netloc in {parse_local.netloc, f'www.{parse_local.netloc}'}


def is_absolute(link: str) -> bool:
    return bool(re.search('//', link))


def download_content(file_url: str, page_url: str) -> bytes:
    if is_absolute(file_url):
        absolute_file_url = file_url
    else:
        absolute_file_url = urljoin(page_url, file_url)
    response = requests.get(absolute_file_url)
    if response.ok:
        return response.content
    raise ConnectionError(
        f'Error on request. Returned status code: {response.status_code}',
    )


def save_file(content: bytes, folder: str, file_name: str) -> str:
    if not os.path.exists(folder):
        os.mkdir(folder)
    file_path = os.path.join(folder, file_name)
    with open(file_path, 'wb') as f:  # noqa: WPS111
        f.write(content)
    return file_path


def make_name(
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
              or adds default if there was no
        False: returns name without extension
        str: adds specified extension, replaces existing

    Example: https://example.com/file.jpg
    Coverts to: example-com-file.jpg
    """
    scheme = re.match('.+//', url)
    trimmed_url = url[len(scheme[0]):] if scheme else url
    trimmed_url = trimmed_url[1:] if trimmed_url[0] == '/' else trimmed_url
    trimmed_url = trimmed_url[:-1] if trimmed_url[-1] == '/' else trimmed_url

    # Regex explanation: two conditions with OR
    # first: (?<=//).+/\S+(\.\w+)$
    # if there is // in the line, consider (\.\w+) template only if there is '/' between it and //
    # or second: ^(?:(?!//).)*?(\.\w+)$
    # if there is no // in the line, take (\.\w+) template at the end of the line
    match = re.search(r'(?<=//).+/\S+(\.\w+)$|^(?:(?!//).)*?(\.\w+)$', url)  # noqa: E501
    if match:
        group1, group2 = match.groups()
        ending = group1 if group1 else group2
        trimmed_url = trimmed_url[:-len(ending)]
    else:
        ending = default_extension
    transformed_url = re.sub(r'[\W_]', '-', trimmed_url)
    if not set_extension:
        return transformed_url
    if set_extension is True:
        return f'{transformed_url}{ending}'
    return f'{transformed_url}{set_extension}'

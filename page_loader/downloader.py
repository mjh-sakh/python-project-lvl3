import os
import re
from typing import Union, Optional

import requests
from bs4 import BeautifulSoup  # type: ignore


def download(url: str, folder: Optional[str] = None) -> str:
    if folder is None:
        folder = os.getcwd()
    page = requests.get(url)
    if page.status_code != 200:
        raise Exception(
            f'Error on page request. Page status returned: {page.status_code}',
        )
    if not os.path.isdir(folder):
        os.mkdir(folder)
    file_name = make_name(url, '.html')
    file_path = os.path.join(folder, file_name)
    with open(file_path, 'w') as f:  # noqa: WPS111
        f.write(page.text)
    soup = BeautifulSoup(page.content, features='html.parser')
    img_folder = make_name(url, '_files')
    img_folder = os.path.join(folder, img_folder)
    for img in soup.find_all('img'):
        img_src = img['src']
        save_file(img_src, url, img_folder)
    return file_path


def is_absolute(link: str) -> bool:
    return True if re.search('//', link) else False


def save_file(file_url: str, page_url: str, folder: str) -> None:
    if not os.path.exists(folder):
        os.mkdir(folder)
    if is_absolute(file_url):
        absolute_file_url = file_url
    else:
        absolute_file_url = fr'{page_url}/{file_url}'
    downloaded_file = requests.get(absolute_file_url)
    file_name = make_name(file_url)
    file_path = os.path.join(folder, file_name)
    with open(file_path, 'wb') as f:  # noqa: WPS111
        f.write(downloaded_file.content)


def make_name(url: str, extension: Union[bool, str] = True) -> str:
    """
    Make file name out of url.

    Name is made by first removing schema
    and then replacing non-letters and non-numbers with '-'.

    Add extension options:
        True: default, keeps original extension
        False: returns name without extension
        str: adds specified extension

    Example: https://example.com/file.jpg
    Coverts to: example-com-file.jpg
    """
    scheme = re.findall('.+//', url)[0]
    trimmed_url = url[len(scheme):]
    trimmed_url = trimmed_url[1:] if trimmed_url[0] == '/' else trimmed_url
    trimmed_url = trimmed_url[:-1] if trimmed_url[-1] == '/' else trimmed_url
    ending = re.findall(r'\W\w+$', trimmed_url)[0]
    trimmed_url = trimmed_url[:-len(ending)]
    transformed_url = re.sub(r'\W', '-', trimmed_url)
    if not extension:
        return transformed_url
    if extension is True:
        return f'{transformed_url}{ending}'
    return f'{transformed_url}{extension}'

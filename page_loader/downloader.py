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
    return bool(re.search('//', link))


def save_file(file_url: str, page_url: str, folder: str) -> None:
    if not os.path.exists(folder):
        os.mkdir(folder)
    if is_absolute(file_url):
        absolute_file_url = file_url
    else:
        absolute_file_url = f'{page_url}/{file_url}'
    downloaded_file = requests.get(absolute_file_url)
    file_name = make_name(file_url)
    file_path = os.path.join(folder, file_name)
    with open(file_path, 'wb') as f:  # noqa: WPS111
        f.write(downloaded_file.content)


def make_name(url: str, set_extension: Union[bool, str] = True) -> str:
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
    scheme = re.match('.+//', url)
    trimmed_url = url[len(scheme[0]):] if scheme else url
    trimmed_url = trimmed_url[1:] if trimmed_url[0] == '/' else trimmed_url
    trimmed_url = trimmed_url[:-1] if trimmed_url[-1] == '/' else trimmed_url
    """
    Regex explanation: two conditions with OR
    first: (?<=//).+/\w+(\.\w+)$
    if there // in the line, consider only (\.\w+) template if there is '/' between it and //
    or second: ^(?:(?!//).)*?(\.\w+)$
    if there is no // in the line, take \.\w+ template at the end of the line
    """
    match = re.search(r'(?<=//).+/\w+(\.\w+)$|^(?:(?!//).)*?(\.\w+)$', trimmed_url)
    ending = match[0][0] if match else ''
    trimmed_url = trimmed_url[:-len(ending)]
    transformed_url = re.sub(r'\W', '-', trimmed_url)
    if not set_extension:
        return transformed_url
    if set_extension is True:
        return f'{transformed_url}{ending}'
    return f'{transformed_url}{set_extension}'

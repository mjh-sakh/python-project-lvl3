import os
import re

import requests


def download(url: str, folder: str) -> str:
    page = requests.get(url)
    if page.status_code != 200:
        raise Exception(
            f'Error on page request. Page status returned: {page.status_code}',
        )

    scheme = re.findall('.+//', url)[0]
    trimmed_url = url[len(scheme):]
    trimmed_url = trimmed_url[:-1] if trimmed_url[-1] == '/' else trimmed_url
    ending = re.findall(r'\W\w+$', trimmed_url)[0]
    if ending in ('.htm', '.html'):
        trimmed_url = trimmed_url[:-len(ending)]
    transformed_url = re.sub(r'\W', '-', trimmed_url)
    file_name = f'{transformed_url}.html'
    file_path = os.path.join(folder, file_name)
    with open(file_path, 'w') as f:
        f.write(page.text)
    return file_path

"""Utilities to work with URL."""
import logging
import re
from urllib.parse import urlparse, urljoin

import requests

from page_loader import SYSTEM_EXIT_CODES


def is_local(link: str, local_link: str) -> bool:
    """
    Check if link is local to referred page.

    Args:
        link: link to be checked, str
        local_link: referred local page, str

    Returns:
        True if local, otherwise False
    """
    parse = urlparse(link)
    if not parse.netloc:
        return True
    parse_local = urlparse(local_link)
    return parse.netloc in {parse_local.netloc, f'www.{parse_local.netloc}'}


def is_absolute(link: str) -> bool:
    """
    Check if scheme is present in the link.

    Args:
        link: link to be checked.

    Returns:
        True if scheme is present and therefore absolute.
    """
    return bool(re.search('//', link))


def convert_to_absolute(url: str, page_url: str) -> str:
    """
    Check if link relative and convert it to absolute if it is.

    Args:
        url: url to be converted, str
        page_url: home url as reference to make absolute link, str

    Returns:
        Original link if it was absolute.
        New link with scheme and netlok if it was relative.
    """
    if is_absolute(url):
        absolute_url = url
    else:
        if re.search(r'/\w+\.\w+$', page_url):  # finds .html like ending
            absolute_url = urljoin(page_url, url)
        else:
            absolute_url = urljoin(f'{page_url}/', url)
    return absolute_url


def check_url_and_get_code(url: str) -> str:
    """
    Check url to be valid and return it's content as txt.

    Args:
        url: page url, str

    Returns:
        Page content.

    Raises:
        ConnectionError: page is bad.
    """
    if not re.search('//', url):
        logging.warning(f'Looks that schema is missed in "{url}", added "http://" and continue.')
        url = f'http://{url}'
    try:  # noqa:WPS229 second line is needed for raising HTTPerror
        page = requests.get(url)
        page.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        err_message = f'Was not able to load page. Aborted.\n\tReturned error was: {http_err}.'
        logging.error(err_message)
        raise ConnectionError(err_message, SYSTEM_EXIT_CODES['connection_bad_response'])  # noqa: E501
    except requests.exceptions.ConnectionError as ex:
        logging.debug(ex)
        err_message = f'Invalid url: {url}. Aborted.'
        logging.error(err_message)
        raise ConnectionError(err_message, SYSTEM_EXIT_CODES['connection_bad_url']) from ex
    except Exception as ex:
        err_message = 'Some other error arose. Aborted.'
        logging.debug('Unknown error:', exc_info=True)
        logging.error(err_message, exc_info=False)
        raise ConnectionError('Some other error arose. Aborted.', SYSTEM_EXIT_CODES['connection_other']) from ex
    return page.text

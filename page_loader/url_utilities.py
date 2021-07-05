"""Utilities to work with URL."""

import re
from urllib.parse import urlparse, urljoin


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
        absolute_url = urljoin(page_url, url)
    return absolute_url

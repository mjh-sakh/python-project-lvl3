"""Module to parse arguments when work in CLI."""

import argparse

from page_loader import __version__

DESCRIPTION = """
page_loader -f hexlet http://hexlet.io
"""


def get_parser() -> argparse.ArgumentParser:
    """
    Provide parser to main function.

    Returns:
        argparse ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description='Utility to download web page from internet and save it locally.',  # noqa: E501
        usage=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter,
        prog='page-loader',
    )
    parser.add_argument('url', help='Page address.')
    parser.add_argument(
        '-V', '--version',
        help='Show version number.',
        action='version',
        version=f"{parser.prog}'s version is {__version__}.",
    )
    parser.add_argument('-o', '--output', help='Folder to save file. Default is cwd.')
    return parser

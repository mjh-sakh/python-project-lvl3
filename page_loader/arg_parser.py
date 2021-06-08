import argparse

DESCRIPTION = """
page_loader -f hexlet http://hexlet.io
"""


def get_parser():
    parser = argparse.ArgumentParser(
        description='Utility to download web page from internet and save it locally.',  # noqa: E501
        usage=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument('url', help='Page address.')
    parser.add_argument('-f', '--folder', help='Folder to save file.')
    return parser

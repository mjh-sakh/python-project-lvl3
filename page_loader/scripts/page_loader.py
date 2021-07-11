# flake8: noqa
import sys

from page_loader import download
from page_loader.arg_parser import get_parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    try:
        file_path = download(
            args.url,
            args.output,
        )
    except Exception as ex:
        sys.exit(ex.args[-1])
    print(file_path)


if __name__ == '__main__':
    main()

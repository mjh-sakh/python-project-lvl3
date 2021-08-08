# flake8: noqa
import logging
import sys

from page_loader import download, SYSTEM_EXIT_CODES
from page_loader.arg_parser import get_parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    try:
        file_path = download(
            args.url,
            args.output,
        )
    except ConnectionError:
        sys.exit(SYSTEM_EXIT_CODES['connection_err'])
    except OSError:
        sys.exit(SYSTEM_EXIT_CODES['file_sys_err'])
    except Exception as ex:
        logging.error(f"Unexpected error has happened during handling '{args.url}'.")
        sys.exit(SYSTEM_EXIT_CODES['other'])
    print(file_path)


if __name__ == '__main__':
    main()

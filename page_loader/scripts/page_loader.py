# flake8: noqa

from page_loader import download
from page_loader.arg_parser import get_parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    file_path = download(
        args.url,
        args.folder,
    )
    print(file_path)


if __name__ == '__main__':
    main()

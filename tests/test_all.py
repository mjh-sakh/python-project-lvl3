import os
from pathlib import Path
import tempfile
from typing import TextIO

import pytest

from page_loader import download

TEST_FOLDER = "tests"
FIXTURES_FOLDER = "fixtures"


def locate(file_name):
    file_path = os.path.join(TEST_FOLDER, FIXTURES_FOLDER, file_name)
    return file_path


def check_if_same(file1: TextIO, file2: TextIO):
    lines1 = file1.readlines()
    lines2 = file2.readlines()
    if len(lines1) != len(lines2):
        return False
    for line1, line2 in zip(lines1, lines2):
        if line1 != line2:
            return False
    return True


@pytest.fixture
def temp_folder():
    with tempfile.TemporaryDirectory() as temp_folder:
        yield temp_folder


class TestClassBlackBoxTests:
    @pytest.mark.parametrize("page_address, expected_file", [
        ("https://sheldonbrown.com/harris/bikes.html", "sheldonbrown-com-harris-bikes.html"),
    ])
    def test_download(self, temp_folder, page_address, expected_file):
        file_path = download(page_address, temp_folder)
        assert os.path.isfile(file_path)
        folder_path, file_name = os.path.split(file_path)
        assert folder_path == temp_folder
        assert file_name == expected_file
        # with open(file_path) as file1:
        #     with open(locate(expected_file)) as file2:
        #         assert check_if_same(file1, file2)

    @pytest.mark.parametrize("page_address, sub_folder", [
        ("https://sheldonbrown.com/harris/bikes.html", "test"),
    ])
    def test_download_creates_folder(self, temp_folder, sub_folder, page_address):
        save_folder = os.path.join(temp_folder, sub_folder)
        file_path = download(page_address, save_folder)
        assert os.path.isdir(save_folder)

    @pytest.mark.parametrize("page_address", [
        ("https://sheldonbrown.com/harris/bikes.html"),
    ])
    def test_download_defaults_to_cwd(self, temp_folder, page_address):
        os.chdir(temp_folder)
        file_path = download(page_address)
        folder_path = os.path.dirname(file_path)
        assert Path(folder_path).resolve() == Path(temp_folder).resolve()


class TestClassWhiteBoxTests:
    pass

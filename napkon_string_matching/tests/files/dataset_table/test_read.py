import unittest
from pathlib import Path

from napkon_string_matching.files.dataset_table.read import read
from napkon_string_matching.tests import DISABLE_LOCAL_FILE_TESTS


class TestRead(unittest.TestCase):
    @unittest.skipIf(DISABLE_LOCAL_FILE_TESTS, "local test file needs to be available")
    def test_read(self):
        file = Path("input/hap_test.xlsx")
        result = read(file)
        self.assertIsNotNone(result)

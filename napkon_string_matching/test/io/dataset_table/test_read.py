import unittest
from pathlib import Path

from napkon_string_matching.io.dataset_table.read import read


class TestRead(unittest.TestCase):
    @unittest.skip("test file needs to be available")
    def test_read(self):
        file = Path("hap_test.xlsx")
        result = read(file)
        self.assertIsNotNone(result)

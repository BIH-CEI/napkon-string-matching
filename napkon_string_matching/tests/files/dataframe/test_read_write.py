import unittest
from pathlib import Path

import pandas as pd
from napkon_string_matching.constants import DATA_COLUMN_IDENTIFIER
from napkon_string_matching.files.dataframe import read, write
from pandas.testing import assert_frame_equal


class TestReadWrite(unittest.TestCase):
    def test_read_write(self):
        df = pd.DataFrame(
            {
                "Identifier": ["1", "2", "3"],
                "words": ["one", "two", "three"],
                "arrays": [[1, "one"], [2, "two"], [3, "three"]],
            },
        ).set_index(DATA_COLUMN_IDENTIFIER)

        file = Path("test_" + __name__ + ".json")
        if file.exists():
            file.unlink()

        write(file, df)
        result = read(file)

        file.unlink()

        assert_frame_equal(df, result)

import unittest

import pandas as pd
from napkon_string_matching.constants import (
    DATA_COLUMN_CATEGORIES,
    DATA_COLUMN_FILE,
    DATA_COLUMN_ITEM,
    DATA_COLUMN_OPTIONS,
    DATA_COLUMN_QUESTION,
    DATA_COLUMN_SHEET,
)
from napkon_string_matching.files.dataset_table import (
    COLUMN_DB_COLUMN,
    COLUMN_FILE,
    COLUMN_ITEM,
    COLUMN_OPTIONS,
    COLUMN_QUESTION,
    COLUMN_SHEET_NAME,
    COLUMN_TYPE,
    TYPE_HEADER,
    SheetParser,
)


class TestSheetParser(unittest.TestCase):
    def test_parse_row(self):
        parser = SheetParser()

        row_dicts = [
            {
                COLUMN_TYPE: TYPE_HEADER,
                COLUMN_QUESTION: "Header",
                COLUMN_ITEM: None,
                COLUMN_DB_COLUMN: None,
                COLUMN_SHEET_NAME: "Test Sheet",
                COLUMN_FILE: "Testfile",
            },
            {
                COLUMN_TYPE: "other",
                COLUMN_QUESTION: "Subheader",
                COLUMN_ITEM: None,
                COLUMN_DB_COLUMN: None,
                COLUMN_SHEET_NAME: "Test Sheet",
                COLUMN_FILE: "Testfile",
            },
            {
                COLUMN_TYPE: "QuestionGroup",
                COLUMN_QUESTION: "This is a question",
                COLUMN_ITEM: "This is an item with options",
                COLUMN_OPTIONS: "Option A;Option B",
                COLUMN_DB_COLUMN: "foo column",
                COLUMN_SHEET_NAME: "Test Sheet",
                COLUMN_FILE: "Testfile",
            },
            {
                COLUMN_ITEM: "Another item for same question",
                COLUMN_DB_COLUMN: "bar column",
                COLUMN_SHEET_NAME: "Test Sheet",
                COLUMN_FILE: "Testfile",
            },
        ]

        expected_results = [
            None,
            None,
            {
                DATA_COLUMN_ITEM: "This is an item with options",
                DATA_COLUMN_SHEET: "Test Sheet",
                DATA_COLUMN_FILE: "Testfile",
                DATA_COLUMN_CATEGORIES: ["Header", "Subheader"],
                DATA_COLUMN_QUESTION: "This is a question",
                DATA_COLUMN_OPTIONS: ["Option A", "Option B"],
            },
            {
                DATA_COLUMN_ITEM: "Another item for same question",
                DATA_COLUMN_SHEET: "Test Sheet",
                DATA_COLUMN_FILE: "Testfile",
                DATA_COLUMN_CATEGORIES: ["Header", "Subheader"],
                DATA_COLUMN_QUESTION: "This is a question",
            },
        ]

        for row_dict, expected in zip(row_dicts, expected_results):
            row = pd.Series(row_dict)
            result = parser._parse_row(row)
            if isinstance(expected, dict):
                self.assertDictEqual(expected, result)
            else:
                self.assertEqual(expected, result)

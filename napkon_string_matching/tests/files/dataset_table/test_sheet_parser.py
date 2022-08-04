import unittest

import pandas as pd
from napkon_string_matching.constants import (
    DATA_COLUMN_CATEGORIES,
    DATA_COLUMN_FILE,
    DATA_COLUMN_IDENTIFIER,
    DATA_COLUMN_ITEM,
    DATA_COLUMN_OPTIONS,
    DATA_COLUMN_QUESTION,
    DATA_COLUMN_SHEET,
)
from napkon_string_matching.files.dataset_table import (
    DATASETTABLE_COLUMN_DB_COLUMN,
    DATASETTABLE_COLUMN_FILE,
    DATASETTABLE_COLUMN_ITEM,
    DATASETTABLE_COLUMN_OPTIONS,
    DATASETTABLE_COLUMN_QUESTION,
    DATASETTABLE_COLUMN_SHEET_NAME,
    DATASETTABLE_COLUMN_TYPE,
    DATASETTABLE_TYPE_HEADER,
    SheetParser,
)


class TestSheetParser(unittest.TestCase):
    def test_parse_row(self):
        parser = SheetParser()

        row_dicts = [
            {
                DATASETTABLE_COLUMN_TYPE: DATASETTABLE_TYPE_HEADER,
                DATASETTABLE_COLUMN_QUESTION: "Header",
                DATASETTABLE_COLUMN_ITEM: None,
                DATASETTABLE_COLUMN_DB_COLUMN: None,
                DATASETTABLE_COLUMN_SHEET_NAME: "Test Sheet",
                DATASETTABLE_COLUMN_FILE: "Testfile",
            },
            {
                DATASETTABLE_COLUMN_TYPE: "other",
                DATASETTABLE_COLUMN_QUESTION: "Subheader",
                DATASETTABLE_COLUMN_ITEM: None,
                DATASETTABLE_COLUMN_DB_COLUMN: None,
                DATASETTABLE_COLUMN_SHEET_NAME: "Test Sheet",
                DATASETTABLE_COLUMN_FILE: "Testfile",
            },
            {
                DATASETTABLE_COLUMN_TYPE: "QuestionGroup",
                DATASETTABLE_COLUMN_QUESTION: "This is a question",
                DATASETTABLE_COLUMN_ITEM: "This is an item with options",
                DATASETTABLE_COLUMN_OPTIONS: "Option A;Option B",
                DATASETTABLE_COLUMN_DB_COLUMN: "foo column",
                DATASETTABLE_COLUMN_SHEET_NAME: "Test Sheet",
                DATASETTABLE_COLUMN_FILE: "Testfile",
            },
            {
                DATASETTABLE_COLUMN_ITEM: "Another item for same question",
                DATASETTABLE_COLUMN_DB_COLUMN: "bar column",
                DATASETTABLE_COLUMN_SHEET_NAME: "Test Sheet",
                DATASETTABLE_COLUMN_FILE: "Testfile",
            },
        ]

        expected_results = [
            None,
            None,
            {
                DATA_COLUMN_IDENTIFIER: "Testfile#Test-Sheet#None",
                DATA_COLUMN_ITEM: "This is an item with options",
                DATA_COLUMN_SHEET: "Test Sheet",
                DATA_COLUMN_FILE: "Testfile",
                DATA_COLUMN_CATEGORIES: ["Header", "Subheader"],
                DATA_COLUMN_QUESTION: "This is a question",
                DATA_COLUMN_OPTIONS: ["Option A", "Option B"],
            },
            {
                DATA_COLUMN_IDENTIFIER: "Testfile#Test-Sheet#None",
                DATA_COLUMN_ITEM: "Another item for same question",
                DATA_COLUMN_SHEET: "Test Sheet",
                DATA_COLUMN_FILE: "Testfile",
                DATA_COLUMN_CATEGORIES: ["Header", "Subheader"],
                DATA_COLUMN_QUESTION: "This is a question",
                DATA_COLUMN_OPTIONS: None,
            },
        ]

        for row_dict, expected in zip(row_dicts, expected_results):
            row = pd.Series(row_dict)
            result = parser._parse_row(row)
            if isinstance(expected, dict):
                self.assertDictEqual(expected, result)
            else:
                self.assertEqual(expected, result)

import unittest
from pathlib import Path

import pandas as pd

from napkon_string_matching.tests import DISABLE_DB_TESTS, DISABLE_LOCAL_FILE_TESTS
from napkon_string_matching.types.comparable_data import ComparableColumns
from napkon_string_matching.types.dataset_table.dataset_table import (
    DATASETTABLE_COLUMN_DB_COLUMN,
    DATASETTABLE_COLUMN_FILE,
    DATASETTABLE_COLUMN_ITEM,
    DATASETTABLE_COLUMN_OPTIONS,
    DATASETTABLE_COLUMN_QUESTION,
    DATASETTABLE_COLUMN_SHEET_NAME,
    DATASETTABLE_COLUMN_TYPE,
    DATASETTABLE_TYPE_HEADER,
    DatasetTable,
    SheetParser,
)
from napkon_string_matching.types.questionnaire import Columns

TEST_DATA_DIR = "../napkon-string-matching-data/test/"


class TestDatasetTable(unittest.TestCase):
    @unittest.skipIf(DISABLE_LOCAL_FILE_TESTS, "local test file needs to be available")
    def test_read(self):
        file = Path(TEST_DATA_DIR + "suep_test.xlsx")
        result = DatasetTable.read_original_format(file)
        self.assertIsNotNone(result)

    @unittest.skipIf(
        DISABLE_DB_TESTS or DISABLE_LOCAL_FILE_TESTS,
        "requires active db contianer and local test file",
    )
    def test_add_terms_live(self):
        data = DatasetTable.read_original_format(TEST_DATA_DIR + "pop_test.xlsx")

        data.add_terms()
        self.assertIsNotNone(data.term)


class TestSheetParser(unittest.TestCase):
    def test_parse_row(self):
        row_dicts = [
            {
                DATASETTABLE_COLUMN_TYPE: DATASETTABLE_TYPE_HEADER,
                DATASETTABLE_COLUMN_QUESTION: "Header",
                DATASETTABLE_COLUMN_ITEM: None,
                DATASETTABLE_COLUMN_DB_COLUMN: None,
                DATASETTABLE_COLUMN_FILE: "Testfile",
            },
            {
                DATASETTABLE_COLUMN_TYPE: "emnpother",
                DATASETTABLE_COLUMN_QUESTION: "Subheader",
                DATASETTABLE_COLUMN_ITEM: None,
                DATASETTABLE_COLUMN_DB_COLUMN: None,
                DATASETTABLE_COLUMN_FILE: "Testfile",
            },
            {
                DATASETTABLE_COLUMN_TYPE: "QuestionGroup",
                DATASETTABLE_COLUMN_QUESTION: "This is a question",
                DATASETTABLE_COLUMN_ITEM: "This is an item with options",
                DATASETTABLE_COLUMN_OPTIONS: "Option A;Option B",
                DATASETTABLE_COLUMN_DB_COLUMN: "foo column",
                DATASETTABLE_COLUMN_FILE: "Testfile",
            },
            {
                DATASETTABLE_COLUMN_ITEM: "Another item for same question",
                DATASETTABLE_COLUMN_DB_COLUMN: "bar column",
                DATASETTABLE_COLUMN_FILE: "Testfile",
            },
        ]

        expected_results = [
            {
                ComparableColumns.IDENTIFIER.value: "emnpother#foo-column",
                Columns.UID.value: "Testfile#emnpother#foo-column#2",
                Columns.ITEM.value: "This is an item with options",
                Columns.SHEET.value: "Test_Sheet",
                Columns.FILE.value: "Testfile",
                Columns.HEADER.value: ["Header", "Subheader"],
                Columns.QUESTION.value: "This is a question",
                Columns.OPTIONS.value: ["Option A", "Option B"],
                Columns.VARIABLE.value: "foo column",
                Columns.PARAMETER.value: "Header:Subheader:This is a question:"
                + "This is an item with options",
                Columns.CATEGORY.value: [],
            },
            {
                ComparableColumns.IDENTIFIER.value: "emnpother#bar-column",
                Columns.UID.value: "Testfile#emnpother#bar-column#3",
                Columns.ITEM.value: "Another item for same question",
                Columns.SHEET.value: "Test_Sheet",
                Columns.FILE.value: "Testfile",
                Columns.HEADER.value: ["Header", "Subheader"],
                Columns.QUESTION.value: "This is a question",
                Columns.OPTIONS.value: None,
                Columns.VARIABLE.value: "bar column",
                Columns.PARAMETER.value: "Header:Subheader:This is a question:"
                + "Another item for same question",
                Columns.CATEGORY.value: [],
            },
        ]

        parser = SheetParser()
        input = pd.DataFrame(row_dicts)
        result = parser.parse_rows(input, sheet_name="Test Sheet")

        self.maxDiff = None
        for row, expected in zip(result.iterrows(), expected_results):
            _, row = row
            self.assertDictEqual(expected, row.to_dict())

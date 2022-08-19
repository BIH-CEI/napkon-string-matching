import unittest
from pathlib import Path

import pandas as pd
from napkon_string_matching.tests import DISABLE_LOCAL_FILE_TESTS
from napkon_string_matching.types.questionnaire import (
    DATASETTABLE_COLUMN_DB_COLUMN,
    DATASETTABLE_COLUMN_FILE,
    DATASETTABLE_COLUMN_ITEM,
    DATASETTABLE_COLUMN_OPTIONS,
    DATASETTABLE_COLUMN_QUESTION,
    DATASETTABLE_COLUMN_SHEET_NAME,
    DATASETTABLE_COLUMN_TYPE,
    DATASETTABLE_TYPE_HEADER,
    Columns,
    Questionnaire,
    SheetParser,
)


class TestQuestionnaire(unittest.TestCase):
    def test_read_write(self):
        quest = Questionnaire(
            {
                "Identifier": ["1", "2", "3"],
                "words": ["one", "two", "three"],
                "arrays": [[1, "one"], [2, "two"], [3, "three"]],
            },
        )

        file = Path("test_" + __name__ + ".json")
        if file.exists():
            file.unlink()

        quest.write_json(file)
        result = Questionnaire.read_json(file)

        file.unlink()

        self.assertDictEqual(quest.to_dict(), result.to_dict())

    @unittest.skipIf(DISABLE_LOCAL_FILE_TESTS, "local test file needs to be available")
    def test_read(self):
        file = Path("input/suep_test.xlsx")
        result = Questionnaire.read_dataset_table(file)
        self.assertIsNotNone(result)

    def test_parse_row(self):
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
            {
                Columns.IDENTIFIER.value: "Testfile#Test-Sheet#2",
                Columns.ITEM.value: "This is an item with options",
                Columns.SHEET.value: "Test Sheet",
                Columns.FILE.value: "Testfile",
                Columns.CATEGORIES.value: ["Header", "Subheader"],
                Columns.QUESTION.value: "This is a question",
                Columns.OPTIONS.value: ["Option A", "Option B"],
                Columns.VARIABLE.value: "foo column",
            },
            {
                Columns.IDENTIFIER.value: "Testfile#Test-Sheet#3",
                Columns.ITEM.value: "Another item for same question",
                Columns.SHEET.value: "Test Sheet",
                Columns.FILE.value: "Testfile",
                Columns.CATEGORIES.value: ["Header", "Subheader"],
                Columns.QUESTION.value: "This is a question",
                Columns.OPTIONS.value: None,
                Columns.VARIABLE.value: "bar column",
            },
        ]

        parser = SheetParser()
        input = pd.DataFrame(row_dicts)
        result = parser.parse_rows(input)

        for row, expected in zip(result.iterrows(), expected_results):
            _, row = row
            self.assertDictEqual(expected, row.to_dict())

import json
import unittest
from pathlib import Path

import pandas as pd
from napkon_string_matching.prepare.match_preparator import MatchPreparator
from napkon_string_matching.tests import DISABLE_DB_TESTS, DISABLE_LOCAL_FILE_TESTS
from napkon_string_matching.types.comparable_data import ComparableColumns
from napkon_string_matching.types.dataset_table.dataset_table import DatasetTable
from napkon_string_matching.types.questionnaire import Columns, Questionnaire


class TestMatchPreparator(unittest.TestCase):
    def setUp(self):
        config = {
            "terminology": {
                "mesh": {
                    "db": {
                        "host": "localhost",
                        "port": 5432,
                        "db": "mesh",
                        "user": "postgres",
                        "passwd": "meshterms",
                    }
                }
            }
        }

        self.preparator = MatchPreparator(config)

    @unittest.skipIf(DISABLE_DB_TESTS, "requires active db contianer")
    def test_load_terms(self):
        self.preparator.terminology_provider.initialize()
        self.assertIsNotNone(self.preparator.terminology_provider.synonyms)
        self.assertIsNotNone(self.preparator.terminology_provider.headings)

    def test_add_tokens(self):
        data_dir = Path("napkon_string_matching/tests/data")

        references = pd.DataFrame(json.loads((data_dir / "references.json").read_text()))
        headings = pd.DataFrame(json.loads((data_dir / "headings.json").read_text()))

        self.preparator.terminology_provider.providers[0]._synonyms = references
        self.preparator.terminology_provider.providers[0]._headings = headings

        data = Questionnaire(
            [
                {
                    Columns.SHEET.value: "Test Sheet",
                    Columns.FILE.value: "Testfile",
                    Columns.HEADER.value: None,
                    ComparableColumns.TERM.value: "Hatte Sie Dialyse oder sonstiges?".split(),
                },
            ]
        )

        self.preparator.add_tokens(data, 0.1, verbose=False, timeout=None)

        self.assertIsNotNone(data.tokens)
        self.assertIsNotNone(data.token_ids)
        self.assertIsNotNone(data.token_match)

        self.assertTrue(any(["Dialyse" in entry for entry in data.tokens[0]]))
        self.assertTrue(any(["Sonstiges" in entry for entry in data.tokens[0]]))

    def test_add_terms_and_tokens(self):
        data = Questionnaire(
            [
                {
                    Columns.ITEM.value: "Hatte Sie Dialyse oder sonstiges?",
                    Columns.SHEET.value: "Test Sheet",
                    Columns.FILE.value: "Testfile",
                    Columns.HEADER.value: None,
                    Columns.QUESTION.value: "Dialyse",
                }
            ]
        )

        data_dir = Path("napkon_string_matching/tests/data")

        references = pd.DataFrame(json.loads((data_dir / "references.json").read_text()))
        headings = pd.DataFrame(json.loads((data_dir / "headings.json").read_text()))

        self.preparator.terminology_provider.providers[0]._synonyms = references
        self.preparator.terminology_provider.providers[0]._headings = headings

        data.add_terms()
        self.preparator.add_tokens(data, 0.1, verbose=False, timeout=None)

        self.assertIsNotNone(data.tokens)
        self.assertIsNotNone(data.token_ids)
        self.assertIsNotNone(data.token_match)

        self.assertTrue(any(["Dialyse" in entry for entry in data.tokens[0]]))
        self.assertTrue(any(["Sonstiges" in entry for entry in data.tokens[0]]))

    @unittest.skipIf(
        DISABLE_DB_TESTS or DISABLE_LOCAL_FILE_TESTS,
        "takes long time and requires active db contianer and local test file",
    )
    def test_add_terms_and_tokens_live(self):
        data = DatasetTable.read_original_format("input/pop_test.xlsx")

        data = data[:100]

        data.add_terms()
        self.preparator.add_tokens(data, 90, verbose=False, timeout=None)

        self.assertIsNotNone(data.tokens)
        self.assertIsNotNone(data.token_ids)
        self.assertIsNotNone(data.token_match)

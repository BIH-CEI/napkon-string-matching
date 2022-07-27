import json
import unittest
from pathlib import Path

import pandas as pd
from napkon_string_matching.constants import (
    DATA_COLUMN_CATEGORIES,
    DATA_COLUMN_FILE,
    DATA_COLUMN_ITEM,
    DATA_COLUMN_QUESTION,
    DATA_COLUMN_SHEET,
    DATA_COLUMN_TERM,
    DATA_COLUMN_TOKEN_IDS,
    DATA_COLUMN_TOKEN_MATCH,
    DATA_COLUMN_TOKENS,
)
from napkon_string_matching.files.dataset_table import read
from napkon_string_matching.prepare import MatchPreparator
from napkon_string_matching.tests import (
    DISABLE_DB_TESTS,
    DISABLE_LOCAL_FILE_TESTS,
    DISABLE_LONG_LASTING_TESTS,
)


class TestMatchPreparator(unittest.TestCase):
    def setUp(self):
        dbConfig = {
            "host": "localhost",
            "port": 5432,
            "db": "mesh",
            "user": "postgres",
            "passwd": "meshterms",
        }

        self.preparator = MatchPreparator(dbConfig)
        self.test_file = Path("input/pop_test.xlsx")

    @unittest.skipIf(DISABLE_DB_TESTS, "requires active db contianer")
    def test_load_terms(self):
        self.preparator.load_terms()
        self.assertIsNotNone(self.preparator.terms)
        self.assertIsNotNone(self.preparator.headings)

    def test_add_terms(self):
        data = pd.DataFrame(
            [
                {
                    DATA_COLUMN_ITEM: "An item without categories",
                    DATA_COLUMN_SHEET: "Test Sheet",
                    DATA_COLUMN_FILE: "Testfile",
                    DATA_COLUMN_CATEGORIES: None,
                    DATA_COLUMN_QUESTION: "This is a question",
                },
                {
                    DATA_COLUMN_ITEM: "An item without categories 1",
                    DATA_COLUMN_SHEET: "Test Sheet",
                    DATA_COLUMN_FILE: "Testfile",
                    DATA_COLUMN_CATEGORIES: None,
                    DATA_COLUMN_QUESTION: "This is another question 1",
                },
            ]
        )

        self.preparator.add_terms(data, language="english")

        self.assertIn(DATA_COLUMN_TERM, data)
        self.assertEqual(2, len(data[DATA_COLUMN_TERM].values))
        self.assertEqual(
            "categories item question without", data[DATA_COLUMN_TERM].values[0]
        )
        self.assertEqual(
            "1 1 another categories item question without",
            data[DATA_COLUMN_TERM].values[1],
        )

    @unittest.skipIf(
        DISABLE_DB_TESTS or DISABLE_LOCAL_FILE_TESTS,
        "requires active db contianer and local test file",
    )
    def test_add_terms_live(self):
        data = read(self.test_file)

        self.preparator.add_terms(data)
        self.assertIn(DATA_COLUMN_TERM, data)

    def test_add_tokens_not_initialized(self):
        self.assertRaises(RuntimeError, self.preparator.add_tokens, None, 100)

    def test_add_tokens(self):
        data_dir = Path("napkon_string_matching/tests/prepare/data")

        references = pd.DataFrame(
            json.loads((data_dir / "references.json").read_text())
        )
        headings = pd.DataFrame(json.loads((data_dir / "headings.json").read_text()))

        self.preparator.terms = references
        self.preparator.headings = headings

        data = pd.DataFrame(
            [
                {
                    DATA_COLUMN_SHEET: "Test Sheet",
                    DATA_COLUMN_FILE: "Testfile",
                    DATA_COLUMN_CATEGORIES: None,
                    DATA_COLUMN_TERM: "Hatte Sie Dialyse oder sonstiges?",
                },
            ]
        )

        self.preparator.add_tokens(data, 80)

        self.assertIn(DATA_COLUMN_TOKENS, data)
        self.assertIn(DATA_COLUMN_TOKEN_IDS, data)
        self.assertIn(DATA_COLUMN_TOKEN_MATCH, data)

        self.assertIn("Dialyse", data[DATA_COLUMN_TOKENS][0])

    @unittest.skipIf(
        DISABLE_DB_TESTS or DISABLE_LOCAL_FILE_TESTS or DISABLE_LONG_LASTING_TESTS,
        "takes long time and requires active db contianer and local test file",
    )
    def test_add_terms_and_tokens_live(self):
        data = read(self.test_file)

        self.preparator.load_terms()
        self.preparator.add_terms(data)

        self.preparator.add_tokens(data, 90, verbose=False, timeout=None)

        self.assertIn(DATA_COLUMN_TOKENS, data)
        self.assertIn(DATA_COLUMN_TOKEN_IDS, data)
        self.assertIn(DATA_COLUMN_TOKEN_MATCH, data)

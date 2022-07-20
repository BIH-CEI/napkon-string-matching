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
)
from napkon_string_matching.prepare import MatchPreparator


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

    @unittest.skip("requires active db contianer")
    def test_load_terms(self):
        self.preparator.load_terms()
        self.assertIsNotNone(self.preparator.terms)
        self.assertIsNotNone(self.preparator.headings)

    def test_add_terms_and_token_not_initialized(self):
        self.assertRaises(RuntimeError, self.preparator.add_terms, None)

    def test_add_terms(self):
        data_dir = Path("napkon_string_matching/tests/prepare/data")

        references = pd.DataFrame(
            json.loads((data_dir / "references.json").read_text())
        )
        headings = pd.DataFrame(json.loads((data_dir / "headings.json").read_text()))

        self.preparator.terms = references
        self.preparator.headings = headings

        QUESTION = "This is another question"
        ITEM = "An item without categories"

        data = pd.DataFrame(
            [
                {
                    DATA_COLUMN_ITEM: ITEM,
                    DATA_COLUMN_SHEET: "Test Sheet",
                    DATA_COLUMN_FILE: "Testfile",
                    DATA_COLUMN_CATEGORIES: None,
                    DATA_COLUMN_QUESTION: QUESTION,
                },
            ]
        )

        self.preparator.add_terms(data)

        self.assertIn(DATA_COLUMN_TERM, data)
        self.assertEqual(1, len(data[DATA_COLUMN_TERM].values))
        self.assertEqual(f"{QUESTION} {ITEM}", data[DATA_COLUMN_TERM].values[0])
